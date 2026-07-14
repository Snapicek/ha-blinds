# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant custom integration (`custom_components/ha_blinds`) that automates tilt/position blinds based on sun azimuth/elevation, illuminance (lux), time, and season. It runs entirely local (`iot_class: local_polling`, no cloud dependency) via a periodic tick that evaluates a priority-ordered rule set and issues `cover.set_cover_position` commands. Also published as a HACS repository and a Home Assistant add-on (`addons/ha-blinds`).

## Commands

```bash
# Run the full test suite (only tests logic.py — no HA runtime required)
python3 -m pytest tests/ -v

# Alternative runner (unittest discovery, same tests)
python3 tools/run_logic_tests.py

# Run a single test
python3 -m pytest tests/test_logic.py::TestDecisionEngine::test_night_close_triggers -v
```

There is no build/lint step configured (no linter config or CI found in the repo). `pyproject.toml` only declares project metadata and pytest config (`testpaths = ["tests"]`).

## Architecture

The integration is deliberately split so that all decision-making logic is pure and testable without any Home Assistant runtime:

```
config_flow.py     — Setup UI, options UI, input validation
coordinator.py     — Runtime controller per config entry (HA I/O)
logic.py           — Pure decision engine (no HA imports, fully unit-testable)
sensor.py          — Read-only status sensors
switch.py          — Feature toggle switches
button.py          — Manual action buttons ("Evaluate Now")
```

Data flows one direction: `coordinator` reads HA state → calls `logic.DecisionEngine.evaluate()` → writes the result back to HA (cover commands, sensor/switch state).

**`logic.py`** — `DecisionEngine.evaluate()` takes a `DecisionInputs` snapshot (time, sun azimuth/elevation, lux, temp, current position, paused flag) and a `DecisionConfig`, and returns a decision (`should_move`, `target_position`, `reason`) with no side effects. Rules are evaluated in a fixed priority order (paused → too_early → sunset_closing → pre_sunrise_closing → privacy_hour → night_close → sun_blocked_by_obstacle → direct_sun_high_lux/peak_heat/sun_elevation_tracking → daytime_cloudy → daytime_open). See `ARCHITECTURE.md` for the full table, the sun-at-window geometry formula, and the elevation→position mapping — read it before touching rule ordering.

**`coordinator.py`** — One `HaBlindsController` per config entry. Registers the `tick_minutes` interval callback, reads live entity state (`sun.sun`, cover, lux sensor, optional temp sensor), computes actual sunrise/sunset times from `sun.sun`'s next-event attributes (non-trivial — see `ARCHITECTURE.md` § "Sunrise/sunset time computation"), tracks runtime state (`paused_until`, `privacy_entered_at`, `high_lux_since`), calls into `logic.py`, then caps movement via `max_step_per_tick` and sends `cover.set_cover_position` with a unique `Context` per command (used to distinguish automated moves from manual ones). Manual cover moves are detected via `async_track_state_change_event` and pause automation for `manual_override_minutes`.

**Config entry layout**: `entry.data` holds stable identifiers set once at setup (cover entities, lux/temp sensors, window azimuth/view angles). `entry.options` holds everything user-tunable afterward (thresholds, timing, feature toggles) and reconfiguring options triggers a full entry reload via `_async_reload_entry` in `__init__.py`.

### Adding a new decision rule

Follow this sequence (from `ARCHITECTURE.md`):

1. Add new config fields to `DecisionConfig` in `logic.py` and to `DEFAULTS` in `const.py`
2. Wire the field into `_decision_config()` in `coordinator.py`
3. If the rule needs time-tracking state (like `high_lux_since`), add a field to `_RuntimeState` in `coordinator.py` and update it in `_async_evaluate()`
4. Insert the rule at the correct priority position in `evaluate()`
5. Expose it in the options UI in `config_flow.py` if user-configurable
6. Add a toggle switch entity in `switch.py` if the rule needs on/off control
7. Write unit tests in `tests/test_logic.py`: one asserting the rule fires when expected, one asserting a higher-priority rule preempts it

### Testing conventions

`tests/test_logic.py` constructs a `DecisionConfig` via a local `_cfg(**overrides)` helper with sane defaults, then calls `engine.evaluate(DecisionInputs(...))` and asserts on `res.should_move`, `res.target_position`, and `res.reason`. No HA mocks are used or needed — keep new logic tests in this pure style.

## Versioning

Three files carry independent version numbers that must be kept in sync manually for the integration itself: `pyproject.toml`, `custom_components/ha_blinds/manifest.json`, and `hacs.json`. `addons/ha-blinds/addon.yaml` has its own separate version line (add-on packaging version, not the integration version).

## Key conventions

- Domain constant `DOMAIN = "ha_blinds"`; all `CONF_*` option keys and their defaults live centrally in `const.py` (`DEFAULTS` dict) — don't hardcode option keys or default values elsewhere.
- Config entry migrations go in `async_migrate_entry` in `__init__.py` (see the v1→v2 example adding `CONF_COVER_ENTITIES`).
- Services (`ha_blinds.pause`, `ha_blinds.resume`, `ha_blinds.evaluate_now`) are registered once in `async_setup` in `__init__.py` and dispatch to one or all controllers via `entry_id` (schema in `services.yaml`).
- Winter is hardcoded as months `(11, 12, 1, 2, 3)`; heat protection and privacy hour use separate winter/summer thresholds.
