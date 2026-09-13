"""Mouse Magic controls and an interactive local preview."""
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from gi.repository import Gtk, Gdk, GLib
from mouse_core import PRESETS, World


class MousePanel(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        self.app = app
        self.syncing = False
        self.set_border_width(18)
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        self.scroller.set_vexpand(True)
        self.pack_start(self.scroller,True,True,0)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=15)
        self.scroller.add(box)
        heading = Gtk.Label(xalign=0)
        heading.set_markup('<span size="24000" weight="bold">Mouse Magic</span>')
        box.pack_start(heading,False,False,0)
        intro = Gtk.Label(label='A little company for your cursor. Colors follow Edgeglow’s palette.',xalign=0)
        intro.set_line_wrap(True)
        box.pack_start(intro,False,False,0)
        self.enabled_switch = Gtk.Switch()
        self.enabled_switch.set_active(app.settings['mouse']['enabled'])
        self.enabled_switch.connect('notify::active',lambda s,*_: app.set_module_enabled(s.get_active(),'mouse'))
        self.row(box,'Enable Mouse Magic',self.enabled_switch)
        presets = Gtk.ComboBoxText()
        presets.append('custom','Custom mix')
        for name in PRESETS:
            presets.append(name,name)
        presets.set_active_id('custom')
        self.presets = presets
        presets.connect('changed',self.preset_changed)
        self.row(box,'Start with a preset',presets)
        self.toggles = {}
        for key,title in [('ribbon','Flowing comet ribbon'),('dust','Sparks & fairy dust'),
                          ('ripples','Click ripples'),('field','Scattered particles'),
                          ('idle','Small cloud while the cursor rests'),('fullscreen','Show over fullscreen games & videos')]:
            toggle = Gtk.Switch()
            toggle.set_active(app.settings['mouse'][key])
            toggle.connect('notify::active',lambda s,p,k=key: self.change(k,s.get_active()))
            self.toggles[key] = toggle
            self.row(box,title,toggle)
        self.reaction = Gtk.ComboBoxText()
        for key,title in [('swirl','Swirl around'),('scatter','Scatter away'),('attract','Attract, then drift')]:
            self.reaction.append(key,title)
        self.reaction.set_active_id(app.settings['mouse']['reaction'])
        self.reaction.connect('changed',lambda c: self.change('reaction',c.get_active_id()))
        self.row(box,'When particles meet your cursor',self.reaction)
        self.controls = {}
        for key,title in [('motion','Motion · gentle → wild'),('density','Particle density'),('brightness','Brightness')]:
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,0,100,1)
            scale.set_hexpand(True)
            scale.set_size_request(180,-1)
            scale.set_digits(0)
            scale.set_value(app.settings['mouse'][key])
            scale.connect('value-changed',lambda s,k=key: self.change(k,s.get_value()))
            self.controls[key] = scale
            self.row(box,title,scale)
        box.pack_start(Gtk.Label(label='Try it here · move and click in the preview',xalign=0),False,False,0)
        self.preview = Gtk.DrawingArea()
        self.preview.set_size_request(-1,180)
        self.preview.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK)
        self.preview.connect('draw',self.draw_preview)
        self.preview.connect('motion-notify-event',self.preview_pointer,False)
        self.preview.connect('button-press-event',self.preview_pointer,True)
        self.preview.connect('map',self.preview_start)
        self.preview.connect('unmap',self.preview_stop)
        self.preview.connect('destroy',self.preview_stop)
        self.preview.connect('size-allocate',self.preview_resize)
        self.world = World(42)
        self.preview_timer = 0
        self.previous = time.monotonic()
        box.pack_start(self.preview,False,False,0)
        self.status = Gtk.Label(label=app.mouse.status if app.mouse else 'Desktop effects require KDE Plasma Wayland.',xalign=0)
        self.status.set_line_wrap(True)
        self.status.set_max_width_chars(55)
        self.status.set_selectable(True)
        box.pack_start(self.status,False,False,0)
        actions = Gtk.Box(spacing=10)
        reconnect = Gtk.Button(label='Reconnect')
        reconnect.connect('clicked',lambda *_: app.mouse.reconnect() if app.mouse else None)
        setup = Gtk.Button(label='Set up click helper…')
        setup.connect('clicked',self.setup_helper)
        actions.pack_start(reconnect,False,False,0)
        actions.pack_start(setup,False,False,0)
        box.pack_start(actions,False,False,0)
        note = Gtk.Label(label='Click helper setup opens a terminal and asks for administrator authentication.\nCursor effects work without it. Re-run setup after a KDE upgrade if clicks stop.',xalign=0)
        note.set_line_wrap(True)
        note.set_max_width_chars(55)
        box.pack_start(note,False,False,0)

    def row(self,box,title,control):
        row = Gtk.Box(spacing=12)
        label = Gtk.Label(label=title,xalign=0)
        label.set_line_wrap(True)
        row.pack_start(label,True,True,0)
        row.pack_end(control,False,False,0)
        box.pack_start(row,False,False,0)

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
        cr.set_source_rgb(.14,.12,.18);cr.paint()
        self.world.draw(cr,time.monotonic(),self.app.settings['mouse'],self.app.settings['palette'])
        return True

    def setup_helper(self,*args):
        script = str(Path(__file__).with_name('setup-mouse.sh'))
        terminal = shutil.which('konsole')
        if terminal:
            subprocess.Popen([terminal,'--separate','-e','bash',script])
        else:
            self.status.set_text('Run in a terminal: bash '+shlex.quote(script))
