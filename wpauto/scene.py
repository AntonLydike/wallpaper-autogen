import math
import random
from typing import Tuple, List

import cairo

from .defs import SceneParameters, ColorGradients, HSV
from .interpol import sample_linear


def draw_sky(surface: cairo.Surface, params: SceneParameters, palette: ColorGradients):
    ctx = cairo.Context(surface)
    ctx.rectangle(0, 0, *params.img_dimensions)
    ctx.set_line_width(0)
    ctx.set_source(palette.SkyBlue.linear_gradient(0, 0, *params.img_dimensions))
    ctx.fill()


def good_random_numbers(num: int, min: float, max: float, min_diff_percent: float = 0.2):
    """
    Generate random numbers between min und max, which are at least
    min_diff_percent different

    :param num: how many numbers to generate
    :param min: minimum value
    :param max: maximum value
    :param min_diff_percent: percentage (of max-min) each value differs from the previous
    :return: a generator generating num random values
    """
    if num == 0:
        return

    if min_diff_percent > 0.45:
        print("Warning: some value might be overtuned, rng generation is very restricted and might take a long time")

    if min_diff_percent > 0.49:
        print("Values were corrected to prevent infinite loops!")
        min_diff_percent = 0.49

    size = max - min
    prev = random.random()
    yield prev * size + min

    for i in range(num - 1):
        new = random.random()
        while abs(new - prev) < min_diff_percent:
            new = random.random()
        yield new * size + min
        prev = new


def generate_peaks(num: Tuple[int, int], bounds: Tuple[float, float], dims: Tuple[int, int], peakiness: float,
                   roughness: float=0):
    min, max = bounds
    # we generate two extra peaks, which will be positioned off-screen on the left and right sides
    num_peaks = random.randint(*num) + 2

    # generate the height of the peaks
    peaks_y = [pos for pos in good_random_numbers(num_peaks, min, max, 0.3 * peakiness)]

    # generate the x positions of the peaks
    # we want somewhat evenly distributed peaks among the x-axis
    # so we start with a completely even distribution
    peaks_x = [(i - .5) / (num_peaks - 2) for i in range(num_peaks)]
    # se subtract .5 to space them in the middle of each interval

    # now we add a little bit of random jitter (20% of the space between mountains)
    jitter_amount = .2 / (num_peaks - 2)
    # we also transform coordinates from [0,1) to [0,pic_width)

    peaks_x = [
        (x + (random.random() - .5) * jitter_amount) for x in peaks_x
    ]

    # TODO: introduce roughness into cliffs

    # transform to pixel space
    peaks_x = [
        (1-x) * dims[0] for x in peaks_x
    ]
    peaks_y = [
        y * dims[1] for y in peaks_y
    ]

    # "fill" the box by adding two points on the bottom of the frame
    return list(zip(peaks_x, peaks_y)) + [(0, dims[1]), (dims[0], dims[1])]


def draw_mountains(surface: cairo.Surface, params: SceneParameters, palette: ColorGradients):
    start, end = params.mountain_position
    num_mountains = params.mountain_range_count

    def get_bounds(i: int):
        return sample_linear(
            start, end,
            i, num_mountains
        ), sample_linear(
            start * params.mountain_peakiness, end,
            i + 1, params.mountain_range_count
        )

    ctx = cairo.Context(surface)
    ctx.set_line_width(0)

    for i in range(num_mountains):
        # calc where these mountains start and end
        bounds = get_bounds(i)

        # generate path for the mountains
        peakiness = sample_linear(0.4, 0.1, i, num_mountains - 1)
        path = generate_peaks(params.mountain_peaks, bounds, params.img_dimensions, peakiness)

        # generate a color for the mountains
        darken_factor = sample_linear(0, .85, i, num_mountains - 1)
        desaturation_factor = sample_linear(0, 1, i, num_mountains - 1)
        mountain_gradient = palette.MountainRed.map(
            darken_mapper(darken_factor, desaturation_factor)  # darken more with each layer
        ).linear_gradient(
            0, 0, *params.img_dimensions
        )
        # draw mountains
        _draw_path(ctx, path, mountain_gradient)

        # calculate color for fog
        gradient_end = params.img_dimensions[1] - min(pt[1] for pt in path)
        thickness = sample_linear(params.fog_thickness, params.fog_thickness / 4, i, num_mountains - 1)
        _draw_path(ctx, path, palette.get_fog_at_level(thickness).linear_gradient(0, params.img_dimensions[1], 0, gradient_end / 2))



def _draw_path(ctx: cairo.Context, path: List[Tuple[float,float]], fill: cairo.Pattern):
    ctx.move_to(*path[0])
    for x, y in path[1:]:
        ctx.line_to(x, y)
    ctx.close_path()

    ctx.set_source(fill)
    ctx.fill()

def draw_sun(surface: cairo.Surface, params: SceneParameters, palette: ColorGradients):
    ctx = cairo.Context(surface)
    ctx.set_line_width(0)

    ctx.arc(params.img_dimensions[0] * 0.85, params.img_dimensions[1] * (1 - params.sun_height),
            params.img_dimensions[1] * params.sun_size, 0, 2 * math.pi)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()


def darken_mapper(val: float, sat: float):
    def inner(i: int, color: HSV):
        return color.darken(val).desaturate(sat)
    return inner


def create_scene(fname: str, params: SceneParameters, palette: ColorGradients):
    with cairo.SVGSurface(fname, *params.img_dimensions) as surface:
        draw_sky(surface, params, palette)
        draw_sun(surface, params, palette)
        draw_mountains(surface, params, palette)

    print("done")
