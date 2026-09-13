#!/usr/bin/env bash
set -euo pipefail
trap 'echo "Setup failed. Keep this output for troubleshooting."; read -r -p "Press Enter to close."' ERR
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
echo 'This installs the small Playground click helper into KDE’s system plugin directory.'
echo 'It requires administrator authentication. Re-run after a major KDE update.'
if ! command -v pacman >/dev/null; then
    echo 'Automatic dependency setup currently supports CachyOS and Arch only.'
    exit 1
fi
sudo pacman -S --needed base-devel cmake extra-cmake-modules vulkan-headers
build_dir=$(mktemp -d -t playground-mouse-build.XXXXXX)
cmake -S kwin_mouse -B "$build_dir" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build "$build_dir" --parallel 2
# Install a new inode so an already loaded helper is never overwritten in place.
plugin_dir=/usr/lib/qt6/plugins/kwin/effects/plugins
sudo install -Dm755 "$build_dir/playground_mouse.so" "$plugin_dir/playground_mouse.so.new"
sudo mv -f -- "$plugin_dir/playground_mouse.so.new" "$plugin_dir/playground_mouse.so"
echo 'Helper installed. Return to Mouse Magic and press Reconnect.'
read -r -p 'Press Enter to close.'
