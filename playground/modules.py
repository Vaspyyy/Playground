"""Small module lifecycle registry. Modules are independently enabled, never exclusive."""
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class ModuleSpec:
    key: str
    title: str
    summary: str
    color: str
    available: bool = False

CATALOG = (
    ModuleSpec('edgeglow', 'Edgeglow', 'A little magic around the edges.\nWaves, sparks, comets & color.', '#a48bd4', True),
    ModuleSpec('mouse', 'Mouse magic', 'Trails, click ripples and tiny sparks\nthat follow your curiosity.', '#d99580', True),
    ModuleSpec('atmosphere', 'Atmosphere', 'Rainy afternoons, falling snow\nand a sky full of fireflies.', '#78a897'),
    ModuleSpec('toys', 'Little toys', 'Bouncy things, curious creatures\nand a little playful physics.', '#d1af65'),
    ModuleSpec('audio', 'Sound & color', 'Let your desktop dance\nto whatever is playing.', '#88a8cf'),
)

class ModuleController:
    def __init__(self):
        self._callbacks: dict[str, Callable[[bool], None]] = {}
        self._enabled: dict[str, bool] = {}

    def register(self, key, callback, enabled=False):
        if key in self._callbacks:
            raise ValueError('Module already registered: ' + key)
        self._callbacks[key] = callback
        self._enabled[key] = bool(enabled)

    def enabled(self, key):
        return self._enabled.get(key, False)

    def set_enabled(self, key, enabled):
        if key not in self._callbacks:
            raise KeyError('Module is not installed: ' + key)
        enabled = bool(enabled)
        if self._enabled[key] != enabled:
            self._callbacks[key](enabled)
            self._enabled[key] = enabled

    def active_count(self):
        return sum(self._enabled.values())
