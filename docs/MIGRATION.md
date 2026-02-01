# Oracle Database Migration

This directory contains migration scripts to upgrade your MAPIT_VEHICLE_TRACKING table schema.

## When to Migrate

If you have been using this application before the addition of battery, hdop, odometer, and last_coord_ts fields, you need to run the migration script to add these columns to your existing table.

**Signs you need to migrate:**
- Error messages like "ORA-00904: invalid identifier" when running the tracker
- The tracker was working before but stopped after updating to a newer version
- Your table was created before 2024-02-01

## How to Migrate

### Prerequisites
- Working Oracle connection configured in `settings.py`
- Oracle wallet files in the `wallet/` directory
- Python environment with `oracledb` package installed

### Migration Steps

1. **Backup your data** (recommended):
   ```bash
   # Export current data to backup
   python mapit.py --export-geojson backup_$(date +%Y%m%d).geojson
   ```

2. **Run the migration**:
   ```bash
   python migrate_oracle_table.py
   ```

3. **Verify the migration**:
   The script will output success messages for each column added:
   ```
   [20:24:15 2026-02-01] INFO - Adding column battery...
   ✓ Column battery added successfully
   [20:24:15 2026-02-01] INFO - Adding column hdop...
   ✓ Column hdop added successfully
   ...
   [20:24:16 2026-02-01] INFO - Migration completed successfully!
   ```

4. **Resume normal operation**:
   ```bash
   python mapit.py --checker --sleep-time 5
   ```

## What the Migration Does

The migration adds the following columns to MAPIT_VEHICLE_TRACKING:

| Column | Type | Description |
|--------|------|-------------|
| battery | NUMBER(3) | Battery percentage (0-100) |
| hdop | NUMBER(6,2) | GPS accuracy indicator |
| odometer | NUMBER(10,2) | Odometer reading in km |
| last_coord_ts | NUMBER(13) | Timestamp of last coordinate update |

**Note**: The migration is safe to run multiple times. If a column already exists, it will be skipped.

## Troubleshooting

### "Table or view does not exist"
- Verify your Oracle connection settings in `settings.py`
- Make sure the wallet files are in the `wallet/` directory
- Check that you've run the application at least once to create the initial table

### "Insufficient privileges"
- Ensure your Oracle user has ALTER TABLE privileges
- Contact your database administrator if you're using a restricted account

### Other Errors
- Check the Oracle error code in the message
- Verify your Oracle Autonomous Database is running
- Ensure the connection timeout isn't too short (default: 10 seconds)

## Rolling Back

If you need to remove the new columns:

```sql
ALTER TABLE MAPIT_VEHICLE_TRACKING DROP COLUMN battery;
ALTER TABLE MAPIT_VEHICLE_TRACKING DROP COLUMN hdop;
ALTER TABLE MAPIT_VEHICLE_TRACKING DROP COLUMN odometer;
ALTER TABLE MAPIT_VEHICLE_TRACKING DROP COLUMN last_coord_ts;
```

**Warning**: This will delete all data in these columns.
