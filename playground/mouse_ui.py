"""Mouse Magic controls and an interactive local preview."""
import shlex
import shutil
import subprocess
import time
from pathlib import Path
import cairo
from gi.repository import Gtk, Gdk, GLib
from mouse_core import PRESETS, World
from ui_kit import SPECS, Choice, button, caption, group, hero, label, page, rounded, row, slider, switch


class MousePanel(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.syncing = False
        spec = SPECS['mouse']
        self.scroller, box = page(spec)
        self.pack_start(self.scroller, True, True, 0)
        self.enabled_switch = switch(app.settings['mouse']['enabled'])
        self.enabled_switch.connect('notify::active', lambda s, *_: app.set_module_enabled(s.get_active(), 'mouse'))
        box.pack_start(hero(spec, 'A little company for your cursor. Colors follow Edgeglow’s palette.',
                            self.enabled_switch), False, False, 0)

        self.preview = Gtk.DrawingArea()
        self.preview.set_size_request(-1, 190)
        self.preview.set_tooltip_text('Move and click here to try your mix')
        self.preview.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK)
        self.preview.connect('draw', self.draw_preview)
        self.preview.connect('motion-notify-event', self.preview_pointer, False)
        self.preview.connect('button-press-event', self.preview_pointer, True)
        self.preview.connect('map', self.preview_start)
        self.preview.connect('unmap', self.preview_stop)
        self.preview.connect('destroy', self.preview_stop)
        self.preview.connect('size-allocate', self.preview_resize)
        self.world = World(42)
        self.preview_timer = 0
        self.previous = time.monotonic()
        box.pack_start(self.preview, False, False, 0)

        self.presets = Choice([('custom', 'Custom mix')]+[(name, name) for name in PRESETS])
        self.presets.set_active_id('custom')
        self.presets.connect('changed', self.preset_changed)
        box.pack_start(group('Start with a preset', row(None, self.presets, stacked=True)), False, False, 0)

        self.toggles = {}
        rows = []
        for key, title, hint in [
                ('ribbon', 'Flowing comet ribbon', None),
                ('dust', 'Sparks & fairy dust', None),
                ('ripples', 'Click ripples', 'Ripples on desktop clicks need the click helper below.'),
                ('field', 'Scattered particles', None),
                ('idle', 'Small cloud while the cursor rests', None)]:
            toggle = switch(app.settings['mouse'][key])
            toggle.connect('notify::active', lambda s, p, k=key: self.change(k, s.get_active()))
            self.toggles[key] = toggle
            rows.append(row(title, toggle, hint))
        box.pack_start(group('Effects', *rows), False, False, 0)

        self.reaction = Choice([('swirl', 'Swirl'), ('scatter', 'Scatter'), ('attract', 'Attract')], kind='segmented')
        self.reaction.set_active_id(app.settings['mouse']['reaction'])
        self.reaction.connect('changed', lambda c: self.change('reaction', c.get_active_id()))
        fullscreen = switch(app.settings['mouse']['fullscreen'])
        fullscreen.connect('notify::active', lambda s, p: self.change('fullscreen', s.get_active()))
        self.toggles['fullscreen'] = fullscreen
        sizes = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        self.controls = {}
        feel = []
        for key, title, hint in [('motion', 'Motion', 'gentle → wild'), ('density', 'Particle density', None),
                                 ('brightness', 'Brightness', None)]:
            scale = slider(0, 100, 1, 0, app.settings['mouse'][key])
            scale.connect('value-changed', lambda s, k=key: self.change(k, s.get_value()))
            self.controls[key] = scale
            feel.append(row(title, scale, hint, size_group=sizes))
        box.pack_start(group('Feel', *feel,
                             row('When particles meet your cursor', self.reaction, 'Attract pulls them in, then lets them drift.'),
                             row('Show over fullscreen games & videos', fullscreen)), False, False, 0)

        self.status = label(app.mouse.status if app.mouse else 'Desktop effects require KDE Plasma Wayland.')
        self.status.set_max_width_chars(55)
        self.status.set_selectable(True)
        actions = Gtk.Box(spacing=8)
        actions.pack_start(button('Reconnect', on_click=lambda *_: app.mouse.reconnect() if app.mouse else None), False, False, 0)
        self.setup_button = button('Set up click helper…', on_click=self.setup_helper)
        actions.pack_start(self.setup_button, False, False, 0)
        box.pack_start(group('Connection', row('Status', None, self.status),
                             row(None, actions, 'Click helper setup opens a terminal and asks for administrator '
                                 'authentication. Cursor effects work without it. Re-run setup after a KDE upgrade if clicks stop.',
                                 stacked=True)), False, False, 0)

    def change(self,key,value):
        if self.syncing:
            return
        self.app.settings['mouse'][key] = value
        self.presets.set_active_id('custom')
        self.app.save_settings()

    def preset_changed(self,combo):
        preset = PRESETS.get(combo.get_active_id())
        if not preset:
            return
        self.app.settings['mouse'].update(preset)
        self.syncing = True
        for key,control in self.toggles.items():
            control.set_active(self.app.settings['mouse'][key])
        for key,control in self.controls.items():
            control.set_value(self.app.settings['mouse'][key])
        self.reaction.set_active_id(self.app.settings['mouse']['reaction'])
        self.syncing = False
        self.app.save_settings()

    def preview_resize(self,widget,allocation):
        self.world.reset([(0,0,allocation.width,allocation.height)])

    def preview_pointer(self,widget,event,pressed):
        self.world.pointer(event.x,event.y,pressed,time.monotonic(),self.app.settings['mouse'])
        return True

    def preview_start(self,*args):
        self.previous = time.monotonic()
        if not self.preview_timer:
            self.preview_timer = GLib.timeout_add(16,self.preview_tick)

    def preview_stop(self,*args):
        if self.preview_timer:
            GLib.source_remove(self.preview_timer)
            self.preview_timer = 0

    def preview_tick(self):
        now = time.monotonic()
        self.world.step(now,now-self.previous,self.app.settings['mouse'])
        self.previous = now
        self.preview.queue_draw()
        return True

    def draw_preview(self,widget,cr):
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        rounded(cr, 0, 0, width, height, 18)
        cr.clip()
        backdrop = cairo.LinearGradient(0, 0, 0, height)
        backdrop.add_color_stop_rgb(0, .19, .16, .24)
        backdrop.add_color_stop_rgb(1, .11, .10, .15)
        cr.set_source(backdrop)
        cr.paint()
        caption(widget, cr, 'Move and click here', 16, height-34)
        self.world.draw(cr,time.monotonic(),self.app.settings['mouse'],self.app.settings['palette'])
        return True

    def setup_helper(self,*args):
        script = str(Path(__file__).with_name('setup-mouse.sh'))
        terminal = shutil.which('konsole')
        if terminal:
            subprocess.Popen([terminal,'--separate','-e','bash',script])
        else:
            self.status.set_text('Run in a terminal: bash '+shlex.quote(script))
