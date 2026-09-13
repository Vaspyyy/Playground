from pathlib import Path
import hashlib
import tarfile

root = Path(__file__).resolve().parent.parent
out = root/'dist'
out.mkdir(exist_ok=True)
archive = out/'playground.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    for path in sorted((root/'playground').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            tar.add(path, arcname=path.relative_to(root), recursive=False)
(out/'playground.tar.gz.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  playground.tar.gz\n')
