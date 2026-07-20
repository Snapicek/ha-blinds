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

    class AbortFlow(Exception):
        """Mirrors homeassistant.data_entry_flow.AbortFlow closely enough to
        test _abort_if_unique_id_configured's collision path — our code never
        imports AbortFlow directly, it just lets the base class raise it."""

        def __init__(self, reason: str) -> None:
            self.reason = reason
            super().__init__(reason)

    class ConfigFlow:
        """Structural + behavioral stub covering only what
        async_step_reconfigure's *submission* path touches (not the
        show-form path, which needs real voluptuous/selector — out of scope
        here). Test wiring: set flow._reconfigure_entry and, to simulate a
        unique_id collision, flow._simulate_unique_id_collision = True.
        """

        def __init_subclass__(cls, domain=None, **kwargs) -> None:
            super().__init_subclass__()

        def __init__(self) -> None:
            self.context: dict = {}
            self.hass = None
            self._reconfigure_entry = None
            self._simulate_unique_id_collision = False
            self.unique_id = None

        def _get_reconfigure_entry(self):
            return self._reconfigure_entry

        async def async_set_unique_id(self, unique_id):
            self.unique_id = unique_id
            return None

        def _abort_if_unique_id_configured(self, updates=None, reload_on_update=True) -> None:
            if self._simulate_unique_id_collision:
                raise AbortFlow("already_configured")

        def async_update_and_abort(self, entry, **kwargs):
            """The non-reloading sibling of async_update_reload_and_abort —
            updates the entry and aborts, without itself triggering a
            reload. Records what it was called with so tests can assert the
            reload-triggering variant was NOT used."""
            if "data" in kwargs:
                entry.data = dict(kwargs["data"])
            if "options" in kwargs:
                entry.options = dict(kwargs["options"])
            if "unique_id" in kwargs:
                entry.unique_id = kwargs["unique_id"]
            return {"type": "abort", "reason": kwargs.get("reason")}

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

    class OptionsFlow:  # structural stub
        pass

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.OptionsFlow = OptionsFlow
    config_entries.AbortFlow = AbortFlow

    # -- homeassistant.components.switch/sensor/button --
    components = types.ModuleType("homeassistant.components")
    components_switch = types.ModuleType("homeassistant.components.switch")
    components_sensor = types.ModuleType("homeassistant.components.sensor")
    components_button = types.ModuleType("homeassistant.components.button")

    class SwitchEntity:  # structural stub; switch.py subclasses this
        pass

    class SensorEntity:  # structural stub; sensor.py subclasses this
        pass

    class ButtonEntity:  # structural stub; button.py subclasses this
        pass

    components_switch.SwitchEntity = SwitchEntity
    components_sensor.SensorEntity = SensorEntity
    components_button.ButtonEntity = ButtonEntity
    components.switch = components_switch
    components.sensor = components_sensor
    components.button = components_button

    # -- homeassistant.core --
    core = types.ModuleType("homeassistant.core")

    class Context:
        def __init__(self, *args, **kwargs) -> None:
            self.id = f"fake-context-{next(_context_ids)}"
            self.parent_id = None

    class HomeAssistant:  # structural stub; only used as a type hint
        pass

    class ServiceCall:  # structural stub; only .data is read by __init__.py's handlers
        def __init__(self, data: dict | None = None) -> None:
            self.data = data or {}

    def callback(func):
        return func

    core.Context = Context
    core.HomeAssistant = HomeAssistant
    core.ServiceCall = ServiceCall
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

    entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")

    class AddEntitiesCallback:  # structural stub; only used as a type hint
        pass

    entity_platform.AddEntitiesCallback = AddEntitiesCallback

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

    # __init__.py's async_setup builds vol.Schema(...) service schemas at
    # call time (not just at import time), so unlike selector above these
    # need to actually work — but only enough to construct the schema
    # object; tests invoke the registered service handlers directly and
    # never call the schema on data, so no real validation is implemented.
    config_validation = types.ModuleType("homeassistant.helpers.config_validation")
    config_validation.string = str

    ha.config_entries = config_entries
    ha.core = core
    ha.util = util
    ha.helpers = helpers
    ha.components = components
    helpers.event = event
    helpers.dispatcher = dispatcher
    helpers.storage = storage
    helpers.selector = selector
    helpers.entity_platform = entity_platform
    helpers.config_validation = config_validation

    # -- voluptuous (only what's needed to import config_flow.py and to
    # construct __init__.py's service schemas) --
    voluptuous = types.ModuleType("voluptuous")

    class Invalid(Exception):
        pass

    class Optional:
        """Marker for an optional schema key; only .key matters here since
        schemas are never actually validated in these tests."""

        def __init__(self, key, default=None) -> None:
            self.key = key
            self.default = default

        def __hash__(self):
            return hash(self.key)

        def __eq__(self, other) -> bool:
            return self.key == getattr(other, "key", other)

    class Schema:
        def __init__(self, schema, *args, **kwargs) -> None:
            self.schema = schema

        def __call__(self, data):
            return data

    def Coerce(type_):
        def _validator(value):
            return type_(value)

        return _validator

    voluptuous.Invalid = Invalid
    voluptuous.Optional = Optional
    voluptuous.Schema = Schema
    voluptuous.Coerce = Coerce

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
            "homeassistant.helpers.entity_platform": entity_platform,
            "homeassistant.helpers.config_validation": config_validation,
            "homeassistant.components": components,
            "homeassistant.components.switch": components_switch,
            "homeassistant.components.sensor": components_sensor,
            "homeassistant.components.button": components_button,
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
        self._handlers: dict[tuple[str, str], object] = {}

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

    def has_service(self, domain: str, service: str) -> bool:
        return (domain, service) in self._handlers

    def async_register(self, domain: str, service: str, handler, schema=None) -> None:
        self._handlers[(domain, service)] = handler


class FakeConfigEntries:
    """Records reload calls and mimics async_update_entry's listener-firing.

    Real HA fires each of an entry's update listeners via
    hass.async_create_task (fire-and-forget) whenever async_update_entry
    changes data/options; async_reload is the only thing that serializes
    with entry.setup_lock. Tests use `reload_calls` to assert a data/options
    change results in exactly one reload, not a race between this and some
    other caller triggering its own reload on top.
    """

    def __init__(self, hass: "FakeHass") -> None:
        self._hass = hass
        self.reload_calls: list[str] = []

    def async_update_entry(self, entry: "FakeEntry", data: dict | None = None, options: dict | None = None) -> None:
        if data is not None:
            entry.data = dict(data)
        if options is not None:
            entry.options = dict(options)
        for listener in list(entry._update_listeners):
            self._hass.async_create_task(listener(self._hass, entry))

    async def async_reload(self, entry_id: str) -> bool:
        self.reload_calls.append(entry_id)
        return True


class FakeHass:
    def __init__(self, states: dict | None = None) -> None:
        self.states = FakeStates(states)
        self.services = FakeServices()
        self.created_tasks: list = []
        self.config_entries = FakeConfigEntries(self)
        self.data: dict = {}

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
        self._update_listeners: list = []
        self._unload_callbacks: list = []

    def add_update_listener(self, listener):
        self._update_listeners.append(listener)
        return lambda: self._update_listeners.remove(listener)

    def async_on_unload(self, callback) -> None:
        self._unload_callbacks.append(callback)
