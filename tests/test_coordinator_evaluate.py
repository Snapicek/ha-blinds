"""Tests for HaBlindsController._async_evaluate — the main orchestration loop.

Exercises the pieces that logic.py's DecisionEngine tests can't reach:
missing-entity error backoff, movement-step clamping, multi-cover
dispatch, privacy-hour / high-lux state tracking across ticks, and
pause auto-expiry. Uses ha_stubs' FakeHass (fake states/services) with
dt_util.now() monkeypatched per test for deterministic "now".
"""

from __future__ import annotations

from datetime import datetime, timedelta
import unittest

import ha_stubs

ha_stubs.install()

import custom_components.ha_blinds.coordinator as coordinator_module
from custom_components.ha_blinds.const import (
    CONF_COVER_ENTITIES,
    CONF_COVER_ENTITY,
    CONF_LUX_SENSOR,
    CONF_MANUAL_OVERRIDE_MINUTES,
    CONF_MAX_STEP_PER_TICK,
    CONF_MIN_POSITION,
    CONF_SUMMER_PRIVACY_HOUR,
    CONF_TEMP_SENSOR,
    DEFAULTS,
)
from custom_components.ha_blinds.coordinator import HaBlindsController


def _set_now(dt: datetime) -> None:
    coordinator_module.dt_util.now = lambda: dt


def _sun_state(azimuth: float, elevation: float) -> ha_stubs.FakeState:
    return ha_stubs.FakeState({"azimuth": azimuth, "elevation": elevation})


def _cover_state(position: int) -> ha_stubs.FakeState:
    return ha_stubs.FakeState({"current_position": position})


def _controller(
    states: dict,
    options: dict | None = None,
    data: dict | None = None,
) -> HaBlindsController:
    hass = ha_stubs.FakeHass(states)
    base_data = {CONF_COVER_ENTITY: "cover.blind", CONF_LUX_SENSOR: "sensor.lux"}
    base_data.update(data or {})
    entry = ha_stubs.FakeEntry(data=base_data, options=options or {})
    return HaBlindsController(hass, entry)


class TestMissingEntities(unittest.IsolatedAsyncioTestCase):
    async def test_missing_sun_entity_increments_error_and_skips(self) -> None:
        controller = _controller({"cover.blind": _cover_state(50)})
        _set_now(datetime(2026, 7, 1, 12, 0))
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.error_count, 1)
        self.assertEqual(controller.hass.services.calls, [])

    async def test_missing_cover_entity_increments_error_and_skips(self) -> None:
        controller = _controller({"sun.sun": _sun_state(230, 45)})
        _set_now(datetime(2026, 7, 1, 12, 0))
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.error_count, 1)
        self.assertEqual(controller.hass.services.calls, [])

    async def test_error_count_resets_once_entities_reappear(self) -> None:
        controller = _controller({"cover.blind": _cover_state(50)})
        _set_now(datetime(2026, 7, 1, 12, 0))
        await controller._async_evaluate()
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.error_count, 2)

        controller.hass.states._states["sun.sun"] = _sun_state(230, 45)
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.error_count, 0)


class TestMovement(unittest.IsolatedAsyncioTestCase):
    async def test_move_is_clamped_to_max_step_per_tick(self) -> None:
        """Night close wants position 0; from 75 the default max_step_per_tick=10
        should only move it to 65 in a single tick."""
        controller = _controller({
            "cover.blind": _cover_state(75),
            "sun.sun": _sun_state(230, -5),
        })
        _set_now(datetime(2026, 7, 1, 10, 0))
        await controller._async_evaluate()

        self.assertEqual(len(controller.hass.services.calls), 1)
        call = controller.hass.services.calls[0]
        self.assertEqual(call["domain"], "cover")
        self.assertEqual(call["service"], "set_cover_position")
        self.assertEqual(call["data"], {"entity_id": "cover.blind", "position": 65})
        self.assertEqual(controller._runtime.last_target, 65)

    async def test_step_large_enough_reaches_target_directly(self) -> None:
        controller = _controller(
            {"cover.blind": _cover_state(75), "sun.sun": _sun_state(230, -5)},
            options={CONF_MAX_STEP_PER_TICK: 100},
        )
        _set_now(datetime(2026, 7, 1, 10, 0))
        await controller._async_evaluate()

        call = controller.hass.services.calls[0]
        # Target is 0 but clamps to min_position (prevents slat flip on overshoot).
        self.assertEqual(call["data"]["position"], DEFAULTS[CONF_MIN_POSITION])

    async def test_no_move_issues_no_service_call(self) -> None:
        """current_position already at the target (within movement_threshold)."""
        controller = _controller({
            "cover.blind": _cover_state(0),
            "sun.sun": _sun_state(230, -5),
        })
        _set_now(datetime(2026, 7, 1, 10, 0))
        await controller._async_evaluate()

        self.assertEqual(controller.hass.services.calls, [])
        self.assertEqual(controller._runtime.last_reason, "night_close")

    async def test_multiple_covers_all_receive_the_command(self) -> None:
        controller = _controller(
            {"cover.blind": _cover_state(75), "sun.sun": _sun_state(230, -5)},
            data={CONF_COVER_ENTITIES: ["cover.blind_2", "cover.blind_3"]},
        )
        _set_now(datetime(2026, 7, 1, 10, 0))
        await controller._async_evaluate()

        entities_commanded = [c["data"]["entity_id"] for c in controller.hass.services.calls]
        self.assertEqual(entities_commanded, ["cover.blind", "cover.blind_2", "cover.blind_3"])


class TestPausing(unittest.IsolatedAsyncioTestCase):
    async def test_paused_until_future_blocks_movement(self) -> None:
        controller = _controller({
            "cover.blind": _cover_state(75),
            "sun.sun": _sun_state(230, -5),
        })
        now = datetime(2026, 7, 1, 10, 0)
        controller._runtime.paused_until = now + timedelta(minutes=10)
        _set_now(now)
        await controller._async_evaluate()

        self.assertEqual(controller.hass.services.calls, [])
        self.assertEqual(controller._runtime.last_reason, "paused")
        self.assertIsNotNone(controller._runtime.paused_until)

    async def test_pause_auto_expires_once_now_passes_it(self) -> None:
        controller = _controller({
            "cover.blind": _cover_state(75),
            "sun.sun": _sun_state(230, -5),
        })
        now = datetime(2026, 7, 1, 10, 0)
        controller._runtime.paused_until = now - timedelta(minutes=1)
        _set_now(now)
        await controller._async_evaluate()

        self.assertIsNone(controller._runtime.paused_until)
        self.assertEqual(controller._runtime.last_reason, "night_close")


class TestPrivacyHourTracking(unittest.IsolatedAsyncioTestCase):
    async def test_entering_privacy_hour_records_entry_time(self) -> None:
        controller = _controller({
            "cover.blind": _cover_state(75),
            "sun.sun": _sun_state(90, 20),
        })
        now = datetime(2026, 7, 1, 20, 0)  # past default summer_privacy_hour=19
        _set_now(now)
        await controller._async_evaluate()

        self.assertEqual(controller._runtime.last_reason, "privacy_hour")
        self.assertEqual(controller._runtime.privacy_entered_at, now)

    async def test_entry_time_does_not_reset_on_later_ticks(self) -> None:
        controller = _controller({
            "cover.blind": _cover_state(0),
            "sun.sun": _sun_state(90, 20),
        })
        entered_at = datetime(2026, 7, 1, 20, 0)
        _set_now(entered_at)
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.privacy_entered_at, entered_at)

        _set_now(entered_at + timedelta(minutes=30))
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.privacy_entered_at, entered_at)

    async def test_exit_clears_entry_after_duration_expires_past_midnight(self) -> None:
        """privacy_duration_minutes=480 (8h): enter at 20:00, expires 04:00 next day.
        At that point the coordinator should clear privacy_entered_at."""
        controller = _controller({
            "cover.blind": _cover_state(0),
            "sun.sun": _sun_state(90, -10),
        })
        entered_at = datetime(2026, 7, 1, 20, 0)
        _set_now(entered_at)
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.privacy_entered_at, entered_at)

        _set_now(entered_at + timedelta(hours=8, minutes=1))
        await controller._async_evaluate()
        self.assertIsNone(controller._runtime.privacy_entered_at)
        self.assertNotEqual(controller._runtime.last_reason, "privacy_hour")


class TestHighLuxTracking(unittest.IsolatedAsyncioTestCase):
    async def test_high_lux_since_recorded_on_first_high_reading(self) -> None:
        controller = _controller({
            "cover.blind": _cover_state(75),
            "sun.sun": _sun_state(230, 45),
            "sensor.lux": ha_stubs.FakeState({}, state="80000"),
        })
        now = datetime(2026, 7, 1, 13, 0)
        _set_now(now)
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.high_lux_since, now)

    async def test_high_lux_since_not_reset_while_still_high(self) -> None:
        controller = _controller({
            "cover.blind": _cover_state(75),
            "sun.sun": _sun_state(230, 45),
            "sensor.lux": ha_stubs.FakeState({}, state="80000"),
        })
        first = datetime(2026, 7, 1, 13, 0)
        _set_now(first)
        await controller._async_evaluate()

        _set_now(first + timedelta(minutes=10))
        await controller._async_evaluate()
        self.assertEqual(controller._runtime.high_lux_since, first)

    async def test_high_lux_since_clears_when_lux_drops(self) -> None:
        controller = _controller({
            "cover.blind": _cover_state(75),
            "sun.sun": _sun_state(230, 45),
            "sensor.lux": ha_stubs.FakeState({}, state="80000"),
        })
        first = datetime(2026, 7, 1, 13, 0)
        _set_now(first)
        await controller._async_evaluate()
        self.assertIsNotNone(controller._runtime.high_lux_since)

        controller.hass.states._states["sensor.lux"] = ha_stubs.FakeState({}, state="500")
        _set_now(first + timedelta(minutes=10))
        await controller._async_evaluate()
        self.assertIsNone(controller._runtime.high_lux_since)


class TestExceptionHandling(unittest.IsolatedAsyncioTestCase):
    async def test_engine_exception_is_caught_and_counted(self) -> None:
        controller = _controller({
            "cover.blind": _cover_state(75),
            "sun.sun": _sun_state(230, 45),
        })
        _set_now(datetime(2026, 7, 1, 12, 0))

        def _boom(_inputs):
            raise RuntimeError("boom")

        controller._engine.evaluate = _boom
        await controller._async_evaluate()  # must not raise
        self.assertEqual(controller._runtime.error_count, 1)
        self.assertEqual(controller.hass.services.calls, [])


if __name__ == "__main__":
    unittest.main()
