"""Minimal fake `homeassistant` modules.

The real `homeassistant` package is not installed in this dev/test
environment (it is a heavy runtime dependency). `coordinator.py` only
needs a handful of names to *exist* at import time — most of them are
never called by the coordinator logic we unit-test here (event
listeners, dispatcher, storage). `dt_util.as_local` is the one function
actually invoked by the code under test, so it's stubbed as an identity
function: we're testing the day-shifting/offset arithmetic in
`coordinator.py`, not homeassistant's own timezone conversion.

Call `install()` before importing anything from
`custom_components.ha_blinds.coordinator`.
"""

from __future__ import annotations

import itertools
import sys
import types

_context_ids = itertools.count()

# Store persists in-memory, keyed by (hass identity, storage key), so that
# separate `Store(hass, version, key)` instances created across coordinator
# calls (it builds a fresh one each time) still see each other's writes —
# same as real HA's on-disk Store keyed by file path.
_store_backing: dict[tuple[int, str], object] = {}


def install() -> None:
    """Register fake `homeassistant.*` modules in sys.modules, if needed."""
    if "homeassistant" in sys.modules:
        return

    ha = types.ModuleType("homeassistant")

    # -- homeassistant.config_entries --
    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:  # structural stub; only used as a type hint
        pass

    class ConfigFlow:  # structural stub; config_flow.py subclasses this with domain=DOMAIN
        def __init_subclass__(cls, domain=None, **kwargs) -> None:
            super().__init_subclass__()

    class OptionsFlow:  # structural stub
        pass

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.OptionsFlow = OptionsFlow

    # -- homeassistant.core --
    core = types.ModuleType("homeassistant.core")

    class Context:
        def __init__(self, *args, **kwargs) -> None:
            self.id = f"fake-context-{next(_context_ids)}"
            self.parent_id = None

    class HomeAssistant:  # structural stub; only used as a type hint
        pass

    def callback(func):
        return func

    core.Context = Context
    core.HomeAssistant = HomeAssistant
    core.callback = callback

    # -- homeassistant.util / homeassistant.util.dt --
    util = types.ModuleType("homeassistant.util")
    dt_util = types.ModuleType("homeassistant.util.dt")

    def as_local(value):
        return value

    def parse_datetime(value):
        from datetime import datetime

        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    def now():
        from datetime import datetime

        return datetime.now()

    dt_util.as_local = as_local
    dt_util.parse_datetime = parse_datetime
    dt_util.now = now
    util.dt = dt_util

    # -- homeassistant.helpers.* --
    helpers = types.ModuleType("homeassistant.helpers")
    event = types.ModuleType("homeassistant.helpers.event")
    dispatcher = types.ModuleType("homeassistant.helpers.dispatcher")
    storage = types.ModuleType("homeassistant.helpers.storage")

    def _unimplemented(*args, **kwargs):
        raise NotImplementedError("not stubbed for this test")

    event.async_track_state_change_event = _unimplemented
    event.async_track_time_interval = _unimplemented

    def async_dispatcher_send(hass, signal, *args, **kwargs) -> None:
        pass  # entities aren't constructed in these tests; nothing to notify

    def async_dispatcher_connect(hass, signal, target):
        return lambda: None  # unsubscribe callable

    dispatcher.async_dispatcher_send = async_dispatcher_send
    dispatcher.async_dispatcher_connect = async_dispatcher_connect

    class Store:
        def __init__(self, hass, version, key, *args, **kwargs) -> None:
            self._store_key = (id(hass), key)

        async def async_load(self):
            return _store_backing.get(self._store_key)

        async def async_save(self, data) -> None:
            _store_backing[self._store_key] = data

    storage.Store = Store

    # config_flow.py's schema-building functions reference sel.* attributes,
    # but only inside function bodies we never call in these tests — the
    # submodule just needs to exist for the `import ... as sel` to succeed.
    selector = types.ModuleType("homeassistant.helpers.selector")

    ha.config_entries = config_entries
    ha.core = core
    ha.util = util
    ha.helpers = helpers
    helpers.event = event
    helpers.dispatcher = dispatcher
    helpers.storage = storage
    helpers.selector = selector

    # -- voluptuous (only what's needed to import config_flow.py) --
    voluptuous = types.ModuleType("voluptuous")

    class Invalid(Exception):
        pass

    voluptuous.Invalid = Invalid

    sys.modules.update(
        {
            "homeassistant": ha,
            "homeassistant.config_entries": config_entries,
            "homeassistant.core": core,
            "homeassistant.util": util,
            "homeassistant.util.dt": dt_util,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.event": event,
            "homeassistant.helpers.dispatcher": dispatcher,
            "homeassistant.helpers.storage": storage,
            "homeassistant.helpers.selector": selector,
            "voluptuous": voluptuous,
        }
    )


class FakeState:
    def __init__(self, attributes: dict, state: str = "some_state", context=None) -> None:
        self.attributes = attributes
        self.state = state
        self.context = context


class FakeContext:
    """Lightweight stand-in for homeassistant.core.Context in test events."""

    def __init__(self, id: str = "test-context", parent_id: str | None = None) -> None:
        self.id = id
        self.parent_id = parent_id


class FakeStates:
    def __init__(self, states: dict | None = None) -> None:
        self._states = states or {}

    def get(self, entity_id: str):
        return self._states.get(entity_id)


class FakeServices:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def async_call(self, domain, service, service_data, context=None, blocking=False) -> None:
        self.calls.append(
            {
                "domain": domain,
                "service": service,
                "data": dict(service_data),
                "context": context,
                "blocking": blocking,
            }
        )


class FakeHass:
    def __init__(self, states: dict | None = None) -> None:
        self.states = FakeStates(states)
        self.services = FakeServices()
        self.created_tasks: list = []

    def async_create_task(self, coro, name: str | None = None):
        import asyncio

        task = asyncio.ensure_future(coro)
        self.created_tasks.append(task)
        return task


class FakeEntry:
    def __init__(self, data: dict | None = None, options: dict | None = None, entry_id: str = "test_entry") -> None:
        self.data = data or {}
        self.options = options or {}
        self.entry_id = entry_id
