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

import sys
import types


def install() -> None:
    """Register fake `homeassistant.*` modules in sys.modules, if needed."""
    if "homeassistant" in sys.modules:
        return

    ha = types.ModuleType("homeassistant")

    # -- homeassistant.config_entries --
    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:  # structural stub; only used as a type hint
        pass

    config_entries.ConfigEntry = ConfigEntry

    # -- homeassistant.core --
    core = types.ModuleType("homeassistant.core")

    class Context:
        def __init__(self, *args, **kwargs) -> None:
            self.id = "fake-context-id"
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
    dispatcher.async_dispatcher_send = _unimplemented
    dispatcher.async_dispatcher_connect = _unimplemented

    class Store:  # structural stub; only constructed, never used in these tests
        def __init__(self, *args, **kwargs) -> None:
            pass

    storage.Store = Store

    ha.config_entries = config_entries
    ha.core = core
    ha.util = util
    ha.helpers = helpers
    helpers.event = event
    helpers.dispatcher = dispatcher
    helpers.storage = storage

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
        }
    )


class FakeState:
    def __init__(self, attributes: dict) -> None:
        self.attributes = attributes


class FakeStates:
    def __init__(self, states: dict | None = None) -> None:
        self._states = states or {}

    def get(self, entity_id: str):
        return self._states.get(entity_id)


class FakeHass:
    def __init__(self, states: dict | None = None) -> None:
        self.states = FakeStates(states)


class FakeEntry:
    def __init__(self, data: dict | None = None, options: dict | None = None, entry_id: str = "test_entry") -> None:
        self.data = data or {}
        self.options = options or {}
        self.entry_id = entry_id
