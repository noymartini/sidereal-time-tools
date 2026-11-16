"""Sidereal time conversion utilities.

This package exposes :func:`local_sidereal_time` and :class:`SiderealTime`.
"""

from .core import SiderealTime, local_sidereal_time

__all__ = ["SiderealTime", "local_sidereal_time"]
