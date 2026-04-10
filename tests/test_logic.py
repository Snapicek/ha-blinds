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
        self.assertEqual(res.target_position, 100)
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


if __name__ == "__main__":
    unittest.main()

