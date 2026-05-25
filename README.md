# HA Blinds

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![Project Maintenance](https://img.shields.io/badge/maintainer-%40Snapicek-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.5.0%2B-green.svg)

Smart blind automation for Home Assistant using sun position, lux, temperature (optional), and time-based rules.

## Features

- UI-based setup via Config Flow (no YAML setup required)
- Per-blind multi-instance support
- Sun elevation and window-azimuth based positioning
- High-lux and low-lux debounce protection
- Optional heat-protection mode (temperature sensor)
- Privacy hour and optional sunset closing
- Runtime controls via services (`pause`, `resume`, `evaluate_now`)
- Diagnostic sensors for state, reason, target, and error count

## Requirements

- Home Assistant Core `2026.5.0` or newer

## Installation

### HACS (recommended)

1. Open HACS.
2. Go to **Integrations**.
3. Click the menu (top-right) -> **Custom repositories**.
4. Add repository URL:
   - `https://github.com/Snapicek/ha-blinds`
   - Category: **Integration**
5. Find **HA Blinds** in HACS and install.
6. Restart Home Assistant.

### Manual

1. Copy `custom_components/ha_blinds` into your Home Assistant config directory:

```text
/config/custom_components/ha_blinds
```

2. Restart Home Assistant.

## Configuration

1. Go to **Settings -> Devices & Services -> Add Integration**.
2. Search for **HA Blinds**.
3. Select:
   - Cover entity (required)
   - Lux sensor (required, illuminance)
   - Temperature sensor (optional)
4. Set window geometry:
   - Window azimuth (0-359)
   - View left / view right (0-180)
5. Finish setup, then tune behavior in **Options**.

### Common options

- Tick interval (`tick_minutes`): evaluation frequency
- Debounce (`debounce_minutes`): anti-flapping delay
- Lux thresholds (summer/winter open/close)
- Heat protection (start/end hours, position, temp threshold)
- Privacy hours (winter/summer) and duration
- Night close position (`0` or `100`)
- Feature toggles (sun tracking, lux, heat, privacy, sunset)

## Entities

Each config entry creates sensors under the HA Blinds device, including:

- `sensor.<entry>_state`
- `sensor.<entry>_last_reason`
- `sensor.<entry>_target_position`
- `sensor.<entry>_last_decision`
- `sensor.<entry>_error_count`
- `sensor.<entry>_sun_at_window`

## Services

- `ha_blinds.pause`
  - Optional: `entry_id`, `minutes`
- `ha_blinds.resume`
  - Optional: `entry_id`
- `ha_blinds.evaluate_now`
  - Optional: `entry_id`

Example:

```yaml
service: ha_blinds.pause
data:
  entry_id: "your_entry_id"
  minutes: 30
```

## Troubleshooting

1. Enable debug logs:

```yaml
logger:
  logs:
    custom_components.ha_blinds: debug
```

2. Check integration sensors (`*_state`, `*_last_reason`, `*_error_count`).
3. Use `ha_blinds.evaluate_now` to trigger an immediate decision.
4. Verify configured entities exist and report valid values.

## Changelog

### v1.16.1

- Raised minimum Home Assistant version to `2026.5.0`
- Updated options flow for newer Home Assistant patterns
- Improved options persistence and reload stability
- Updated diagnostics and monitoring docs

## Support

- Issues: `https://github.com/Snapicek/ha-blinds/issues`
- Repository: `https://github.com/Snapicek/ha-blinds`

## Notes

- Local-only processing (no cloud required)
- Works offline after setup
- Designed for safe periodic evaluation and gradual movement
