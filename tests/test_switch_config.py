"""Regression tests for HaBlindsBaseSwitch._async_update_config.

This used to call hass.config_entries.async_reload() explicitly right
after async_update_entry() — a second, unsynchronized reload racing the
entry's own update listener (see test_init_reload.py). The fix relies
solely on the listener firing once from async_update_entry. These tests
pin that: exactly one options update, and no direct reload call from the
switch itself.
"""

from __future__ import annotations

import unittest

import ha_stubs

ha_stubs.install()

from custom_components.ha_blinds.const import CONF_ENABLE_PRIVACY_HOUR
from custom_components.ha_blinds.switch import HaBlindsPrivacyHourSwitch


class TestSwitchUpdateConfig(unittest.IsolatedAsyncioTestCase):
    async def test_turn_on_updates_options_without_calling_reload_directly(self):
        hass = ha_stubs.FakeHass()
        entry = ha_stubs.FakeEntry(options={CONF_ENABLE_PRIVACY_HOUR: False})
        switch = HaBlindsPrivacyHourSwitch(coordinator=None, entry=entry)
        switch.hass = hass

        await switch.async_turn_on()

        self.assertEqual(entry.options[CONF_ENABLE_PRIVACY_HOUR], True)
        # The switch itself must not trigger a reload — only the entry's
        # registered update listener may do that (and only if one is
        # actually registered, which it isn't in this narrow test).
        self.assertEqual(hass.config_entries.reload_calls, [])

    async def test_turn_off_updates_options(self):
        hass = ha_stubs.FakeHass()
        entry = ha_stubs.FakeEntry(options={CONF_ENABLE_PRIVACY_HOUR: True})
        switch = HaBlindsPrivacyHourSwitch(coordinator=None, entry=entry)
        switch.hass = hass

        await switch.async_turn_off()

        self.assertEqual(entry.options[CONF_ENABLE_PRIVACY_HOUR], False)
        self.assertEqual(hass.config_entries.reload_calls, [])

    async def test_update_config_plus_registered_listener_reloads_exactly_once(self):
        """End-to-end: with the real listener registered (as __init__.py
        does at setup), toggling a switch must still result in exactly one
        reload — not the double/racing reload this bug used to cause.
        """
        from custom_components.ha_blinds import _async_reload_entry

        hass = ha_stubs.FakeHass()
        entry = ha_stubs.FakeEntry(entry_id="entry1", options={CONF_ENABLE_PRIVACY_HOUR: False})
        entry.add_update_listener(_async_reload_entry)
        switch = HaBlindsPrivacyHourSwitch(coordinator=None, entry=entry)
        switch.hass = hass

        await switch.async_turn_on()
        for task in hass.created_tasks:
            await task

        self.assertEqual(hass.config_entries.reload_calls, ["entry1"])


if __name__ == "__main__":
    unittest.main()
