# sidereal-time-tools

Converts civil time to local mean sidereal time for astronomical observations.

## Usage

```python
from datetime import datetime, timezone
from sidereal_time_tools import local_sidereal_time

# 1987 April 10, 0h UT at Greenwich
st = local_sidereal_time(datetime(1987, 4, 10, 0, 0, 0, tzinfo=timezone.utc), longitude=0.0)
print(st.hours, st.minutes, st.seconds)  # 13 10 46.3668...
print(st.degrees)                        # 197.693195...
print(st.total_hours)                    # 13.179546...
```

The function accepts a `datetime` (naive datetimes are treated as UTC), a
longitude in degrees (east positive by default), and an optional
`longitude_east=False` keyword to supply a west-positive longitude.

## Why this exists

Sidereal time is the angle between the observer's meridian and the vernal
equinox, and it is the coordinate you need to point a telescope at a known
right ascension.  Doing the conversion by hand is error-prone: the formula
involves Julian dates, a polynomial in Julian centuries, and modular
arithmetic in degrees.  This library wraps that in one call and returns a
small immutable value object with the result split into hours, minutes,
seconds, and degrees.

The trade-off: we implement the IAU 1982 Greenwich mean sidereal time
expression (Meeus, *Astronomical Algorithms*, 2nd ed., chapter 12) rather
than the newer IAU 2006 expression.  The 1982 formula is simpler, well
documented, and accurate to about 0.1 seconds for dates between 1900 and
2100, which is ample for visual and small-telescope work.  If you need
sub-second accuracy near the limits of that range, use a full ephemeris
library instead.

## The awkward edge

Naive `datetime` objects are interpreted as UTC.  This is a deliberate
choice: an astronomical library should not silently use the local timezone
of the machine, and requiring the caller to attach a timezone for every
call is tedious.  If you have a local civil time, convert it to UTC before
passing it in.  Aware datetimes are converted to UTC internally.

Longitudes must be between -180 and 180 degrees.  Values outside that range
raise `ValueError` rather than being wrapped, because a longitude of 200
degrees almost always indicates a sign or unit mistake.
