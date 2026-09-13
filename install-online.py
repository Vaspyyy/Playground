"""GitHub release discovery and bounded, verified extraction. No GTK dependency."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import tarfile
import tempfile
import urllib.request

REPOSITORY = 'Vaspyyy/Playground'
API = f'https://api.github.com/repos/{REPOSITORY}/releases/latest'
MAX_ARCHIVE = 16 * 1024 * 1024
MAX_UNPACKED = 40 * 1024 * 1024
REQUIRED = {'edgeglow.py', 'core.py', 'render.py', 'modules.py', 'playground_ui.py',
            'updater.py', 'update_ui.py', 'update_helper.py', 'version.py', 'install.py', 'install.sh', 'edgeglow.svg', 'LICENSE'}


def version_tuple(version):
    if not isinstance(version, str) or not re.fullmatch(r'v?\d+\.\d+\.\d+', version):
        raise ValueError('Invalid release version')
    return tuple(map(int, version.lstrip('v').split('.')))


def fetch(url, limit):
    if not url.startswith('https://'):
        raise ValueError('Only HTTPS downloads are supported')
    request = urllib.request.Request(url, headers={'User-Agent': 'Playground-Updater', 'Accept': 'application/vnd.github+json' if url == API else 'application/octet-stream'})
    with urllib.request.urlopen(request, timeout=20) as response:
        if not response.geturl().startswith('https://'):
            raise ValueError('Insecure download redirect')
        data = response.read(limit+1)
    if len(data) > limit:
        raise ValueError('Download exceeds size limit')
    return data


def parse_release(raw):
    tag = raw.get('tag_name')
    version_tuple(tag)
    if raw.get('draft') or raw.get('prerelease'):
        raise ValueError('Release is not stable')
    prefix = f'https://github.com/{REPOSITORY}/releases/download/{tag}/'
    assets = {a.get('name'): a.get('browser_download_url') for a in raw.get('assets', [])}
    result = {'version': tag.lstrip('v')}
    for name, key in [('playground.tar.gz', 'archive'), ('playground.tar.gz.sha256', 'checksum')]:
        if assets.get(name) != prefix+name:
            raise ValueError('Release assets are missing or have unexpected URLs')
        result[key] = assets[name]
    return result


def latest_release():
    return parse_release(json.loads(fetch(API, 2*1024*1024)))


def extract_verified(data, expected, directory, release_version):
    if not re.fullmatch('[a-fA-F0-9]{64}', expected) or hashlib.sha256(data).hexdigest() != expected.lower():
        raise ValueError('Release checksum mismatch')
    directory = Path(directory)
    seen, total = set(), 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        if len(members) > 500:
            raise ValueError('Too many archive entries')
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'playground':
                raise ValueError('Unsafe archive path')
            if not (member.isdir() or member.isfile()):
                raise ValueError('Archive links and special files are not allowed')
            if path.as_posix() in seen:
                raise ValueError('Duplicate archive entry')
            seen.add(path.as_posix())
            total += member.size
            if total > MAX_UNPACKED:
                raise ValueError('Unpacked release too large')
        files = {str(PurePosixPath(m.name).relative_to('playground')) for m in members if m.isfile()}
        if not REQUIRED.issubset(files):
            raise ValueError('Incomplete release')
        for member in members:
            dest = directory / member.name
            if member.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source:
                    dest.write_bytes(source.read())
                dest.chmod(0o755 if member.name.endswith('.sh') else 0o644)
    root = directory/'playground'
    text = (root/'version.py').read_text()
    if text.strip() != f"VERSION = '{release_version}'":
        raise ValueError('Release version does not match archive')
    for source in root.rglob('*.py'):
        compile(source.read_text(), str(source), 'exec')
    return root


def stage_release(release, parent):
    data = fetch(release['archive'], MAX_ARCHIVE)
    checksum = fetch(release['checksum'], 1024).decode('ascii').strip().split()[0]
    with tempfile.TemporaryDirectory(prefix='.playground-download-', dir=parent) as temporary:
        root = extract_verified(data, checksum, temporary, release['version'])
        # Move validated files to a persistent staging directory for the restart helper.
        staged = Path(tempfile.mkdtemp(prefix='.playground-update-', dir=parent))
        root.rename(staged/'playground')
        return staged/'playground'


if __name__ == '__main__':
    import subprocess
    import sys
    if os.geteuid() == 0:
        sys.exit('Run this installer without sudo.')
    print('Finding the latest Playground release…', flush=True)
    with tempfile.TemporaryDirectory(prefix='playground-install-') as folder:
        release = latest_release()
        staged = stage_release(release, folder)
        print('Verified Playground '+release['version']+'. Installing…', flush=True)
        subprocess.run(['/bin/bash', str(staged/'install.sh')], check=True)
