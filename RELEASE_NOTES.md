# Playground 0.5.0 · Mouse Magic

- Mix a flowing cursor ribbon, fairy dust, soft click ripples, and scattered particles.
- Switch particle reactions between swirl, scatter, and attract. Keep a small idle cursor cloud.
- Separate toggles, four presets, and live motion, density, and brightness controls.
- Colors follow Edgeglow's palette. Both modules can run together.
- Fullscreen visibility toggle and an interactive preview inside settings.
- Read-only KWin cursor tracking, click-through overlays, and an optional native helper for global clicks.
- Existing Edgeglow settings and notification behavior are preserved.

Update through **Check for updates → Update & restart**, then open Mouse Magic and enable it.
For desktop click ripples, choose **Set up click helper…**, complete the terminal setup,
and press **Reconnect**. Setup targets CachyOS/Arch and requires administrator authentication.
Cursor trails and particles work without the helper. Rebuild the helper after KDE upgrades if needed.

Automated checks cover the renderer, settings, GTK controls, and a disposable KDE Wayland session.
Mixed monitor scaling and hardware-specific fullscreen behavior still need testing on your desktop.
