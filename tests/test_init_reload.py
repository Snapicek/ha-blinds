"""Regression tests for the config-entry reload listener.

The update listener registered in __init__.py used to call the module's
own async_unload_entry/async_setup_entry directly, bypassing HA core's
entry.setup_lock. Any caller that changed entry data/options and *also*
explicitly triggered its own reload (config_flow's reconfigure step,
switch.py's feature toggles) raced this unlocked listener with a second,
properly-locked reload — two concurrent unload/setup cycles for the same
entry, which is what hung Home Assistant. The fix routes the listener
through hass.config_entries.async_reload() so there is only ever one
reload path. These tests assert that behavior directly.
"""

from __future__ import annotations

import unittest

import ha_stubs

ha_stubs.install()

from custom_components.ha_blinds import _async_reload_entry


class TestReloadListener(unittest.IsolatedAsyncioTestCase):
    async def test_reload_listener_uses_locked_async_reload(self):
        hass = ha_stubs.FakeHass()
        entry = ha_stubs.FakeEntry(entry_id="entry1")

        await _async_reload_entry(hass, entry)

        self.assertEqual(hass.config_entries.reload_calls, ["entry1"])

    async def test_data_or_options_update_triggers_exactly_one_reload(self):
        """Mirrors what switch.py and config_flow's reconfigure step do:
        change entry data/options via async_update_entry, which fires this
        listener. Only one reload should ever result from a single change.
        """
        hass = ha_stubs.FakeHass()
        entry = ha_stubs.FakeEntry(entry_id="entry1", options={"enable_privacy_hour": False})
        entry.add_update_listener(_async_reload_entry)

        hass.config_entries.async_update_entry(entry, options={"enable_privacy_hour": True})
        for task in hass.created_tasks:
            await task

        self.assertEqual(hass.config_entries.reload_calls, ["entry1"])

    async def test_reload_listener_swallows_reload_errors(self):
        hass = ha_stubs.FakeHass()
        entry = ha_stubs.FakeEntry(entry_id="entry1")

        async def boom(entry_id):
            raise RuntimeError("reload failed")

        hass.config_entries.async_reload = boom

        # Must not raise — a broken reload shouldn't crash the listener.
        await _async_reload_entry(hass, entry)


if __name__ == "__main__":
    unittest.main()
