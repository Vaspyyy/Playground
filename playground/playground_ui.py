"""Playground's module browser. GTK styling is scoped to this window only."""
from pathlib import Path
import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from modules import CATALOG
from update_ui import UpdateControls
from mouse_ui import MousePanel
from ui_kit import ModuleArt, button, hover_bounce, install_theme, label, styled, switch

ICON = Path(__file__).with_name('edgeglow.svg')


def app_icon(size):
    try:
        return Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(str(ICON), size, size))
    except GLib.Error:
        return None


def section(title, text=None):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    box.pack_start(label(title.upper(), 'pg-overline'), False, False, 0)
    if text:
        box.pack_start(label(text, 'pg-muted', wrap=True), False, False, 0)
    return box


class PlaygroundWindow(Gtk.ApplicationWindow):
    def __init__(self, app, panel_class, autostart, desktop_entry):
        super().__init__(application=app, title='Playground')
        self.owner = app
        self.set_icon_name(app.get_application_id())
        self.set_default_size(860, 820)
        self.set_size_request(660, 460)
        styled(self, 'playground')
        install_theme(self.get_screen())
        self.connect('delete-event', self.close_window)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(260)
        self.stack.set_hhomogeneous(False)
        self.stack.set_vhomogeneous(False)
        root.pack_start(self.stack, True, True, 0)
        self.module_switches = {}
        self.stack.add_named(self.build_home(app), 'home')
        self.panel = panel_class(app)
        self.stack.add_named(self.module_page(self.panel), 'edgeglow')
        self.mouse_panel = MousePanel(app)
        self.stack.add_named(self.module_page(self.mouse_panel), 'mouse')
        self.module_switch = self.module_switches['edgeglow']
        self.status = self.panel.status
        self.effect_label = self.panel.effect_label
        self.continuous_switch = self.panel.continuous_switch
        root.pack_end(self.build_footer(app, autostart, desktop_entry), False, False, 0)
        self.sync_modules()

    def build_home(self, app):
        home = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header = Gtk.Box(spacing=14)
        for side, value in [('start', 24), ('end', 24), ('top', 22), ('bottom', 12)]:
            getattr(header, 'set_margin_'+side)(value)
        icon = app_icon(46)
        if icon:
            header.pack_start(icon, False, False, 0)
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        titles.set_valign(Gtk.Align.CENTER)
        titles.pack_start(label('Playground', 'pg-brand'), False, False, 0)
        titles.pack_start(label('Make a little room for play.', 'pg-tagline'), False, False, 0)
        header.pack_start(titles, True, True, 0)
        self.count = label('', 'pg-status')
        self.count.set_valign(Gtk.Align.CENTER)
        header.pack_end(self.count, False, False, 0)
        home.pack_start(header, False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for side, value in [('start', 24), ('end', 24), ('top', 8), ('bottom', 24)]:
            getattr(content, 'set_margin_'+side)(value)
        content.pack_start(section('Modules', 'Switch them on one by one. They happily share the same desktop.'), False, False, 0)
        cards = Gtk.Grid(column_spacing=14, row_spacing=14)
        cards.set_column_homogeneous(True)
        available = [spec for spec in CATALOG if spec.available]
        for i, spec in enumerate(available):
            cards.attach(self.module_card(app, spec), i % 2, i//2, 1, 1)
        content.pack_start(cards, False, False, 0)
        planned = [spec for spec in CATALOG if not spec.available]
        if planned:
            soon = section('Coming soon')
            soon.set_margin_top(14)
            content.pack_start(soon, False, False, 0)
            minis = Gtk.Grid(column_spacing=12, row_spacing=12)
            minis.set_column_homogeneous(True)
            for i, spec in enumerate(planned):
                minis.attach(self.mini_card(spec), i % 3, i//3, 1, 1)
            content.pack_start(minis, False, False, 0)
        self.home_scroller = Gtk.ScrolledWindow()
        self.home_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.home_scroller.add(content)
        home.pack_start(self.home_scroller, True, True, 0)
        return home

    def module_card(self, app, spec):
        card = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12), 'pg-card', 'pg-mod-'+spec.key)
        art = hover_bounce(ModuleArt(spec, height=108, banner=True))
        art.connect('button-press-event', lambda widget, event, key=spec.key: event.button == 1 and self.open_module(key))
        art.set_tooltip_text('Open '+spec.title)
        card.pack_start(art, False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        body.set_margin_start(6)
        body.set_margin_end(4)
        header = Gtk.Box(spacing=10)
        header.pack_start(label(spec.title, 'pg-card-title'), True, True, 0)
        toggle = switch(app.modules.enabled(spec.key))
        toggle.set_tooltip_text('Turn '+spec.title+' on or off')
        toggle.connect('notify::active', lambda toggle, param, key=spec.key: app.set_module_enabled(toggle.get_active(), key))
        self.module_switches[spec.key] = toggle
        header.pack_end(toggle, False, False, 0)
        body.pack_start(header, False, False, 0)
        body.pack_start(label(spec.summary, 'pg-secondary', wrap=True), False, False, 0)
        card.pack_start(body, False, False, 0)
        customize = button('Customize  →', 'pg-link', on_click=lambda *_, key=spec.key: self.open_module(key))
        customize.set_halign(Gtk.Align.END)
        card.pack_end(customize, False, False, 0)
        return card

    def mini_card(self, spec):
        card = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6), 'pg-mini')
        art = ModuleArt(spec, height=50, width=50, scale=.68)
        art.set_halign(Gtk.Align.START)
        card.pack_start(hover_bounce(art), False, False, 0)
        card.pack_start(label(spec.title, 'pg-mini-title'), False, False, 0)
        card.pack_start(label(spec.summary.replace('\n', ' '), 'pg-muted', 'pg-small', wrap=True), False, False, 0)
        return card

    def module_page(self, panel):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        back = button('←  All modules', 'pg-quiet', on_click=lambda *_: self.go_home())
        back.set_halign(Gtk.Align.START)
        back.set_margin_start(16)
        back.set_margin_top(14)
        back.set_margin_bottom(6)
        page.pack_start(back, False, False, 0)
        page.pack_start(panel, True, True, 0)
        return page

    def build_footer(self, app, autostart, desktop_entry):
        footer = styled(Gtk.Box(spacing=10), 'pg-footer')
        footer.pack_start(UpdateControls(app), True, True, 0)
        startup_switch = switch(autostart.exists())
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
        quit_button = button('Quit', 'pg-quiet', on_click=lambda *_: app.quit())
        quit_button.set_tooltip_text('Stop all effects and close Playground')
        quit_button.set_valign(Gtk.Align.CENTER)
        quit_button.set_margin_start(10)
        footer.pack_end(quit_button, False, False, 0)
        footer.pack_end(startup_switch, False, False, 0)
        login = label('Start at login', 'pg-secondary')
        login.set_valign(Gtk.Align.CENTER)
        footer.pack_end(login, False, False, 0)
        return footer

    def open_module(self, key):
        self.stack.set_visible_child_name(key)
        return True

    def sync_modules(self):
        for key, panel in [('edgeglow', self.panel), ('mouse', self.mouse_panel)]:
            active = self.owner.modules.enabled(key)
            for switch in (self.module_switches[key], panel.enabled_switch):
                if switch.get_active() != active:
                    switch.set_active(active)
        count = self.owner.modules.active_count()
        text = 'Resting' if not count else str(count)+(' module on' if count == 1 else ' modules on')
        dot = '#72b48c' if count else '#c9bfcd'
        self.count.set_markup(f'<span foreground="{dot}">●</span>  {text}')

    def go_home(self):
        self.continuous_switch.set_active(False)
        self.stack.set_visible_child_name('home')

    def close_window(self, *args):
        self.continuous_switch.set_active(False)
        self.hide()
        return True
