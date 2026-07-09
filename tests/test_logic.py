from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from custom_components.ha_blinds.logic import DecisionConfig, DecisionEngine, DecisionInputs


def _cfg(**overrides) -> DecisionConfig:
    base = dict(
        window_azimuth=240,
        window_view_left=60,
        window_view_right=60,
        lux_close_summer=35000,
        lux_close_winter=20000,
        debounce_minutes=5,
        heat_start_hour=10,
        heat_end_hour=17,
        heat_position=20,
        temp_threshold=24.0,
        winter_privacy_hour=16,
        summer_privacy_hour=19,
        night_close_position=0,
        earliest_open_hour=7,
        earliest_open_minute=30,
        lux_low_threshold=5000,
        daytime_cloudy_position=90,
        movement_threshold=10,
    )
    base.update(overrides)
    return DecisionConfig(**base)


class TestDecisionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine(_cfg())

    # ── Paused ──────────────────────────────────────────────────────────────

    def test_paused_makes_no_change(self) -> None:
        now = datetime(2026, 7, 1, 13, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 230, 45, 80000, 28.0, 75, paused=True)
        )
        self.assertFalse(res.should_move)
        self.assertEqual(res.reason, "paused")

    # ── Night / elevation ────────────────────────────────────────────────────

    def test_night_close_triggers(self) -> None:
        now = datetime(2026, 7, 1, 3, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 230, -5, 5000, 22.0, 75, paused=False)
        )
        self.assertTrue(res.should_move)
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "too_early")

    def test_night_already_closed_no_move(self) -> None:
        now = datetime(2026, 7, 1, 3, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 180, -20, 100, 18.0, 0, paused=False)
        )
        self.assertFalse(res.should_move)
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "too_early")

    def test_night_close_after_earliest_open(self) -> None:
        """After earliest_open but sun below horizon → night_close."""
        engine = DecisionEngine(_cfg(earliest_open_hour=7, earliest_open_minute=0))
        now = datetime(2026, 11, 1, 7, 30, 0)
        res = engine.evaluate(
            DecisionInputs(now, 180, -5, 100, 18.0, 75, paused=False)
        )
        self.assertTrue(res.should_move)
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "night_close")

    # ── Privacy hour ─────────────────────────────────────────────────────────

    def test_privacy_hour_closes(self) -> None:
        now = datetime(2026, 12, 1, 17, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 220, 5, 10000, 21.0, 75, paused=False)
        )
        self.assertTrue(res.should_move)
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "privacy_hour")

    # ── Daytime open (sun NOT at window) ─────────────────────────────────────

    def test_morning_sun_not_at_window_opens(self) -> None:
        """Morning: sun in the east, window faces SW → daytime_open to 75%."""
        # Window 240° ±60° covers 180–300°; azimuth 103° is outside → not at window
        now = datetime(2026, 6, 22, 9, 30, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 103, 42, 11000, 20.0, 0, paused=False)
        )
        self.assertTrue(res.should_move)
        self.assertEqual(res.target_position, 70)
        self.assertEqual(res.reason, "daytime_open")

    def test_sun_not_at_window_high_lux_still_opens(self) -> None:
        """High lux protection must NOT fire when sun is outside the window azimuth."""
        now = datetime(2026, 7, 1, 9, 0, 0)
        start = now - timedelta(minutes=10)
        res = self.engine.evaluate(
            DecisionInputs(now, 80, 45, 80000, 28.0, 0, paused=False, high_lux_since=start)
        )
        # Still opens because sun is not at window
        self.assertEqual(res.reason, "daytime_open")
        self.assertEqual(res.target_position, 70)

    # ── Sun at window — elevation tracking ───────────────────────────────────

    def test_low_sun_at_window_closes(self) -> None:
        """Sun at 8° elevation at window → close to 0% (eye-level glare)."""
        now = datetime(2026, 7, 1, 8, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 230, 8, 5000, 18.0, 75, paused=False)
        )
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "sun_elevation_tracking")

    def test_high_sun_at_window_opens(self) -> None:
        """Sun at 70° elevation at window → open to 75% (overhead)."""
        now = datetime(2026, 7, 1, 9, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 230, 70, 30000, 18.0, 50, paused=False)
        )
        self.assertEqual(res.target_position, 75)
        self.assertEqual(res.reason, "sun_elevation_tracking")

    # ── High lux protection ──────────────────────────────────────────────────

    # ── Heat protection ──────────────────────────────────────────────────────

    def test_heat_protection_skipped_below_threshold(self) -> None:
        """Heat protection must not fire when temperature is below threshold."""
        engine = DecisionEngine(_cfg(enable_heat_protection=True, temp_threshold=24.0))
        now = datetime(2026, 7, 1, 13, 0, 0)
        res = engine.evaluate(
            DecisionInputs(now, 230, 45, 10000, 20.0, 70, paused=False)
        )
        self.assertNotEqual(res.reason, "peak_heat_hours")

    def test_heat_protection_fires_without_temp_sensor(self) -> None:
        """Heat protection fires on time-of-day when no temp sensor is configured."""
        engine = DecisionEngine(_cfg(enable_heat_protection=True))
        now = datetime(2026, 7, 1, 13, 0, 0)
        res = engine.evaluate(
            DecisionInputs(now, 230, 45, 10000, None, 70, paused=False)
        )
        self.assertEqual(res.reason, "peak_heat_hours")
        self.assertEqual(res.target_position, 20)

    def test_high_lux_debounce_closes(self) -> None:
        """High lux debounced → close when sun is at window."""
        start = datetime(2026, 7, 1, 13, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(
                start + timedelta(minutes=5), 230, 45, 40000, 26.0, 75,
                paused=False,
                high_lux_since=start,
            )
        )
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "direct_sun_high_lux")

    def test_high_lux_not_debounced_yet_uses_elevation(self) -> None:
        """High lux before debounce expires → elevation tracking, not close."""
        start = datetime(2026, 7, 1, 13, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(
                start + timedelta(minutes=2), 230, 45, 40000, 26.0, 75,
                paused=False,
                high_lux_since=start,
            )
        )
        self.assertNotEqual(res.reason, "direct_sun_high_lux")

    def test_high_lux_drops_sun_at_window_resumes_elevation(self) -> None:
        """When lux drops (high_lux_since=None), elevation tracking resumes.
        Use 9am to avoid heat_protection hours (10–17)."""
        now = datetime(2026, 7, 1, 9, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 230, 40, 15000, 20.0, 0, paused=False, high_lux_since=None)
        )
        self.assertEqual(res.reason, "sun_elevation_tracking")

    # ── Sunset / Sunrise ─────────────────────────────────────────────────────

    def test_pre_sunrise_keeps_closed(self) -> None:
        """Before sunrise+offset but after earliest_open → pre_sunrise_closing."""
        engine = DecisionEngine(_cfg(enable_sunset_closing=True, earliest_open_hour=7, earliest_open_minute=0))
        now = datetime(2026, 7, 1, 7, 10, 0)
        sunrise = datetime(2026, 7, 1, 7, 30, 0)  # sunrise + offset
        res = engine.evaluate(
            DecisionInputs(now, 90, 5, 500, 18.0, 0, paused=False, sunrise_time=sunrise)
        )
        self.assertFalse(res.should_move)
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "pre_sunrise_closing")

    def test_after_sunrise_opens(self) -> None:
        """After sunrise+offset, sun not yet at SW window → daytime_open."""
        engine = DecisionEngine(_cfg(enable_sunset_closing=True, earliest_open_hour=7, earliest_open_minute=0))
        now = datetime(2026, 7, 1, 8, 0, 0)
        sunrise = datetime(2026, 7, 1, 7, 30, 0)
        # Azimuth 90° = east, not at SW window (180–300°)
        res = engine.evaluate(
            DecisionInputs(now, 90, 15, 8000, 18.0, 0, paused=False, sunrise_time=sunrise)
        )
        self.assertEqual(res.reason, "daytime_open")
        self.assertEqual(res.target_position, 70)

    def test_sunset_closes(self) -> None:
        engine = DecisionEngine(_cfg(enable_sunset_closing=True))
        now = datetime(2026, 7, 1, 21, 0, 0)
        sunset = datetime(2026, 7, 1, 20, 30, 0)
        res = engine.evaluate(
            DecisionInputs(now, 260, 5, 1000, 20.0, 75, paused=False, sunset_time=sunset)
        )
        self.assertTrue(res.should_move)
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "sunset_closing")

    def test_night_close_does_not_fire_in_sunset_offset_window(self) -> None:
        """Between actual sunset and sunset+offset, night_close must not fire."""
        engine = DecisionEngine(_cfg(enable_sunset_closing=True))
        # Sun is below horizon (21:31) but offset window ends at 22:02
        now = datetime(2026, 6, 24, 21, 31, 0)
        sunset_with_offset = datetime(2026, 6, 24, 22, 2, 0)
        sunrise = datetime(2026, 6, 25, 4, 50, 0)
        res = engine.evaluate(
            DecisionInputs(now, 300, -1.5, 100, 18.0, 75, paused=False,
                           sunset_time=sunset_with_offset, sunrise_time=sunrise)
        )
        self.assertNotEqual(res.reason, "night_close")

    def test_pre_sunrise_does_not_fire_in_sunset_offset_window(self) -> None:
        """Between actual sunset and sunset+offset, blinds should stay open — not pre_sunrise."""
        engine = DecisionEngine(_cfg(enable_sunset_closing=True))
        # Sunset was at 21:00, offset window ends at 22:00; it's now 21:04
        now = datetime(2026, 6, 24, 21, 4, 0)
        sunset_with_offset = datetime(2026, 6, 24, 22, 0, 0)   # today sunset + 60 min
        sunrise = datetime(2026, 6, 25, 4, 50, 0)               # tomorrow
        res = engine.evaluate(
            DecisionInputs(now, 300, -1, 200, 18.0, 75, paused=False,
                           sunset_time=sunset_with_offset, sunrise_time=sunrise)
        )
        self.assertNotEqual(res.reason, "pre_sunrise_closing")

    def test_blinds_closed_after_sunset_offset_window(self) -> None:
        """After sunset+offset, blinds should be closed (sunset_closing or pre_sunrise_closing)."""
        engine = DecisionEngine(_cfg(enable_sunset_closing=True))
        now = datetime(2026, 6, 24, 22, 5, 0)                   # past offset window
        sunset_with_offset = datetime(2026, 6, 24, 22, 0, 0)
        sunrise = datetime(2026, 6, 25, 4, 50, 0)
        res = engine.evaluate(
            DecisionInputs(now, 300, -1, 200, 18.0, 75, paused=False,
                           sunset_time=sunset_with_offset, sunrise_time=sunrise)
        )
        self.assertIn(res.reason, ("sunset_closing", "pre_sunrise_closing"))
        self.assertEqual(res.target_position, 0)


    # ── Earliest open time ────────────────────────────────────────────────────

    def test_too_early_keeps_closed(self) -> None:
        """Before earliest_open_time, blinds stay closed regardless of sun."""
        engine = DecisionEngine(_cfg(earliest_open_hour=7, earliest_open_minute=30))
        now = datetime(2026, 7, 1, 5, 10, 0)
        res = engine.evaluate(
            DecisionInputs(now, 90, 10, 8000, 20.0, 75, paused=False)
        )
        self.assertTrue(res.should_move)
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "too_early")

    def test_earliest_open_allows_after(self) -> None:
        """After earliest_open_time, normal logic applies."""
        engine = DecisionEngine(_cfg(earliest_open_hour=7, earliest_open_minute=30))
        now = datetime(2026, 7, 1, 8, 0, 0)
        res = engine.evaluate(
            DecisionInputs(now, 90, 30, 15000, 20.0, 0, paused=False)
        )
        self.assertEqual(res.reason, "daytime_open")

    # ── Pre-sunrise fix verification ─────────────────────────────────────────

    def test_pre_sunrise_works_at_510am_with_offset(self) -> None:
        """5:10 AM with sunrise+offset at 7:00 — must stay closed (was the original bug)."""
        engine = DecisionEngine(_cfg(
            enable_sunset_closing=True,
            earliest_open_hour=5, earliest_open_minute=0,
        ))
        now = datetime(2026, 7, 1, 5, 10, 0)
        sunrise_with_offset = datetime(2026, 7, 1, 7, 0, 0)
        sunset = datetime(2026, 7, 1, 21, 0, 0)
        res = engine.evaluate(
            DecisionInputs(now, 90, 5, 500, 18.0, 0, paused=False,
                           sunrise_time=sunrise_with_offset, sunset_time=sunset)
        )
        self.assertFalse(res.should_move)
        self.assertEqual(res.target_position, 0)
        self.assertEqual(res.reason, "pre_sunrise_closing")

    # ── Lux-driven daytime logic ─────────────────────────────────────────────

    def test_sun_at_window_low_lux_opens(self) -> None:
        """Sun at window (azimuth) but lux low → sun blocked by obstacle."""
        engine = DecisionEngine(_cfg(lux_low_threshold=5000))
        now = datetime(2026, 7, 1, 17, 0, 0)
        res = engine.evaluate(
            DecisionInputs(now, 230, 15, 2000, 22.0, 0, paused=False)
        )
        self.assertEqual(res.reason, "sun_blocked_by_obstacle")
        self.assertEqual(res.target_position, 70)

    def test_cloudy_day_uses_cloudy_position(self) -> None:
        """Low lux, sun not at window → cloudy position."""
        engine = DecisionEngine(_cfg(daytime_cloudy_position=90, lux_low_threshold=5000))
        now = datetime(2026, 7, 1, 12, 0, 0)
        res = engine.evaluate(
            DecisionInputs(now, 90, 45, 3000, 20.0, 0, paused=False)
        )
        self.assertEqual(res.reason, "daytime_cloudy")
        self.assertEqual(res.target_position, 90)

    def test_lux_none_does_not_trigger_sun_blocked(self) -> None:
        """When lux is None (sensor unavailable), fall back to azimuth-based logic."""
        now = datetime(2026, 7, 1, 9, 0, 0)
        res = self.engine.evaluate(
            DecisionInputs(now, 230, 40, None, 20.0, 0, paused=False)
        )
        self.assertEqual(res.reason, "sun_elevation_tracking")

    # ── Movement threshold ───────────────────────────────────────────────────

    def test_movement_threshold_prevents_small_moves(self) -> None:
        """8% difference with threshold 10 → no move."""
        engine = DecisionEngine(_cfg(movement_threshold=10))
        now = datetime(2026, 7, 1, 12, 0, 0)
        res = engine.evaluate(
            DecisionInputs(now, 90, 30, 15000, 20.0, 62, paused=False)
        )
        self.assertFalse(res.should_move)

    def test_movement_threshold_allows_large_moves(self) -> None:
        """25% difference with threshold 10 → move."""
        engine = DecisionEngine(_cfg(movement_threshold=10))
        now = datetime(2026, 7, 1, 12, 0, 0)
        res = engine.evaluate(
            DecisionInputs(now, 90, 30, 15000, 20.0, 45, paused=False)
        )
        self.assertTrue(res.should_move)


if __name__ == "__main__":
    unittest.main()
