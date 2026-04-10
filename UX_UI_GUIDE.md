# HA Blinds - Complete UX/UI Guide

## 🎯 User Interface Overview

HA Blinds provides a **professional, intuitive, menu-driven configuration experience** with three main sections for easy management.

---

## 📱 Main Configuration Menu

When you open **Settings → Devices & Services → HA Blinds → Options**, you see:

```
┌─────────────────────────────────────┐
│    HA Blinds Options                │
├─────────────────────────────────────┤
│ Choose what to adjust:              │
│                                     │
│ 🎚️  Adjust Thresholds              │
│     (Lux, Heat, Privacy)            │
│                                     │
│ ⏱️  Adjust Timing                   │
│     (Tick, Debounce, Step)          │
│                                     │
│ 🔧 Reconfigure Entities            │
│     (Cover, Sensor)                 │
└─────────────────────────────────────┘
```

### Benefits of Menu-Driven UI

✅ **Organized**: Settings grouped by purpose  
✅ **Discoverable**: Easy to find what you need  
✅ **Simplified**: Not overwhelmed by all options at once  
✅ **Clear Purpose**: Each section clearly labeled with icon  
✅ **Mobile-Friendly**: Works well on phone UI  

---

## 🎚️ Thresholds Menu

### Path
Settings → Devices & Services → HA Blinds → Options → **Adjust Thresholds**

### What You Can Change

#### Lux Settings (Light-Based Control)
| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| **Lux Close Summer** | 35000 | 1k-120k | Close blinds when this bright (summer) |
| **Lux Open Summer** | 20000 | 500-120k | Open blinds when light drops below this (summer) |
| **Lux Close Winter** | 20000 | 500-120k | Close blinds when this bright (winter) |
| **Lux Open Winter** | 12000 | 500-120k | Open blinds when light drops below this (winter) |

**Pro Tip**: Close threshold should ALWAYS be higher than open threshold  
❌ Wrong: Close=20000, Open=35000  
✅ Correct: Close=35000, Open=20000

#### Heat Protection (Summer Only)
| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| **Heat Start Hour** | 10 | 0-23 | When to start closing for heat (10=10AM) |
| **Heat End Hour** | 17 | 0-23 | When to stop closing for heat (17=5PM) |
| **Heat Position %** | 20 | 0-100 | How closed to get (20%=mostly open) |
| **Temp Threshold** | 24°C | 10-40 | Temperature to trigger (24°C=75°F) |

**Example**: On hot summer day at 2PM with temp >24°C → blinds close to 20%

#### Privacy Hours (Automatic Closure)
| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| **Winter Privacy Hour** | 16 | 0-23 | Close for privacy in winter (4PM) |
| **Summer Privacy Hour** | 19 | 0-23 | Close for privacy in summer (7PM) |

**Behavior**: At configured hour, blinds automatically close to 100% (fully closed)

---

## ⏱️ Timing Menu

### Path
Settings → Devices & Services → HA Blinds → Options → **Adjust Timing**

### What You Can Change

| Parameter | Default | Range | Purpose | Impact |
|-----------|---------|-------|---------|--------|
| **Tick (minutes)** | 5 | 1-30 | Check every X minutes | Lower=more responsive, more CPU |
| **Max Step %** | 10 | 1-50 | Move max X% per check | Lower=smoother, slower |
| **Debounce (minutes)** | 5 | 1-30 | Wait X min before reacting to light | Higher=less flapping |
| **Manual Override (minutes)** | 45 | 5-240 | Pause X min after manual adjust | Longer=more time to adjust |

### Use Cases

**Blinds moving too much (flapping)?**
- Increase Debounce to 10-15 minutes

**Blinds not responding fast enough?**
- Decrease Tick to 3 minutes
- Increase Max Step to 20%

**Blinds moving too jerky?**
- Decrease Max Step to 5%

**Want quicker pause after manual adjustment?**
- Decrease Manual Override to 20 minutes

---

## 🔧 Entities Menu

### Path
Settings → Devices & Services → HA Blinds → Options → **Reconfigure Entities**

### What You Can Change

#### Entities
- **Blinds Cover** (Required): Select your blind/shutter entity
- **Lux Sensor** (Required): Select light level sensor
- **Temperature Sensor** (Optional): Select temp sensor for heat protection

#### Window Configuration
| Parameter | Range | Purpose |
|-----------|-------|---------|
| **Window Azimuth** | 0-359° | Direction window faces |
| **View Left** | 0-180° | How far left you can see |
| **View Right** | 0-180° | How far right you can see |

### How to Get Azimuth

1. Open compass app on phone
2. Stand AT your window
3. Face OUT the window (important!)
4. Read the direction shown
   - North = 0°
   - East = 90°
   - South = 180°
   - West = 270°

### Changing Entities

✅ **YES - You can reconfigure without deleting:**
- Simply go to Options → Entities menu
- Select new entities
- Click save
- Integration automatically reloads
- **No need to delete and re-add!**

---

## ✨ UI Features

### Real-Time Updates

All changes take effect **immediately** without restart:
- ⚡ Thresholds applied instantly
- ⚡ Timing adjusted next evaluation
- ⚡ Entities reloaded automatically

### Visual Feedback

When you see:
- ✅ Green checkmark: Saved successfully
- ⚠️ Yellow warning: Value may not be optimal
- ❌ Red error: Invalid value (won't save)

### Field Descriptions

Every field has helpful text explaining:
- What it does
- Recommended value
- Why it matters
- Examples

Example:
```
Lux Close Summer: 35000
📝 Lux threshold to close blinds in summer.
   Higher = close only in bright sun.
   Recommended: 35000
```

---

## 🎨 User Experience Principles

### 1. Progressive Disclosure
- Main menu shows 3 simple choices
- Not overwhelming all options at once
- Users can drill down to what they need

### 2. Sensible Defaults
- All parameters have recommended defaults
- Works out-of-the-box without tweaking
- Users can customize if needed

### 3. Helpful Guidance
- Descriptions for every field
- Recommended values shown
- Examples provided

### 4. Non-Destructive Changes
- No need to delete and recreate
- Options menu allows entity changes
- Changes can be undone by changing back

### 5. Clear Organization
- Thresholds grouped together (lux, heat, privacy)
- Timing grouped together (intervals, movement)
- Entities grouped together (cover, sensor, location)

### 6. Immediate Feedback
- Changes take effect immediately
- No restart required
- User sees results instantly

---

## 📊 Configuration Workflows

### Workflow 1: Initial Setup (5 minutes)

1. Install via HACS
2. Add Integration → HA Blinds
3. Select cover and lux sensor
4. Set window direction (use compass)
5. Done! Uses recommended defaults

### Workflow 2: Fine-Tune Thresholds (3 minutes)

1. Monitor automation for 1-2 days
2. Settings → Devices & Services → HA Blinds
3. Options → Adjust Thresholds
4. Tweak lux values
5. Watch for improvement

### Workflow 3: Fix Flapping (2 minutes)

1. Seeing blinds move up/down constantly
2. Options → Adjust Timing
3. Increase Debounce to 10-15
4. Apply - should stop immediately

### Workflow 4: Change Entities (1 minute)

1. Got new sensors?
2. Options → Reconfigure Entities
3. Select new entities
4. Save - integration reloads automatically
5. No need to delete entry!

---

## 🎯 Navigation Paths

### Access Configuration
```
Home Assistant UI
  ↓
Settings → Devices & Services
  ↓
HA Blinds Integration
  ↓
Your Entry (e.g., "HA Blinds - cover.bedroom")
  ↓
[⚙️ Options button]
  ↓
Choose menu option
```

### Access Status
```
Home Assistant UI
  ↓
Developer Tools → States
  ↓
Search: ha_blinds
  ↓
View status attributes
```

### Access Diagnostics
```
Home Assistant UI
  ↓
Settings → Devices & Services
  ↓
HA Blinds Integration
  ↓
Your Entry
  ↓
[⋯ Three dots menu]
  ↓
"Create Diagnostic"
```

---

## 🆘 Help & Feedback in UI

### Field Help
Every field shows:
- **Label**: What to change
- **Description**: Why it matters
- **Suggested Value**: Recommended
- **Range**: Min-max allowed

### Step Descriptions
Each menu shows:
- **Title**: What this section is for
- **Description**: What you can do here
- **Fields**: Organized logically

### Error Messages
If you enter wrong value:
- Clear message explaining issue
- Suggests correct range
- Won't let you save until fixed

---

## 📱 Mobile-Friendly Design

✅ Works perfectly on mobile:
- Touch-friendly buttons
- Large input fields
- Readable text
- No horizontal scrolling needed
- Menu format works better than long form

### Mobile Workflow
1. Open Home Assistant mobile app
2. Tap Settings
3. Tap Devices & Services
4. Tap HA Blinds
5. Tap your entry
6. Tap Options (gear icon)
7. Select menu item
8. Make changes
9. Save (appears immediately)

---

## 🎓 Best Practices

### When Setting Up

✅ **DO**
- Use compass app for azimuth
- Start with default thresholds
- Monitor for first few days
- Adjust gradually

❌ **DON'T**
- Guess window direction
- Change many settings at once
- Expect perfect results immediately
- Set debounce too high (>30)

### When Troubleshooting

✅ **DO**
- Check status entity first
- Read field descriptions
- Try one change at a time
- Create diagnostic report

❌ **DON'T**
- Delete and recreate (use Options instead)
- Make huge threshold changes
- Set conflicting values (lux_open > lux_close)
- Ignore warning messages

---

## 🔄 Reconfiguration Without Deletion

### Scenario: Change cover entity

**OLD WAY** (Don't do this):
1. Go to Devices & Services
2. Find HA Blinds entry
3. Click three dots
4. Delete integration
5. Re-add integration
6. Re-enter all settings
7. 😞 Lost all your custom values

**NEW WAY** (Use this):
1. Go to Devices & Services  
2. Find HA Blinds entry
3. Click Options
4. Select "Reconfigure Entities"
5. Choose new cover entity
6. Click Save
7. Integration reloads automatically
8. 😊 All your other settings preserved!

### What You Can Change Without Deletion

✅ Cover entity
✅ Lux sensor
✅ Temperature sensor
✅ Window azimuth
✅ View angles
✅ All thresholds
✅ All timing values
✅ Privacy hours

### What Persists

When you reconfigure:
- All your custom threshold values stay
- All your timing preferences stay  
- Only specified field changes
- No disruption to automation

---

## 📊 Settings Summary Card

### Quick Reference - What Changes What

| Menu | Changes | Reload? | Immediate? |
|------|---------|---------|-----------|
| Thresholds | Lux/Heat/Privacy | No | Yes ⚡ |
| Timing | Check freq/Movement | No | Next tick |
| Entities | Cover/Sensor | Yes | After reload |

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Integration appears in Settings
- [ ] Device shows in Devices & Services
- [ ] Status sensors appear in States
- [ ] Can open Options menu
- [ ] Can see all three menu items
- [ ] Can adjust Thresholds
- [ ] Can adjust Timing
- [ ] Can access Entities

---

## 🎉 UX/UI Summary

**HA Blinds provides:**

✅ Intuitive menu-driven UI  
✅ Organized settings by category  
✅ Helpful descriptions everywhere  
✅ Sensible defaults  
✅ Non-destructive entity reconfiguration  
✅ Immediate feedback & updates  
✅ Mobile-friendly design  
✅ Clear navigation paths  
✅ Professional presentation  

**Users can:**
- Set up in 5 minutes
- Adjust without restarting
- Change entities without re-adding
- Get instant feedback
- Find help easily
- Troubleshoot independently

---

**Status**: ✅ **PROFESSIONAL UX/UI IMPLEMENTED**

Date: April 10, 2026  
Version: 1.10.0+

