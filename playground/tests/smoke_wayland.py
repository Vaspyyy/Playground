"""Run inside a disposable virtual KWin session, with the compiled helper installed."""
import os
from pathlib import Path
import sys
import tempfile
import time
import subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory() as directory:
    os.environ['XDG_CONFIG_HOME'] = directory
    import edgeglow
    from gi.repository import GLib, Gtk
    app = edgeglow.Edgeglow()
    app.register(None)
    app.activate()
    assert app.supported, 'Layer shell unavailable in virtual KWin'
    def settle(ms=600):
        loop = GLib.MainLoop()
        GLib.timeout_add(ms,lambda: loop.quit() or False)
        loop.run()
    app.set_module_enabled(True,'mouse')
    settle()
    mouse = app.mouse
    assert mouse.native, mouse.status
    assert time.monotonic()-mouse.last_frame<1, 'No native bridge frames received'
    assert mouse.world.cursor is not None, 'Native cursor missing'
    assert any(w.get_visible() for w in mouse.overlays), 'Mouse overlays not mapped'
    for overlay in mouse.overlays:
        assert overlay.get_window().get_pass_through(), 'Overlay intercepts mouse input'
    # A real Wayland click must reach the underlying app and create exactly one ripple.
    target = Gtk.Window()
    button = Gtk.Button(label='Click-through target')
    clicks = []
    button.connect('clicked',lambda *_: clicks.append(True))
    target.add(button)
    target.fullscreen()
    target.show_all()
    target.present()
    settle()
    mouse.world.ripples.clear()
    subprocess.run([os.environ['PLAYGROUND_TEST_INPUT'],'400','300'],check=True)
    settle(180)
    assert clicks, 'Click did not reach the application under the overlay'
    assert len(mouse.world.ripples)==1, 'Native click did not produce exactly one ripple'
    app.settings['mouse']['fullscreen'] = False
    settle(180)
    assert all(not w.get_visible() for w in mouse.overlays), 'Fullscreen suppression failed'
    target.destroy()
    app.settings['mouse']['fullscreen'] = True
    settle()
    # Exercise the fallback script in the same real compositor.
    original_call = mouse.call
    def without_native(path,interface,method,*args,**kwargs):
        if method == 'loadEffect':
            return GLib.Variant('(b)',(False,))
        return original_call(path,interface,method,*args,**kwargs)
    mouse.call = without_native
    mouse.reconnect()
    # This disposable compositor deliberately has no screen locker service.
    mouse.locked = False
    settle()
    assert mouse.script, mouse.status
    assert time.monotonic()-mouse.last_frame<1, 'No script bridge frames received'
    assert mouse.world.cursor is not None, 'Script cursor missing'
    app.set_module_enabled(False,'mouse')
    assert mouse.timer == 0 and mouse.owner is None
    assert all(not w.get_visible() for w in mouse.overlays)
    assert app.modules.enabled('edgeglow'), 'Mouse shutdown disabled Edgeglow'
    app.window.destroy()
    mouse.close()
    app.mouse = None
    app.quit()
    print('Virtual KDE Wayland bridge and click-through smoke test passed')
