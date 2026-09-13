#!/usr/bin/python3
"""Per-user installation. No root privileges or changes to KDE settings."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parent
DATA = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
TARGET = DATA / 'edgeglow'
ENTRY = DATA / 'applications/io.github.edgeglow.desktop'
STARTUP = CONFIG / 'autostart/io.github.edgeglow.desktop'
ICON = DATA / 'icons/hicolor/scalable/apps/io.github.edgeglow.svg'
FILES = ['edgeglow.py', 'core.py', 'render.py', 'README.md', 'LICENSE', 'install.py', 'modules.py', 'playground_ui.py', 'updater.py', 'update_ui.py', 'update_helper.py', 'version.py', 'edgeglow.svg', 'mouse_core.py', 'mouse_magic.py', 'mouse_ui.py', 'pointer.js', 'setup-mouse.sh',
         'kwin_mouse/CMakeLists.txt', 'kwin_mouse/main.cpp', 'kwin_mouse/metadata.json']


def desktop(argument=''):
    path = str(TARGET / 'edgeglow.py')
    path = path.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
    return ('[Desktop Entry]\nType=Application\nName=Playground\n'
            'Comment=A cozy desktop effects playground\nIcon=io.github.edgeglow\n'
            f'Exec=/usr/bin/python3 "{path}" {argument}\n'
            'Terminal=false\nCategories=Utility;\nStartupNotify=false\n')


def stop_existing():
    if (TARGET / 'edgeglow.py').exists() and os.environ.get('WAYLAND_DISPLAY'):
        try:
            subprocess.run(['/usr/bin/python3', str(TARGET / 'edgeglow.py'), '--quit'],
                           timeout=8, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            sys.exit('Close Edgeglow before updating or uninstalling, then retry.')


def main():
    if os.geteuid() == 0:
        sys.exit('Run the installer as your normal desktop user, without sudo.')
    stop_existing()
    if '--uninstall' in sys.argv:
        for path in [ENTRY, STARTUP, ICON] + [TARGET / name for name in FILES]:
            path.unlink(missing_ok=True)
        print('Playground removed. Your saved settings were kept in ' + str(CONFIG / 'edgeglow'))
        return
    TARGET.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        if (SOURCE / name).resolve() != (TARGET / name).resolve():
            (TARGET / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / name, TARGET / name)
    for path, content in [(ENTRY, desktop()), (STARTUP, desktop('--background')),
                          (ICON, (SOURCE / 'edgeglow.svg').read_text())]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    if shutil.which('update-desktop-database'):
        subprocess.run(['update-desktop-database', str(ENTRY.parent)], check=False)
    print('Installed. Open Playground from your application launcher. Login startup is enabled.')
    if os.environ.get('WAYLAND_DISPLAY'):
        subprocess.Popen(['/usr/bin/python3', str(TARGET / 'edgeglow.py')],
                         start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
