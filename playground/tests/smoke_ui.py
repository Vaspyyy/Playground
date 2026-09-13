"""Exercise the actual GTK settings in a virtual X11 session, without overlays."""
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory() as directory:
    os.environ['XDG_CONFIG_HOME'] = directory
    os.environ['GDK_BACKEND'] = 'x11'
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
    Gtk.init([])
    import edgeglow
    app = edgeglow.Edgeglow()
    app.register(None)
    app.activate()
    assert app.window is not None
    window = app.window
    for _ in range(30):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
    window.stack.set_visible_child_name('edgeglow')
    def settle():
        loop = GLib.MainLoop()
        GLib.timeout_add(400, lambda: loop.quit() or False)
        loop.run()

    # Widget existence alone missed a collapsed scrolling viewport in 0.4.0.
    for width, height in [(850, 820), (700, 620)]:
        window.resize(width, height)
        settle()
        scroller = window.panel.scroller
        assert scroller.get_allocated_height() > 180, 'Settings viewport collapsed'
        adjustment = scroller.get_vadjustment()
        adjustment.set_value(0)
        settle()
        favorite = window.panel.favorites['sparks']
        x, y = favorite.translate_coordinates(scroller, 0, 0)
        assert 0 <= y < scroller.get_allocated_height(), 'Favorites clipped at top'
        adjustment.set_value(adjustment.get_upper()-adjustment.get_page_size())
        settle()
        enabled = window.panel.enabled_switch
        x, y = enabled.translate_coordinates(scroller, 0, 0)
        assert 0 <= y < scroller.get_allocated_height(), 'Lower controls unreachable'
    window.panel.controls['chaos'].set_value(72)
    assert app.settings['chaos'] == 72
    window.module_switch.set_active(False)
    assert not app.modules.enabled('edgeglow')
    assert not window.panel.enabled_switch.get_active()
    window.panel.enabled_switch.set_active(True)
    assert window.module_switch.get_active()
    window.go_home()
    assert window.stack.get_visible_child_name() == 'home'
    window.destroy()
    app.quit()
    print('GTK settings smoke test passed')
