"""Tests for the button entities in button.py: Evaluate Now and the preset
position buttons. Both just forward to real HaBlindsController methods
already covered by test_coordinator_evaluate.py, so these tests only pin
that button presses call the right coordinator method with the right args.
"""

from __future__ import annotations

from datetime import datetime
import unittest

import ha_stubs

ha_stubs.install()

import custom_components.ha_blinds.coordinator as coordinator_module
from custom_components.ha_blinds.const import CONF_COVER_ENTITIES, CONF_COVER_ENTITY, CONF_LUX_SENSOR
from custom_components.ha_blinds.coordinator import HaBlindsController
from custom_components.ha_blinds.button import (
    PRESET_POSITIONS,
    HaBlindsEvaluateNowButton,
    HaBlindsPresetPositionButton,
)


def _set_now(dt: datetime) -> None:
    coordinator_module.dt_util.now = lambda: dt


def _sun_state(azimuth: float, elevation: float) -> ha_stubs.FakeState:
    return ha_stubs.FakeState({"azimuth": azimuth, "elevation": elevation})


def _cover_state(position: int) -> ha_stubs.FakeState:
    return ha_stubs.FakeState({"current_position": position})


def _controller(states: dict, data: dict | None = None) -> HaBlindsController:
    hass = ha_stubs.FakeHass(states)
    base_data = {CONF_COVER_ENTITY: "cover.blind", CONF_LUX_SENSOR: "sensor.lux"}
    base_data.update(data or {})
    entry = ha_stubs.FakeEntry(data=base_data)
    return HaBlindsController(hass, entry)


class TestEvaluateNowButton(unittest.IsolatedAsyncioTestCase):
    async def test_press_triggers_real_evaluation(self) -> None:
        controller = _controller(
            {
                "cover.blind": _cover_state(75),
                "sun.sun": _sun_state(azimuth=180.0, elevation=45.0),
            }
        )
        _set_now(datetime(2026, 7, 1, 12, 0))
        button = HaBlindsEvaluateNowButton(controller, controller.entry)

        await button.async_press()

        self.assertEqual(controller._runtime.last_decision_time, datetime(2026, 7, 1, 12, 0))
        self.assertEqual(controller._runtime.error_count, 0)

    async def test_press_with_missing_entities_counts_as_error(self) -> None:
        controller = _controller({})
        button = HaBlindsEvaluateNowButton(controller, controller.entry)

        await button.async_press()

        self.assertEqual(controller._runtime.error_count, 1)

    def test_unique_id_and_icon(self) -> None:
        controller = _controller({})
        button = HaBlindsEvaluateNowButton(controller, controller.entry)

        self.assertEqual(button.unique_id, f"{controller.entry.entry_id}_evaluate_now")
        self.assertEqual(button.name, "Evaluate Now")
        self.assertEqual(button.icon, "mdi:refresh")


class TestPresetPositionButton(unittest.IsolatedAsyncioTestCase):
    async def test_press_sets_position_and_pauses(self) -> None:
        controller = _controller({"cover.blind": _cover_state(50)})
        _set_now(datetime(2026, 7, 1, 12, 0))
        button = HaBlindsPresetPositionButton(controller, controller.entry, "close", 0, "mdi:blinds", "Close (0%)")

        await button.async_press()

        calls = controller.hass.services.calls
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["domain"], "cover")
        self.assertEqual(calls[0]["service"], "set_cover_position")
        self.assertEqual(calls[0]["data"], {"entity_id": "cover.blind", "position": 0})
        self.assertEqual(controller._runtime.last_target, 0)
        self.assertTrue(controller.is_paused)

    async def test_press_targets_every_configured_cover(self) -> None:
        controller = _controller(
            {"cover.blind": _cover_state(50), "cover.blind2": _cover_state(50)},
            data={CONF_COVER_ENTITIES: ["cover.blind2"]},
        )
        _set_now(datetime(2026, 7, 1, 12, 0))
        button = HaBlindsPresetPositionButton(controller, controller.entry, "half", 50, "mdi:blinds", "Half Open (50%)")

        await button.async_press()

        entities = {call["data"]["entity_id"] for call in controller.hass.services.calls}
        self.assertEqual(entities, {"cover.blind", "cover.blind2"})

    def test_unique_ids_are_distinct_per_preset(self) -> None:
        controller = _controller({})
        buttons = [
            HaBlindsPresetPositionButton(controller, controller.entry, key, position, icon, label)
            for key, position, icon, label in PRESET_POSITIONS
        ]

        unique_ids = {button.unique_id for button in buttons}
        self.assertEqual(len(unique_ids), len(PRESET_POSITIONS))


if __name__ == "__main__":
    unittest.main()
