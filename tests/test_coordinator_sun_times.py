"""Tests for HaBlindsController._get_sunrise_time / _get_sunset_time.

These derive "today's" sunrise/sunset (plus configured offsets) from the
sun.sun entity's next_rising/next_setting attributes, which always point
at the *next future* occurrence and therefore flip to tomorrow's value
right after today's sunrise/sunset happens. Getting the day-recovery and
offset arithmetic wrong here previously caused a real bug (see the
"5:10 AM" regression test in test_logic.py) — logic.py's own tests only
exercise the DecisionEngine with sunrise/sunset times injected directly,
so this derivation was never actually verified.

homeassistant is not installed in this environment; ha_stubs installs
minimal fake modules so coordinator.py can be imported. dt_util.as_local
is stubbed as identity, so all datetimes below can be treated as already
being in local time.
"""

from __future__ import annotations

from datetime import datetime
import unittest

import ha_stubs

ha_stubs.install()

from custom_components.ha_blinds.const import (
    CONF_SUNRISE_OFFSET_MINUTES,
    CONF_SUNSET_OFFSET_MINUTES,
)
from custom_components.ha_blinds.coordinator import HaBlindsController


def _controller(sun_attrs: dict | None = None, options: dict | None = None) -> HaBlindsController:
    states = {"sun.sun": ha_stubs.FakeState(sun_attrs)} if sun_attrs is not None else {}
    hass = ha_stubs.FakeHass(states)
    entry = ha_stubs.FakeEntry(options=options or {})
    return HaBlindsController(hass, entry)


class TestGetSunsetTime(unittest.TestCase):
    def test_no_sun_entity_returns_none(self) -> None:
        controller = _controller(sun_attrs=None)
        self.assertIsNone(controller._get_sunset_time(datetime(2026, 7, 1, 21, 0)))

    def test_daytime_before_sunset_returns_todays_sunset(self) -> None:
        """Before today's sunset: next_setting is today's, next_rising is tomorrow's."""
        controller = _controller(sun_attrs={
            "next_setting": datetime(2026, 7, 1, 20, 30),
            "next_rising": datetime(2026, 7, 2, 4, 50),
        })
        result = controller._get_sunset_time(datetime(2026, 7, 1, 12, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 20, 30))

    def test_post_sunset_recovers_todays_actual_sunset(self) -> None:
        """After today's sunset: next_setting flips to tomorrow's — must subtract a day."""
        controller = _controller(sun_attrs={
            "next_setting": datetime(2026, 7, 2, 20, 31),
            "next_rising": datetime(2026, 7, 2, 4, 50),
        })
        result = controller._get_sunset_time(datetime(2026, 7, 1, 21, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 20, 31))

    def test_offset_applied_after_day_recovery(self) -> None:
        controller = _controller(
            sun_attrs={
                "next_setting": datetime(2026, 7, 2, 20, 31),
                "next_rising": datetime(2026, 7, 2, 4, 50),
            },
            options={CONF_SUNSET_OFFSET_MINUTES: 45},
        )
        result = controller._get_sunset_time(datetime(2026, 7, 1, 21, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 21, 16))

    def test_negative_offset_applied(self) -> None:
        controller = _controller(
            sun_attrs={
                "next_setting": datetime(2026, 7, 1, 20, 30),
                "next_rising": datetime(2026, 7, 2, 4, 50),
            },
            options={CONF_SUNSET_OFFSET_MINUTES: -30},
        )
        result = controller._get_sunset_time(datetime(2026, 7, 1, 12, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 20, 0))

    def test_missing_next_rising_skips_day_recovery(self) -> None:
        """Without next_rising to compare against, no day-subtraction should happen."""
        controller = _controller(sun_attrs={"next_setting": datetime(2026, 7, 1, 20, 30)})
        result = controller._get_sunset_time(datetime(2026, 7, 1, 12, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 20, 30))


class TestGetSunriseTime(unittest.TestCase):
    def test_no_sun_entity_returns_none(self) -> None:
        controller = _controller(sun_attrs=None)
        self.assertIsNone(controller._get_sunrise_time(datetime(2026, 7, 1, 3, 0)))

    def test_nighttime_returns_todays_upcoming_sunrise(self) -> None:
        """Before today's sunrise: next_rising is today's, next_setting is also today's (later)."""
        controller = _controller(sun_attrs={
            "next_rising": datetime(2026, 7, 1, 4, 50),
            "next_setting": datetime(2026, 7, 1, 20, 30),
        })
        result = controller._get_sunrise_time(datetime(2026, 7, 1, 3, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 4, 50))

    def test_nighttime_offset_applied(self) -> None:
        controller = _controller(
            sun_attrs={
                "next_rising": datetime(2026, 7, 1, 4, 50),
                "next_setting": datetime(2026, 7, 1, 20, 30),
            },
            options={CONF_SUNRISE_OFFSET_MINUTES: 15},
        )
        result = controller._get_sunrise_time(datetime(2026, 7, 1, 3, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 5, 5))

    def test_nighttime_negative_offset_applied(self) -> None:
        controller = _controller(
            sun_attrs={
                "next_rising": datetime(2026, 7, 1, 4, 50),
                "next_setting": datetime(2026, 7, 1, 20, 30),
            },
            options={CONF_SUNRISE_OFFSET_MINUTES: -20},
        )
        result = controller._get_sunrise_time(datetime(2026, 7, 1, 3, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 4, 30))

    def test_daytime_no_offset_returns_none(self) -> None:
        """Already past sunrise and no sleep-in offset configured: no gating needed."""
        controller = _controller(sun_attrs={
            "next_rising": datetime(2026, 7, 2, 4, 51),
            "next_setting": datetime(2026, 7, 1, 20, 30),
        })
        result = controller._get_sunrise_time(datetime(2026, 7, 1, 12, 0))
        self.assertIsNone(result)

    def test_daytime_within_sleep_in_window_returns_sleep_in_end(self) -> None:
        """Just after actual sunrise, inside the configured sleep-in window."""
        controller = _controller(
            sun_attrs={
                "next_rising": datetime(2026, 7, 2, 4, 51),
                "next_setting": datetime(2026, 7, 1, 20, 30),
            },
            options={CONF_SUNRISE_OFFSET_MINUTES: 30},
        )
        result = controller._get_sunrise_time(datetime(2026, 7, 1, 5, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 5, 21))

    def test_daytime_after_sleep_in_window_returns_none(self) -> None:
        """Once the sleep-in window has elapsed, gating lifts."""
        controller = _controller(
            sun_attrs={
                "next_rising": datetime(2026, 7, 2, 4, 51),
                "next_setting": datetime(2026, 7, 1, 20, 30),
            },
            options={CONF_SUNRISE_OFFSET_MINUTES: 30},
        )
        result = controller._get_sunrise_time(datetime(2026, 7, 1, 6, 0))
        self.assertIsNone(result)

    def test_daytime_negative_offset_ignored(self) -> None:
        """Negative offsets only apply in the nighttime branch, not for sleep-in gating."""
        controller = _controller(
            sun_attrs={
                "next_rising": datetime(2026, 7, 2, 4, 51),
                "next_setting": datetime(2026, 7, 1, 20, 30),
            },
            options={CONF_SUNRISE_OFFSET_MINUTES: -15},
        )
        result = controller._get_sunrise_time(datetime(2026, 7, 1, 5, 0))
        self.assertIsNone(result)

    def test_missing_next_setting_treated_as_nighttime(self) -> None:
        """Without next_setting to compare against, falls through to the nighttime branch."""
        controller = _controller(sun_attrs={"next_rising": datetime(2026, 7, 1, 4, 50)})
        result = controller._get_sunrise_time(datetime(2026, 7, 1, 3, 0))
        self.assertEqual(result, datetime(2026, 7, 1, 4, 50))


if __name__ == "__main__":
    unittest.main()
