"""Standalone process: wait for exit, replace app directory, verify startup, roll back."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def swap_install(target, staged, backup):
    target.rename(backup)
    try:
        staged.rename(target)
    except Exception:
        backup.rename(target)
        raise


def main():
    target, staged, old_pid = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), int(sys.argv[3])
    data = Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share')).resolve()
    if target != data/'edgeglow' or staged.parent.parent != data or not staged.parent.name.startswith('.playground-update-'):
        raise ValueError('Unexpected update location')
    state = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'playground'
    state.mkdir(parents=True, exist_ok=True)
    log = state/'last-update.txt'
    backup_parent = Path(tempfile.mkdtemp(prefix='edgeglow-previous-', dir=data))
    backup = backup_parent/'edgeglow'
    ready = staged.parent/'ready'
    try:
        for _ in range(100):
            try:
                os.kill(old_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Playground did not exit. Update was not installed.')
        swap_install(target, staged, backup)
        try:
            with (state/'startup.log').open('w') as output:
                process = subprocess.Popen(['/usr/bin/python3', str(target/'edgeglow.py'), '--update-ready', str(ready)],
                    stdout=output, stderr=output, start_new_session=True)
            for _ in range(150):
                if ready.exists():
                    log.write_text('Update installed. Previous version: '+str(backup))
                    return
                if process.poll() is not None:
                    break
                time.sleep(.1)
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
            raise RuntimeError('New version failed its startup check')
        except Exception:
            failed = backup_parent/'failed-update'
            target.rename(failed)
            backup.rename(target)
            subprocess.Popen(['/usr/bin/python3', str(target/'edgeglow.py')], start_new_session=True)
            raise
    except Exception as error:
        log.write_text('Update failed: '+str(error)+'. If replacement occurred, the previous version was restored.')


if __name__ == '__main__':
    main()
