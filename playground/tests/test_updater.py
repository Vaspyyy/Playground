import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from updater import REQUIRED, extract_verified, parse_release, version_tuple
from update_helper import swap_install

class UpdaterTests(unittest.TestCase):
    def archive(self, extra=None):
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode='w:gz') as tar:
            for name in REQUIRED:
                body=b"VERSION = '0.4.0'\n" if name=='version.py' else b'\n'
                info=tarfile.TarInfo('playground/'+name);info.size=len(body)
                tar.addfile(info,io.BytesIO(body))
            if extra:
                tar.addfile(extra)
        return data.getvalue()

    def test_version_order(self):
        self.assertGreater(version_tuple('0.10.0'),version_tuple('v0.9.9'))
        with self.assertRaises(ValueError):version_tuple('0.4.0-rc1')

    def test_verified_release_extracts(self):
        data=self.archive()
        with tempfile.TemporaryDirectory() as folder:
            root=extract_verified(data,hashlib.sha256(data).hexdigest(),folder,'0.4.0')
            self.assertTrue((root/'edgeglow.py').is_file())

    def test_rejects_corruption_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):extract_verified(self.archive(),'0'*64,folder,'0.4.0')
            self.assertEqual(list(Path(folder).iterdir()),[])

    def test_rejects_traversal_and_symlinks(self):
        bad=[tarfile.TarInfo('../outside'),tarfile.TarInfo('/tmp/outside'),tarfile.TarInfo('playground/link')]
        bad[-1].type=tarfile.SYMTYPE;bad[-1].linkname='/tmp/outside'
        for entry in bad:
            data=self.archive(entry)
            with tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(ValueError):extract_verified(data,hashlib.sha256(data).hexdigest(),folder,'0.4.0')
                self.assertEqual(list(Path(folder).iterdir()),[])

    def test_rejects_unrelated_release_assets(self):
        with self.assertRaises(ValueError):
            parse_release({'tag_name':'v0.4.0','assets':[{'name':'playground.tar.gz','browser_download_url':'https://evil.example/app'}]})

    def test_failed_swap_restores_previous_app(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=root/'app';target.mkdir();(target/'old').write_text('works')
            with self.assertRaises(FileNotFoundError):swap_install(target,root/'missing',root/'backup')
            self.assertEqual((target/'old').read_text(),'works')

    def test_successful_swap_keeps_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=root/'app';target.mkdir();(target/'old').write_text('old')
            new=root/'new';new.mkdir();(new/'new').write_text('new')
            swap_install(target,new,root/'backup')
            self.assertEqual((target/'new').read_text(),'new')
            self.assertEqual((root/'backup/old').read_text(),'old')
