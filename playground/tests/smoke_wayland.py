"""Run inside a disposable virtual KWin session, with the compiled helper installed."""
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory() as directory:
    os.environ['XDG_CONFIG_HOME'] = directory
    import edgeglow
    from gi.repository import GLib
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
