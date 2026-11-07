#!/usr/bin/python3
"""Edgeglow: a passive notification glow for KDE Plasma Wayland."""
import os
import sys
import time
import random
from pathlib import Path

os.environ['GDK_BACKEND'] = 'wayland'
try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import Gtk, Gdk, Gio, GLib, GtkLayerShell
    import cairo
except (ImportError, ValueError) as error:
    sys.exit('Missing desktop dependencies. Run ./install.sh from the extracted Edgeglow folder.\n' + str(error))

from core import DEFAULTS, EFFECTS, PALETTES, Pulse, load, save
from render import draw_effect, color as palette_color
from modules import ModuleController
from playground_ui import PlaygroundWindow
from ui_kit import SPECS, Choice, button, caption, group, hero, label, page, rounded, row, slider, styled, switch
from mouse_magic import MouseMagic

CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
SETTINGS = CONFIG / 'edgeglow' / 'settings.json'
AUTOSTART = CONFIG / 'autostart' / 'io.github.edgeglow.desktop'
APP_ID = 'io.github.edgeglow'
# Plasma matches native Wayland windows to their desktop-file identity.
GLib.set_prgname(APP_ID)
GLib.set_application_name('Playground')
Gdk.set_program_class(APP_ID)


class NotificationMonitor:
    """Dedicated read-only monitor connection; never takes the notification name."""
    def __init__(self, callback, status):
        self.callback, self.status = callback, status
        self.connection = None
        self.stopped = False
        self.retry = 0
        self.connect()

    def connect(self):
        self.retry = 0
        if self.stopped:
            return False
        try:
            address = Gio.dbus_address_get_for_bus_sync(Gio.BusType.SESSION, None)
            connection = Gio.DBusConnection.new_for_address_sync(
                address, Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT |
                Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
            connection.set_exit_on_close(False)
            connection.add_filter(self.filter_message, None)
            rule = "type='method_call',interface='org.freedesktop.Notifications',member='Notify',path='/org/freedesktop/Notifications'"
            connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                'org.freedesktop.DBus.Monitoring', 'BecomeMonitor',
                GLib.Variant('(asu)', ([rule], 0)), None,
                Gio.DBusCallFlags.NONE, 5000, None)
            self.connection = connection
            connection.connect('closed', self.closed)
            self.status('Listening for notifications, including during Do Not Disturb')
        except GLib.Error as error:
            if 'connection' in locals() and not connection.is_closed():
                connection.close_sync(None)
            self.status('Notification listener unavailable: ' + error.message)
            self.retry = GLib.timeout_add_seconds(15, self.connect)
        return False

    def filter_message(self, connection, message, incoming, user_data):
        if incoming and message.get_message_type() == Gio.DBusMessageType.METHOD_CALL:
            if (message.get_interface() == 'org.freedesktop.Notifications'
                    and message.get_member() == 'Notify'
                    and message.get_path() == '/org/freedesktop/Notifications'):
                # Read headers only. No notification text is parsed or retained.
                GLib.idle_add(self.callback, time.monotonic())
            # A monitor must never send automatic replies to observed method calls.
            return None
        return message

    def closed(self, connection, vanished, error):
        self.connection = None
        if not self.stopped:
            self.status('Notification connection lost. Reconnecting…')
            if not self.retry:
                self.retry = GLib.timeout_add_seconds(5, self.connect)

    def stop(self):
        self.stopped = True
        if self.retry:
            GLib.source_remove(self.retry)
        if self.connection and not self.connection.is_closed():
            self.connection.close_sync(None)


class GlowWindow(Gtk.Window):
    def __init__(self, app, monitor):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.owner = app
        self.effect_surface = None
        self.set_title('Edgeglow overlay')
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_accept_focus(False)
        self.set_focus_on_map(False)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, 'edgeglow')
        GtkLayerShell.set_monitor(self, monitor)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        # -1 allows the overlay to cover panel-reserved areas too.
        GtkLayerShell.set_exclusive_zone(self, -1)
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                     GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, edge, True)
        self.connect('realize', self.click_through)
        self.connect('map', self.click_through)
        self.connect('draw', self.draw)
        style = Gtk.CssProvider()
        style.load_from_data(b'window { background-color: transparent; background-image: none; box-shadow: none; }')
        self.get_style_context().add_provider(style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)

    def click_through(self, *args):
        self.input_shape_combine_region(cairo.Region())
        window = self.get_window()
        if window:
            window.set_pass_through(True)

    def draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        width, height = self.get_allocated_width(), self.get_allocated_height()
        # Soft light needs no full-resolution intermediate. Bound raster work on 4K displays.
        scale = min(1.0, 960 / max(width, height))
        rw, rh = max(1, round(width*scale)), max(1, round(height*scale))
        if self.effect_surface is None or self.effect_surface.get_width() != rw or self.effect_surface.get_height() != rh:
            self.effect_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, rw, rh)
        effect_cr = cairo.Context(self.effect_surface)
        effect_cr.set_operator(cairo.OPERATOR_SOURCE)
        effect_cr.set_source_rgba(0, 0, 0, 0)
        effect_cr.paint()
        effect_cr.set_operator(cairo.OPERATOR_OVER)
        effect_cr.scale(rw/width, rh/height)
        draw_effect(effect_cr, width, height, self.owner.settings, self.owner.effect,
                    self.owner.frame_elapsed, self.owner.frame_opacity, self.owner.seed)
        cr.save()
        cr.scale(width/rw, height/rh)
        cr.set_source_surface(self.effect_surface, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint()
        cr.restore()
        return True


class PaletteSwatch(Gtk.DrawingArea):
    def __init__(self, palette):
        super().__init__()
        self.palette = palette
        self.set_size_request(54, 26)
        self.connect('draw', self.draw)

    def draw(self, widget, cr):
        width, height = self.get_allocated_width(), self.get_allocated_height()
        gradient = cairo.LinearGradient(0, 0, width, 0)
        for i in range(13):
            gradient.add_color_stop_rgb(i/12, *palette_color(self.palette, i/12))
        rounded(cr, 0, 0, width, height, 9)
        cr.set_source(gradient)
        cr.fill()
        return True


def swatch(palette):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    box.pack_start(PaletteSwatch(palette), False, False, 0)
    name = Gtk.Label(label=palette.title())
    box.pack_start(name, False, False, 0)
    return box


class GlowPreview(Gtk.DrawingArea):
    """A small desktop that loops your favorite effects with the current look."""
    SLOT = 4.0

    def __init__(self, app):
        super().__init__()
        self.owner = app
        self.tick_id = 0
        self.started = time.monotonic()
        self.drawn = 0
        self.set_size_request(-1, 170)
        self.connect('draw', self.draw)
        self.connect('map', self.start)
        self.connect('unmap', self.stop)

    def start(self, *args):
        # Frame-clock ticks pause on their own while the compositor hides the window.
        if not self.tick_id:
            self.started = time.monotonic()
            self.tick_id = self.add_tick_callback(self.tick)

    def stop(self, *args):
        if self.tick_id:
            self.remove_tick_callback(self.tick_id)
            self.tick_id = 0

    def tick(self, widget, clock):
        now = time.monotonic()
        if now - self.drawn >= 1/40:
            self.drawn = now
            self.queue_draw()
        return True

    def draw(self, widget, cr):
        width, height = self.get_allocated_width(), self.get_allocated_height()
        favorites = self.owner.settings['favorites']
        elapsed = time.monotonic() - self.started
        slot = int(elapsed // self.SLOT)
        effect = favorites[slot % len(favorites)]
        local = elapsed % self.SLOT
        fade = max(0.0, min(1.0, local/.4, (self.SLOT-local)/.6))
        rounded(cr, 0, 0, width, height, 18)
        cr.clip()
        backdrop = cairo.LinearGradient(0, 0, 0, height)
        backdrop.add_color_stop_rgb(0, .19, .16, .24)
        backdrop.add_color_stop_rgb(1, .11, .10, .15)
        cr.set_source(backdrop)
        cr.paint()
        # A hint of a desktop: two windows and a panel.
        cr.set_source_rgba(1, 1, 1, .045)
        rounded(cr, width*.12, height*.18, width*.36, height*.5, 8)
        cr.fill()
        rounded(cr, width*.54, height*.3, width*.3, height*.4, 8)
        cr.fill()
        cr.rectangle(0, height-18, width, 18)
        cr.fill()
        caption(widget, cr, effect.title(), 16, height-44)
        # Drawn at a typical monitor scale so glow width reads as it will on screen.
        scale = width/960
        cr.scale(scale, scale)
        draw_effect(cr, 960, height/scale, self.owner.settings, effect, elapsed, fade*fade*(3-2*fade), slot)
        return True


class EdgeglowPanel(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.owner = app
        spec = SPECS['edgeglow']
        self.scroller, box = page(spec)
        self.pack_start(self.scroller, True, True, 0)
        self.enabled_switch = switch(app.settings['enabled'])
        self.enabled_switch.connect('notify::active', self.toggle, 'enabled')
        box.pack_start(hero(spec, 'A little color, right when something happens.', self.enabled_switch), False, False, 0)
        self.preview = GlowPreview(app)
        box.pack_start(self.preview, False, False, 0)

        effects = Gtk.Box(spacing=8)
        self.favorites = {}
        for effect in EFFECTS:
            chip = styled(Gtk.ToggleButton(label=effect.title()), 'pg-chip')
            chip.set_active(effect in app.settings['favorites'])
            chip.connect('toggled', self.favorite_changed, effect)
            effects.pack_start(chip, False, False, 0)
            self.favorites[effect] = chip
        box.pack_start(group('Favorite effects', row(None, effects, 'Each notification plays one of these at random.',
                                                     stacked=True)), False, False, 0)

        self.palette = Choice([(palette, swatch(palette)) for palette in PALETTES], kind='swatches', spacing=4)
        self.palette.set_active_id(app.settings['palette'])
        self.palette.connect('changed', self.palette_changed)
        box.pack_start(group('Color palette', row(None, self.palette, stacked=True)), False, False, 0)

        sizes = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        self.controls = {}
        rows = []
        for key, title, hint, low, high, step, digits in [
                ('chaos', 'Chaos', 'subtle → ridiculous', 0, 100, 1, 0),
                ('width', 'Glow width', 'logical pixels', 8, 120, 1, 0),
                ('brightness', 'Brightness', 'percent', 5, 100, 1, 0),
                ('speed', 'Flow speed', 'laps per second', .02, 1, .01, 2),
                ('duration', 'Duration', 'seconds per glow', .5, 10, .1, 1)]:
            scale = slider(low, high, step, digits, app.settings[key])
            scale.connect('value-changed', self.change, key)
            self.controls[key] = scale
            rows.append(row(title, scale, hint, size_group=sizes))
        self.reset_button = button('Reset look', 'pg-link', on_click=self.reset)
        box.pack_start(group('Look', *rows, action=self.reset_button), False, False, 0)

        self.continuous_switch = switch()
        self.continuous_switch.connect('notify::active', self.continuous_changed)
        self.effect_label = label('Preview is off. Notifications still use your favorites.')
        self.try_button = button('Play', on_click=lambda *_: app.try_effect())
        box.pack_start(group('On your screen',
                             row('Continuous preview', self.continuous_switch, self.effect_label),
                             row('Try an effect', self.try_button, 'Plays one of your favorites, the way a notification would.')),
                       False, False, 0)

        note = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6), 'pg-note')
        self.status = label(app.status_text, 'pg-secondary', 'pg-small', wrap=True)
        self.status.set_max_width_chars(65)
        self.status.set_selectable(True)
        note.pack_start(self.status, False, False, 0)
        note.pack_start(label('All monitors · Visible over fullscreen apps · Glows during Do Not Disturb · '
                              'Extra arrivals are ignored while glowing', 'pg-muted', 'pg-small', wrap=True), False, False, 0)
        box.pack_start(note, False, False, 0)

    def on_close(self, *args):
        self.continuous_switch.set_active(False)
        self.hide()
        return True

    def favorite_changed(self, button, effect):
        selected = [key for key, control in self.favorites.items() if control.get_active()]
        if not selected:
            button.set_active(True)
            return
        self.owner.settings['favorites'] = selected
        self.owner.save_settings()
        if self.owner.continuous and self.owner.effect not in selected:
            self.owner.pick_effect()

    def palette_changed(self, combo):
        self.owner.settings['palette'] = combo.get_active_id()
        self.owner.save_settings()

    def continuous_changed(self, switch, param):
        self.owner.set_continuous(switch.get_active())

    def change(self, scale, key):
        self.owner.settings[key] = scale.get_value()
        self.owner.save_settings()

    def toggle(self, switch, param, key):
        if key == 'autostart':
            try:
                if switch.get_active():
                    AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
                    AUTOSTART.write_text(desktop_entry('--background'))
                else:
                    AUTOSTART.unlink(missing_ok=True)
            except OSError as error:
                self.owner.set_status('Could not update login startup: ' + str(error))
        else:
            self.owner.set_module_enabled(switch.get_active())

    def reset(self, *args):
        for key, control in self.controls.items():
            control.set_value(DEFAULTS[key])
        self.palette.set_active_id(DEFAULTS['palette'])


def desktop_entry(argument=''):
    from install import desktop
    return desktop(argument)



class Edgeglow(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.settings = load(SETTINGS)
        self.modules = ModuleController()
        self.modules.register('edgeglow', self.apply_edgeglow_enabled, self.settings['enabled'])
        self.modules.register('mouse', self.apply_mouse_enabled, self.settings['mouse']['enabled'])
        self.mouse = None
        self.pulse = Pulse()
        self.continuous = False
        self.preview_start = 0
        self.effect = 'classic'
        self.seed = 0
        self.frame_elapsed = 0
        self.frame_opacity = 0
        self.overlays = []
        self.window = None
        self.monitor = None
        self.timer = 0
        self.status_text = 'Starting notification listener…'

    def do_startup(self):
        Gtk.Application.do_startup(self)
        Gtk.Window.set_default_icon_name(APP_ID)
        from install import TARGET, refresh_desktop_integration
        if Path(__file__).resolve().parent == TARGET.resolve():
            try:
                refresh_desktop_integration()
            except OSError as error:
                print('Could not refresh Playground launcher/icon: '+str(error), flush=True)
        self.hold()
        Gtk.Settings.get_default().set_property('gtk-application-prefer-dark-theme', True)
        self.supported = GtkLayerShell.is_supported()
        if self.supported:
            display = Gdk.Display.get_default()
            display.connect('monitor-added', self.rebuild)
            display.connect('monitor-removed', self.rebuild)
            self.rebuild()
            self.monitor = NotificationMonitor(self.trigger, self.set_status)
            self.mouse = MouseMagic(self, GlowWindow)
            if self.settings['mouse']['enabled']:
                self.mouse.reconnect()
        else:
            self.set_status('Wayland layer shell is unavailable. Run this in your KDE Plasma Wayland session.')

    def do_command_line(self, command):
        args = command.get_arguments()[1:]
        if '--quit' in args:
            self.quit()
        elif '--preview' in args:
            self.trigger(time.monotonic(), True)
        elif '--background' not in args or not self.supported:
            self.do_activate()
        if '--update-ready' in args and self.window is not None:
            marker = Path(args[args.index('--update-ready') + 1])
            GLib.idle_add(lambda: marker.write_text('ready') and False)
        return 0

    def do_activate(self):
        if not self.window:
            self.window = PlaygroundWindow(self, EdgeglowPanel, AUTOSTART, desktop_entry)
        self.window.show_all()
        self.window.present()

    def apply_edgeglow_enabled(self, enabled):
        self.settings['enabled'] = enabled
        if not enabled:
            self.set_continuous(False)
            if self.window:
                self.window.continuous_switch.set_active(False)
        self.save_settings()

    def apply_mouse_enabled(self, enabled):
        self.settings['mouse']['enabled'] = enabled
        self.save_settings()
        if self.mouse:
            if enabled:
                self.mouse.reconnect()
            else:
                self.mouse.stop()

    def set_module_enabled(self, enabled, key='edgeglow'):
        self.modules.set_enabled(key, enabled)
        if self.window:
            self.window.sync_modules()

    def save_settings(self):
        try:
            save(SETTINGS, self.settings)
        except OSError as error:
            self.set_status('Could not save settings: ' + str(error))

    def set_status(self, text):
        self.status_text = text
        if self.window:
            self.window.status.set_text(text)
        print(text, flush=True)

    def rebuild(self, *args):
        for overlay in self.overlays:
            overlay.destroy()
        display = Gdk.Display.get_default()
        self.overlays = [GlowWindow(self, display.get_monitor(i)) for i in range(display.get_n_monitors())]
        if self.continuous or self.pulse.active(time.monotonic()):
            for overlay in self.overlays:
                overlay.show_all()

    def trigger(self, received_at=None, preview=False):
        if self.continuous:
            return False
        if not self.supported or (not preview and not self.settings['enabled']):
            return False
        now = time.monotonic()
        # Arrival timestamps prevent queued notifications replaying after a busy frame.
        if received_at is not None and received_at < self.pulse.start + self.pulse.duration:
            return False
        if self.pulse.trigger(now, self.settings['duration']):
            self.pick_effect()
            self.frame_elapsed, self.frame_opacity = 0, 0
            for overlay in self.overlays:
                overlay.show_all()
            if not self.timer:
                self.timer = GLib.timeout_add(16, self.tick)
        return False

    def pick_effect(self):
        self.effect = random.choice(self.settings['favorites'])
        self.seed = random.randrange(2**30)
        if self.window:
            self.window.effect_label.set_text('Playing: ' + self.effect.title() + ' · Adjust any slider live')

    def try_effect(self):
        if self.continuous:
            self.pick_effect()
            self.preview_start = time.monotonic()
        else:
            self.trigger(time.monotonic(), True)

    def set_continuous(self, active):
        self.continuous = active and self.supported
        if self.continuous:
            self.pick_effect()
            self.preview_start = time.monotonic()
            self.frame_elapsed, self.frame_opacity = 0, 1
            for overlay in self.overlays:
                overlay.show_all()
            if not self.timer:
                self.timer = GLib.timeout_add(16, self.tick)
        else:
            self.pulse.start = -float('inf')
            if self.timer:
                GLib.source_remove(self.timer)
                self.timer = 0
            for overlay in self.overlays:
                overlay.hide()
            if self.window:
                self.window.effect_label.set_text('Preview is off. Notifications still use your favorites.')

    def tick(self):
        now = time.monotonic()
        self.frame_elapsed = now - (self.preview_start if self.continuous else self.pulse.start)
        self.frame_opacity = 1 if self.continuous else self.pulse.opacity(now)
        if not self.continuous and not self.pulse.active(now):
            for overlay in self.overlays:
                overlay.hide()
            self.timer = 0
            return False
        for overlay in self.overlays:
            overlay.queue_draw()
        return True

    def do_shutdown(self):
        if self.mouse:
            self.mouse.close()
        if self.timer:
            GLib.source_remove(self.timer)
        if self.monitor:
            self.monitor.stop()
        for overlay in self.overlays:
            overlay.destroy()
        Gtk.Application.do_shutdown(self)


if __name__ == '__main__':
    sys.exit(Edgeglow().run(sys.argv))
