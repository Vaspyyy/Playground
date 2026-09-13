import unittest
from core import DEFAULTS, EFFECTS, PALETTES, normalize
from render import cairo, draw_effect, color, perimeter_point

class EffectsTests(unittest.TestCase):
    def render(self, effect, palette='rainbow', chaos=45, seed=17):
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, 480, 270)
        draw_effect(cairo.Context(s), 480, 270, dict(DEFAULTS, palette=palette, chaos=chaos), effect, .8, seed=seed)
        s.flush()
        return bytes(s.get_data())

    def test_all_effects_palettes_and_chaos_extremes(self):
        for effect in EFFECTS:
            for palette in PALETTES:
                for chaos in (0, 100):
                    with self.subTest(effect=effect, palette=palette, chaos=chaos):
                        pixels = self.render(effect, palette, chaos)
                        self.assertTrue(any(pixels))
                        center = (135*480+240)*4
                        self.assertEqual(pixels[center:center+4], b'\0'*4)

    def test_same_seed_same_frame(self):
        self.assertEqual(self.render('sparks'), self.render('sparks'))
        self.assertNotEqual(self.render('sparks'), self.render('sparks', seed=18))

    def test_palette_wraps_continuously(self):
        for palette in PALETTES:
            for a,b in zip(color(palette, 0), color(palette, 1-1e-8)):
                self.assertAlmostEqual(a,b, places=5)

    def test_monitors_cross_corners_together(self):
        for t in (0,.1,.25,.5,.75,.98):
            x,y=perimeter_point(t,1920,1080)
            a,b=perimeter_point(t,1080,1920)
            self.assertAlmostEqual(x/1920,a/1080)
            self.assertAlmostEqual(y/1080,b/1920)

    def test_migration_and_invalid_favorites(self):
        self.assertEqual(normalize({'width':60})['width'],60)
        for value in ([], ['missing'], None, 'sparks'):
            self.assertEqual(normalize({'favorites':value})['favorites'],DEFAULTS['favorites'])
        self.assertEqual(normalize({'favorites':['waves','waves','missing']})['favorites'],['waves'])
        self.assertEqual(normalize({'palette':'missing'})['palette'],'rainbow')
