"""
interpolation helpers
"""
from typing import Tuple


def sample_linear(start: float, end: float, i: int, max_i: int):
    """
    Sample a function [0,max_i] -> [start,end]
    defined by their start and end values
        f(0) := start and f(max_i) = end
    at the point i
    """
    percentage = i / max_i
    return start * (1 - percentage) + end * percentage


class Polynomial:
    terms: Tuple[float]

    def __init__(self, *terms: float):
        self.terms = tuple(terms)

    def sample(self, x: float):
        return sum(a * (x ** n) for n, a in enumerate(self.terms))



