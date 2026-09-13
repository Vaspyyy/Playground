import unittest
from render import cairo, draw_glow


class RenderTests(unittest.TestCase):
    def render(self, width=640, height=360, phase=.15, opacity=.9):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        draw_glow(cairo.Context(surface), width, height, 44, phase, opacity)
        surface.flush()
        return surface

    def pixel(self, surface, x, y):
        import sys
        data = bytes(surface.get_data())
        offset = y * surface.get_stride() + x * 4
        return int.from_bytes(data[offset:offset+4], sys.byteorder)

    def test_transparent_center_and_all_edges(self):
        surface = self.render()
        self.assertEqual(self.pixel(surface, 320, 180), 0)
        for x, y in [(320, 1), (638, 180), (320, 358), (1, 180)]:
            self.assertGreater(self.pixel(surface, x, y) >> 24, 100)
        self.assertGreater(self.pixel(surface, 320, 1) >> 24,
                           self.pixel(surface, 320, 30) >> 24)

    def test_phase_changes_color_without_changing_opacity(self):
        a = self.pixel(self.render(phase=0), 320, 1)
        b = self.pixel(self.render(phase=.3), 320, 1)
        self.assertNotEqual(a & 0xffffff, b & 0xffffff)
        self.assertEqual(a >> 24, b >> 24)

    def test_zero_opacity_is_empty(self):
        surface = self.render(opacity=0)
        self.assertFalse(any(bytes(surface.get_data())))

    def test_portrait_monitor(self):
        surface = self.render(360, 640)
        self.assertEqual(self.pixel(surface, 180, 320), 0)
        self.assertGreater(self.pixel(surface, 358, 320) >> 24, 100)
