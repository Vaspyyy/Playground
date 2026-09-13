import unittest
from modules import ModuleController

class ModuleTests(unittest.TestCase):
    def test_modules_run_independently(self):
        events=[]
        m=ModuleController()
        m.register('a',lambda enabled:events.append(('a',enabled)))
        m.register('b',lambda enabled:events.append(('b',enabled)))
        m.set_enabled('a',True);m.set_enabled('b',True)
        self.assertEqual(m.active_count(),2)
        m.set_enabled('a',False)
        self.assertTrue(m.enabled('b'))
        self.assertEqual(events,[('a',True),('b',True),('a',False)])

    def test_duplicate_ui_updates_do_not_restart_modules(self):
        events=[];m=ModuleController();m.register('a',events.append)
        m.set_enabled('a',True);m.set_enabled('a',True)
        self.assertEqual(events,[True])

    def test_unavailable_module_cannot_be_enabled(self):
        m=ModuleController()
        with self.assertRaises(KeyError):m.set_enabled('missing',True)
        self.assertEqual(m.active_count(),0)

    def test_failed_start_does_not_report_active(self):
        m=ModuleController()
        def fail(enabled):raise RuntimeError('start failed')
        m.register('a',fail)
        with self.assertRaises(RuntimeError):m.set_enabled('a',True)
        self.assertFalse(m.enabled('a'))
