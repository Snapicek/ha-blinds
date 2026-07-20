"""Tests for HaBlindsConfigFlow.async_step_reconfigure's submission path.

This step was completely untested before — it's also the exact step that
caused a real production hang (see test_init_reload.py / test_switch_config.py
for the underlying double-reload race). It now uses async_update_and_abort
instead of async_update_reload_and_abort so the entry's update listener is
the only thing that ever reloads (HA core deprecated the old combination:
warns since 2026.6, hard error in 2026.12). These tests pin that choice, plus
the unique-id-collision and temp-sensor-clearing behavior the step relies on.

Only the *submission* path (user_input provided) is covered — the show-form
path builds a real voluptuous schema with entity selectors, which would need
much heavier stubbing (real vol.Schema/selector.*) for no behavioral payoff
here.
"""

from __future__ import annotations

import unittest

import ha_stubs

ha_stubs.install()

from homeassistant.config_entries import AbortFlow
from custom_components.ha_blinds.config_flow import HaBlindsConfigFlow
from custom_components.ha_blinds.const import (
    CONF_COVER_ENTITIES,
    CONF_COVER_ENTITY,
    CONF_LUX_SENSOR,
    CONF_TEMP_SENSOR,
    CONF_WINDOW_AZIMUTH,
    CONF_WINDOW_VIEW_LEFT,
    CONF_WINDOW_VIEW_RIGHT,
)


def _entry(**data_overrides):
    data = {
        CONF_COVER_ENTITY: "cover.blind",
        CONF_COVER_ENTITIES: [],
        CONF_LUX_SENSOR: "sensor.old_lux",
        CONF_WINDOW_AZIMUTH: 240,
        CONF_WINDOW_VIEW_LEFT: 60,
        CONF_WINDOW_VIEW_RIGHT: 60,
    }
    data.update(data_overrides)
    return ha_stubs.FakeEntry(data=data)


def _flow(entry) -> HaBlindsConfigFlow:
    flow = HaBlindsConfigFlow()
    flow._reconfigure_entry = entry
    return flow


class TestReconfigureSubmission(unittest.IsolatedAsyncioTestCase):
    async def test_updates_lux_sensor_without_touching_cover(self):
        entry = _entry()
        flow = _flow(entry)

        result = await flow.async_step_reconfigure(
            {
                CONF_COVER_ENTITY: "cover.blind",
                CONF_LUX_SENSOR: "sensor.new_lux",
                CONF_WINDOW_AZIMUTH: 240,
                CONF_WINDOW_VIEW_LEFT: 60,
                CONF_WINDOW_VIEW_RIGHT: 60,
            }
        )

        self.assertEqual(entry.data[CONF_LUX_SENSOR], "sensor.new_lux")
        self.assertEqual(entry.data[CONF_COVER_ENTITY], "cover.blind")
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "reconfigure_successful")
        # unique_id was never touched — cover entity didn't change.
        self.assertIsNone(flow.unique_id)

    async def test_cover_entity_change_sets_unique_id_when_no_collision(self):
        entry = _entry()
        flow = _flow(entry)

        await flow.async_step_reconfigure(
            {
                CONF_COVER_ENTITY: "cover.new_blind",
                CONF_LUX_SENSOR: "sensor.old_lux",
                CONF_WINDOW_AZIMUTH: 240,
                CONF_WINDOW_VIEW_LEFT: 60,
                CONF_WINDOW_VIEW_RIGHT: 60,
            }
        )

        self.assertEqual(flow.unique_id, "cover.new_blind")
        self.assertEqual(entry.data[CONF_COVER_ENTITY], "cover.new_blind")
        self.assertEqual(entry.unique_id, "cover.new_blind")

    async def test_cover_entity_collision_aborts_without_mutating_entry(self):
        entry = _entry()
        flow = _flow(entry)
        flow._simulate_unique_id_collision = True

        with self.assertRaises(AbortFlow) as ctx:
            await flow.async_step_reconfigure(
                {
                    CONF_COVER_ENTITY: "cover.already_used_elsewhere",
                    CONF_LUX_SENSOR: "sensor.old_lux",
                    CONF_WINDOW_AZIMUTH: 240,
                    CONF_WINDOW_VIEW_LEFT: 60,
                    CONF_WINDOW_VIEW_RIGHT: 60,
                }
            )

        self.assertEqual(ctx.exception.reason, "already_configured")
        # Aborted before any data was written.
        self.assertEqual(entry.data[CONF_COVER_ENTITY], "cover.blind")

    async def test_clearing_temp_sensor_field_removes_it(self):
        entry = _entry(**{CONF_TEMP_SENSOR: "sensor.old_temp"})
        flow = _flow(entry)

        await flow.async_step_reconfigure(
            {
                CONF_COVER_ENTITY: "cover.blind",
                CONF_LUX_SENSOR: "sensor.old_lux",
                CONF_TEMP_SENSOR: "",
                CONF_WINDOW_AZIMUTH: 240,
                CONF_WINDOW_VIEW_LEFT: 60,
                CONF_WINDOW_VIEW_RIGHT: 60,
            }
        )

        self.assertNotIn(CONF_TEMP_SENSOR, entry.data)

    async def test_does_not_use_the_reload_and_abort_variant(self):
        """Regression guard for the HA-core-deprecated double-reload
        pattern: the stub deliberately has no async_update_reload_and_abort
        at all, so a regression back to it fails loudly (AttributeError)
        instead of silently reintroducing the race."""
        entry = _entry()
        flow = _flow(entry)
        self.assertFalse(hasattr(flow, "async_update_reload_and_abort"))

        result = await flow.async_step_reconfigure(
            {
                CONF_COVER_ENTITY: "cover.blind",
                CONF_LUX_SENSOR: "sensor.new_lux",
                CONF_WINDOW_AZIMUTH: 240,
                CONF_WINDOW_VIEW_LEFT: 60,
                CONF_WINDOW_VIEW_RIGHT: 60,
            }
        )
        self.assertEqual(result["type"], "abort")


if __name__ == "__main__":
    unittest.main()
