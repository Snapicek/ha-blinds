"""Tests for HaBlindsController._on_cover_state_changed.

This detects manual cover movement (someone using a physical remote or
the HA UI directly) and pauses the automation — but must NOT pause when
the position change was caused by the integration's own
set_cover_position call. That distinction is made purely by comparing
context ids, so getting it wrong either makes manual moves invisible or
makes the automation pause itself on every tick.
"""

from __future__ import annotations

from datetime import datetime
import unittest

import ha_stubs

ha_stubs.install()

import custom_components.ha_blinds.coordinator as coordinator_module
from custom_components.ha_blinds.const import CONF_COVER_ENTITY, CONF_LUX_SENSOR
from custom_components.ha_blinds.coordinator import HaBlindsController


def _set_now(dt: datetime) -> None:
    coordinator_module.dt_util.now = lambda: dt


class FakeEvent:
    def __init__(self, data: dict) -> None:
        self.data = data


def _cover_state(position, state="closed", context=None) -> ha_stubs.FakeState:
    return ha_stubs.FakeState({"current_position": position}, state=state, context=context)


def _controller() -> HaBlindsController:
    hass = ha_stubs.FakeHass({})
    entry = ha_stubs.FakeEntry(data={CONF_COVER_ENTITY: "cover.blind", CONF_LUX_SENSOR: "sensor.lux"})
    return HaBlindsController(hass, entry)


class TestManualOverrideDetection(unittest.IsolatedAsyncioTestCase):
    async def test_not_armed_ignores_event(self) -> None:
        controller = _controller()
        controller._listener_armed = False
        event = FakeEvent({
            "old_state": _cover_state(75, context=ha_stubs.FakeContext()),
            "new_state": _cover_state(50, context=ha_stubs.FakeContext()),
        })
        controller._on_cover_state_changed(event)
        self.assertEqual(controller.hass.created_tasks, [])

    async def test_missing_new_state_is_ignored(self) -> None:
        controller = _controller()
        controller._listener_armed = True
        event = FakeEvent({"old_state": _cover_state(75), "new_state": None})
        controller._on_cover_state_changed(event)
        self.assertEqual(controller.hass.created_tasks, [])

    async def test_unavailable_new_state_is_ignored(self) -> None:
        controller = _controller()
        controller._listener_armed = True
        event = FakeEvent({
            "old_state": _cover_state(75),
            "new_state": _cover_state(50, state="unavailable", context=ha_stubs.FakeContext()),
        })
        controller._on_cover_state_changed(event)
        self.assertEqual(controller.hass.created_tasks, [])

    async def test_missing_position_attribute_is_ignored(self) -> None:
        controller = _controller()
        controller._listener_armed = True
        new_state = ha_stubs.FakeState({}, context=ha_stubs.FakeContext())  # no current_position
        event = FakeEvent({"old_state": _cover_state(75), "new_state": new_state})
        controller._on_cover_state_changed(event)
        self.assertEqual(controller.hass.created_tasks, [])

    async def test_unchanged_position_is_ignored(self) -> None:
        controller = _controller()
        controller._listener_armed = True
        event = FakeEvent({
            "old_state": _cover_state(50),
            "new_state": _cover_state(50, context=ha_stubs.FakeContext()),
        })
        controller._on_cover_state_changed(event)
        self.assertEqual(controller.hass.created_tasks, [])

    async def test_genuine_manual_move_triggers_pause(self) -> None:
        controller = _controller()
        controller._listener_armed = True
        now = datetime(2026, 7, 1, 12, 0)
        _set_now(now)

        event = FakeEvent({
            "old_state": _cover_state(75),
            "new_state": _cover_state(40, context=ha_stubs.FakeContext(id="manual-move-1")),
        })
        controller._on_cover_state_changed(event)

        self.assertEqual(len(controller.hass.created_tasks), 1)
        await controller.hass.created_tasks[0]
        self.assertIsNotNone(controller._runtime.paused_until)

    async def test_self_issued_command_context_id_does_not_pause(self) -> None:
        controller = _controller()
        controller._listener_armed = True
        controller._last_command_context_ids.add("own-context-id")

        event = FakeEvent({
            "old_state": _cover_state(75),
            "new_state": _cover_state(40, context=ha_stubs.FakeContext(id="own-context-id")),
        })
        controller._on_cover_state_changed(event)
        self.assertEqual(controller.hass.created_tasks, [])

    async def test_self_issued_command_parent_id_does_not_pause(self) -> None:
        """HA sometimes reports the child context id but keeps our command's id as parent_id."""
        controller = _controller()
        controller._listener_armed = True
        controller._last_command_context_ids.add("own-context-id")

        event = FakeEvent({
            "old_state": _cover_state(75),
            "new_state": _cover_state(40, context=ha_stubs.FakeContext(id="child-id", parent_id="own-context-id")),
        })
        controller._on_cover_state_changed(event)
        self.assertEqual(controller.hass.created_tasks, [])

    async def test_real_command_context_from_async_evaluate_is_recognized(self) -> None:
        """End-to-end: a move issued by _async_evaluate must not re-trigger a pause
        when its own resulting state change event comes back through the listener."""
        from custom_components.ha_blinds.const import CONF_MAX_STEP_PER_TICK

        controller = _controller()
        controller.hass.states._states["cover.blind"] = _cover_state(75)
        controller.hass.states._states["sun.sun"] = ha_stubs.FakeState({"azimuth": 230, "elevation": -5})
        controller._listener_armed = True
        _set_now(datetime(2026, 7, 1, 10, 0))  # between earliest_open and privacy hour

        await controller._async_evaluate()
        self.assertEqual(len(controller.hass.services.calls), 1)
        issued_context = controller.hass.services.calls[0]["context"]

        event = FakeEvent({
            "old_state": _cover_state(75),
            "new_state": _cover_state(65, context=ha_stubs.FakeContext(id=issued_context.id)),
        })
        controller._on_cover_state_changed(event)
        self.assertEqual(controller.hass.created_tasks, [])


if __name__ == "__main__":
    unittest.main()
