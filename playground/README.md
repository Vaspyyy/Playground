# Playground 0.3.0

A cozy desktop effects playground for CachyOS / KDE Plasma Wayland. Edgeglow is its first working module.

## New in Playground 0.3.0

- A soft pastel module browser with rounded cards and springy illustrated hover animations.
- Edgeglow has its own control page and synchronized enable switches on its card and controls.
- An independent module lifecycle controller, ready for simultaneous modules without exclusive selection.
- Mouse magic, Atmosphere, Little toys, and Sound & color are clearly marked Planned.
  They have no working effects or toggles in this release. Interactive play mode is also future work.
- Start-at-login control and Quit Playground are available in the global footer.
- Returning to the module browser stops continuous preview; notification effects keep working.

### Upgrade from Edgeglow

Extract this release into a fresh folder, then run `./install.sh`. Your dependencies,
settings, favorites, palettes, and startup integration are reused. The application
launcher now says **Playground**. The internal application ID and installed directory
remain `edgeglow` to prevent duplicate startup entries and preserve existing settings.
No extra packages are required.

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

### Upgrade from 0.1.0

Extract this release into a new folder and run `./install.sh` there. No new packages
are required if the previous version works. The installer stops the previous instance,
updates the installed files, and opens settings. Existing appearance values are preserved.
New defaults select Sparks, Comets, and Waves, Rainbow palette, and 45% chaos.
Continuous preview is never saved or enabled automatically on startup.

## Install

Extract `playground-0.3.0.tar.gz`, open a terminal in the extracted `edgeglow` folder, and run:

```sh
sudo pacman -S --needed python python-gobject python-cairo gtk3 gtk-layer-shell
./install.sh
```

Run the installer as your normal desktop user. Only the package installation uses sudo.
The installer copies the app into your user application directory, adds its icon and
application launcher entry, enables login startup, and opens settings when run from
a Wayland session. No compilation, pip, AUR helper, or KDE restart is needed.

Open **Playground** in KDE's application launcher whenever you want to change settings.
Closing the settings window leaves the listener running. The **Quit** button stops
it until the next launch or login. Disable login startup in settings if desired.
Reinstalling enables login startup again; your appearance settings are preserved.

## Your defaults

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
service. Notification text is neither parsed nor saved. It has no network code.

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
- **Settings hidden:** open Edgeglow again from the launcher. Only one app instance
  owns the listener, including when login startup has already launched it.

To see diagnostic output, quit Edgeglow, then run:

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

Eighteen automated tests pass, covering the original timing and settings checks,
all effect/palette combinations at both chaos extremes, deterministic particles,
synchronized corner positions, palette continuity, migration from old settings, and independent module lifecycle behavior. Python syntax and the installer shell syntax were checked.
`preview.png` is rendered with the app's actual Cairo drawing function over a demo
background. It is not a screenshot of a live desktop or settings window.

You reported the original 0.1.0 worked in your desktop tests. This update preserves
that notification and Wayland integration. The Playground module browser and its controls have not been run in a live KDE
session here. The renderer and module lifecycle tests run independently of GTK;
the new interface still needs verification on your desktop.
Effects use a reusable lower-resolution intermediate for soft light to limit raster
work on large screens. Continuous preview consumes CPU while running; it stops
when you close settings. Notification bursts are ignored during continuous preview.

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
