"""Explicit user-triggered updater. Network and validation run off the GTK thread."""
import os
from pathlib import Path
import shutil
import subprocess
import threading
from gi.repository import Gtk, GLib
from version import VERSION
from updater import latest_release, stage_release, version_tuple


class UpdateControls(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.app, self.release = app, None
        row = Gtk.Box(spacing=10)
        self.label = Gtk.Label(label='Playground '+VERSION, xalign=0)
        row.pack_start(self.label, True, True, 0)
        self.button = Gtk.Button(label='Check for updates')
        self.button.connect('clicked', self.clicked)
        row.pack_end(self.button, False, False, 0)
        self.pack_start(row, False, False, 0)
        self.detail = Gtk.Label(label='Updates from Vaspyyy/Playground on GitHub', xalign=0)
        self.detail.set_line_wrap(True)
        self.detail.set_max_width_chars(65)
        self.pack_start(self.detail, False, False, 0)

    def clicked(self, *args):
        self.button.set_sensitive(False)
        self.detail.set_text('Downloading and checking update…' if self.release else 'Checking GitHub…')
        threading.Thread(target=self.work, daemon=True).start()

    def work(self):
        try:
            if not self.release:
                release = latest_release()
                GLib.idle_add(self.checked, release)
            else:
                target = Path(__file__).resolve().parent
                data = Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share')).resolve()
                if target != data/'edgeglow':
                    raise RuntimeError('Run ./install.sh once before using in-app updates')
                staged = stage_release(self.release, data)
                # Use the currently installed helper, outside the directory being replaced.
                helper = staged.parent/'update_helper.py'
                shutil.copy2(target/'update_helper.py', helper)
                GLib.idle_add(self.restart, helper, target, staged)
        except Exception as error:
            GLib.idle_add(self.failed, str(error))

    def checked(self, release):
        self.button.set_sensitive(True)
        if version_tuple(release['version']) > version_tuple(VERSION):
            self.release = release
            self.button.set_label('Update & restart')
            self.detail.set_text('Version '+release['version']+' is available. Your settings will be kept.')
        else:
            self.detail.set_text('You’re up to date.')
        return False

    def failed(self, message):
        self.button.set_sensitive(True)
        self.detail.set_text('Update unavailable: '+message)
        return False

    def restart(self, helper, target, staged):
        try:
            subprocess.Popen(['/usr/bin/python3', str(helper), str(target), str(staged), str(os.getpid())], start_new_session=True)
            self.app.quit()
        except OSError as error:
            self.failed(str(error))
        return False
