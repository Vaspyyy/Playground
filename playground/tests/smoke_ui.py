"""Exercise the actual GTK settings in a virtual X11 session, without overlays."""
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory() as directory:
    os.environ['XDG_CONFIG_HOME'] = directory
    import edgeglow
    os.environ['GDK_BACKEND'] = 'x11'
    from gi.repository import Gtk, GLib
    app = edgeglow.Edgeglow()
    app.register(None)
    app.activate()
    assert app.window is not None
    window = app.window
    for _ in range(30):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
    window.stack.set_visible_child_name('edgeglow')
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
