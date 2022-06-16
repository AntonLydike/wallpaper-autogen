from colorsys import hsv_to_rgb
from dataclasses import dataclass
from typing import Tuple, Callable

import cairo


@dataclass(frozen=True)
class HSV:
    hue: int
    saturation: float
    value: float
    alpha: float = 1.0

    def __iter__(self):
        return self.hue, self.saturation, self.value, self.alpha

    def tuple(self):
        return self.hue, self.saturation, self.value, self.alpha

    def rgb(self):
        return hsv_to_rgb(self.hue / 359, self.saturation, self.value)

    def rgba(self) -> Tuple[float, float, float, float]:
        r, g, b = hsv_to_rgb(self.hue / 359, self.saturation, self.value)
        return r, g, b, self.alpha

    def darken(self, ammount: float) -> 'HSV':
        return HSV(self.hue, self.saturation, self.value * (1 - ammount), self.alpha)

    def desaturate(self, ammount: float) -> 'HSV':
        return HSV(self.hue, self.saturation * (1 - ammount), self.value, self.alpha)

    def copy(self, hue: int = None, saturation: float = None, value: int = None, alpha: float = None) -> 'HSV':
        """
        Create a copy, optionally overwriting existing values
        """
        orig = self.tuple()
        overrides = (hue, saturation, value, alpha)
        return HSV(*[a if a is not None else b for a, b in zip(overrides, orig)])


class Gradient:
    stops: Tuple[HSV]

    def __init__(self, *args: HSV):
        self.stops = tuple(args)

    def __getitem__(self, item):
        return self.stops[item]

    def __iter__(self):
        return iter(self.stops)

    def __len__(self):
        return len(self.stops)

    @property
    def start(self):
        return self[0]

    @property
    def end(self):
        return self[-1]

    def linear_gradient(self, x0: float, y0: float, x1: float, y1: float):
        grad = cairo.LinearGradient(x0, y0, x1, y1)
        for i, stop in enumerate(self.stops):
            grad.add_color_stop_rgba(i / len(self.stops), *stop.rgba())

        return grad

    def map(self, mapper: Callable[[int, HSV], HSV]):
        return Gradient(*(mapper(i, c) for i, c in enumerate(self.stops)))


# keep a reference to all gradients used
@dataclass(frozen=True)
class ColorGradients:
    MountainRed: Gradient = Gradient(HSV(347, .67, .65), HSV(14, .8, .95))
    SkyBlue: Gradient = Gradient(HSV(228, .85, 1), HSV(196, 1, 1))
    SunYellow: Gradient = Gradient(HSV(0, 0, 1), HSV(43, 1, 1))
    Fog: Gradient = Gradient(HSV(0, 0, 1, 1), HSV(0, 0, 0, 0))  # white to transparent

    def get_fog_at_level(self, thickness: float):
        return self.Fog.map(lambda i, c: c.copy(alpha=c.alpha * thickness))


@dataclass
class SceneParameters:
    img_dimensions: Tuple[int, int] = (3840, 2160)

    sun_height: float = .85
    sun_size: float = .1

    fog_height: float = .8
    fog_thickness: float = 1

    mountain_range_count: int = 8
    mountain_position = (.15, 0.7)
    mountain_peaks: Tuple[int, int] = (9, 22)
    mountain_roughness: float = .2
    mountain_peakiness: float = 4
