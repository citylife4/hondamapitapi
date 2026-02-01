#!/usr/bin/env python3
"""Migration script to add new columns to MAPIT_VEHICLE_TRACKING table.

This script adds battery, hdop, odometer, and last_coord_ts columns
to existing MAPIT_VEHICLE_TRACKING tables that were created before
these fields were added.

Usage:
    python migrate_oracle_table.py
"""

import oracledb
import logging
import os
from settings import oracle_user, oracle_password, oracle_dns

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S %d-%m-%Y'
)
logger = logging.getLogger()

def migrate_table():
    """Add new columns to existing MAPIT_VEHICLE_TRACKING table."""
    mypath = os.path.dirname(os.path.realpath(__file__))
    
    logger.info("Connecting to Oracle Database...")
    conn = oracledb.connect(
        config_dir=f"{mypath}/wallet",
        user=oracle_user,
        password=oracle_password,
        dsn=oracle_dns,
        wallet_location=f"{mypath}/wallet",
        wallet_password=oracle_password,
        tcp_connect_timeout=10
    )
    
    cursor = conn.cursor()
    
    # List of columns to add
    columns = [
        ("battery", "NUMBER(3)"),
        ("hdop", "NUMBER(6, 2)"),
        ("odometer", "NUMBER(10, 2)"),
        ("last_coord_ts", "NUMBER(13)")
    ]
    
    for column_name, column_type in columns:
        try:
            logger.info(f"Adding column {column_name}...")
            cursor.execute(
                f"ALTER TABLE MAPIT_VEHICLE_TRACKING ADD {column_name} {column_type}"
            )
            conn.commit()
            logger.info(f"✓ Column {column_name} added successfully")
        except oracledb.DatabaseError as e:
            error_code = e.args[0].code if hasattr(e.args[0], 'code') else None
            if error_code == 1430:  # Column already exists
                logger.info(f"✓ Column {column_name} already exists, skipping")
            else:
                logger.error(f"✗ Error adding column {column_name}: {e}")
                raise
    
    conn.close()
    logger.info("Migration completed successfully!")

if __name__ == "__main__":
    try:
        migrate_table()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        exit(1)
