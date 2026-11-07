"""Playground's look: one window-scoped CSS theme plus a few small shared widgets.

Class names carry a pg- prefix so desktop themes (adw-gtk3, Breeze) cannot restyle them.
"""
import math
import random
import time
import cairo
import gi
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, GLib, GObject, PangoCairo
from modules import CATALOG

SPECS = {spec.key: spec for spec in CATALOG}
INK = '#3a3245'
FONT = '"Inter", "Noto Sans", "Cantarell", sans-serif'


def rgb(color):
    return tuple(int(color[i:i+2], 16)/255 for i in (1, 3, 5))


def mix(a, b, amount):
    return '#'+''.join(f'{round((x*(1-amount)+y*amount)*255):02x}' for x, y in zip(rgb(a), rgb(b)))


BASE_CSS = '''
@define-color pg_bg #f7f3ee;
@define-color pg_surface #fffdfa;
@define-color pg_sunken #f1ece6;
@define-color pg_ink #3a3245;
@define-color pg_ink2 #665c71;
@define-color pg_muted #978ca1;
@define-color pg_line #ebe3ea;
@define-color pg_line_soft #f3eef1;
@define-color pg_accent #8f74be;
@define-color pg_accent_deep #6b519a;
@define-color pg_accent_soft #f1ebf8;
@define-color pg_good #72b48c;

.playground {
  background-color: @pg_bg;
  background-image: linear-gradient(to bottom, #faf7f2, #f3eee8);
  color: @pg_ink;
  font-family: FONT;
  font-size: 14px;
}
.playground label { color: inherit; }
.playground label selection { background-color: alpha(@pg_accent, .25); color: @pg_ink; }
.playground stack, .playground scrolledwindow, .playground viewport {
  background-color: transparent; background-image: none; border: none; box-shadow: none;
}
.playground scrolledwindow undershoot, .playground scrolledwindow overshoot,
.playground scrolledwindow junction { background-color: transparent; background-image: none; border: none; }

/* Text */
.playground .pg-brand { font-size: 24px; font-weight: 800; letter-spacing: -0.3px; }
.playground .pg-tagline { color: @pg_muted; font-size: 13px; }
.playground .pg-overline { color: @pg_muted; font-size: 11px; font-weight: 700; letter-spacing: 1.2px; }
.playground .pg-hero-title { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.playground .pg-card-title { font-size: 17px; font-weight: 700; }
.playground .pg-mini-title { font-size: 14px; font-weight: 700; color: @pg_ink2; }
.playground .pg-muted { color: @pg_muted; }
.playground .pg-secondary { color: @pg_ink2; }
.playground .pg-small { font-size: 12px; }
.playground .pg-row-title { font-weight: 600; }
.playground .pg-row-sub { color: @pg_muted; font-size: 12px; }

/* Surfaces */
.playground .pg-card {
  background-color: @pg_surface; border: 1px solid @pg_line; border-radius: 20px; padding: 10px 10px 12px 10px;
  box-shadow: 0 1px 2px alpha(@pg_ink, .04), 0 6px 16px alpha(@pg_ink, .05);
}
.playground .pg-mini {
  background-color: alpha(@pg_surface, .55); border: 1px dashed #e3d9e2; border-radius: 16px; padding: 12px;
}
.playground .pg-group {
  background-color: @pg_surface; border: 1px solid @pg_line; border-radius: 16px;
  box-shadow: 0 1px 2px alpha(@pg_ink, .03);
}
.playground .pg-row { padding: 12px 16px; border-top: 1px solid @pg_line_soft; }
.playground .pg-row:first-child { border-top-width: 0; }
.playground .pg-note { background-color: alpha(@pg_sunken, .7); border-radius: 14px; padding: 12px 14px; }
.playground .pg-status {
  background-color: @pg_surface; border: 1px solid @pg_line; border-radius: 999px; padding: 6px 12px;
  color: @pg_ink2; font-size: 12px; font-weight: 600;
}
.playground .pg-footer { border-top: 1px solid @pg_line; padding: 10px 24px 12px 24px; }

/* Buttons */
.playground button {
  background-color: @pg_surface; background-image: none; color: @pg_ink;
  border: 1px solid @pg_line; border-radius: 12px; padding: 7px 14px;
  box-shadow: 0 1px 2px alpha(@pg_ink, .05); text-shadow: none; -gtk-icon-shadow: none;
  font-weight: 600; outline-color: alpha(@pg_accent, .55); transition: all 150ms ease;
}
.playground button:hover { background-color: #fcf9fd; border-color: #dccfe7; }
.playground button:active { background-color: @pg_accent_soft; }
.playground button:disabled { opacity: .5; }
.playground button.pg-primary { background-color: @pg_accent; border-color: @pg_accent; color: #ffffff; }
.playground button.pg-primary:hover { background-color: @pg_accent_deep; border-color: @pg_accent_deep; }
.playground button.pg-link {
  background-color: transparent; border-color: transparent; box-shadow: none; color: @pg_accent_deep; padding: 5px 9px;
}
.playground button.pg-link:hover { background-color: @pg_accent_soft; }
.playground button.pg-link.pg-small { padding: 2px 8px; font-size: 12px; }
.playground button.pg-quiet { background-color: transparent; box-shadow: none; color: @pg_ink2; }
.playground button.pg-quiet:hover { background-color: @pg_surface; color: @pg_ink; }
.playground button.pg-chip { border-radius: 999px; padding: 6px 14px; color: @pg_ink2; box-shadow: none; }
.playground button.pg-chip:checked { background-color: @pg_accent_soft; border-color: @pg_accent; color: @pg_accent_deep; }
.playground button.pg-swatch { border-radius: 14px; border-width: 2px; border-color: transparent; padding: 6px; box-shadow: none; background-color: transparent; color: @pg_ink2; font-weight: 600; font-size: 12px; }
.playground button.pg-swatch:hover { background-color: @pg_sunken; }
.playground button.pg-swatch:checked { background-color: @pg_accent_soft; border-color: @pg_accent; color: @pg_accent_deep; }
.playground .pg-segmented { background-color: @pg_sunken; border-radius: 12px; padding: 3px; }
.playground .pg-segmented button {
  background-color: transparent; border-color: transparent; box-shadow: none; border-radius: 9px; padding: 5px 12px; color: @pg_ink2;
}
.playground .pg-segmented button:hover { color: @pg_ink; }
.playground .pg-segmented button:checked { background-color: @pg_surface; color: @pg_ink; box-shadow: 0 1px 3px alpha(@pg_ink, .14); }

/* Controls */
.playground switch {
  background-color: #e3dce6; background-image: none; border: 2px solid #e3dce6; border-radius: 999px;
  box-shadow: none; color: transparent; padding: 0; transition: all 180ms ease;
}
.playground switch:checked { background-color: @pg_accent; border-color: @pg_accent; }
.playground switch slider {
  background-color: #ffffff; background-image: none; border: none; border-radius: 999px;
  min-width: 20px; min-height: 20px; margin: 0; box-shadow: 0 1px 3px alpha(#000000, .18);
}
.playground switch image { color: transparent; -gtk-icon-shadow: none; }
.playground scale { padding: 6px 0; }
.playground scale trough { background-color: #e9e2ee; background-image: none; border: none; border-radius: 999px; min-height: 6px; }
.playground scale highlight { background-color: @pg_accent; background-image: none; border: none; border-radius: 999px; }
.playground scale slider {
  background-color: #ffffff; background-image: none; border: 2px solid @pg_accent; border-radius: 999px;
  min-width: 14px; min-height: 14px; margin: -6px; box-shadow: 0 1px 3px alpha(@pg_ink, .2);
}
.playground scale value { color: @pg_ink2; font-size: 12px; font-weight: 600; min-width: 34px; margin-left: 10px; }
.playground scrollbar { background-color: transparent; background-image: none; border: none; }
.playground scrollbar slider { background-color: alpha(@pg_ink, .22); border: none; border-radius: 999px; min-width: 6px; min-height: 6px; }
.playground scrollbar slider:hover { background-color: alpha(@pg_ink, .38); }
'''.replace('FONT', FONT)


def module_css(spec):
    """Each module page and card uses its own color for switches, sliders and choices."""
    soft, deep = mix(spec.color, '#ffffff', .84), mix(spec.color, INK, .42)
    k = '.playground .pg-mod-'+spec.key
    return f'''
{k} switch:checked {{ background-color: {spec.color}; border-color: {spec.color}; }}
{k} scale highlight {{ background-color: {spec.color}; }}
{k} scale slider {{ border-color: {spec.color}; }}
{k} button.pg-chip:checked, {k} button.pg-swatch:checked {{ background-color: {soft}; border-color: {spec.color}; color: {deep}; }}
{k} button.pg-link {{ color: {deep}; }}
{k} button.pg-link:hover {{ background-color: {soft}; }}
{k} .pg-segmented button:checked {{ color: {deep}; }}
'''


def install_theme(screen):
    provider = Gtk.CssProvider()
    provider.load_from_data((BASE_CSS+''.join(module_css(spec) for spec in CATALOG)).encode())
    Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    return provider


def styled(widget, *names):
    context = widget.get_style_context()
    for name in names:
        context.add_class(name)
    return widget


def label(text, *styles, wrap=False, markup=False):
    widget = Gtk.Label(xalign=0)
    if markup:
        widget.set_markup(text)
    else:
        widget.set_text(text)
    if wrap:
        widget.set_line_wrap(True)
    return styled(widget, *styles)


def switch(active=False):
    widget = Gtk.Switch()
    widget.set_active(active)
    widget.set_valign(Gtk.Align.CENTER)
    return widget


def button(text, *styles, on_click=None):
    widget = styled(Gtk.Button(label=text), *styles)
    if on_click:
        widget.connect('clicked', on_click)
    return widget


def slider(low, high, step, digits, value):
    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, low, high, step)
    scale.set_hexpand(True)
    scale.set_size_request(160, -1)
    scale.set_digits(digits)
    scale.set_value_pos(Gtk.PositionType.RIGHT)
    scale.set_value(value)
    return scale


def row(title, control=None, subtitle=None, stacked=False, size_group=None):
    """A settings row: title and optional subtitle, with the control beside or below."""
    box = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL if stacked else Gtk.Orientation.HORIZONTAL,
                         spacing=10 if stacked else 16), 'pg-row')
    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    text.set_valign(Gtk.Align.CENTER)
    if title:
        text.pack_start(label(title, 'pg-row-title', wrap=True), False, False, 0)
    if subtitle is not None:
        sub = subtitle if isinstance(subtitle, Gtk.Label) else label(subtitle)
        sub.set_xalign(0)
        sub.set_line_wrap(True)
        text.pack_start(styled(sub, 'pg-row-sub'), False, False, 0)
    if size_group:
        size_group.add_widget(text)
    # A stretching control (a slider) takes the spare width; otherwise the text does.
    stretch = control is not None and control.get_hexpand()
    box.pack_start(text, stacked or not stretch, True, 0)
    if control is None:
        return box
    if stacked or stretch:
        box.pack_start(control, stretch, True, 0)
    else:
        control.set_valign(Gtk.Align.CENTER)
        box.pack_end(control, False, False, 0)
    return box


def group(title, *rows, action=None):
    """An overline title, with an optional small action beside it, above a rounded card of rows."""
    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6 if action else 8)
    if title:
        heading = Gtk.Box(spacing=8)
        overline = label(title.upper(), 'pg-overline')
        overline.set_margin_start(4)
        overline.set_valign(Gtk.Align.CENTER)
        heading.pack_start(overline, True, True, 0)
        if action:
            styled(action, 'pg-small')
            action.set_valign(Gtk.Align.CENTER)
            heading.pack_end(action, False, False, 0)
        outer.pack_start(heading, False, False, 0)
    card = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL), 'pg-group')
    for item in rows:
        card.pack_start(item, False, False, 0)
    outer.pack_start(card, False, False, 0)
    outer.card = card
    return outer


class Choice(Gtk.Box):
    """Single choice as chips or a segmented control, with ComboBoxText's id API."""
    __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, options, kind='chips', spacing=8):
        super().__init__(spacing=0 if kind == 'segmented' else spacing)
        if kind == 'segmented':
            styled(self, 'pg-segmented')
            self.set_valign(Gtk.Align.CENTER)
        self.buttons = {}
        self.active = None
        self.syncing = False
        for key, content in options:
            toggle = Gtk.ToggleButton()
            if isinstance(content, str):
                toggle.set_label(content)
            else:
                toggle.add(content)
            if kind == 'chips':
                styled(toggle, 'pg-chip')
            elif kind == 'swatches':
                styled(toggle, 'pg-swatch')
            toggle.connect('toggled', self.toggled, key)
            self.buttons[key] = toggle
            self.pack_start(toggle, kind == 'swatches', True, 0)

    def toggled(self, toggle, key):
        if self.syncing:
            return
        if toggle.get_active():
            self.set_active_id(key)
        elif key == self.active:
            self.sync()

    def sync(self):
        self.syncing = True
        for key, toggle in self.buttons.items():
            toggle.set_active(key == self.active)
        self.syncing = False

    def set_active_id(self, key):
        if key not in self.buttons:
            return False
        changed = key != self.active
        self.active = key
        self.sync()
        if changed:
            self.emit('changed')
        return True

    def get_active_id(self):
        return self.active


def rounded(cr, x, y, width, height, radius):
    radius = min(radius, width/2, height/2)
    cr.new_sub_path()
    cr.arc(x+width-radius, y+radius, radius, -math.pi/2, 0)
    cr.arc(x+width-radius, y+height-radius, radius, 0, math.pi/2)
    cr.arc(x+radius, y+height-radius, radius, math.pi/2, math.pi)
    cr.arc(x+radius, y+radius, radius, math.pi, 3*math.pi/2)
    cr.close_path()


def caption(widget, cr, text, x, y, alpha=.55):
    """Small light text for dark preview stages."""
    layout = widget.create_pango_layout('')
    layout.set_markup('<span size="small" weight="600">'+GLib.markup_escape_text(text)+'</span>', -1)
    cr.save()
    cr.set_source_rgba(1, 1, 1, alpha)
    cr.move_to(x, y)
    PangoCairo.show_layout(cr, layout)
    cr.restore()


def draw_glyph(cr, key, color):
    """Module symbols, drawn around the origin within a radius of about 30."""
    cr.set_source_rgb(*color)
    cr.set_line_width(3)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    if key == 'edgeglow':
        for n in range(3):
            cr.move_to(-26, -13+n*13)
            cr.curve_to(-9, -32+n*13, 8, 6+n*13, 26, -13+n*13)
            cr.stroke()
    elif key == 'mouse':
        cr.move_to(-11, -22); cr.line_to(17, 0); cr.line_to(3, 4)
        cr.line_to(-4, 18); cr.close_path(); cr.fill()
        for x, y, r in [(22, -20, 3), (24, 18, 2.4), (-21, 13, 2.6)]:
            cr.arc(x, y, r, 0, math.tau); cr.fill()
    elif key == 'atmosphere':
        for x, y, r in [(-15, -5, 10), (0, -11, 13.5), (15, -5, 9)]:
            cr.arc(x, y, r, 0, math.tau); cr.fill()
        cr.rectangle(-15, -5, 30, 9); cr.fill()
        for x in (-13, 0, 13):
            cr.move_to(x, 13); cr.line_to(x-4, 21); cr.stroke()
    elif key == 'toys':
        cr.arc(0, 0, 21, 0, math.tau); cr.fill()
        cr.set_source_rgb(1, 1, 1)
        for x in (-7, 7):
            cr.arc(x, -4, 2.8, 0, math.tau); cr.fill()
        cr.set_line_width(2.6)
        cr.arc(0, 3, 9, .25, math.pi-.25); cr.stroke()
    else:
        for i in range(7):
            height = 6+17*(.5+.5*math.sin(i*1.6))
            cr.move_to(-24+i*8, -height); cr.line_to(-24+i*8, height); cr.stroke()


def sparkle(cr, x, y, size):
    cr.move_to(x, y-size)
    for angle in range(1, 8):
        radius = size if angle % 2 == 0 else size*.28
        a = angle*math.pi/4-math.pi/2
        cr.line_to(x+math.cos(a)*radius, y+math.sin(a)*radius)
    cr.close_path()
    cr.fill()


class ModuleArt(Gtk.DrawingArea):
    """A module's symbol. Banner mode fills its width with a soft tinted panel."""

    def __init__(self, spec, height=88, width=-1, banner=False, scale=1.0):
        super().__init__()
        self.spec, self.banner, self.scale = spec, banner, scale
        self.started = 0
        self.timer = 0
        self.set_size_request(width, height)
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
        if time.monotonic()-self.started > .8:
            self.timer = 0
            self.started = 0
            return False
        return True

    def draw_art(self, widget, cr):
        width, height = self.get_allocated_width(), self.get_allocated_height()
        color = rgb(self.spec.color)
        if self.banner:
            rounded(cr, 0, 0, width, height, 14)
            tint = cairo.LinearGradient(0, 0, width, height)
            tint.add_color_stop_rgba(0, *color, .22)
            tint.add_color_stop_rgba(1, *color, .07)
            cr.set_source(tint)
            cr.fill()
            rng = random.Random(self.spec.key)
            for i in range(12):
                x, y = rng.uniform(.05, .95)*width, rng.uniform(.14, .86)*height
                if abs(x-width/2) < 58:
                    continue
                cr.set_source_rgba(*color, rng.uniform(.22, .5))
                if i % 3 == 0:
                    sparkle(cr, x, y, rng.uniform(4, 6.5))
                else:
                    cr.arc(x, y, rng.uniform(1.4, 2.8), 0, math.tau)
                    cr.fill()
        age = time.monotonic()-self.started if self.started else 1
        bounce = .17*math.exp(-5*age)*math.sin(13*age) if age < .8 else 0
        size = self.scale*(1+bounce)
        cr.translate(width/2, height/2-14*bounce*self.scale)
        cr.scale(size, size)
        if self.banner:
            cr.set_source_rgba(1, 1, 1, .62)
        else:
            cr.set_source_rgba(*color, .16)
        cr.arc(0, 0, 32, 0, math.tau)
        cr.fill()
        draw_glyph(cr, self.spec.key, color)
        return True


def hover_bounce(art):
    """Wraps art in an event box that replays its bounce on hover."""
    box = Gtk.EventBox()
    box.set_visible_window(False)
    box.add(art)
    box.connect('enter-notify-event', art.bounce)
    return box


def hero(spec, subtitle, control):
    """A module page header: symbol, title, subtitle, and its on/off switch."""
    box = Gtk.Box(spacing=16)
    art = ModuleArt(spec, height=68, width=68, scale=.95)
    art.set_valign(Gtk.Align.CENTER)
    box.pack_start(hover_bounce(art), False, False, 0)
    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    text.set_valign(Gtk.Align.CENTER)
    text.pack_start(label(spec.title, 'pg-hero-title'), False, False, 0)
    text.pack_start(label(subtitle, 'pg-secondary', wrap=True), False, False, 0)
    box.pack_start(text, True, True, 0)
    control.set_tooltip_text('Turn '+spec.title+' on or off')
    box.pack_end(control, False, False, 0)
    return box


def page(spec):
    """A scrolling module page whose content uses the module's color."""
    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroller.set_vexpand(True)
    box = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=22), 'pg-mod-'+spec.key)
    box.set_margin_start(24)
    box.set_margin_end(24)
    box.set_margin_top(6)
    box.set_margin_bottom(24)
    scroller.add(box)
    return scroller, box
