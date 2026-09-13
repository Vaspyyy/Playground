import math
import tempfile
from pathlib import Path
import unittest
from core import load, save, normalize as normalize_all
from mouse_core import DEFAULTS, PRESETS, World, normalize
from render import cairo

class MouseTests(unittest.TestCase):
    def test_settings_migrate_and_do_not_share_mutable_defaults(self):
        a,b = normalize_all({'palette':'ice'}),normalize_all({})
        a['mouse']['enabled'] = True
        self.assertFalse(b['mouse']['enabled'])
        self.assertEqual(a['palette'],'ice')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'settings.json'
            save(path,a)
            self.assertEqual(load(path),a)
        self.assertEqual(normalize({'motion':math.inf,'fullscreen':'yes'}),DEFAULTS)

    def test_click_edges_only_create_ripples_when_requested(self):
        world = World()
        settings = dict(DEFAULTS)
        world.pointer(20,20,False,0,settings)
        self.assertEqual(len(world.ripples),0)
        world.pointer(20,20,True,.1,settings)
        self.assertEqual(len(world.ripples),1)
        settings['ripples'] = False
        world.pointer(20,20,True,.2,settings)
        self.assertEqual(len(world.ripples),1)
        world.step(2,.016,settings)
        self.assertFalse(world.ripples)

    def test_stress_stays_bounded_and_finite_on_negative_origin_monitors(self):
        settings = dict(DEFAULTS,motion=100,density=100)
        world = World()
        world.reset([(-1920,0,1920,1080),(0,-300,2560,1440)])
        for i in range(2000):
            now = i/120
            world.pointer(math.sin(now)*1000,math.cos(now)*400,True,now,settings)
            world.step(now,1/120,settings)
        self.assertLessEqual(len(world.trail),100)
        self.assertLessEqual(len(world.dust),350)
        self.assertLessEqual(len(world.ripples),32)
        self.assertLessEqual(len(world.field),244)
        self.assertTrue(all(math.isfinite(v) for p in world.field for v in p))
        world.reset()
        self.assertIsNone(world.cursor)
        self.assertFalse(world.ripples)

    def test_scatter_and_attract_move_in_opposite_directions(self):
        positions = []
        for reaction in ('scatter','attract'):
            settings = dict(DEFAULTS,reaction=reaction,density=0)
            world = World()
            world.reset([(0,0,400,400)])
            world.cursor = (200,200)
            world.field = [[240.,200.,0.,0.,0.,0] for _ in range(12)]
            world.step(0,.05,settings)
            positions.append(world.field[0][0])
        self.assertGreater(positions[0],240)
        self.assertLess(positions[1],240)

    def test_presets_render_and_all_off_is_transparent(self):
        for preset in PRESETS.values():
            settings = dict(DEFAULTS,**preset)
            world = World()
            world.reset([(0,0,400,240)])
            for i in range(30):
                world.pointer(80+i*5,120+math.sin(i)*10,i==20,i/60,settings)
                world.step(i/60,1/60,settings)
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,400,240)
            world.draw(cairo.Context(surface),.5,settings,'aurora')
            surface.flush()
            self.assertTrue(any(bytes(surface.get_data())))
        off = dict(DEFAULTS, ribbon=False,dust=False,ripples=False,field=False,idle=False)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,400,240)
        world.draw(cairo.Context(surface),.5,off,'rainbow')
        surface.flush()
        self.assertFalse(any(bytes(surface.get_data())))
