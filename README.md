# HA Blinds

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![Project Maintenance](https://img.shields.io/badge/maintainer-%40Snapicek-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.5.0%2B-green.svg)

Smart blind automation for Home Assistant using sun position, light level, optional temperature input, and time-based rules.

## What This Integration Can Do

- Automatically move blinds during the day based on sun elevation and window direction
- Reduce glare with direct-sun + high-lux protection
- Re-open blinds when lux drops, with debounce to prevent flapping
- Apply heat protection during configured hours (summer behavior)
- Enforce privacy mode at configured evening times (winter/summer split)
- Close at sunset (optional feature)
- Pause/resume automation instantly using built-in services
- Run multiple independent blind automations in one Home Assistant instance

## Requirements

- Home Assistant Core `2026.5.0` or newer

## Installation

### HACS (recommended)

1. Open HACS.
2. Go to **Integrations**.
3. Open menu (top-right) -> **Custom repositories**.
4. Add repository URL:
   - `https://github.com/Snapicek/ha-blinds`
   - Category: **Integration**
5. Install **HA Blinds**.
6. Restart Home Assistant.

### Manual

1. Copy `custom_components/ha_blinds` to:

```text
/config/custom_components/ha_blinds
```

2. Restart Home Assistant.

## Quick Setup

1. Go to **Settings -> Devices & Services -> Add Integration**.
2. Search for **HA Blinds**.
3. Pick entities:
   - Cover (required)
   - Lux sensor (required)
   - Temperature sensor (optional)
4. Set window geometry:
   - Window azimuth (`0..359`)
   - View left (`0..180`)
   - View right (`0..180`)
5. Save and tune behavior in **Options**.

## How the Code Works

The integration is split into clear runtime layers:

- `custom_components/ha_blinds/config_flow.py`
  - Handles setup and options UI
  - Validates and normalizes user input (time selectors, numeric ranges)
  - Persists stable identifiers in `entry.data` and behavior values in `entry.options`
- `custom_components/ha_blinds/coordinator.py`
  - Runtime controller for each config entry
  - Triggers periodic evaluation every `tick_minutes`
  - Reads states from `cover`, `sun.sun`, lux sensor, and optional temp sensor
  - Applies movement limits (`max_step_per_tick`) and optional Zigbee delay
- `custom_components/ha_blinds/logic.py`
  - Pure decision engine (no Home Assistant dependencies)
  - Produces deterministic target + reason based on config + inputs
- `custom_components/ha_blinds/sensor.py`, `switch.py`, `button.py`
  - Expose status, toggles, and manual actions in UI

### Runtime flow

1. Controller gathers current states.
2. Decision engine evaluates rules in priority order.
3. Result returns `should_move`, `target_position`, and a reason.
4. Controller sends `cover.set_cover_position` when needed.
5. Sensors update with reason, target, timestamps, and error counters.

## Decision Model (Priority)

Highest to lowest:

1. Paused automation
2. Sunset closing (if enabled)
3. Privacy hour duration window
4. Night close (sun below horizon)
5. High lux + direct sun protection
6. Heat protection
7. Low lux reopen
8. Sun elevation tracking

This order ensures safety and privacy rules override comfort rules.

## Main Options and Their Impact

- `tick_minutes`: how often logic runs
- `max_step_per_tick`: smooth vs aggressive movement
- `debounce_minutes`: anti-flapping delay for lux-triggered transitions
- Lux thresholds (`lux_close_*`, `lux_open_*`): when to close/reopen
- Heat window (`heat_start_hour`, `heat_end_hour`, `heat_position`, `temp_threshold`)
- Privacy (`winter_privacy_hour`, `summer_privacy_hour`, `privacy_duration_minutes`)
- `night_close_position`: `0` (closed) or `100` (privacy mode)
- Feature toggles: enable/disable specific rule groups

## Entities Created

Each config entry creates sensors on the HA Blinds device:

- `sensor.<entry>_state`
- `sensor.<entry>_last_reason`
- `sensor.<entry>_target_position`
- `sensor.<entry>_last_decision`
- `sensor.<entry>_error_count`
- `sensor.<entry>_sun_at_window`

Useful attributes on `sensor.<entry>_state` include `last_reason`, `last_target`, `paused_until`, and `error_count`.

## Services

- `ha_blinds.pause`
  - Optional fields: `entry_id`, `minutes`
- `ha_blinds.resume`
  - Optional field: `entry_id`
- `ha_blinds.evaluate_now`
  - Optional field: `entry_id`

Example:

```yaml
service: ha_blinds.pause
data:
  entry_id: "your_entry_id"
  minutes: 30
```

## Typical Use Cases

- **Home office glare control**: enable high-lux protection + longer debounce
- **Summer cooling**: set heat protection hours and lower temp threshold
- **Privacy-first setup**: earlier privacy hour + long privacy duration
- **Quiet Zigbee network**: add `zigbee_delay_seconds` for slow cover hardware

## Troubleshooting

1. Enable integration debug logs:

```yaml
logger:
  logs:
    custom_components.ha_blinds: debug
```

2. Check these sensors first:
   - `sensor.<entry>_state`
   - `sensor.<entry>_last_reason`
   - `sensor.<entry>_error_count`
3. Run `ha_blinds.evaluate_now` to test immediate response.
4. Verify configured entities exist and have valid numeric states.

## Limitations and Notes

- Requires valid cover + lux entities to act.
- Heat protection depends on optional temperature sensor and summer conditions.
- Logic is local-only; no external cloud dependency.
- Designed for periodic, bounded movement (not continuous real-time tracking).

## Changelog

### v1.16.1

- Raised minimum Home Assistant version to `2026.5.0`
- Updated options flow for newer Home Assistant patterns
- Improved options persistence and reload stability
- Updated diagnostics and monitoring docs

## Support

- Issues: `https://github.com/Snapicek/ha-blinds/issues`
- Repository: `https://github.com/Snapicek/ha-blinds`

