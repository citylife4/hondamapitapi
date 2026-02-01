# Quick Start Guide - Home Assistant Integration

## 🏍️ Track Your Motorcycle in 5 Minutes

This guide gets you up and running with motorcycle tracking in Home Assistant.

---

## Step 1: Install the Integration (2 minutes)

### Copy Files
```bash
# On your Home Assistant machine:
cd /config
mkdir -p custom_components
cd custom_components
# Copy the mapit_tracker folder here
```

Your structure should look like:
```
/config/
  └── custom_components/
      └── mapit_tracker/
          ├── __init__.py
          ├── config_flow.py
          ├── device_tracker.py
          ├── sensor.py
          ├── mapit_api.py
          └── ... (other files)
```

### Restart Home Assistant
```
Settings → System → Restart
```

---

## Step 2: Add the Integration (1 minute)

1. **Go to**: Settings → Devices & Services
2. **Click**: + Add Integration
3. **Search**: "Mapit Motorcycle Tracker"
4. **Click**: Mapit Motorcycle Tracker

---

## Step 3: Configure (1 minute)

You'll see a form asking for:

| Field | Example | Where to Find |
|-------|---------|---------------|
| Email Address | `your.email@example.com` | Your Mapit.me login |
| Password | `your_password` | Your Mapit.me password |
| Identity Pool ID | `eu-west-1:abc123...` | See below ⬇️ |
| User Pool ID | `eu-west-1_XYZ123` | See below ⬇️ |
| User Pool Client ID | `abc123xyz...` | See below ⬇️ |

### Finding AWS Configuration IDs

**Method 1: From your existing setup**
If you have `settings.py` from the standalone app:
```python
mappit_identityPoolId = "eu-west-1:..."      # Copy this
mappit_userPoolId = "eu-west-1_..."          # Copy this  
mappit_userPoolWebClientId = "..."           # Copy this
```

**Method 2: Browser inspection** (Advanced)
1. Open https://app.mapit.me in Chrome/Firefox
2. Press F12 for Developer Tools
3. Go to Network tab
4. Log in to Mapit.me
5. Filter by "cognito"
6. Look for these IDs in the request payloads

---

## Step 4: Verify Setup (30 seconds)

After submitting, you should see:
- ✅ "Success" message
- A new device called "Motorcycle"
- 5 new entities created

Check: Settings → Devices & Services → Mapit Motorcycle Tracker

---

## Step 5: Add to Dashboard (30 seconds)

### Option A: Simple Map View
1. Edit your dashboard
2. Add a new card
3. Choose "Map"
4. Select entity: `device_tracker.motorcycle`
5. Save

### Option B: Complete Status Panel

Add this to your dashboard (Edit Dashboard → Raw Configuration):

```yaml
type: vertical-stack
cards:
  # Map showing motorcycle location
  - type: map
    entities:
      - device_tracker.motorcycle
    hours_to_show: 2
    aspect_ratio: 16:9
    
  # Status information
  - type: entities
    title: Motorcycle Status
    entities:
      - entity: sensor.motorcycle_status
        name: Status
        icon: mdi:motorbike
      - entity: sensor.motorcycle_speed
        name: Speed
        icon: mdi:speedometer
      - entity: sensor.motorcycle_gps_accuracy
        name: GPS Accuracy
        icon: mdi:crosshairs-gps
      - entity: sensor.motorcycle_battery
        name: Battery
        icon: mdi:battery
```

---

## Bonus: Add Notifications

### Get notified when your motorcycle moves:

```yaml
automation:
  - alias: "Motorcycle Movement Alert"
    trigger:
      - platform: state
        entity_id: sensor.motorcycle_status
        to: "MOVING"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🏍️ Motorcycle Alert"
          message: "Your motorcycle has started moving!"
```

### Get alerted for speeding:

```yaml
automation:
  - alias: "Speed Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.motorcycle_speed
        above: 100  # km/h
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "⚠️ Speed Alert"
          message: "Motorcycle speed: {{ states('sensor.motorcycle_speed') }} km/h"
```

Add these to: Settings → Automations & Scenes → + Create Automation → Edit in YAML

---

## What You Get

After setup, you'll have these entities:

| Entity | What it Shows | Updates |
|--------|---------------|---------|
| `device_tracker.motorcycle` | GPS location on map | Every 30s |
| `sensor.motorcycle_speed` | Current speed (km/h) | Every 30s |
| `sensor.motorcycle_status` | MOVING or AT_REST | Every 30s |
| `sensor.motorcycle_gps_accuracy` | GPS accuracy (meters) | Every 30s |
| `sensor.motorcycle_battery` | Battery level (%) | Every 30s |

---

## Troubleshooting

### "Cannot connect" error
- ✅ Check your internet connection
- ✅ Verify email and password are correct
- ✅ Ensure Mapit.me service is online

### "Invalid auth" error
- ✅ Double-check the three AWS IDs
- ✅ Remove any extra spaces
- ✅ Make sure IDs match your Mapit.me account

### Entities not updating
- Wait 30 seconds for first update
- Check Settings → System → Logs for errors
- Try removing and re-adding the integration

### Still having issues?
1. Enable debug logging (see INSTALL_HOMEASSISTANT.md)
2. Check the logs for specific errors
3. Open an issue on GitHub with log excerpts

---

## Next Steps

Now that you're tracking your motorcycle:

1. **Create automations** for movement detection
2. **Set up geofencing** to know when it leaves home
3. **Track your rides** with location history
4. **Monitor battery** to prevent dead batteries
5. **Share location** with family members

---

## Questions?

- 📖 Detailed docs: `INSTALL_HOMEASSISTANT.md`
- 🏗️ Architecture: `INTEGRATION_SUMMARY.md`  
- 🐛 Issues: https://github.com/citylife4/hondamapitapi/issues

---

**Enjoy tracking your motorcycle! 🏍️✨**
