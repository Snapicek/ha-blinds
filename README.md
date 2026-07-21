# HA Blinds

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![Project Maintenance](https://img.shields.io/badge/maintainer-%40Snapicek-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.5.0%2B-green.svg)

Smart blind automation for Home Assistant. Moves blinds based on sun position, light level, and time — without cloud dependency.

## How it works

The integration runs a decision engine on a configurable tick interval (default 5 min). Each tick it reads the current sun position, lux level, and cover state, evaluates a priority-ordered rule set, and issues a `cover.set_cover_position` command when needed. Movement is capped per tick (`max_step_per_tick`) for smooth, gradual transitions.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full decision flow.

## Requirements

- Home Assistant `2026.5.0` or newer
- A cover entity with position support
- An illuminance sensor (lux)
- The built-in `sun.sun` entity (always present in HA)

## Installation

### HACS (recommended)

1. Open HACS → **Integrations** → menu (top-right) → **Custom repositories**
2. Add `https://github.com/Snapicek/ha-blinds` — category: **Integration**
3. Install **HA Blinds** and restart Home Assistant

### Manual

Copy `custom_components/ha_blinds` into `/config/custom_components/` and restart.

## Setup

1. **Settings → Devices & Services → Add Integration → HA Blinds**
2. Select entities:
   - Cover (required) — primary blind
   - Additional covers (optional) — moved together with the primary
   - Lux sensor (required) — illuminance in lux
   - Temperature sensor (optional) — needed for heat protection
3. Set window geometry:
   - **Window azimuth** — compass direction the window faces (0–359°, 0=N, 90=E, 180=S, 270=W)
   - **View left / right** — degrees of sky visible left and right of centre (e.g. 60+60 = 120° arc)
4. Configure behavior in **Options** (accessible any time from the integration page)

## Features

### Earliest open time
Blinds never open before `earliest_open_hour`:`earliest_open_minute` (default 07:30), regardless of sunrise, sun position, or lux. This prevents early-morning disturbance in summer when sunrise is very early.

### Daytime open
When the sun is above the horizon but not yet facing the window (morning, evening), blinds open to `daytime_open_position_summer` (default 60%) or `daytime_open_position_winter` (default 70%), depending on the season (winter = months 11–3), to let in diffuse light.

### Lux-driven daytime logic
The lux sensor now actively influences daytime decisions:
- **Sun blocked by obstacle**: When sun azimuth points at the window but lux is below `lux_low_threshold` (default 5000), the sun is blocked by a building or clouds — blinds open to the seasonal daytime open position instead of closing.
- **Cloudy day**: When sun is not at window and lux is below `lux_low_threshold`, blinds open wider to `daytime_cloudy_position` (default 90%) to let in more diffuse light.

### Sun elevation tracking
When the sun faces the window, slat angle is adjusted based on elevation:

| Elevation | Position | Reason |
|---|---|---|
| < 10° | min_position (closed) | Direct eye-level glare |
| 10–25° | 50% | Low angle — partial block |
| ≥ 25° | 75% | High sun — open |

### High lux protection
When lux exceeds the close threshold and the sun is at the window, blinds close to `min_position` after a debounce delay. Reopens automatically (via elevation tracking) when lux drops.

### Heat protection *(optional)*
During configured hours in summer, blinds close to a fixed position regardless of lux. Requires a temperature sensor and temperature above the threshold.

### Sunset closing *(optional)*
Closes blinds at `actual_sunset + sunset_offset_minutes`. Keeps them closed until `actual_sunrise + sunrise_offset_minutes` (sleep-in support). Both offsets default to 0.

Before the hard cutoff, **dusk closing** watches lux instead: within `dusk_window_minutes` of sunset, if lux drops below `dusk_lux_threshold`, blinds close early. This makes closing feel natural for windows shaded early by a neighboring building or terrain — direct light can disappear well before astronomical sunset. `sunset_closing` still applies afterwards as a fallback in case the lux sensor is missing or stays bright.

### Privacy hour *(optional)*
From a configured evening hour, blinds close and stay closed for `privacy_duration_minutes`. Separate thresholds for winter and summer.

### Manual override
Any manual cover movement pauses the automation for `manual_override_minutes`. Each subsequent manual move resets the timer. Resume earlier via the **Automation Enabled** switch or the `ha_blinds.resume` service.

## Configuration reference

Options are split into four menus: **Thresholds**, **Timing**, **Sunset**, **Features**.

### Thresholds

| Option | Default | Description |
|---|---|---|
| `lux_close_summer` | 35000 lx | Lux above which blinds close (summer) |
| `lux_close_winter` | 20000 lx | Lux above which blinds close (winter) |
| `heat_start_hour` | 10 | Heat protection start hour |
| `heat_end_hour` | 17 | Heat protection end hour |
| `heat_position` | 20% | Blind position during heat protection |
| `temp_threshold` | 24.0°C | Temperature above which heat protection activates |
| `winter_privacy_hour` | 16:00 | Privacy hour start (Nov–Mar) |
| `summer_privacy_hour` | 19:00 | Privacy hour start (Apr–Oct) |
| `night_close_position` | 0% | Position for night/privacy/sunset close (0 or 100) |
| `daytime_open_position_summer` | 60% | Position when sun is not at window (morning/evening), Apr–Oct |
| `daytime_open_position_winter` | 70% | Position when sun is not at window (morning/evening), Nov–Mar |
| `lux_low_threshold` | 5000 lx | Below this, sun is considered blocked (building, clouds) |
| `daytime_cloudy_position` | 90% | Position when overcast (lux below low threshold) |
| `movement_threshold` | 5% | Minimum position difference to trigger a move (reduces noise) |
| `min_position` | 3% | Motor never goes below this position (prevents slat flip on overshoot) |

### Timing

| Option | Default | Description |
|---|---|---|
| `tick_minutes` | 5 | How often the decision engine runs |
| `max_step_per_tick` | 10% | Maximum position change per tick (smooth movement) |
| `debounce_minutes` | 5 | Delay before high-lux close triggers |
| `manual_override_minutes` | 45 | How long manual override pauses automation |

### Sunset

| Option | Default | Description |
|---|---|---|
| `enable_sunset_closing` | off | Enable sunset/sunrise feature (also gates dusk closing) |
| `sunset_offset_minutes` | 0 | Close this many minutes after actual sunset (negative = before) |
| `sunrise_offset_minutes` | 0 | Open this many minutes after actual sunrise (sleep-in) |
| `dusk_lux_threshold` | 1000 lx | Below this, close early during the dusk window (before sunset_time) |
| `dusk_window_minutes` | 60 | How long before sunset_time the dusk-lux check is active |
| `earliest_open_hour` | 7 | Blinds never open before this hour (hard floor) |
| `earliest_open_minute` | 30 | Minute part of earliest open time |

### Features

| Option | Default | Description |
|---|---|---|
| `enable_privacy_hour` | on | Enable privacy hour rule |
| `enable_high_lux_protection` | on | Enable high lux close |
| `enable_heat_protection` | on | Enable heat protection |
| `enable_sun_elevation_tracking` | on | Enable slat angle tracking when sun is at window |

## Entities

Each config entry creates a device with these entities:

| Entity | Type | Description |
|---|---|---|
| `sensor.*_state` | Sensor | Last decision reason and metadata |
| `sensor.*_last_reason` | Sensor | Most recent rule that fired |
| `sensor.*_target_position` | Sensor | Last commanded position |
| `sensor.*_last_decision` | Sensor | Timestamp of last evaluation |
| `sensor.*_error_count` | Sensor | Consecutive evaluation errors |
| `sensor.*_sun_at_window` | Sensor | Whether sun is currently facing the window |
| `switch.*_automation_enabled` | Switch | Pause/resume automation |
| `switch.*_privacy_hour_enabled` | Switch | Toggle privacy hour |
| `switch.*_high_lux_protection_enabled` | Switch | Toggle high lux protection |
| `switch.*_heat_protection_enabled` | Switch | Toggle heat protection |
| `switch.*_sun_tracking_enabled` | Switch | Toggle sun elevation tracking |
| `button.*_evaluate_now` | Button | Trigger immediate evaluation |

## Services

| Service | Fields | Description |
|---|---|---|
| `ha_blinds.pause` | `entry_id` (opt), `minutes` (opt) | Pause automation |
| `ha_blinds.resume` | `entry_id` (opt) | Resume immediately |
| `ha_blinds.evaluate_now` | `entry_id` (opt) | Force immediate evaluation |

Example:

```yaml
service: ha_blinds.pause
data:
  minutes: 60
```

If `entry_id` is omitted, the service applies to all HA Blinds entries.

## Troubleshooting

**Blinds not moving**
- Check `sensor.*_last_reason` — it tells you which rule is active
- Check `sensor.*_error_count` — errors mean a required entity is missing or unavailable
- Verify the cover entity supports `set_cover_position`

**Debug logs**

```yaml
logger:
  logs:
    custom_components.ha_blinds: debug
```

**Force evaluation**

Use the **Evaluate Now** button on the device, or call `ha_blinds.evaluate_now`.

**Slow Zigbee covers**

Set `zigbee_delay_seconds` (in Timing options) to 1–2 s to stagger commands across multiple covers in the same group.

## Changelog

See [GitHub Releases](https://github.com/Snapicek/ha-blinds/releases) for full history.

## Support

- Issues: [github.com/Snapicek/ha-blinds/issues](https://github.com/Snapicek/ha-blinds/issues)
