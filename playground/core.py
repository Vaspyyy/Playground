"""Settings and animation timing, independent of the desktop toolkit."""
import json
import math
import os
import tempfile
from pathlib import Path

EFFECTS = ('sparks', 'comets', 'waves', 'classic')
PALETTES = ('rainbow', 'aurora', 'fire', 'ice', 'candy', 'sunset')
DEFAULTS = dict(width=44, brightness=90, speed=0.22, duration=2.0, enabled=True,
                chaos=45, palette='rainbow', favorites=['sparks', 'comets', 'waves'])
LIMITS = dict(width=(8, 120), brightness=(5, 100), speed=(0.02, 1.0), duration=(0.5, 10.0), chaos=(0, 100))


def normalize(raw):
    result = dict(DEFAULTS, favorites=list(DEFAULTS['favorites']))
    if not isinstance(raw, dict):
        return result
    for key, (low, high) in LIMITS.items():
        value = raw.get(key)
        if type(value) in (int, float) and math.isfinite(value):
            result[key] = max(low, min(high, value))
    if type(raw.get('enabled')) is bool:
        result['enabled'] = raw['enabled']
    if raw.get('palette') in PALETTES:
        result['palette'] = raw['palette']
    if isinstance(raw.get('favorites'), list):
        favorites = [e for e in EFFECTS if e in raw['favorites']]
        if favorites:
            result['favorites'] = favorites
    return result


def load(path):
    try:
        return normalize(json.loads(Path(path).read_text()))
    except (OSError, ValueError):
        return normalize({})


def save(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.settings-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as output:
            json.dump(normalize(values), output, indent=2)
            output.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Pulse:
    def __init__(self):
        self.start = -math.inf
        self.duration = 2.0

    def active(self, now):
        return 0 <= now - self.start < self.duration

    def trigger(self, now, duration):
        if self.active(now):
            return False
        self.start, self.duration = now, duration
        return True

    def opacity(self, now):
        age = now - self.start
        if not self.active(now):
            return 0.0
        fade_in = min(0.16, self.duration / 4)
        fade_out = min(0.45, self.duration / 3)
        fraction = min(1.0, age / fade_in, (self.duration - age) / fade_out)
        return fraction * fraction * (3 - 2 * fraction)
