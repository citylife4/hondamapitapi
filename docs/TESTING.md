# Testing Guide for Speed Normalization and Enhanced Data Storage

## Overview
This guide helps you test the speed normalization fix and enhanced data storage features.

## Test Scenarios

### Scenario 1: Speed Normalization When AT_REST

**Expected Behavior**: When the vehicle status is "AT_REST", the speed should be normalized to 0, even if the API reports a residual value like 5 km/h.

**Test Steps**:
1. Ensure your motorcycle is parked and not moving
2. Run the tracker in continuous mode:
   ```bash
   python mapit.py --continuous
   ```
3. Observe the output - it should show:
   ```
   Summary retrieved at Xs: <lng>, <lat>, AT_REST at 0 km/h
   ```
   NOT: `AT_REST at 5 km/h`

**Home Assistant Test**:
1. Check the speed sensor in Home Assistant
2. When motorcycle is parked (status: AT_REST), speed should be 0 km/h

### Scenario 2: Speed When Moving

**Expected Behavior**: When the vehicle is moving (status: "MOVING"), the actual speed from the API should be displayed.

**Test Steps**:
1. Start moving with your motorcycle
2. Check that the status changes to "MOVING"
3. Verify that speed shows the actual km/h value (not 0)

### Scenario 3: Enhanced Data Storage (New Installation)

**Expected Behavior**: For new installations, the table should be created with all 9 columns.

**Test Steps**:
1. On a system without existing MAPIT_VEHICLE_TRACKING table
2. Run the tracker:
   ```bash
   python mapit.py --checker --sleep-time 5
   ```
3. Move the motorcycle to trigger a storage event
4. Check Oracle database - the table should have these columns:
   - id, lng, lat, speed, status, battery, hdop, odometer, last_coord_ts, creation_ts

### Scenario 4: Database Migration (Existing Installation)

**Expected Behavior**: Existing databases should be upgraded to include the new columns.

**Test Steps**:
1. Backup your data:
   ```bash
   python mapit.py --export-geojson backup_before_migration.geojson
   ```

2. Run the migration:
   ```bash
   python migrate_oracle_table.py
   ```

3. Expected output:
   ```
   [HH:MM:SS DD-MM-YYYY] INFO - Connecting to Oracle Database...
   [HH:MM:SS DD-MM-YYYY] INFO - Adding column battery...
   ✓ Column battery added successfully
   [HH:MM:SS DD-MM-YYYY] INFO - Adding column hdop...
   ✓ Column hdop added successfully
   [HH:MM:SS DD-MM-YYYY] INFO - Adding column odometer...
   ✓ Column odometer added successfully
   [HH:MM:SS DD-MM-YYYY] INFO - Adding column last_coord_ts...
   ✓ Column last_coord_ts added successfully
   [HH:MM:SS DD-MM-YYYY] INFO - Migration completed successfully!
   ```

4. Run the tracker again and verify no errors occur

5. Compare exported data:
   ```bash
   python mapit.py --export-geojson backup_after_migration.geojson
   ```

### Scenario 5: Additional Fields in Storage

**Expected Behavior**: New records should include battery, hdop, odometer, and last_coord_ts values.

**Test Steps**:
1. Run checker mode:
   ```bash
   python mapit.py --checker --sleep-time 5
   ```

2. Move the motorcycle to different locations

3. Query the database to verify new fields are populated:
   ```sql
   SELECT id, lng, lat, speed, status, battery, hdop, odometer, last_coord_ts, creation_ts
   FROM MAPIT_VEHICLE_TRACKING
   ORDER BY creation_ts DESC
   FETCH FIRST 10 ROWS ONLY;
   ```

4. Verify that:
   - battery shows percentage (0-100)
   - hdop shows GPS accuracy value
   - odometer shows distance (if available)
   - last_coord_ts shows epoch timestamp

### Scenario 6: Export with New Fields

**Expected Behavior**: Exported GeoJSON and KML files should include the new fields in properties.

**Test Steps**:
1. Export to GeoJSON:
   ```bash
   python mapit.py --export-geojson test_export.geojson
   ```

2. Check the file content - each feature should have properties with the new fields

3. Export to KML:
   ```bash
   python mapit.py --export-kml test_export.kml
   ```

4. Verify the KML file includes battery and other metadata

## Validation Checklist

- [ ] Speed shows 0 when status is AT_REST (not 5 or other residual values)
- [ ] Speed shows actual value when status is MOVING
- [ ] New Oracle table includes all 9 columns
- [ ] Migration script successfully adds columns to existing tables
- [ ] Migration script is idempotent (safe to run multiple times)
- [ ] Battery, hdop, odometer, and last_coord_ts are populated in new records
- [ ] Historical data export includes new fields
- [ ] Home Assistant integration shows correct speed (0 when AT_REST)
- [ ] All Python tests pass
- [ ] No CodeQL security alerts

## Troubleshooting

### "ORA-00904: invalid identifier" Error
- This means the migration hasn't been run yet
- Run `python migrate_oracle_table.py` to add the new columns

### Speed Still Shows Non-Zero When AT_REST
- Verify you're using the latest version of the code
- Check that both mapit.py and mapit_api.py have been updated
- Restart Home Assistant if using the HA integration

### Migration Script Fails
- Check Oracle connection settings in settings.py
- Verify wallet files are in the wallet/ directory
- Ensure your Oracle user has ALTER TABLE privileges

## Expected API Response Fields

Based on the problem statement, the API provides these fields in the state object:

```json
{
  "id": "d-2WWA9eav89wjyBYyx27w2w073KJ",
  "deviceId": "d-2WWA9eav89wjyBYyx27w2w073KJ",
  "model": "M305",
  "location": "0101000020E6100000326601C92A4F21C09B3E96992D964440",
  "version": "03.29.00_931",
  "battery": 30,
  "voltage": 0,
  "odometer": null,
  "vin": null,
  "lastTs": 1769969394000,
  "lastCoordTs": 1769522445000,
  "status": "AT_REST",
  "speed": 5,
  "hdop": 12,
  "lng": -8.6546233,
  "lat": 41.1732666,
  ...
}
```

Our normalization logic converts speed from 5 to 0 when status is "AT_REST".
