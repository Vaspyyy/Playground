"""Mouse Magic lifecycle and read-only KWin bridge."""
import json
import math
from pathlib import Path
import time
from gi.repository import Gdk, Gio, GLib, GtkLayerShell
import cairo
from mouse_core import World

PATH = '/io/github/Playground/Pointer'
IFACE = 'io.github.Playground.Pointer'
SCRIPT = 'playground-pointer'
EFFECT = 'playground_mouse'


class MouseMagic:
    def __init__(self, app, overlay_class):
        self.app = app
        self.world = World()
        self.overlays = []
        self.timer = 0
        self.last_frame = 0
        self.previous = time.monotonic()
        self.fullscreen = None
        self.locked = True
        self.native = False
        self.script = False
        self.owner = None
        self.status = 'Off. Enable Mouse Magic to start.'
        self.stale_reported = False
        self.bus = app.get_dbus_connection()
        info = Gio.DBusNodeInfo.new_for_xml('<node><interface name="'+IFACE+'"><method name="Frame"><arg type="s" direction="in"/></method></interface></node>')
        self.registration = self.bus.register_object(PATH, info.interfaces[0], self.receive, None, None)
        self.lock_signal = self.bus.signal_subscribe('org.freedesktop.ScreenSaver',
            'org.freedesktop.ScreenSaver', 'ActiveChanged', '/ScreenSaver', None,
            Gio.DBusSignalFlags.NONE, self.lock_changed)
        self.name_signal = self.bus.signal_subscribe('org.freedesktop.DBus',
            'org.freedesktop.DBus', 'NameOwnerChanged', '/org/freedesktop/DBus', 'org.kde.KWin',
            Gio.DBusSignalFlags.NONE, self.kwin_changed)
        runtime = self
        class MouseWindow(overlay_class):
            def __init__(self, monitor):
                self.monitor_geometry = monitor.get_geometry()
                super().__init__(app, monitor)
                self.set_title('Playground Mouse Magic overlay')
                GtkLayerShell.set_namespace(self, 'playground-mouse')
            def draw(self, widget, cr):
                cr.set_operator(cairo.OPERATOR_SOURCE)
                cr.set_source_rgba(0,0,0,0); cr.paint()
                cr.set_operator(cairo.OPERATOR_OVER)
                g = self.monitor_geometry
                cr.translate(-g.x,-g.y)
                runtime.world.draw(cr,time.monotonic(),app.settings['mouse'],app.settings['palette'])
                return True
        self.window_class = MouseWindow
        display = Gdk.Display.get_default()
        self.monitor_signals = [display.connect('monitor-added', self.rebuild),
                                display.connect('monitor-removed', self.rebuild)]
        self.rebuild()

    def call(self, path, interface, method, args=None, service='org.kde.KWin'):
        return self.bus.call_sync(service,path,interface,method,args,None,
                                  Gio.DBusCallFlags.NO_AUTO_START,1500,None)

    def set_status(self, text):
        self.status = text
        if self.app.window:
            self.app.window.mouse_panel.status.set_text(text)

    def reconnect(self):
        self.stop()
        if not self.app.settings['mouse']['enabled']:
            return
        try:
            self.owner = self.call('/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner',
                GLib.Variant('(s)',('org.kde.KWin',)), 'org.freedesktop.DBus').unpack()[0]
            try:
                self.locked = self.call('/ScreenSaver','org.freedesktop.ScreenSaver','GetActive',
                    service='org.freedesktop.ScreenSaver').unpack()[0]
            except GLib.Error:
                self.locked = True
            # Remove our own leftovers after an app crash before starting a fresh bridge.
            self.call('/Effects','org.kde.kwin.Effects','unloadEffect',GLib.Variant('(s)',(EFFECT,)))
            self.call('/Scripting','org.kde.kwin.Scripting','unloadScript',GLib.Variant('(s)',(SCRIPT,)))
            self.native = self.call('/Effects','org.kde.kwin.Effects','loadEffect',
                                      GLib.Variant('(s)',(EFFECT,))).unpack()[0]
            if self.native:
                self.set_status('Connected to KDE · all effects ready, including click ripples.')
            else:
                source = str(Path(__file__).with_name('pointer.js'))
                script_id = self.call('/Scripting','org.kde.kwin.Scripting','loadScript',
                    GLib.Variant('(ss)',(source,SCRIPT))).unpack()[0]
                if script_id < 0:
                    raise RuntimeError('KWin could not load the cursor script')
                self.script = True
                self.call('/Scripting/Script'+str(script_id),'org.kde.kwin.Script','run')
                self.set_status('Cursor effects ready. Click ripples need the KDE click helper below.')
            self.previous = time.monotonic()
            self.last_frame = self.previous
            self.stale_reported = False
            self.timer = GLib.timeout_add(16,self.tick)
        except (GLib.Error, RuntimeError) as error:
            self.stop()
            self.set_status('Could not connect to KDE: '+str(error)+' · Try Reconnect.')

    def receive(self, connection, sender, path, interface, method, parameters, invocation):
        if sender != self.owner or not self.app.settings['mouse']['enabled']:
            invocation.return_dbus_error(IFACE+'.Inactive','Pointer bridge is inactive')
            return
        try:
            payload = parameters.unpack()[0]
            if len(payload)>2048:
                raise ValueError('Frame too large')
            data = json.loads(payload)
            x,y = data['x'],data['y']
            if not all(type(v) in (int,float) and math.isfinite(v) for v in (x,y)):
                raise ValueError('Invalid coordinates')
            if self.native:
                self.locked = bool(data.get('locked',True))
            rect = data.get('fullscreen')
            self.fullscreen = rect if isinstance(rect,list) and len(rect)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in rect) else None
            now = time.monotonic()
            self.last_frame = now
            if not self.locked:
                self.world.pointer(x,y,bool(data.get('pressed')) if self.native else False,
                                   now,self.app.settings['mouse'])
            invocation.return_value(None)
        except (ValueError, KeyError, TypeError):
            invocation.return_dbus_error(IFACE+'.Invalid','Invalid pointer frame')

    def lock_changed(self, connection, sender, path, interface, signal, parameters):
        self.locked = parameters.unpack()[0]
        self.world.reset()
        if self.locked:
            for overlay in self.overlays:
                overlay.hide()

    def kwin_changed(self, *args):
        # Re-resolve the compositor's unique bus name after a compositor restart.
        if self.app.settings['mouse']['enabled']:
            GLib.idle_add(self.reconnect)

    def rebuild(self, *args):
        for overlay in self.overlays:
            overlay.destroy()
        display = Gdk.Display.get_default()
        monitors = [display.get_monitor(i) for i in range(display.get_n_monitors())]
        self.overlays = [self.window_class(m) for m in monitors]
        self.world.reset([(g.x,g.y,g.width,g.height) for g in (m.get_geometry() for m in monitors)])

    def tick(self):
        now = time.monotonic()
        settings = self.app.settings['mouse']
        fresh = now-self.last_frame < 2
        if not fresh and not self.stale_reported:
            self.stale_reported = True
            self.set_status('Cursor connection stopped. Press Reconnect to try again.')
        elif fresh and self.stale_reported:
            self.stale_reported = False
            self.set_status('Connected to KDE · all effects ready, including click ripples.' if self.native
                            else 'Cursor effects ready. Click ripples need the KDE click helper below.')
        visible = not self.locked and fresh
        self.world.step(now, now-self.previous, settings)
        self.previous = now
        for overlay in self.overlays:
            g = overlay.monitor_geometry
            blocked = False
            if not settings['fullscreen'] and self.fullscreen:
                x,y,w,h = self.fullscreen
                blocked = x<g.x+g.width and x+w>g.x and y<g.y+g.height and y+h>g.y
            if visible and not blocked:
                if not overlay.get_visible():
                    overlay.show_all()
                overlay.queue_draw()
            else:
                overlay.hide()
        return True

    def stop(self):
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0
        for overlay in self.overlays:
            overlay.hide()
        for active,path,interface,method,name in [
            (self.native,'/Effects','org.kde.kwin.Effects','unloadEffect',EFFECT),
            (self.script,'/Scripting','org.kde.kwin.Scripting','unloadScript',SCRIPT)]:
            if active:
                try:
                    self.call(path,interface,method,GLib.Variant('(s)',(name,)))
                except GLib.Error:
                    pass
        self.native = self.script = False
        self.owner = None
        self.last_frame = 0
        self.world.reset()
        self.set_status('Off. Enable Mouse Magic to start.')

    def close(self):
        self.stop()
        self.bus.unregister_object(self.registration)
        self.bus.signal_unsubscribe(self.lock_signal)
        self.bus.signal_unsubscribe(self.name_signal)
        for signal in self.monitor_signals:
            Gdk.Display.get_default().disconnect(signal)
        for overlay in self.overlays:
            overlay.destroy()
