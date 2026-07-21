# Architecture

Technical reference for contributors and integrators.

## Layer overview

```
config_flow.py     — Setup UI, options UI, input validation
coordinator.py     — Runtime controller per config entry
logic.py           — Pure decision engine (no HA dependency)
sensor.py          — Read-only status sensors
switch.py          — Feature toggle switches
button.py          — Manual action buttons
```

Data flows in one direction: `coordinator` reads HA state, calls `logic`, then writes back to HA.

## coordinator.py

One `HaBlindsController` instance per config entry. Responsibilities:

- Registers a time interval callback (`tick_minutes`)
- Reads `sun.sun`, cover, lux sensor, optional temperature sensor
- Computes `sunrise_time` and `sunset_time` with offsets (see below)
- Tracks runtime state: `paused_until`, `privacy_entered_at`, `high_lux_since`
- Calls `logic.DecisionEngine.evaluate()`
- Applies `max_step_per_tick` to cap movement per tick
- Sends `cover.set_cover_position` with a unique `Context` per command
- Detects manual cover movements via `async_track_state_change_event`

### Sunrise/sunset time computation

`sun.sun` always exposes the **next** upcoming event. After actual sunset, `next_setting` flips to tomorrow's value; after actual sunrise, `next_rising` flips to tomorrow's.

`_get_sunset_time()` detects post-sunset state by checking `next_setting > next_rising` (if tomorrow's sunset is after tomorrow's sunrise, we are in nighttime). When post-sunset, it subtracts one day to recover today's actual sunset before applying the offset.

`_get_sunrise_time()` uses the same pattern: `next_setting < next_rising` means daytime. During daytime, if a sleep-in offset is configured and the window hasn't expired yet, it returns `today_sunrise + offset` so the engine keeps the pre-sunrise gate active.

### Manual override detection

The cover state change listener fires on every position change. A change is considered manual if:

1. The event context does not match any context stored in `_last_command_context_ids` (set each tick before issuing commands), **and**
2. The new position is not within ±2% of `last_target` — fallback for devices (e.g. Sonoff/Zigbee) that do not propagate HA service call context through device state updates

When a manual move is detected, `async_pause()` is called and the pause timer is reset regardless of whether a pause was already active.

### Step movement

```python
step = max_step_per_tick
if target > current:
    commanded = min(target, current + step)
else:
    commanded = max(target, current - step)
```

With `max_step_per_tick = 20` and `tick_minutes = 5`, moving from 0% to 75% takes 4 ticks (20 minutes).

## logic.py

`DecisionEngine.evaluate()` is a pure function: same inputs always produce the same output. No HA imports, fully unit-testable.

### Decision priority (highest → lowest)

```
1. paused
2. too_early              — now < earliest_open_hour:earliest_open_minute
3. dusk_closing           — sunset - dusk_window <= now < sunset AND lux < dusk_lux_threshold
4. sunset_closing         — now >= actual_sunset + sunset_offset (fallback ceiling, ignores lux)
5. pre_sunrise_closing    — now < actual_sunrise + sunrise_offset AND hour < 12
6. privacy_hour           — time-based or duration-based
7. night_close            — elevation < 0
                            UNLESS in sunset offset window (elevation < 0 but not yet sunset_time)
8. [sun_at_window = True AND lux < lux_low_threshold]
   sun_blocked_by_obstacle — open to seasonal daytime_open_position (sun behind building/clouds)
9. [sun_at_window = True AND lux >= lux_low_threshold (or lux unavailable)]
   a. direct_sun_high_lux — lux >= close_threshold, debounced
   b. peak_heat_hours     — summer + heat hours + enable_heat_protection
   c. sun_elevation_tracking — elevation-based slat position
   d. sun_tracking_disabled  — tracking off, hold position
10. [sun_at_window = False AND lux < lux_low_threshold]
   daytime_cloudy         — open to daytime_cloudy_position (more light on overcast days)
11. [sun_at_window = False]
   daytime_open           — open to daytime_open_position_summer or _winter, by season
```

Rules 3–6 form the **night/offset window**. `dusk_closing` closes early when it's actually
getting dark (lux-driven) — useful for windows shaded early by a neighboring building, where
direct sun disappears well before the astronomical sunset. `sunset_closing` remains a fallback
ceiling: if the lux sensor is missing or stays bright past sunset, it closes anyway. The guards
on rules 4 and 6 ensure `pre_sunrise_closing` and `night_close` do not fire prematurely during
the sunset offset window (between actual sunset and `sunset + offset`).

### Sun-at-window geometry

```
left  = (window_azimuth - window_view_left)  % 360
right = (window_azimuth + window_view_right) % 360
```

For a window at azimuth 240° with ±60° view: left = 180°, right = 300°. The sun is at the window when azimuth is within this arc **and** elevation > 0°.

### Elevation → position mapping

Applied only when sun is at the window:

| Elevation | Target position |
|---|---|
| < 10° | min_position — very low sun, direct glare |
| 10–25° | 50% — low angle, partial block |
| ≥ 25° | 75% — overhead, open |

### Winter vs summer

Winter months: November, December, January, February, March (`now.month in (11, 12, 1, 2, 3)`).

Heat protection and privacy hour use separate thresholds for winter/summer.

### High lux debounce

`high_lux_since` is set by the coordinator the first time lux exceeds `lux_close_*`. The engine only closes when `now - high_lux_since >= debounce_minutes`. This prevents rapid oscillation on transient lux spikes.

When lux drops, `high_lux_since` is cleared and elevation tracking resumes on the next tick.

## State tracking

`_RuntimeState` in coordinator:

| Field | Purpose |
|---|---|
| `paused_until` | Datetime until automation is paused; persisted to `.storage` across restarts |
| `privacy_entered_at` | When privacy hour was first triggered (used for duration window) |
| `high_lux_since` | When lux first exceeded close threshold (debounce timer) |
| `last_reason` | Most recent decision reason string |
| `last_target` | Most recent commanded position |
| `sun_at_window` | Boolean exposed to sensors |
| `error_count` | Consecutive evaluation failures |

`paused_until` is the only field persisted to HA storage (via `Store`). All others reset on reload.

## Testing

Unit tests live in `tests/test_logic.py` and cover `logic.py` only — no HA mocks needed.

Run:

```bash
python3 -m pytest tests/ -v
# or
python3 tools/run_logic_tests.py
```

Tests pass `DecisionInputs` directly to `DecisionEngine.evaluate()` and assert on `reason` and `target_position`. When adding a new rule:

1. Add the rule to `evaluate()` in the correct priority position
2. Add a test that verifies the rule fires when expected
3. Add a test that verifies it does **not** fire when a higher-priority rule applies

## Adding a new rule

1. Add any new config fields to `DecisionConfig` in `logic.py` and `DEFAULTS` in `const.py`
2. Add the field to `_decision_config()` in `coordinator.py`
3. If the rule needs time-tracking state (like `high_lux_since`), add a field to `_RuntimeState` and update it in `_async_evaluate()`
4. Insert the rule at the correct priority position in `evaluate()`
5. Add it to the options UI in `config_flow.py` if user-configurable
6. Add a switch entity in `switch.py` if it needs a toggle
7. Write unit tests

## Config entry layout

| Storage | Keys |
|---|---|
| `entry.data` | `cover_entity`, `cover_entities`, `lux_sensor`, `temp_sensor`, `window_azimuth`, `window_view_left`, `window_view_right` |
| `entry.options` | All behavioral options (thresholds, timing, feature toggles) |

`entry.data` holds stable identifiers (entities, window geometry). `entry.options` holds everything the user tunes after setup. This separation allows the options flow to reconfigure behavior without touching entity linkage.
