// Read-only cursor bridge. No shortcuts, input interception, or device access.
var busy = false;
var timer = new QTimer();
timer.interval = 16;
timer.timeout.connect(function () {
    if (busy) return;
    var p = workspace.cursorPos;
    var w = workspace.activeWindow;
    var g = w && w.fullScreen ? w.frameGeometry : null;
    var state = JSON.stringify({x:p.x, y:p.y, pressed:0,
        fullscreen:g ? [g.x,g.y,g.width,g.height] : null});
    busy = true;
    callDBus('io.github.edgeglow', '/io/github/Playground/Pointer',
        'io.github.Playground.Pointer', 'Frame', state, function () { busy = false; });
});
timer.start();
