import math
import unittest
from datetime import datetime, timedelta, timezone

from sidereal_time_tools import SiderealTime, local_sidereal_time


class TestLocalSiderealTime(unittest.TestCase):
    def test_known_value_greenwich(self):
        # 1987 April 10, 0h UT.  Meeus, Astronomical Algorithms, 2nd ed.,
        # example 12.a gives GMST = 13h 10m 46.3668s.
        dt = datetime(1987, 4, 10, 0, 0, 0, tzinfo=timezone.utc)
        st = local_sidereal_time(dt, 0.0)
        expected_degrees = (13 + 10 / 60.0 + 46.3668 / 3600.0) * 15.0
        self.assertAlmostEqual(st.degrees, expected_degrees, places=4)
        self.assertEqual(st.hours, 13)
        self.assertEqual(st.minutes, 10)
        self.assertAlmostEqual(st.seconds, 46.3668, places=3)

    def test_known_value_with_longitude(self):
        # Same instant but at longitude 77.0 degrees east (Washington, DC
        # area).  The sidereal time should advance by 77/15 hours.
        dt = datetime(1987, 4, 10, 0, 0, 0, tzinfo=timezone.utc)
        st_greenwich = local_sidereal_time(dt, 0.0)
        st_local = local_sidereal_time(dt, 77.0)
        expected = (st_greenwich.total_hours + 77.0 / 15.0) % 24.0
        self.assertAlmostEqual(st_local.total_hours, expected, places=6)

    def test_west_positive_longitude(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        east = local_sidereal_time(dt, 45.0, longitude_east=True)
        west = local_sidereal_time(dt, 45.0, longitude_east=False)
        expected_west = (east.total_hours - 2 * 45.0 / 15.0) % 24.0
        self.assertAlmostEqual(west.total_hours, expected_west, places=6)

    def test_naive_datetime_treated_as_utc(self):
        aware = datetime(2020, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        naive = datetime(2020, 6, 1, 0, 0, 0)
        st_aware = local_sidereal_time(aware, 0.0)
        st_naive = local_sidereal_time(naive, 0.0)
        self.assertEqual(st_aware, st_naive)

    def test_non_utc_timezone_converted(self):
        # 2020-06-01 02:00 +02:00 is 2020-06-01 00:00 UTC.
        tz = timezone(timedelta(hours=2))
        local = datetime(2020, 6, 1, 2, 0, 0, tzinfo=tz)
        utc = datetime(2020, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(local_sidereal_time(local, 0.0), local_sidereal_time(utc, 0.0))

    def test_longitude_out_of_range(self):
        dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            local_sidereal_time(dt, 180.1)
        with self.assertRaises(ValueError):
            local_sidereal_time(dt, -180.1)

    def test_seconds_rollover(self):
        # Construct a time where the floating-point seconds would be just
        # below 60.0 but rounding pushes it over; the implementation must
        # normalise to 0 seconds and increment minutes.
        # We can't easily force that from the public API, so we test the
        # constructor's validation instead.
        with self.assertRaises(ValueError):
            SiderealTime(1, 2, 60.0, 15.5, datetime(2020, 1, 1, tzinfo=timezone.utc), 0.0)

    def test_total_hours_property(self):
        st = SiderealTime(1, 30, 0.0, 22.5, datetime(2020, 1, 1, tzinfo=timezone.utc), 0.0)
        self.assertAlmostEqual(st.total_hours, 1.5)

    def test_equality_and_hash(self):
        dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
        a = local_sidereal_time(dt, 10.0)
        b = local_sidereal_time(dt, 10.0)
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        c = local_sidereal_time(dt, 20.0)
        self.assertNotEqual(a, c)

    def test_repr_contains_fields(self):
        dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
        st = local_sidereal_time(dt, 0.0)
        r = repr(st)
        self.assertIn("SiderealTime", r)
        self.assertIn("hours=", r)


if __name__ == "__main__":
    unittest.main()
