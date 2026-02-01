# AGENTS.md - Mapit Vehicle Tracking System

## Overview

This project interfaces with the **Mapit.me vehicle tracking API** to retrieve real-time motorcycle location data and store it in Oracle and MongoDB databases. It also provides visualization capabilities through a web-based map interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          mapit.py                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Cognito   │───▶│   Mapit     │───▶│   Storage Layer     │  │
│  │    Auth     │    │    API      │    │  (Oracle + MongoDB) │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│        │                  │                      │              │
│        ▼                  ▼                      ▼              │
│  ┌──────────┐      ┌──────────┐         ┌─────────────────┐    │
│  │ AWS SigV4│      │ Vehicle  │         │ Visualization   │    │
│  │ Signing  │      │ Summary  │         │ (Flask + Leaflet)│    │
│  └──────────┘      └──────────┘         └─────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  settings.py ─── Configuration (credentials)                    │
│  tokens.json ─── Cached authentication tokens                   │
│  wallet/     ─── Oracle wallet for TLS authentication           │
│  map_server.py ─ Flask web server for live map visualization    │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication Flow

1. **AWS Cognito USER_PASSWORD_AUTH** - Authenticate with Mapit.me credentials
2. **Get Identity** - Obtain Cognito Identity ID from Identity Pool
3. **Get Credentials** - Retrieve temporary AWS credentials (AccessKeyId, SecretKey, SessionToken)
4. **AWS SigV4 Signing** - Sign all API requests with temporary credentials
5. **Token Caching** - Store tokens in `tokens.json` for reuse (auto-refresh on expiry)

## Files

| File | Purpose |
|------|---------|
| `mapit.py` | Main script with Mapit class and CLI entry point |
| `map_server.py` | Flask web server for live map visualization |
| `settings.py` | Configuration file with credentials (DO NOT COMMIT) |
| `tokens.json` | Cached AWS Cognito tokens (auto-generated) |
| `wallet/` | Oracle Autonomous DB wallet files |
| `requirements.txt` | Python dependencies |

## Classes

### `Mapit`

Main class that handles all API interactions and data storage.

**Key Methods:**
- `__init__()` - Initialize with credentials, set up database connections
- `getSummary()` - Get current vehicle state (position, speed, status)
- `checkStatus()` - Extract lat/lng/speed/status from summary
- `storeOracle(data)` - Insert vehicle data into Oracle DB
- `storeMongo(data)` - Insert vehicle data into MongoDB
- `get_history_from_oracle(limit)` - Query historical location data
- `export_geojson(filepath)` - Export history as GeoJSON file
- `export_kml(filepath)` - Export history as KML file
- `close_connections()` - Clean up database connections

### Exceptions

- `RequestFailedException` - Raised when API request fails (non-200 response)
- `TokenExpiredException` - Raised when AWS credentials expire (403 response)

## CLI Arguments

```bash
python mapit.py [OPTIONS]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--debug` | flag | False | Enable debug logging |
| `--continuous` | flag | False | Poll every 5 seconds indefinitely |
| `--checker` | flag | False | Store only when position changes |
| `--sleep-time` | int | 1 | Seconds between polls in checker mode |
| `--serve-map` | flag | False | Start Flask web server with live map |
| `--map-port` | int | 5000 | Port for Flask server |
| `--refresh-rate` | int | 5 | Map auto-refresh interval (seconds) |
| `--export-geojson` | str | None | Export history to GeoJSON file |
| `--export-kml` | str | None | Export history to KML file |

## Operation Modes

### Default Mode
Single query - retrieves and displays current vehicle summary as JSON.

```bash
python mapit.py
```

### Continuous Mode
Polls the API every 5 seconds and logs position/speed/status.

```bash
python mapit.py --continuous
```

### Checker Mode
Only stores to Oracle when vehicle position changes.

```bash
python mapit.py --checker --sleep-time 5
```

### Map Server Mode
Starts a Flask web server with a Leaflet.js map showing current position.

```bash
python mapit.py --serve-map --map-port 8080 --refresh-rate 10
```

### Export Modes
Export historical data from Oracle to GeoJSON or KML format.

```bash
python mapit.py --export-geojson path.geojson
python mapit.py --export-kml path.kml
```

## Running as a Service (Continuous Operation)

To run the tracker continuously in the background:

### Option 1: Using systemd (recommended for production)
```bash
# Create log directory
sudo mkdir -p /var/log/mapit
sudo chown ubuntu:ubuntu /var/log/mapit

# Install the service
sudo cp mapit-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mapit-tracker
sudo systemctl start mapit-tracker

# Check status
sudo systemctl status mapit-tracker
journalctl -u mapit-tracker -f
```

### Option 2: Using nohup (simple background)
```bash
cd /home/ubuntu/dev/mapit
source venv/bin/activate
nohup python mapit.py --checker --sleep-time 5 > tracker.log 2>&1 &
```

### Option 3: Using screen/tmux
```bash
screen -S mapit
cd /home/ubuntu/dev/mapit && source venv/bin/activate
python mapit.py --checker --sleep-time 5
# Detach with Ctrl+A, D
```

## Database Schema

### Oracle Table: `MAPIT_VEHICLE_TRACKING`

This table is prefixed with `MAPIT_` to organize it within a shared database.

| Column | Type | Description |
|--------|------|-------------|
| id | NUMBER (auto) | Primary key |
| lng | NUMBER(10,7) | Longitude (decimal degrees) |
| lat | NUMBER(10,7) | Latitude (decimal degrees) |
| speed | NUMBER(6,2) | Speed in km/h |
| status | VARCHAR2(50) | MOVING or AT_REST |
| creation_ts | TIMESTAMP WITH TIME ZONE | Record creation time |

### MongoDB Collection: `mapit.speed`

```json
{
  "lng": "string",
  "lat": "string",
  "speed": "string",
  "status": "string",
  "datetime": "YYYY-MM-DD HH:MM:SS"
}
```

## Configuration (settings.py)

Required variables:
```python
mappit_username = "your_email@example.com"
mappit_password = "your_password"
mappit_identityPoolId = "eu-west-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
mappit_userPoolId = "eu-west-1_XXXXXXXXX"
mappit_userPoolWebClientId = "xxxxxxxxxxxxxxxxxxxxxxxxxx"
oracle_user = "ADMIN"
oracle_password = "your_oracle_password"
oracle_dns = "your_adb_tns_name"
mongo_url = "mongodb://localhost:27017/"  # Optional
```

## Security Notes

⚠️ **NEVER commit these files:**
- `settings.py` - Contains plaintext credentials
- `tokens.json` - Contains AWS access keys
- `wallet/` - Contains Oracle wallet with passwords

These are excluded via `.gitignore`.

## Dependencies

- `requests` - HTTP client for API calls
- `oracledb` - Oracle Autonomous DB driver
- `pymongo` - MongoDB driver
- `flask` - Web server for map visualization
- `simplekml` - KML file generation

## Common Issues

1. **Token Expired**: Delete `tokens.json` to force re-authentication
2. **Oracle Connection Failed**: Verify wallet files in `wallet/` directory
3. **MongoDB Connection Refused**: Ensure MongoDB is running on localhost:27017
