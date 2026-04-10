# HA Blinds - Professional Blind Automation for Home Assistant

**Complete solution** for automatic blind control with **Home Assistant Integration** and **HAOS Add-on** support.

UI-configurable automation for tilt blinds controlled by sun position, window azimuth, lux levels, and seasonal rules.

## What this integration gives you

- ✅ **Config flow** in **Settings → Devices & Services** with entity selectors
- ✅ **Options flow** to tune thresholds without YAML edits  
- ✅ **Runtime control loop** (no giant automation YAML required)
- ✅ **Services** for pause/resume/evaluate-now
- ✅ **Device registry** for each blind automation
- ✅ **Status sensors** showing automation state and reason
- ✅ **Editable entities** to change settings from UI
- ✅ **Diagnostics** for troubleshooting
- ✅ **Icons & Logos** properly configured
- ✅ **HAOS Add-on ready** for official add-on store
- ✅ **HACS integration** for custom repository
- ✅ **Multi-instance support** - manage multiple blinds independently

## Features

### Smart Automation Logic

- **Sun tracking**: Adjusts blind position based on sun elevation
- **Lux-based control**: Responds to light intensity with configurable thresholds
- **Heat protection**: Closes blinds during peak heat hours if temperature exceeds threshold
- **Privacy mode**: Automatically closes blinds at configured evening hour
- **Seasonal adjustments**: Different thresholds for summer and winter
- **Debounce control**: Prevents flapping by debouncing lux changes
- **Manual override detection**: Respects manual blind adjustments
- **Pause/Resume**: Services to temporarily disable automation

### Customization

- Configure via UI without editing YAML
- 14+ tuning parameters for precise control
- Optional temperature sensor support
- Window azimuth and view angle configuration
- Tick-based evaluation (5-30 minutes recommended)
- Smooth movement with step limiting

## Installation

### Via HACS (Recommended)

1. Open HACS → **Custom repositories**
2. Add `https://github.com/Snapicek/ha-blinds`
3. Category: **Integration**
4. Click **Install**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Create Automation**
7. Select **HA Blinds** and choose your entities

### Manual Installation

Copy `custom_components/ha_blinds` folder to your Home Assistant config:

```bash
/config/custom_components/ha_blinds
```

Then restart Home Assistant and add the integration via UI.

## Configuration

### Step 1: Select Entities

1. **Cover Entity** (required): Your blind/shutter entity
2. **Lux Sensor** (required): A light sensor (lux values)
3. **Temperature Sensor** (optional): For heat protection mode

### Step 2: Set Window Orientation

Use a compass app while facing out the window to get accurate values:

- **Window Azimuth** (0-359°): Direction window faces (180=South, 270=West, 90=East)
- **View Left** (0-180°): Angle of view to the left (90 = clear view)
- **View Right** (0-180°): Angle of view to the right (90 = clear view)

### Step 3: Tune Parameters (Optional)

Access via **Settings → Devices & Services → HA Blinds → Options**:

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| Tick (min) | 5 | 1-30 | Check interval |
| Max Step (%) | 10 | 1-50 | Max change per tick |
| Debounce (min) | 5 | 1-30 | Lux change delay |
| Lux Close Summer | 35000 | 1k-120k | Close threshold (summer) |
| Lux Open Summer | 20000 | 500-120k | Open threshold (summer) |
| Lux Close Winter | 20000 | 500-120k | Close threshold (winter) |
| Lux Open Winter | 12000 | 500-120k | Open threshold (winter) |
| Heat Start Hour | 10 | 0-23 | Heat protection start |
| Heat End Hour | 17 | 0-23 | Heat protection end |
| Heat Position (%) | 20 | 0-100 | Blind position during heat |
| Temp Threshold (°C) | 24 | 10-40 | Activate heat protection |
| Winter Privacy Hour | 16 | 0-23 | Close for privacy (winter) |
| Summer Privacy Hour | 19 | 0-23 | Close for privacy (summer) |
| Manual Override (min) | 45 | 5-240 | Pause after manual change |

## Usage

### Via Services

Call services to control automation:

#### ha_blinds.pause
Temporarily disable automation for a period:

```yaml
service: ha_blinds.pause
data:
  entry_id: "abc123"  # Optional
  minutes: 30         # Optional (uses config default if omitted)
```

#### ha_blinds.resume
Immediately resume automation:

```yaml
service: ha_blinds.resume
data:
  entry_id: "abc123"  # Optional
```

#### ha_blinds.evaluate_now
Force immediate evaluation (ignores tick interval):

```yaml
service: ha_blinds.evaluate_now
data:
  entry_id: "abc123"  # Optional
```

### View Status

Each instance creates a status entity: `{DOMAIN}.{ENTRY_ID}_status`

Check in **Developer Tools → States** for:
- `last_reason`: Why blinds are in current state
- `last_target`: Target position from last evaluation
- `paused_until`: When pause mode ends
- `last_decision`: Last evaluation time
- `error_count`: Number of configuration errors

## Troubleshooting

### No Icon or Device Showing

**Problem**: Integration added but no icon/device appears.

**Solution**:
1. Ensure `cover` and `sensor` entities exist:
   - Go to **Developer Tools → States**
   - Search for `cover.` and `sensor.` 
   - Verify your entities are listed
2. Check logs for errors:
   - Go to **Settings → System → Logs**
   - Search for `ha_blinds`
   - Look for "Missing state" or entity errors

### Blinds Not Moving

**Problem**: Integration running but blinds don't move.

**Solutions**:
1. **Check tick interval**: Increase `tick_minutes` if rarely evaluated
2. **Verify sun position**: Use `ha_blinds.evaluate_now` service to force check
3. **Check lux thresholds**: Adjust lux values - might need higher/lower
4. **Verify manual override**: Check `manual_override_minutes` might be active
5. **Check pause status**: Look at status entity - might be paused
6. **Enable debug logging**:
   ```yaml
   logger:
     logs:
       custom_components.ha_blinds: debug
   ```

### Blinds Flapping

**Problem**: Blinds constantly moving up and down.

**Solution**: Increase `debounce_minutes` value (5-10 recommended).

### Entity Selection Issues

**Problem**: Can't select entities in config flow.

**Solution**:
1. Ensure entities have proper domain:
   - Covers: entity_id starts with `cover.`
   - Sensors: entity_id starts with `sensor.`
2. Restart Home Assistant if newly added

### Configuration Errors

**Problem**: Getting validation errors in config flow.

**Solution**:
1. **Azimuth errors**: Value must be 0-359
2. **Angle errors**: View angles must be 0-180
3. **Lux errors**: Values must be 500-120000
4. **Time errors**: Hours must be 0-23

## Diagnostics

For detailed troubleshooting:

1. Go to **Settings → Devices & Services**
2. Find "HA Blinds" integration
3. Click on your entry
4. Click "Create Diagnostic"
5. Download and review the diagnostic report

Contains:
- Entry configuration
- Controller status
- Current entity states
- Error counts

## Advanced: Using with Automations

You can use services in automations:

```yaml
automation:
  - alias: Pause blinds during meeting
    trigger:
      platform: state
      entity_id: input_boolean.in_meeting
      to: "on"
    action:
      service: ha_blinds.pause
      data:
        minutes: 60
        
  - alias: Resume after meeting
    trigger:
      platform: state
      entity_id: input_boolean.in_meeting
      to: "off"
    action:
      service: ha_blinds.resume
```

## Repository Structure

```
custom_components/ha_blinds/
├── __init__.py              # Integration setup
├── config_flow.py           # Configuration UI
├── const.py                 # Constants & defaults
├── coordinator.py           # Runtime controller
├── logic.py                 # Decision engine
├── diagnostics.py           # Diagnostics support
├── manifest.json            # Integration metadata
├── services.yaml            # Service definitions
└── strings.json             # UI translations
```

## Logic Overview

### Decision Rules (in order)

1. **Paused**: If automation is paused, don't move
2. **Night/Privacy**: Close blinds if sun below horizon or privacy hour
3. **High Lux + Direct Sun**: Close completely (protect from glare)
4. **Heat Protection**: Partially close during heat hours if temp high
5. **Low Lux + Direct Sun**: Open to let in light
6. **Sun Elevation Tracking**: Position based on sun angle
7. **Temperature Adjustment**: Fine-tune based on room temperature

### Seasonal Behavior

- **Winter** (Nov-Mar): Lower lux thresholds, higher privacy hour
- **Summer** (May-Oct): Higher lux thresholds, lower privacy hour, heat protection

## Support

- **Issues**: https://github.com/Snapicek/ha-blinds/issues
- **Docs**: https://github.com/Snapicek/ha-blinds
- **HACS**: https://hacs.xyz

## Notes

- Integration is fully local (no cloud)
- Works offline once configured
- No external API calls
- Existing `blind_automation.yaml` can be kept for reference/migration

## Changelog

### v1.10.0
- ✨ Added device registry support
- ✨ Added status entity with diagnostic info
- ✨ Added diagnostics support
- ✨ Enhanced error handling and logging
- ✨ Improved config flow descriptions
- 🐛 Fixed icon display
- 📝 Updated documentation
