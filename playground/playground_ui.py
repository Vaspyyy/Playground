"""Playground's module browser. GTK styling is scoped to this window only."""
import math
import time
from gi.repository import Gtk, Gdk, GLib
from modules import CATALOG
from update_ui import UpdateControls
from mouse_ui import MousePanel

CSS = b'''
.playground { background-color: #f5f1eb; color: #443b51; }
.playground label { color: #443b51; }
.playground .muted { color: #81758b; }
.playground .brand { font-size: 30px; font-weight: 800; }
.playground .section { font-size: 20px; font-weight: 700; }
.playground .card { background-color: #fffdf9; border: 1px solid #e6dfeb; border-radius: 22px; padding: 18px; }
.playground .card-title { font-size: 19px; font-weight: 700; }
.playground button { background-image: none; background-color: #eee6f6; color: #65517e; border: 1px solid #e0d3ed; border-radius: 14px; padding: 9px 15px; box-shadow: none; transition: 180ms ease; }
.playground button:hover { background-color: #e0d0ef; border-color: #c7afdf; }
.playground button:active { background-color: #d2bde5; }
.playground button:disabled { background-color: #f0ece8; color: #928994; border-color: #e7e0db; }
.playground switch { border-radius: 15px; background-color: #e2dce6; }
.playground switch:checked { background-color: #a18abd; }
.playground switch slider { background-color: #fffdf9; border-radius: 13px; }
.playground scale trough { background-color: #e6deec; border-radius: 8px; }
.playground scale highlight { background-color: #b399ce; border-radius: 8px; }
.playground scale slider { background-color: #a083bb; border: 2px solid #fffdf9; min-width: 15px; min-height: 15px; }
.playground checkbutton check { background-color: #fffdf9; border-color: #c8b9d4; border-radius: 5px; }
.playground checkbutton check:checked { background-color: #aa8bc8; color: white; }
.playground .pill { background-color: #eee7f5; color: #7a6593; border-radius: 10px; padding: 4px 9px; font-size: 11px; }
.playground .footer { background-color: #ebe5ee; border-radius: 15px; padding: 12px; }
'''


def styled(widget, name):
    widget.get_style_context().add_class(name)
    return widget


def label(text, style=None):
    widget = Gtk.Label(label=text, xalign=0)
    if style:
        styled(widget, style)
    return widget


class ModuleArt(Gtk.DrawingArea):
    def __init__(self, spec):
        super().__init__()
        self.spec = spec
        self.started = 0
        self.timer = 0
        self.set_size_request(100, 80)
        self.connect('draw', self.draw_art)
        self.connect('destroy', self.stop)
        self.connect('unmap', self.stop)

    def bounce(self, *args):
        self.started = time.monotonic()
        if not self.timer:
            self.timer = GLib.timeout_add(16, self.tick)

    def stop(self, *args):
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0
        self.started = 0

    def tick(self):
        self.queue_draw()
        if time.monotonic() - self.started > .8:
            self.timer = 0
            self.started = 0
            return False
        return True

    def draw_art(self, widget, cr):
        age = time.monotonic()-self.started if self.started else 1
        bounce = .17*math.exp(-5*age)*math.sin(13*age) if age < .8 else 0
        cr.translate(self.get_allocated_width()/2, 40-18*bounce)
        cr.scale(1+bounce, 1+bounce)
        rgb = tuple(int(self.spec.color[i:i+2],16)/255 for i in (1,3,5))
        cr.set_source_rgba(*rgb,.15)
        cr.arc(0,0,34,0,math.tau);cr.fill()
        cr.set_source_rgb(*rgb)
        cr.set_line_width(3)
        if self.spec.key == 'edgeglow':
            for n in range(3):
                cr.move_to(-29,-14+n*13)
                cr.curve_to(-10,-35+n*13, 8,8+n*13,29,-14+n*13)
                cr.stroke()
        elif self.spec.key == 'mouse':
            cr.move_to(-12,-24);cr.line_to(19,0);cr.line_to(3,4)
            cr.line_to(-5,20);cr.close_path();cr.fill()
            for x,y in [(25,-22),(26,22),(-24,14)]:
                cr.arc(x,y,3,0,math.tau);cr.fill()
        elif self.spec.key == 'atmosphere':
            for x,y,r in [(-17,-5,11),(0,-12,15),(17,-5,10)]:
                cr.arc(x,y,r,0,math.tau);cr.fill()
            for x in (-16,0,16):
                cr.move_to(x,14);cr.line_to(x-4,23);cr.stroke()
        elif self.spec.key == 'toys':
            cr.arc(0,0,23,0,math.tau);cr.fill()
            cr.set_source_rgb(1,1,1)
            for x in (-8,8):
                cr.arc(x,-4,3,0,math.tau);cr.fill()
            cr.arc(0,4,10,.2,math.pi-.2);cr.stroke()
        else:
            for i in range(7):
                height = 8+19*(.5+.5*math.sin(i*1.6))
                cr.move_to(-27+i*9,-height);cr.line_to(-27+i*9,height);cr.stroke()
        return True


class PlaygroundWindow(Gtk.ApplicationWindow):
    def __init__(self, app, panel_class, autostart, desktop_entry):
        super().__init__(application=app, title='Playground')
        self.owner = app
        self.set_default_size(850, 820)
        self.set_size_request(660, 460)
        styled(self, 'playground')
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.connect('delete-event', self.close_window)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        root.set_border_width(22)
        self.add(root)
        top = Gtk.Box(spacing=16)
        top.pack_start(label('Playground', 'brand'), True, True, 0)
        self.count = label('', 'pill')
        top.pack_end(self.count, False, False, 0)
        root.pack_start(top, False, False, 0)
        root.pack_start(label('Make a little room for play.', 'muted'), False, False, 0)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(260)
        self.stack.set_hhomogeneous(False)
        self.stack.set_vhomogeneous(False)
        root.pack_start(self.stack, True, True, 0)
        home = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        home.pack_start(label('Your desktop, your little universe', 'section'), False, False, 0)
        intro = label('Switch modules on individually. They can share the same desktop.', 'muted')
        intro.set_line_wrap(True)
        home.pack_start(intro, False, False, 0)
        grid = Gtk.Grid(column_spacing=14, row_spacing=14)
        grid.set_column_homogeneous(True)
        self.module_switches = {}
        for i, spec in enumerate(CATALOG):
            card = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10), 'card')
            art = ModuleArt(spec)
            art_box = Gtk.EventBox()
            art_box.set_visible_window(False)
            art_box.add(art)
            art_box.connect('enter-notify-event', art.bounce)
            card.pack_start(art_box, False, False, 0)
            header = Gtk.Box(spacing=10)
            header.pack_start(label(spec.title, 'card-title'), True, True, 0)
            if spec.available:
                switch = Gtk.Switch()
                switch.set_active(app.modules.enabled(spec.key))
                switch.connect('notify::active', lambda switch, param, key=spec.key: app.set_module_enabled(switch.get_active(), key))
                self.module_switches[spec.key] = switch
                header.pack_end(switch, False, False, 0)
            else:
                header.pack_end(label('Planned', 'pill'), False, False, 0)
            card.pack_start(header, False, False, 0)
            summary = label(spec.summary, 'muted')
            summary.set_line_wrap(True)
            card.pack_start(summary, False, False, 0)
            if spec.available:
                button = Gtk.Button(label='Open & play')
                button.connect('clicked', lambda button, key=spec.key: self.stack.set_visible_child_name(key))
            else:
                button = Gtk.Button(label='Not built yet')
                button.set_sensitive(False)
            card.pack_end(button, False, False, 0)
            grid.attach(card, i%2, i//2, 1, 1)
        home.pack_start(grid, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(home)
        self.stack.add_named(scroll, 'home')
        module_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        back = Gtk.Button(label='‹  All modules')
        back.set_halign(Gtk.Align.START)
        back.connect('clicked', lambda *_: self.go_home())
        module_page.pack_start(back, False, False, 0)
        self.panel = panel_class(app)
        module_page.pack_start(self.panel, True, True, 0)
        self.stack.add_named(module_page, 'edgeglow')
        self.module_switch = self.module_switches['edgeglow']
        mouse_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mouse_back = Gtk.Button(label='‹  All modules')
        mouse_back.set_halign(Gtk.Align.START)
        mouse_back.connect('clicked', lambda *_: self.go_home())
        mouse_page.pack_start(mouse_back, False, False, 0)
        self.mouse_panel = MousePanel(app)
        mouse_page.pack_start(self.mouse_panel, True, True, 0)
        self.stack.add_named(mouse_page, 'mouse')
        self.status = self.panel.status
        self.effect_label = self.panel.effect_label
        self.continuous_switch = self.panel.continuous_switch
        footer = styled(Gtk.Box(spacing=12), 'footer')
        startup_switch = Gtk.Switch()
        startup_switch.set_active(autostart.exists())
        def startup_changed(switch, param):
            try:
                if switch.get_active():
                    autostart.parent.mkdir(parents=True, exist_ok=True)
                    autostart.write_text(desktop_entry('--background'))
                else:
                    autostart.unlink(missing_ok=True)
            except OSError as error:
                app.set_status('Could not update login startup: '+str(error))
        startup_switch.connect('notify::active', startup_changed)
        footer.pack_start(label('Start at login', 'muted'), False, False, 0)
        footer.pack_start(startup_switch, False, False, 0)
        quit_button = Gtk.Button(label='Quit Playground')
        quit_button.connect('clicked', lambda *_: app.quit())
        footer.pack_end(quit_button, False, False, 0)
        root.pack_end(footer, False, False, 0)
        root.pack_end(UpdateControls(app), False, False, 0)
        self.sync_modules()

    def sync_modules(self):
        for key, panel in [('edgeglow', self.panel), ('mouse', self.mouse_panel)]:
            active = self.owner.modules.enabled(key)
            for switch in (self.module_switches[key], panel.enabled_switch):
                if switch.get_active() != active:
                    switch.set_active(active)
        count = self.owner.modules.active_count()
        self.count.set_text(str(count)+(' module on' if count == 1 else ' modules on'))

    def go_home(self):
        self.continuous_switch.set_active(False)
        self.stack.set_visible_child_name('home')

    def close_window(self, *args):
        self.continuous_switch.set_active(False)
        self.hide()
        return True
