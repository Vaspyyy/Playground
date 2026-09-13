import math
from pathlib import Path
import tempfile
import unittest
from core import Pulse, load, save, normalize, DEFAULTS


class TimingTests(unittest.TestCase):
    def test_burst_never_extends_or_queues(self):
        pulse = Pulse()
        self.assertTrue(pulse.trigger(100, 2))
        for now in (100, 100.5, 101.999):
            self.assertFalse(pulse.trigger(now, 6))
        self.assertFalse(pulse.active(102))
        self.assertEqual(pulse.opacity(102), 0)
        self.assertTrue(pulse.trigger(102, 2))

    def test_smooth_fades_and_no_idle_glow(self):
        pulse = Pulse()
        self.assertEqual(pulse.opacity(0), 0)
        pulse.trigger(10, 2)
        self.assertEqual(pulse.opacity(10), 0)
        self.assertAlmostEqual(pulse.opacity(10.08), .5)
        self.assertEqual(pulse.opacity(11), 1)
        self.assertGreater(pulse.opacity(11.8), pulse.opacity(11.9))
        self.assertEqual(pulse.opacity(12), 0)


class SettingsTests(unittest.TestCase):
    def test_corrupt_settings_fall_back(self):
        for raw in (None, [], 'bad', {'speed': math.nan, 'enabled': 'false'}):
            self.assertEqual(normalize(raw), DEFAULTS)

    def test_clamps_unsafe_values(self):
        result = normalize({'width': -100, 'duration': 500, 'brightness': True})
        self.assertEqual(result['width'], 8)
        self.assertEqual(result['duration'], 10)
        self.assertEqual(result['brightness'], 90)

    def test_atomic_save_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'nested/settings.json'
            save(path, dict(DEFAULTS, enabled=False, duration=3))
            self.assertFalse(load(path)['enabled'])
            self.assertEqual(load(path)['duration'], 3)
            path.write_text('{bad')
            self.assertEqual(load(path), DEFAULTS)


if __name__ == '__main__':
    unittest.main()
