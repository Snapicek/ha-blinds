from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from custom_components.ha_blinds.logic import DecisionConfig, DecisionEngine, DecisionInputs


def _cfg() -> DecisionConfig:
    return DecisionConfig(
        window_azimuth=240,
        window_view_left=60,
        window_view_right=60,
        lux_close_summer=35000,
        lux_open_summer=20000,
        lux_close_winter=20000,
        lux_open_winter=12000,
        debounce_minutes=5,
        heat_start_hour=10,
        heat_end_hour=17,
        heat_position=20,
        temp_threshold=24.0,
        winter_privacy_hour=16,
        summer_privacy_hour=19,
    )


class TestDecisionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine(_cfg())

    def test_privacy_hour_closes(self) -> None:
        now = datetime(2026, 12, 1, 17, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 220, 5, 10000, 21.0, 75, paused=False)
        )
        self.assertTrue(res.should_move)
        self.assertEqual(res.target_position, 100)  # 0% or 100% = zavřeno
        self.assertEqual(res.reason, "privacy_hour")

    def test_high_lux_debounce_closes(self) -> None:
        start = datetime(2026, 7, 1, 13, 0, 0)
        self.engine.evaluate(DecisionInputs(start, 230, 45, 40000, 26.0, 75, paused=False))
        res = self.engine.evaluate(
            DecisionInputs(start + timedelta(minutes=5), 230, 45, 40000, 26.0, 75, paused=False)
        )
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "direct_sun_high_lux")

    def test_sun_not_at_window_no_direct_close(self) -> None:
        now = datetime(2026, 7, 1, 13, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 80, 45, 80000, 28.0, 75, paused=False)
        )
        self.assertNotEqual(res.reason, "direct_sun_high_lux")

    def test_paused_makes_no_change(self) -> None:
        now = datetime(2026, 7, 1, 13, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 230, 45, 80000, 28.0, 75, paused=True)
        )
        self.assertFalse(res.should_move)
        self.assertEqual(res.reason, "paused")

    def test_sunset_closes_blinds(self) -> None:
        """Test that sunset (sun_elevation < 0) closes blinds to 0% or 100%."""
        now = datetime(2026, 7, 1, 19, 30, 0)  # Evening after sunset
        res = self.engine.evaluate(
            DecisionInputs(now, 230, -5, 5000, 22.0, 75, paused=False)
        )
        self.assertTrue(res.should_move)
        self.assertEqual(res.target_position, 100)  # Closed (night)
        self.assertEqual(res.reason, "night_close")

    def test_night_stays_closed(self) -> None:
        """Test that during night, blinds stay closed (0% or 100%)."""
        now = datetime(2026, 7, 1, 22, 0, 0)  # Night time
        res = self.engine.evaluate(
            DecisionInputs(now, 180, -20, 100, 18.0, 100, paused=False)
        )
        self.assertFalse(res.should_move)  # Already at target
        self.assertEqual(res.target_position, 100)  # Closed
        self.assertEqual(res.reason, "night_close")
    
    def test_low_sun_closes(self) -> None:
        """Test that low elevation sun (eye level) closes blinds."""
        now = datetime(2026, 7, 1, 8, 0, 0)  # Early morning
        res = self.engine.evaluate(
            DecisionInputs(now, 230, 8, 5000, 18.0, 75, paused=False)
        )
        # Sun at 8° elevation = directly in eyes = close to 0%
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "sun_elevation_tracking")
    
    def test_high_sun_opens(self) -> None:
        """Test that high elevation sun (overhead) opens blinds."""
        now = datetime(2026, 7, 1, 12, 0, 0)  # Midday
        res = self.engine.evaluate(
            DecisionInputs(now, 230, 70, 30000, 28.0, 50, paused=False)
        )
        # Sun at 70° elevation = from above = open to 75%
        self.assertEqual(res.target_position, 75)
        self.assertEqual(res.reason, "sun_elevation_tracking")


if __name__ == "__main__":
    unittest.main()

