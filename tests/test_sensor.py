"""Tests for the read-only status sensor entities in sensor.py.

Constructs entities directly against a real HaBlindsController (cheap to
build — see test_coordinator_evaluate.py's `_controller` helper) rather than
going through async_setup_entry, since that only needs hass.data plumbing
the entities themselves don't touch.
"""

from __future__ import annotations

from datetime import datetime
import unittest

import ha_stubs

ha_stubs.install()

import custom_components.ha_blinds.coordinator as coordinator_module
from custom_components.ha_blinds.const import CONF_COVER_ENTITY, CONF_LUX_SENSOR
from custom_components.ha_blinds.coordinator import HaBlindsController
from custom_components.ha_blinds.sensor import (
    HaBlindsErrorCountSensor,
    HaBlindsLastDecisionSensor,
    HaBlindsLastReasonSensor,
    HaBlindsStateSensor,
    HaBlindsSunAtWindowSensor,
    HaBlindsTargetPositionSensor,
)


def _set_now(dt: datetime) -> None:
    coordinator_module.dt_util.now = lambda: dt


def _controller(states: dict | None = None) -> HaBlindsController:
    hass = ha_stubs.FakeHass(states or {})
    entry = ha_stubs.FakeEntry(data={CONF_COVER_ENTITY: "cover.blind", CONF_LUX_SENSOR: "sensor.lux"})
    return HaBlindsController(hass, entry)


class TestHaBlindsStateSensor(unittest.IsolatedAsyncioTestCase):
    async def test_active_state_and_icon(self) -> None:
        controller = _controller()
        sensor = HaBlindsStateSensor(controller, controller.entry)

        self.assertEqual(sensor.state, "active")
        self.assertEqual(sensor.icon, "mdi:play")
        self.assertFalse(sensor.should_poll)

    async def test_paused_state_and_icon(self) -> None:
        controller = _controller()
        _set_now(datetime(2026, 7, 1, 12, 0))
        await controller.async_pause(minutes=10)
        sensor = HaBlindsStateSensor(controller, controller.entry)

        self.assertEqual(sensor.state, "paused")
        self.assertEqual(sensor.icon, "mdi:pause")

    async def test_extra_state_attributes_reflect_runtime(self) -> None:
        controller = _controller()
        _set_now(datetime(2026, 7, 1, 12, 0))
        await controller.async_pause(minutes=10)
        controller._runtime.last_reason = "night_close"
        controller._runtime.last_target = 0
        controller._runtime.sun_at_window = True
        sensor = HaBlindsStateSensor(controller, controller.entry)

        attrs = sensor.extra_state_attributes

        self.assertEqual(attrs["last_reason"], "night_close")
        self.assertEqual(attrs["last_target"], 0)
        self.assertEqual(attrs["cover_entity"], "cover.blind")
        self.assertEqual(attrs["error_count"], 0)
        self.assertTrue(attrs["sun_at_window"])
        self.assertEqual(attrs["paused_until"], controller._runtime.paused_until.isoformat())

    def test_unique_id_and_device_info_scoped_to_entry(self) -> None:
        controller = _controller()
        sensor = HaBlindsStateSensor(controller, controller.entry)

        self.assertEqual(sensor.unique_id, f"{controller.entry.entry_id}_state")
        self.assertEqual(sensor.device_info["identifiers"], {("ha_blinds", controller.entry.entry_id)})


class TestOtherSensors(unittest.TestCase):
    def test_last_reason_sensor_reads_runtime(self) -> None:
        controller = _controller()
        controller._runtime.last_reason = "daytime_open"
        sensor = HaBlindsLastReasonSensor(controller, controller.entry)

        self.assertEqual(sensor.state, "daytime_open")

    def test_target_position_sensor_reads_runtime(self) -> None:
        controller = _controller()
        controller._runtime.last_target = 42
        sensor = HaBlindsTargetPositionSensor(controller, controller.entry)

        self.assertEqual(sensor.state, 42)
        self.assertEqual(sensor.unit_of_measurement, "%")

    def test_last_decision_sensor_none_before_first_evaluation(self) -> None:
        controller = _controller()
        sensor = HaBlindsLastDecisionSensor(controller, controller.entry)

        self.assertIsNone(sensor.state)

    def test_last_decision_sensor_reports_isoformat(self) -> None:
        controller = _controller()
        controller._runtime.last_decision_time = datetime(2026, 7, 1, 12, 0)
        sensor = HaBlindsLastDecisionSensor(controller, controller.entry)

        self.assertEqual(sensor.state, "2026-07-01T12:00:00")

    def test_error_count_sensor_reads_runtime(self) -> None:
        controller = _controller()
        controller._runtime.error_count = 3
        sensor = HaBlindsErrorCountSensor(controller, controller.entry)

        self.assertEqual(sensor.state, 3)
        self.assertEqual(sensor.unit_of_measurement, "errors")

    def test_sun_at_window_sensor_reads_runtime(self) -> None:
        controller = _controller()
        controller._runtime.sun_at_window = True
        sensor = HaBlindsSunAtWindowSensor(controller, controller.entry)

        self.assertTrue(sensor.state)


if __name__ == "__main__":
    unittest.main()
