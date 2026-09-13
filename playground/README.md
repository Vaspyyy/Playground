# Playground 0.5.0

A cozy desktop effects playground for CachyOS / KDE Plasma Wayland.
Edgeglow and Mouse Magic can run together, with separate settings and enable switches.
Atmosphere, Little toys, Sound & color, and interactive play mode remain planned.

## Install and update

Existing users: **Check for updates → Update & restart**. Your settings are preserved.
For a new installation, run as your normal desktop user:

```sh
curl -fsSL https://raw.githubusercontent.com/Vaspyyy/Playground/main/install-online.py -o /tmp/playground-install.py && python3 /tmp/playground-install.py
```

For manual source installation, run `./install.sh` from this folder. It lists any
missing desktop dependencies. The base app installs per user without compilation.
The optional Mouse Magic click helper has a separate setup action described below.

The internal app ID and installed directory remain `edgeglow` to preserve settings
and avoid duplicate startup entries. Login startup is controlled in the global footer.

## Included Edgeglow effects

- Sparks scatter glowing particles near the edges.
- Comets race around the border with colorful tails and bright heads.
- Waves ripple as multiple neon ribbons.
- Choose favorites; each notification randomly selects one. Classic remains available.
- Rainbow, Aurora, Fire, Ice, Candy, and Sunset palettes.
- Chaos slider changes particle count, travel distance, comet count and tails, or wave complexity.
- Continuous screen preview keeps the selected effect running while you adjust sliders.
- Use **Try another effect** to pick a new random preview. Random choices can repeat.
- Closing settings stops continuous preview. Notification behavior continues normally.
- Every monitor shares the effect, seed, clock, and palette. New effect corner crossings
  use normalized screen positions, so differently shaped displays stay synchronized.

Open **Playground** in KDE's application launcher whenever you want to change settings.
Closing the settings window leaves the listener running. The **Quit** button stops
it until the next launch or login. Disable login startup in settings if desired.
Reinstalling enables login startup again; your appearance settings are preserved.

## Edgeglow defaults

| Option | Behavior |
| --- | --- |
| Appearance | Vivid rainbow, broad inward glow, 44 logical pixels, 90% brightness |
| Animation | Random favorite: Sparks, Comets, or Waves; Classic is optional |
| Timing | 2 seconds, including a short fade in and a soft fade out |
| Monitors | Every connected monitor, including portrait layouts |
| Fullscreen | Uses Wayland's overlay layer, intended to appear above fullscreen apps |
| Repeated notifications | Arrivals during an active animation are ignored, with no queue or extension |
| Do Not Disturb | Glow still triggers when an app submits a desktop notification |
| KDE popups | KDE retains its own popup behavior and Do Not Disturb settings |
| Mouse and keyboard | Empty input region, no keyboard focus, clicks pass through |
| Settings | Favorites, palette, chaos, width, brightness, speed, duration, enable switch, login startup, continuous preview |
| Idle behavior | Overlay windows are hidden; no animation timer runs |

Width is measured in logical pixels, so display scaling affects its physical size.
There is no tray icon; reopen settings through the application launcher.

## Quick check on your desktop

1. Open Playground, choose **Open & play** on Edgeglow, and confirm that its status says it is listening.
2. Click **Try another effect** for a timed preview, or enable **Continuous screen preview** and adjust sliders. All monitors should animate together.
3. With `notify-send` installed (Arch package `libnotify`), run:

   ```sh
   notify-send 'Edgeglow test' 'The screen edges should glow.'
   ```

4. Enable KDE Do Not Disturb and repeat. The glow should still appear, while KDE
   decides whether to show the ordinary popup.
5. Check a fullscreen app and click near a screen edge during preview to verify
   overlay placement and input pass-through on your KWin version.

The app listens for standard `org.freedesktop.Notifications.Notify` calls using a
separate D-Bus monitoring connection. It never owns or replaces KDE's notification
service. Notification text is neither parsed nor saved. Network access is used only when
you check for or download an app update.

Notifications an application never submits, such as a disabled in-app notification,
cannot trigger the glow. Custom in-app banners that bypass the desktop notification
service are not detected. A notification update submitted through Notify also
counts as an arrival. No attempt is made to display over the secure lock screen.

## Troubleshooting

- **Missing dependencies:** run the pacman command above and retry the installer.
- **Wayland layer shell unavailable:** confirm KDE's About this System page says
  Wayland. This build does not support X11 or GNOME.
- **Listener unavailable:** the settings window displays the actual D-Bus error.
  Monitoring may be restricted by session policy. The app retries periodically and
  does not alter bus policies. Preview remains available.
- **No glow for one app:** check that it actually sends desktop notifications.
- **Settings hidden:** open Playground again from the launcher. Only one app instance
  owns the listener, including when login startup has already launched it.

To see diagnostic output, quit Playground, then run:

```sh
/usr/bin/python3 "${XDG_DATA_HOME:-$HOME/.local/share}/edgeglow/edgeglow.py"
```

## Uninstall

From the extracted folder:

```sh
./install.sh --uninstall
```

Or run the installed uninstaller:

```sh
/usr/bin/python3 "${XDG_DATA_HOME:-$HOME/.local/share}/edgeglow/install.py" --uninstall
```

Saved appearance settings are retained under `${XDG_CONFIG_HOME:-$HOME/.config}/edgeglow`.

## Verification and limitations

Thirty unit tests cover timing, settings migration, bounded particle simulation,
rendering, module independence, and update verification. GTK smoke tests check both
settings pages and their controls. A disposable KDE Wayland session tests native
and script cursor tracking, click ripples, actual input passing to the underlying
window, fullscreen suppression, and module shutdown. The native helper is compiled
against current Arch KWin as a release gate.

These checks do not replace testing mixed monitor scaling, your GPU, and specific
fullscreen games on your desktop. Mouse Magic and continuous Edgeglow preview use
an animation timer while enabled. Closing settings stops the local preview;
Mouse Magic keeps running until its module is disabled or Playground quits.

For development, run `python3 -m unittest discover -s tests -v` from this folder.
Tests can use Pycairo or cairocffi; the installed app uses Pycairo.

## Technical references

- [GTK Layer Shell, including KDE Wayland support](https://github.com/wmww/gtk-layer-shell)
- [Layer placement, monitor anchoring, keyboard mode and exclusive zones](https://wmww.github.io/gtk-layer-shell/)
- [D-Bus monitoring specification](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [Gio message-filter threading and dispatch rules](https://docs.gtk.org/gio/method.DBusConnection.add_filter.html)

MIT licensed. Source is included.


## Adding a module later

`modules.py` owns the catalog and independent lifecycle controller. A future module
can register its own enable/disable callback without stopping other modules. Add its
settings page and implement its runtime before marking its catalog entry available.
The current overlay and notification backend remain in `edgeglow.py`; the module
browser and card illustrations are in `playground_ui.py`.

## Mouse Magic

Open Mouse Magic from the module browser. Mix the ribbon, fairy dust, click ripples,
scattered particles, and idle cursor cloud using separate toggles, or start with
Fairy garden, Comet, Quiet orbit, or Everything. Motion, density, and brightness
change live. Particles can swirl, scatter, or attract. Colors always follow the
Edgeglow palette, even when Edgeglow itself is switched off.

The module is initially off. Enabling it starts a read-only, per-user KWin script
for global cursor position. Normal applications receive mouse input as usual.
The fullscreen switch hides Mouse Magic on the active fullscreen window's monitor.
Locking the session hides the effects. Disabling the module stops the bridge.

Global click ripples need the native KWin helper. **Set up click helper…** opens
Konsole, installs build dependencies with your confirmation, compiles against your
installed KWin headers, and asks for administrator authentication to install the
small plugin. This setup currently targets CachyOS/Arch. Then press **Reconnect**.
Trails and particles work without the helper, and the local preview always supports
clicks. No input device permissions, input grabs, or root background process are used.

After a KDE upgrade, re-run helper setup if the module falls back to cursor-only
mode. The helper is deliberately built on your machine because KWin's native plugin
ABI changes. The app updater preserves Mouse Magic settings, but does not install
system packages or rebuild the helper automatically. To remove the optional helper,
first disable Mouse Magic, then remove
`/usr/lib/qt6/plugins/kwin/effects/plugins/playground_mouse.so` as administrator.
