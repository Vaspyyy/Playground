# Playground

A cozy desktop effects playground for **CachyOS / KDE Plasma Wayland**.

Edgeglow is the first working module: rainbow waves, sparks, comets, six palettes,
a chaos slider, and continuous screen preview. Effects synchronize across monitors
and react to notifications, including during Do Not Disturb. Mouse magic,
atmosphere, toys, and audio visuals are planned.

## Install or upgrade in one command

Run this in your desktop terminal, as your normal user:

```sh
curl -fsSL https://raw.githubusercontent.com/Vaspyyy/Playground/main/install-online.py -o /tmp/playground-install.py && python3 /tmp/playground-install.py
```

It downloads the latest release, verifies its checksum, extracts it automatically,
and runs the per-user installer. Existing settings are kept. No GitHub account or
access token is required. The bootstrap requires Python 3 and curl. If necessary:

```sh
sudo pacman -S --needed python python-gobject python-cairo gtk3 gtk-layer-shell curl
```

After this upgrade, open **Playground → Check for updates → Update & restart**.
There is no automatic background downloading and no repeated manual extraction.

Updates come only from this repository's stable GitHub releases. They are checked
for corruption, invalid paths, links, incomplete contents, and Python syntax.
The previous installation is retained. If the replacement fails its startup check,
the updater restores and relaunches the previous app. Appearance settings live
separately and are not replaced.

The checksum detects damaged downloads; the GitHub repository remains the trust
source for the code. App updates do not install new system dependencies.

## Development

Source lives in `playground/`. Run tests there:

```sh
python3 -m unittest discover -s tests -v
```

Each push to `main` runs tests and a GTK settings smoke test. To publish a new
release, update `playground/version.py` and `RELEASE_NOTES.md`, then push. The workflow
builds assets and publishes `v<VERSION>` only after checks pass. Existing releases
are not overwritten. Overlay behavior still requires a real KDE Wayland session.

[Releases](https://github.com/Vaspyyy/Playground/releases) ·
[Full app guide](playground/README.md)

MIT licensed.
