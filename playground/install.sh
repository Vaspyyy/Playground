#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "${1:-}" == "--uninstall" ]]; then
    exec /usr/bin/python3 install.py --uninstall
fi
if ! /usr/bin/python3 -c 'import gi, cairo; gi.require_version("Gtk", "3.0"); gi.require_version("GtkLayerShell", "0.1"); from gi.repository import Gtk, GtkLayerShell' 2>/dev/null; then
    echo 'Install the required CachyOS packages, then run ./install.sh again:'
    echo 'sudo pacman -S --needed python python-gobject python-cairo gtk3 gtk-layer-shell'
    exit 1
fi
exec /usr/bin/python3 install.py
