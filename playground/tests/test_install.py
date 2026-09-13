from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import install

class DesktopRepairTests(unittest.TestCase):
    def test_update_repairs_icon_and_launcher_without_enabling_autostart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = dict(ENTRY=root/'apps/io.github.edgeglow.desktop',
                          ICON=root/'icons/io.github.edgeglow.svg',
                          STARTUP=root/'autostart/io.github.edgeglow.desktop')
            with patch.multiple(install, **values), patch.object(install.shutil,'which',return_value=None):
                install.refresh_desktop_integration()
                self.assertFalse(install.STARTUP.exists())
                self.assertIn('Icon='+str(install.ICON),install.ENTRY.read_text())
                self.assertIn('StartupWMClass=io.github.edgeglow',install.ENTRY.read_text())
                self.assertEqual(install.ICON.read_text(),(install.SOURCE/'edgeglow.svg').read_text())
                install.ENTRY.write_text('stale launcher')
                install.STARTUP.parent.mkdir()
                install.STARTUP.write_text('stale startup entry')
                install.refresh_desktop_integration()
                self.assertIn('--background',install.STARTUP.read_text())
                self.assertIn('Icon='+str(install.ICON),install.ENTRY.read_text())
