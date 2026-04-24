# HA Blinds - Smart Blind Automation for Home Assistant

🪟 **Professional blind automation** for Home Assistant with **sun tracking**, **lux-responsive control**, **seasonal adjustments**, and **full UI configuration**—no YAML required.

Complete solution supporting **multi-instance setup**, **HACS**, **HAOS Add-on**, and **extensive customization** for every blind automation scenario.

---

## 🎯 What This Integration Does

HA Blinds automatically controls your blinds throughout the day by analyzing:

- ☀️ **Sun position** (azimuth & elevation)
- 💡 **Light levels** (lux sensor)
- 🌡️ **Room temperature** (optional)
- 🗓️ **Time of day** (privacy hours, seasonal rules)

The automation **adapts continuously**, closing blinds when the sun is in your eyes, opening them to let in light, protecting your room from heat and glare, and respecting your privacy at evening hours.

### Key Features

- ✅ **Config flow UI** - No YAML editing required
- ✅ **Options flow** - Fine-tune settings without restarting
- ✅ **Runtime decision engine** - Evaluates every 5-30 minutes
- ✅ **Smart services** - Pause, resume, force-evaluate
- ✅ **Seasonal modes** - Separate logic for summer & winter
- ✅ **Manual override detection** - Respects your manual adjustments
- ✅ **Multi-blind support** - Independent automation for each blind
- ✅ **Diagnostics** - Full troubleshooting data
- ✅ **Device registry** - Professional device integration
- ✅ **Status sensors** - Real-time automation state tracking
- ✅ **Feature toggles** - Enable/disable specific rules
- ✅ **Debounce control** - Prevent blind flapping
- ✅ **Smooth movement** - Gradual position changes
- ✅ **Zigbee support** - Configurable device delays

---

## 📦 Installation

### Via HACS (Recommended)

1. Open **HACS** → **Custom repositories**
2. Add repository: `https://github.com/Snapicek/ha-blinds`
3. Select category: **Integration**
4. Click **Install**
5. **Restart** Home Assistant
6. Go to **Settings → Devices & Services → Create Integration**
7. Search for **HA Blinds** and follow the setup wizard

### Via Manual Installation

1. Download or clone this repository
2. Copy `custom_components/ha_blinds` to your Home Assistant:
   ```
   /config/custom_components/ha_blinds
   ```
3. **Restart** Home Assistant
4. Add via **Settings → Devices & Services → Create Integration** → **HA Blinds**

---

## 🔧 Configuration

### Step 1: Select Your Entities

In the **Create Integration** flow:

- **Cover Entity** (required): Your blind/shutter (e.g., `cover.dining_room_blinds`)
- **Lux Sensor** (required): Light level sensor with illuminance device class (e.g., `sensor.living_room_brightness`)
- **Temperature Sensor** (optional): Room temperature for heat protection (e.g., `sensor.living_room_temp`)

### Step 2: Define Window Orientation

**Why this matters**: The engine needs to know when the sun actually hits your window.

**How to find these values** (use a compass app):

- **Window Azimuth** (0-359°): The direction your window faces
  - 0° = North
  - 90° = East (morning sun)
  - 180° = South (strong midday sun)
  - 270° = West (afternoon sun)

- **View Left** & **View Right** (0-180°): How wide your window's view is
  - 60° left + 60° right = 120° total view width (typical window)
  - Larger values = wider view (building corner windows)

**Example**: South-facing window with 60° on each side
- Azimuth: 180°
- Left: 60°
- Right: 60°
- Sun hits between 120° and 240° azimuth

### Step 3: Tune Advanced Settings (Optional)

Access via **Settings → Devices & Services → HA Blinds → [your entry] → Options flow**

#### Core Parameters

| Parameter | Default | Range | Impact |
|-----------|---------|-------|--------|
| **Tick (min)** | 5 | 1-30 | How often to re-evaluate (lower = more responsive, more network load) |
| **Max Step (%)** | 10 | 1-50 | Max position change per tick (lower = smoother, slower; higher = faster, more noticeable) |

#### Light Thresholds

| Parameter | Default | Impact |
|-----------|---------|--------|
| **Lux Close Summer** | 35,000 | Direct sun threshold when blinds should close |
| **Lux Open Summer** | 20,000 | When blinds can reopen during summer |
| **Lux Close Winter** | 20,000 | Direct sun threshold for winter |
| **Lux Open Winter** | 12,000 | When blinds can reopen during winter |
| **Debounce (min)** | 5 | Wait this long after lux change to act (prevents flickering) |

#### Heat Protection (Summer Only)

| Parameter | Default | Impact |
|-----------|---------|--------|
| **Heat Start Hour** | 10 | When to begin heat protection |
| **Heat End Hour** | 17 | When to stop heat protection |
| **Heat Position (%)** | 20 | Blind position during peak hours (partially closed) |
| **Temp Threshold (°C)** | 24 | Activate heat protection only if temp exceeds this |

**Example**: Between 10 AM and 5 PM, if temperature ≥ 24°C, close blinds to 20% when sun is at window

#### Privacy Mode

| Parameter | Default | Impact |
|-----------|---------|--------|
| **Winter Privacy Hour** | 16 | Close blinds at 4 PM in winter (Nov-Feb) |
| **Summer Privacy Hour** | 19 | Close blinds at 7 PM in summer (May-Sep) |
| **Privacy Duration (min)** | 480 (8h) | How long to keep them closed after privacy hour triggers |

**Example**: In winter (16:00), close blinds for 8 hours (until midnight), then resume normal operation

#### Night & Other

| Parameter | Default | Impact |
|-----------|---------|--------|
| **Night Close Position** | 0 | Position when sun below horizon (0=closed, 100=privacy) |
| **Manual Override (min)** | 45 | Pause automation after you manually move blinds |
| **Zigbee Delay (sec)** | 0 | Add delay for Zigbee devices to prevent flooding |

#### Feature Toggles

Enable/disable specific automation rules:

- **Sun Elevation Tracking**: Track blind position by sun height (default: ON)
- **High Lux Protection**: Close when direct sun + high lux (default: ON)
- **Low Lux Reopen**: Open when direct sun + low lux (default: ON)
- **Heat Protection**: Partial close during peak heat hours (default: ON)
- **Privacy Hour**: Close at evening hour (default: ON)
- **Sunset Closing**: Close at sunset (advanced, default: OFF)

---

## 📅 How It Works: Example Days

### ☀️ Summer Day (South-Facing Window)

**Configuration**: Window facing south (azimuth 180°), summer privacy 7 PM, heat protection 10 AM–5 PM

```
06:00 - Sunrise (~6°)
  ├─ Action: OPEN to 75% (sun low but direct)
  └─ Reason: sun_elevation_tracking + low_lux

08:00 - Morning (8° elevation, bright)
  ├─ Action: CLOSE to 50% (sun in eyes but getting higher)
  └─ Reason: sun_elevation_tracking

11:00 - Late morning (40° elevation, 30k lux, 22°C)
  ├─ Action: OPEN to 75% (sun high + not hot yet)
  └─ Reason: sun_elevation_tracking

12:30 - Peak noon (60° elevation, 45k lux, 26°C)
  ├─ Lux > 35k threshold + Sun at window + Temp > 24°C
  ├─ Action: CLOSE to 20% (heat protection mode)
  └─ Reason: peak_heat_hours

15:00 - Afternoon (still ~50° elevation, 40k lux, 27°C)
  ├─ Action: Stay at 20% (still in heat protection window)
  └─ Reason: peak_heat_hours

17:00 - Late afternoon (heat protection ends)
  ├─ Sun elevation 25° (lower angle now)
  ├─ Lux drops to 28k (below 35k threshold)
  ├─ Temp at 25°C
  ├─ Action: OPEN to 75% (resume sun tracking)
  └─ Reason: sun_elevation_tracking

19:00 - Evening (privacy hour)
  ├─ Action: CLOSE to 0% (privacy mode)
  └─ Reason: privacy_hour (stays closed for 8 hours by default)

23:00 - Night
  ├─ Sun elevation: -25° (below horizon)
  ├─ Action: Stay closed
  └─ Reason: night_close (or still in privacy duration)

06:00 - Next morning
  ├─ Privacy duration expired, sun rising
  ├─ Action: OPEN again
  └─ Reason: sun_elevation_tracking
```

### ❄️ Winter Day (South-Facing Window)

**Configuration**: Same window, winter privacy 4 PM, lower lux thresholds, no heat protection

```
07:00 - Sunrise (~7°)
  ├─ Action: OPEN to 75%
  └─ Reason: sun_elevation_tracking

09:00 - Morning (12° elevation)
  ├─ Action: CLOSE to 50% (sun still low and direct)
  └─ Reason: sun_elevation_tracking

12:00 - Midday (35° elevation, 25k lux)
  ├─ Lux > 20k (winter close threshold) ✓
  ├─ Action: CLOSE to 0%
  └─ Reason: direct_sun_high_lux

14:00 - Afternoon (25° elevation, 15k lux, sun moving)
  ├─ Lux drops below 20k (winter close threshold)
  ├─ Wait 5 minutes debounce...
  ├─ Action: OPEN to 75%
  └─ Reason: low_lux_reopen

16:00 - Privacy hour
  ├─ Action: CLOSE to 0%
  └─ Reason: privacy_hour (only 8 hours, will open at midnight)

17:00 - Sunset (~17° elevation)
  ├─ Action: Stay closed (in privacy mode)
  └─ Reason: privacy_hour

00:00 - Midnight (privacy duration expires)
  ├─ Sun still below horizon
  ├─ Action: Stay closed
  └─ Reason: night_close (sun is still below horizon)

06:30 - Next sunrise
  ├─ Action: OPEN to 75%
  └─ Reason: sun_elevation_tracking
```

---

## 🌞 Decision Logic Deep Dive

### Priority Order (1 = highest priority)

1. **Paused** → No movement
2. **Sunset Closing** (if enabled) → Close at exact sunset time
3. **Privacy Hour** → Close for configured duration
4. **Night** (sun elevation < 0°) → Stay closed
5. **High Lux + Direct Sun** → Close (protect from glare)
6. **Heat Protection** (summer, peak hours, temp high) → Partially close
7. **Low Lux + Direct Sun** → Open (let in light)
8. **Sun Elevation Tracking** → Position by sun height

### Sun Elevation Mapping

The engine automatically calculates blind position based on sun height above horizon:

```
Sun 0-10°   : 0% CLOSED (very direct, eye level)
Sun 10-25°  : 50% OPEN (still low but manageable)
Sun 25-40°  : 75% OPEN (good angle, not in eyes)
Sun 40°+    : 75% OPEN (high, safe to open fully)
```

This prevents the classic low-sun glare problem (like morning/evening sun in your eyes).

### Seasonal Switching

The engine automatically detects season:

- **Winter**: November–March (lower lux thresholds, earlier privacy)
- **Summer**: May–October (higher lux thresholds, later privacy, heat protection active)
- **Spring/Fall**: April, September (transitional, uses winter thresholds in early spring)

---

## 🎛️ Feature Combinations & Examples

### Example 1: Maximize Natural Light

**Use case**: Office/studio where you want maximum daytime light

**Settings**:
- Disable High Lux Protection (turn OFF)
- High lux threshold: 50,000 (raise it high)
- Low lux threshold: 8,000 (lower it)
- Heat Protection: OFF

**Result**: Blinds only close for privacy/night, otherwise track sun position to maximize light

---

### Example 2: Heat Protection Focused

**Use case**: West-facing window with afternoon sun overheating room

**Settings**:
- Azimuth: 270° (west)
- Heat Start: 14 (2 PM)
- Heat End: 19 (7 PM)
- Heat Position: 15% (mostly closed)
- Temp Threshold: 22°C (trigger earlier)
- Enable Heat Protection: ON
- Privacy Hour: 20:00 (8 PM, after heat ends)

**Result**: From 2 PM–7 PM, if temp > 22°C, close blinds to 15%. At 8 PM, enforce privacy. Better AC efficiency!

---

### Example 3: Glare-Free Workspace

**Use case**: Office with direct south sun creating screen glare

**Settings**:
- High Lux Close: 30,000 (aggressive)
- High Lux Open: 15,000 (resistant to reopening)
- Debounce: 10 min (longer delay, prevents flickering)
- Enable High Lux Protection: ON
- Enable Low Lux Reopen: ON (but hard to trigger due to higher thresholds)

**Result**: Blinds close aggressively when sun is bright/direct, stay closed longer

---

### Example 4: Privacy-First Home

**Use case**: Ground floor with street view, privacy is top priority

**Settings**:
- Winter Privacy: 17:00 (5 PM, earlier)
- Summer Privacy: 18:00 (6 PM)
- Privacy Duration: 600 min (10 hours, until late night)
- Night Close Position: 100% (privacy mode = full privacy)
- Manual Override: 240 min (don't reopen if manually adjusted)
- Debounce: 10 min (stable, don't flap)

**Result**: At privacy hour, close to 100% (full privacy position). Stay set for 10 hours. Respect manual adjustments for 4 hours.

---

### Example 5: Seasonal Transition Smart

**Use case**: Adapting UI without manual intervention

**Settings**:
- Winter Privacy: 16:00
- Summer Privacy: 20:00
- Enable Seasonal Switching: (automatic, based on month)
- Different lux thresholds (winter lower, summer higher)

**Result**: On November 1st, privacy hour automatically shifts from 20:00 to 16:00. On May 1st, shifts back to 20:00.

---

## 🚀 Usage & Control

### Services

#### Pause Automation

Temporarily disable all automation:

```yaml
service: ha_blinds.pause
data:
  entry_id: "abc123xyz"    # Optional: specific blind
  minutes: 30              # Optional: duration (uses config default if omitted)
```

**Use cases**:
- During video calls (don't want blinds moving)
- When manually adjusting blinds
- During events with windows
- Quick override for a specific time

#### Resume Automation

Immediately resume control:

```yaml
service: ha_blinds.resume
data:
  entry_id: "abc123xyz"    # Optional: specific blind
```

#### Force Evaluation

Re-evaluate right now (ignores normal tick interval):

```yaml
service: ha_blinds.evaluate_now
data:
  entry_id: "abc123xyz"    # Optional: specific blind
```

**Use cases**:
- After changing settings in options flow
- Testing automation response
- Quick reaction to sudden weather change

### Automation Examples

#### Pause During Meeting

```yaml
automation:
  - id: pause_blinds_meeting
    alias: Pause blinds during meeting
    trigger:
      platform: state
      entity_id: input_boolean.video_call_active
      to: "on"
    action:
      service: ha_blinds.pause
      data:
        entry_id: "dining_room_blinds"
        minutes: 60

  - id: resume_blinds_meeting
    alias: Resume blinds after meeting
    trigger:
      platform: state
      entity_id: input_boolean.video_call_active
      to: "off"
    action:
      service: ha_blinds.resume
      data:
        entry_id: "dining_room_blinds"
```

#### Pause During Movie Time

```yaml
automation:
  - id: pause_blinds_movie
    alias: Pause blinds for movie (sunset+2h)
    trigger:
      platform: sun
      event: sunset
      offset: "+02:00"
    action:
      service: ha_blinds.pause
      data:
        minutes: 120  # Pause for 2 hours
```

#### Alert When Manual Override

```yaml
automation:
  - id: notify_manual_override
    alias: Notify when blinds manually adjusted
    trigger:
      platform: template
      value_template: "{{ state_attr('ha_blinds.my_entry_status', 'last_reason') == 'manual_override' }}"
    action:
      service: notify.mobile_app_phone
      data:
        message: "Blinds were manually adjusted"
```

### Monitoring Status

**Status Entity**: `ha_blinds.{ENTRY_ID}_status`

Check these attributes in **Developer Tools → States**:

```
State: "active" or "paused"

Attributes:
  - last_reason: Why blinds are in current state
  - last_target: Target position (%
  - last_decision: ISO timestamp of last evaluation
  - paused_until: ISO timestamp when pause expires
  - cover_entity: Which blind this controls
  - error_count: Configuration errors (0 is good!)
  - sun_at_window: Is sun currently at this window?
```

**Examples**:
```
last_reason: "peak_heat_hours" → Heat protection active
last_reason: "privacy_hour" → Privacy mode active
last_reason: "direct_sun_high_lux" → High lux protection active
last_reason: "night_close" → Sun is below horizon
last_reason: "paused" → Automation paused by service
```

---

## 🔍 Troubleshooting

### Blinds Won't Open/Close

**Check 1: Verify entities exist**
```
Settings → System → Developer Tools → States
Search for: cover.* and sensor.*
```
If not listed, you need to create these entities first.

**Check 2: Enable debug logging**
```yaml
logger:
  logs:
    custom_components.ha_blinds: debug
```
Then check **Settings → System → Logs** for detailed decision logs.

**Check 3: Check status entity**
```
Developer Tools → States → ha_blinds.{entry_id}_status
```
- If `error_count` is high → Config error
- If `last_reason: "paused"` → Automation is paused
- If `sun_at_window: false` → Sun not hitting window (check azimuth!)

**Check 4: Force evaluation**
```yaml
service: ha_blinds.evaluate_now
```
If blinds don't respond, issue is in Home Assistant or the cover entity itself.

---

### Blinds Moving Too Much (Flapping)

**Cause**: Lux sensor flickering, short debounce time

**Solution**: Increase debounce in options:
- Current: 5 min → Try: 10 min
- If still flapping: 15 min

Or increase `max_step_per_tick` to limit speed (makes movement smoother anyway).

---

### Blinds Not Responding to Lux Changes

**Check 1**: Lux thresholds might be wrong
- Is lux sensor reporting values? Check **Developer Tools → States**
- Are thresholds realistic? (35,000 lux = full direct sun, 5,000 = office lighting)

**Check 2**: Lux protection is disabled
```
Settings → HA Blinds → Options
Enable High Lux Protection: ON (should be checked)
Enable Low Lux Reopen: ON
```

**Check 3**: Sun not at window during testing
- Check `sun_at_window` attribute in status entity
- Calculate if sun is actually in your window's azimuth range at that time

---

### Blinds Respond to Sun But Not Temperature

**Check 1**: Temperature sensor configured
```
Settings → HA Blinds → [Your Entry] → Reconfigure
Select a temperature sensor if you want heat protection
```

**Check 2**: Temperature sensor value is valid
```
Developer Tools → States
Search for your temp sensor, check value is a number (not "unknown")
```

**Check 3**: Heat protection is enabled and in time window
```
Settings → HA Blinds → Options
- Enable Heat Protection: checked
- Heat Start Hour: should be before current time
- Heat End Hour: should be after current time
- Current temp > Temp Threshold
```

**Check 4**: Season is summer (May–October)
Heat protection only works in summer months.

---

### Wrong Time Zone (Privacy Hour at Wrong Time)

**Check**: Home Assistant timezone
```
Settings → System → General
Check your timezone is correct
```

The engine uses Home Assistant's configured timezone for all time calculations.

---

### Configuration Validation Errors

When adding or editing, you get an error. Check these:

| Error | Fix |
|-------|-----|
| Azimuth out of range | Must be 0-359° (try 180 for south) |
| View angles wrong | Must be 0-180° each (typical: 60 & 60) |
| Lux values wrong | Must be 1,000–120,000 lux |
| Time off | Hours must be 0-23 (17 = 5 PM) |
| Missing cover/sensor | Entity must exist in Home Assistant first |

---

## 📊 Diagnostics

For complex issues, create a diagnostic report:

1. **Settings → Devices & Services**
2. Find "HA Blinds" integration
3. Click your entry
4. Click menu (⋯) → **Create Diagnostic**
5. Opens JSON file with full config, status, and entity states

**What's in the report**:
- All configuration values
- Current controller state
- Real-time entity values
- Error counts & messages

Share with support or review yourself to spot issues.

---

## 🔧 Advanced Configuration

### Zigbee Support

If using Zigbee blinds that lag with rapid commands:

```
Settings → HA Blinds → Options
Zigbee Delay (seconds): 1-2
```

Adds delay between position commands to prevent overwhelming the Zigbee network.

---

### Sunset-Based Closing

Close blinds at exact sunset time (instead of privacy hour):

```
Settings → HA Blinds → Options
Enable Sunset Closing: ON
Sunset Offset (minutes): 0 (or adjust +/- to shift time)
Night Close Position: 0 or 100 (your preference)
```

---

### Multiple Blinds Setup

Set up independent automation for each blind:

1. **Settings → Devices & Services → Create Integration → HA Blinds**
2. Select first blind
3. Configure as needed
4. Repeat for each blind

Each blind gets its own **entry_id** for services and independent evaluation.

---

## 📁 Repository Structure

```
custom_components/ha_blinds/
├── __init__.py              # Integration setup & services
├── config_flow.py           # Configuration UI wizard
├── const.py                 # Constants & defaults
├── coordinator.py           # Runtime controller (main loop)
├── logic.py                 # Decision engine (pure logic, testable)
├── sensor.py                # Status entity
├── button.py                # Service buttons in UI
├── switch.py                # Feature toggle switches
├── number.py                # Parameter number entities
├── diagnostics.py           # Diagnostic data export
├── manifest.json            # Integration metadata
├── services.yaml            # Service definitions
├── strings.json             # UI text translations
└── brand/                   # Icons
    └── icon.png
```

---

## 🤝 Integration Theory

### How Decisions Are Made

Every `tick_minutes` (default 5), the engine evaluates:

```
1. Get current state
   - Blind position from cover entity
   - Sun position (azimuth, elevation) from sun.sun
   - Light level from lux sensor
   - Room temp from temp sensor

2. Apply decision rules (see priority order above)
   - Check if paused → return "paused"
   - Check if privacy hour → return "privacy_hour"
   - Check if sun below horizon → return "night_close"
   - [... other rules ...]

3. Calculate target position
   - If moving is needed (target != current, allowing 1% hysteresis)
   - Limit speed: don't move more than max_step_per_tick
   - Send cover.set_cover_position service

4. Update status entity with reason & time
```

### Manual Override Behavior

When you manually move blinds:

1. Home Assistant reports new position
2. Engine detects large mismatch from expected position
3. Sets `paused_until` to now + manual_override_minutes
4. During pause: automation stops checking, blinds won't move
5. After pause expires: automation resumes normal operation

---

## 📝 Changelog

### v1.16.0
- ✨ Added feature toggles (can disable specific rules)
- ✨ Added sunset closing mode (advanced)
- ✨ Added Zigbee device delay support
- ✨ Enhanced sun elevation tracking (better algorithms)
- ✨ Improved Privacy hour with duration tracking
- 🐛 Fixed temperature-based heat protection edge cases
- 📝 Comprehensive documentation update

### v1.10.0
- ✨ Added device registry support
- ✨ Added status entity with diagnostic info
- ✨ Added diagnostics support
- ✨ Enhanced error handling and logging
- 🐛 Fixed icon display

### v1.0.0
- 🎉 Initial release
- Core sun tracking & lux-based control
- Heat protection & privacy modes
- Seasonal adjustments
- Manual override detection

---

## 🆘 Support & Issues

- **Bug Reports**: https://github.com/Snapicek/ha-blinds/issues
- **Feature Requests**: https://github.com/Snapicek/ha-blinds/issues
- **Documentation**: https://github.com/Snapicek/ha-blinds
- **HACS Integration**: https://hacs.xyz

---

## 📋 Notes

- ✓ **Fully local** - No cloud calls, all processing in Home Assistant
- ✓ **Offline capable** - Works without internet after initial setup
- ✓ **No external dependencies** - Uses only Home Assistant core
- ✓ **Respects timezone** - Uses Home Assistant timezone settings
- ✓ **Thread-safe** - Safe to use with multiple blinds
- ✓ **Low resource usage** - Minimal processing every tick
