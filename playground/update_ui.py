"""Explicit user-triggered updater. Network and validation run off the GTK thread."""
import os
from pathlib import Path
import shutil
import subprocess
import threading
from gi.repository import Gtk, GLib
from version import VERSION
from updater import REPOSITORY, latest_release, stage_release, version_tuple
from ui_kit import button, label


class UpdateControls(Gtk.Box):
    def __init__(self, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.app, self.release = app, None
        self.set_valign(Gtk.Align.CENTER)
        row = Gtk.Box(spacing=4)
        self.label = label('Playground '+VERSION, 'pg-muted')
        row.pack_start(self.label, False, False, 0)
        self.button = button('Check for updates', 'pg-link', on_click=self.clicked)
        self.button.set_tooltip_text('Updates come only from '+REPOSITORY+' on GitHub')
        row.pack_start(self.button, False, False, 0)
        self.pack_start(row, False, False, 0)
        self.detail = label('', 'pg-muted', 'pg-small', wrap=True)
        self.detail.set_max_width_chars(60)
        self.detail.set_no_show_all(True)
        self.pack_start(self.detail, False, False, 0)

    def say(self, text):
        self.detail.set_text(text)
        self.detail.set_visible(bool(text))

    def clicked(self, *args):
        self.button.set_sensitive(False)
        self.say('Downloading and checking update…' if self.release else 'Checking GitHub…')
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
            context = self.button.get_style_context()
            context.remove_class('pg-link')
            context.add_class('pg-primary')
            self.say('Version '+release['version']+' is available. Your settings will be kept.')
        else:
            self.say('You’re up to date.')
        return False

    def failed(self, message):
        self.button.set_sensitive(True)
        self.say('Update unavailable: '+message)
        return False

    def restart(self, helper, target, staged):
        try:
            subprocess.Popen(['/usr/bin/python3', str(helper), str(target), str(staged), str(os.getpid())], start_new_session=True)
            self.app.quit()
        except OSError as error:
            self.failed(str(error))
        return False
