# HA Blinds (HACS Custom Integration)

UI-configurable Home Assistant integration for tilt blinds controlled by sun position, window azimuth, lux, and seasonal rules.

## What this integration gives you

- Config flow in **Settings -> Devices & Services** with entity selectors
- Options flow to tune thresholds without YAML edits
- Runtime control loop (no giant automation YAML required)
- Services for pause/resume/evaluate-now
- HACS-ready repository layout

## Repository layout

```text
custom_components/ha_blinds/
  __init__.py
  config_flow.py
  const.py
  coordinator.py
  logic.py
  manifest.json
  services.yaml
  strings.json
  translations/en.json
hacs.json
```

## Install via HACS (custom repository)

1. HACS -> **Custom repositories**
2. Add `https://github.com/Snapicek/ha-blinds`
3. Category: **Integration**
4. Install **HA Blinds**
5. Restart Home Assistant
6. Add integration and choose entities in the UI

## Manual install

Copy `custom_components/ha_blinds` into your Home Assistant config folder.

```text
/config/custom_components/ha_blinds
```

Restart Home Assistant, then add **HA Blinds** from Integrations.

## Services

- `ha_blinds.pause`
- `ha_blinds.resume`
- `ha_blinds.evaluate_now`

## Local logic tests (outside Home Assistant)

```powershell
python tools/run_logic_tests.py
```

## Troubleshooting

If Home Assistant shows:

`Config flow could not be loaded (message: invalid handler specified)`

check these first:

1. Folder structure is exact (no nested folder):

```text
/config/custom_components/ha_blinds/manifest.json
/config/custom_components/ha_blinds/config_flow.py
```

2. Do **not** copy repo root as `/config/custom_components/ha_blinds`.
   Copy only the inner `custom_components/ha_blinds` folder.

3. Remove stale install before reinstall:

```bash
rm -rf /config/custom_components/ha_blinds
```

4. Reinstall from HACS, then fully restart Home Assistant.

5. In logs, search for `ha_blinds` and `config_flow` import errors.

## Notes

- This repo contains a full custom integration scaffold.
- Existing `blind_automation.yaml` can still be kept for reference/migration.
