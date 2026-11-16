"""Core routines for converting civil time to local sidereal time.

The implementation follows the standard Meeus algorithm, which is accurate
to about 0.1 seconds for dates between 1900 and 2100.  We deliberately use
the IAU 1982 GMST formula (Meeus, *Astronomical Algorithms*, 2nd ed.,
chapter 12) rather than the more modern IAU 2006 expression because it is
well documented, compact, and sufficient for visual and small-telescope
observing.  The trade-off is a small loss of precision for dates far from
J2000, which we consider acceptable for this library's purpose.

All angles are in degrees unless stated otherwise.  Time is represented as
a :class:`datetime.datetime` in UTC; naive datetimes are interpreted as UTC
because that is the only sane assumption for astronomical calculations.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Optional

__all__ = ["SiderealTime", "local_sidereal_time"]

# Julian date of the J2000.0 epoch (2000 January 1.5 TT).
_J2000 = 2451545.0

# Number of days in a Julian century.
_DAYS_PER_CENTURY = 36525.0

# Degrees in a full circle.
_FULL_CIRCLE = 360.0


def _to_julian_date(dt: datetime) -> float:
    """Return the Julian Date for a UTC datetime.

    The calculation uses the standard Gregorian calendar formula.  For
    dates before 1582-10-15 the Julian calendar would apply, but this
    library targets modern astronomical observations and does not attempt
    to handle that transition; the formula below is the Gregorian one.
    """
    if dt.tzinfo is None:
        # Treat naive datetimes as UTC.  This is the only interpretation
        # that makes sense for an astronomical library: the user should
        # not have to remember to attach a timezone just to get a result.
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    microsecond = dt.microsecond

    # Fractional day including leap seconds?  We ignore leap seconds
    # because the difference is at most ~1 second and the GMST formula
    # itself has comparable uncertainty.
    day_fraction = (
        hour / 24.0
        + minute / 1440.0
        + second / 86400.0
        + microsecond / 86400_000_000.0
    )

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + a // 4

    jd = (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + day_fraction
        + b
        - 1524.5
    )
    return jd


def _gmst_degrees(jd: float) -> float:
    """Greenwich mean sidereal time in degrees for a Julian Date.

    Uses the IAU 1982 expression as given by Meeus (equation 12.4).
    The result is normalised to [0, 360).
    """
    t = (jd - _J2000) / _DAYS_PER_CENTURY
    # 280.46061837 + 360.98564736629 * d + ...
    d = jd - _J2000
    gmst = (
        280.46061837
        + 360.98564736629 * d
        + 0.000387933 * t * t
        - t * t * t / 38710000.0
    )
    gmst %= _FULL_CIRCLE
    if gmst < 0.0:
        gmst += _FULL_CIRCLE
    return gmst


def local_sidereal_time(
    dt: datetime,
    longitude: float,
    *,
    longitude_east: bool = True,
) -> SiderealTime:
    """Return the local mean sidereal time for a civil time and longitude.

    Parameters
    ----------
    dt : datetime.datetime
        The civil time.  If naive it is interpreted as UTC; if aware it is
        converted to UTC.  The date and time are used as-is, so the caller
        is responsible for supplying the correct UTC instant.
    longitude : float
        The observer's longitude in degrees.  Positive values are east of
        Greenwich by default; pass ``longitude_east=False`` to supply a
        west-positive longitude instead.
    longitude_east : bool, optional
        If ``False``, ``longitude`` is interpreted as west-positive and is
        negated internally.  Defaults to ``True``.

    Returns
    -------
    SiderealTime
        An object carrying the sidereal time in hours, minutes, seconds,
        and degrees, plus the original inputs.

    Raises
    ------
    ValueError
        If ``longitude`` is outside the range [-180, 180] degrees.
    """
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be between -180 and 180 degrees")

    lon = longitude if longitude_east else -longitude

    jd = _to_julian_date(dt)
    gmst = _gmst_degrees(jd)
    lst = (gmst + lon) % _FULL_CIRCLE
    if lst < 0.0:
        lst += _FULL_CIRCLE

    hours = lst / 15.0
    h = int(hours)
    rem_minutes = (hours - h) * 60.0
    m = int(rem_minutes)
    s = (rem_minutes - m) * 60.0

    # Guard against floating-point drift pushing seconds to 60.0.  This
    # happens when the true value is just below the next minute but the
    # arithmetic rounds up; we roll over to keep the fields canonical.
    if s >= 60.0:
        s -= 60.0
        m += 1
    if m >= 60:
        m -= 60
        h += 1
    if h >= 24:
        h -= 24

    return SiderealTime(
        hours=h,
        minutes=m,
        seconds=s,
        degrees=lst,
        utc=dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc),
        longitude=lon,
    )


class SiderealTime:
    """A local sidereal time value.

    Instances are immutable value objects.  They are normally created by
    :func:`local_sidereal_time`; the constructor is public so that callers
    can construct one from an already-known sidereal time if they wish.

    Attributes
    ----------
    hours, minutes : int
        The sidereal time broken into whole hours and minutes.
    seconds : float
        The remaining seconds, in the range [0, 60).
    degrees : float
        The same sidereal time expressed as an angle in degrees, in the
        range [0, 360).
    utc : datetime.datetime
        The UTC instant from which this value was derived.
    longitude : float
        The east-positive longitude used, in degrees.
    """

    __slots__ = ("hours", "minutes", "seconds", "degrees", "utc", "longitude")

    def __init__(
        self,
        hours: int,
        minutes: int,
        seconds: float,
        degrees: float,
        utc: datetime,
        longitude: float,
    ) -> None:
        if not 0 <= hours < 24:
            raise ValueError("hours must be in [0, 24)")
        if not 0 <= minutes < 60:
            raise ValueError("minutes must be in [0, 60)")
        if not 0.0 <= seconds < 60.0:
            raise ValueError("seconds must be in [0, 60)")
        if not 0.0 <= degrees < 360.0:
            raise ValueError("degrees must be in [0, 360)")
        if utc.tzinfo is None:
            raise ValueError("utc must be timezone-aware")
        if not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180 degrees")

        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.degrees = degrees
        self.utc = utc
        self.longitude = longitude

    @property
    def total_hours(self) -> float:
        """Sidereal time as a single floating-point number of hours."""
        return self.hours + self.minutes / 60.0 + self.seconds / 3600.0

    def __repr__(self) -> str:
        return (
            f"SiderealTime(hours={self.hours}, minutes={self.minutes}, "
            f"seconds={self.seconds:.3f}, degrees={self.degrees:.6f}, "
            f"longitude={self.longitude}, utc={self.utc!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SiderealTime):
            return NotImplemented
        # Compare the canonical numeric representation, not the split
        # fields, so that e.g. 1h 30m 0s equals 1h 29m 60s (which the
        # constructor would reject anyway, but this keeps the semantics
        # clear).
        return (
            math.isclose(self.total_hours, other.total_hours, abs_tol=1e-12)
            and math.isclose(self.degrees, other.degrees, abs_tol=1e-12)
            and self.utc == other.utc
            and math.isclose(self.longitude, other.longitude, abs_tol=1e-12)
        )

    def __hash__(self) -> int:
        return hash((round(self.total_hours, 12), round(self.degrees, 12), self.utc, round(self.longitude, 12)))
