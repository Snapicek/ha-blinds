"""Tests for the ha_blinds.pause/resume/evaluate_now services registered in
async_setup (__init__.py). Registration is exercised via the real
async_setup(); dispatch (_iter_targets and the three handlers) is exercised
by grabbing the registered handler off FakeServices and invoking it
directly with a fake ServiceCall, since schema validation itself is not
what's under test here.
"""

from __future__ import annotations

import unittest

import ha_stubs

ha_stubs.install()

from custom_components.ha_blinds import async_setup
from custom_components.ha_blinds.const import (
    ATTR_ENTRY_ID,
    ATTR_MINUTES,
    DOMAIN,
    SERVICE_EVALUATE_NOW,
    SERVICE_PAUSE,
    SERVICE_RESUME,
)


class _FakeCall:
    def __init__(self, data: dict | None = None) -> None:
        self.data = data or {}


class _FakeController:
    def __init__(self) -> None:
        self.paused_minutes: list[int | None] = []
        self.resumed = False
        self.evaluated = False

    async def async_pause(self, minutes=None) -> None:
        self.paused_minutes.append(minutes)

    async def async_resume(self) -> None:
        self.resumed = True

    async def async_evaluate_now(self) -> None:
        self.evaluated = True


class TestServiceRegistration(unittest.IsolatedAsyncioTestCase):
    async def test_services_registered(self) -> None:
        hass = ha_stubs.FakeHass()

        await async_setup(hass, {})

        self.assertTrue(hass.services.has_service(DOMAIN, SERVICE_PAUSE))
        self.assertTrue(hass.services.has_service(DOMAIN, SERVICE_RESUME))
        self.assertTrue(hass.services.has_service(DOMAIN, SERVICE_EVALUATE_NOW))

    async def test_second_setup_call_does_not_duplicate_registration(self) -> None:
        hass = ha_stubs.FakeHass()

        await async_setup(hass, {})
        first_handler = hass.services._handlers[(DOMAIN, SERVICE_PAUSE)]
        await async_setup(hass, {})
        second_handler = hass.services._handlers[(DOMAIN, SERVICE_PAUSE)]

        self.assertIs(first_handler, second_handler)


class TestServiceDispatch(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.hass = ha_stubs.FakeHass()
        await async_setup(self.hass, {})
        self.c1 = _FakeController()
        self.c2 = _FakeController()
        self.hass.data[DOMAIN] = {"entry1": self.c1, "entry2": self.c2}

    async def test_pause_with_no_entry_id_targets_all_controllers(self) -> None:
        handler = self.hass.services._handlers[(DOMAIN, SERVICE_PAUSE)]

        await handler(_FakeCall({ATTR_MINUTES: 30}))

        self.assertEqual(self.c1.paused_minutes, [30])
        self.assertEqual(self.c2.paused_minutes, [30])

    async def test_pause_with_entry_id_targets_only_that_controller(self) -> None:
        handler = self.hass.services._handlers[(DOMAIN, SERVICE_PAUSE)]

        await handler(_FakeCall({ATTR_ENTRY_ID: "entry2", ATTR_MINUTES: 15}))

        self.assertEqual(self.c1.paused_minutes, [])
        self.assertEqual(self.c2.paused_minutes, [15])

    async def test_unknown_entry_id_targets_nothing(self) -> None:
        handler = self.hass.services._handlers[(DOMAIN, SERVICE_PAUSE)]

        await handler(_FakeCall({ATTR_ENTRY_ID: "does_not_exist"}))

        self.assertEqual(self.c1.paused_minutes, [])
        self.assertEqual(self.c2.paused_minutes, [])

    async def test_resume_dispatches_to_all_controllers(self) -> None:
        handler = self.hass.services._handlers[(DOMAIN, SERVICE_RESUME)]

        await handler(_FakeCall())

        self.assertTrue(self.c1.resumed)
        self.assertTrue(self.c2.resumed)

    async def test_evaluate_now_dispatches_to_all_controllers(self) -> None:
        handler = self.hass.services._handlers[(DOMAIN, SERVICE_EVALUATE_NOW)]

        await handler(_FakeCall())

        self.assertTrue(self.c1.evaluated)
        self.assertTrue(self.c2.evaluated)


if __name__ == "__main__":
    unittest.main()
