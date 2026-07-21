"""Tests for HaBlindsDaytimeOpenButton.

The "Open" quick-action button used to be a hardcoded 75% preset,
disconnected from the daytime_open_position option. It must instead
mirror whatever daytime_open_position is currently configured for the
current season — both in its displayed name and in the position it
actually sends. See logic.py's is_winter check for the same seasonal
split (months 11,12,1,2,3 = winter).
"""

from __future__ import annotations

from datetime import datetime
import unittest

import ha_stubs

ha_stubs.install()

import custom_components.ha_blinds.button as button_module
from custom_components.ha_blinds.const import (
    CONF_COVER_ENTITY,
    CONF_DAYTIME_OPEN_POSITION_SUMMER,
    CONF_DAYTIME_OPEN_POSITION_WINTER,
)
from custom_components.ha_blinds.button import HaBlindsDaytimeOpenButton
from custom_components.ha_blinds.coordinator import HaBlindsController

SUMMER_DATE = datetime(2026, 7, 21, 8, 0, 0)
WINTER_DATE = datetime(2026, 1, 21, 8, 0, 0)


def _controller(options: dict | None = None) -> HaBlindsController:
    hass = ha_stubs.FakeHass()
    entry = ha_stubs.FakeEntry(
        data={CONF_COVER_ENTITY: "cover.blind"},
        options=options or {},
    )
    return HaBlindsController(hass, entry)


class TestDaytimeOpenButton(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        button_module.dt_util.now = lambda: SUMMER_DATE

    def test_name_reflects_configured_summer_position(self) -> None:
        controller = _controller({CONF_DAYTIME_OPEN_POSITION_SUMMER: 60})
        button = HaBlindsDaytimeOpenButton(controller, controller.entry)
        self.assertEqual(button.name, "Open (60%)")

    def test_name_reflects_configured_winter_position(self) -> None:
        button_module.dt_util.now = lambda: WINTER_DATE
        controller = _controller({CONF_DAYTIME_OPEN_POSITION_WINTER: 70})
        button = HaBlindsDaytimeOpenButton(controller, controller.entry)
        self.assertEqual(button.name, "Open (70%)")

    def test_name_reflects_default_when_unset(self) -> None:
        controller = _controller()
        button = HaBlindsDaytimeOpenButton(controller, controller.entry)
        self.assertEqual(button.name, "Open (60%)")

    def test_name_updates_when_option_changes(self) -> None:
        """Regression: this must read live config, not a value cached at creation."""
        controller = _controller({CONF_DAYTIME_OPEN_POSITION_SUMMER: 60})
        button = HaBlindsDaytimeOpenButton(controller, controller.entry)
        self.assertEqual(button.name, "Open (60%)")

        controller.entry.options = {CONF_DAYTIME_OPEN_POSITION_SUMMER: 85}
        self.assertEqual(button.name, "Open (85%)")

    async def test_press_sends_configured_position_to_cover(self) -> None:
        controller = _controller({CONF_DAYTIME_OPEN_POSITION_SUMMER: 60})
        button = HaBlindsDaytimeOpenButton(controller, controller.entry)

        await button.async_press()

        call = controller.hass.services.calls[0]
        self.assertEqual(call["domain"], "cover")
        self.assertEqual(call["service"], "set_cover_position")
        self.assertEqual(call["data"], {"entity_id": "cover.blind", "position": 60})


if __name__ == "__main__":
    unittest.main()
