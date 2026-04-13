#!/usr/bin/env python3
"""
Backfill Liquifire images for boats currently showing the generic stock image.

Usage:
    python3 backfill_stock_images.py [--dry-run]
"""

import sys
import mysql.connector
from datetime import datetime

import load_cpq_data
from import_daily_boats import (
    MYSQL_CONFIG, MYSQL_DB, log,
    fetch_cpq_image_urls
)

STOCK_IMAGE_URL = 'https://s3.amazonaws.com/eosstatic/images/0/5880c9a7a9d29ae43164c78f/Generic-01.jpg'


def backfill_stock_images(dry_run: bool = False) -> int:
    """
    Find boats with stock image and SO order numbers, fetch real URLs from CPQ.
    """
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT Boat_SerialNo, ERP_OrderNo, BoatItemNo
        FROM {MYSQL_DB}.SerialNumberMaster
        WHERE LiquifireImageUrl = %s
          AND WebOrderNo LIKE '%%SO%%'
        ORDER BY ERP_OrderNo DESC
    """, (STOCK_IMAGE_URL,))
    
    rows = cursor.fetchall()
    cursor.close()
    
    if not rows:
        log("No boats found with stock image and SO order numbers")
        conn.close()
        return 0
    
    log(f"Found {len(rows)} boat(s) with stock image to backfill")
    
    so_numbers = [r[1] for r in rows]
    itemno_map = {r[1]: r[2] for r in rows}
    serial_map = {r[1]: r[0] for r in rows}
    
    log(f"Fetching CPQ image URLs for {len(so_numbers)} order(s)...")
    image_urls = fetch_cpq_image_urls(so_numbers, itemno_map=itemno_map)
    
    if not image_urls:
        log("No image URLs returned from CPQ")
        conn.close()
        return 0
    
    cursor = conn.cursor()
    updated = 0
    
    for so, url in image_urls.items():
        if url == STOCK_IMAGE_URL:
            log(f"  Skipping {so}: CPQ returned stock image (no better URL found)")
            continue
            
        serial = serial_map.get(so)
        if not serial:
            continue
            
        if dry_run:
            log(f"  [DRY RUN] Would update {serial} ({so}) → {url[:80]}...")
            updated += 1
        else:
            cursor.execute(
                f"UPDATE {MYSQL_DB}.SerialNumberMaster SET LiquifireImageUrl = %s WHERE Boat_SerialNo = %s",
                (url, serial)
            )
            if cursor.rowcount:
                log(f"  Updated {serial} ({so}) → {url[:80]}...")
                updated += 1
    
    if not dry_run:
        conn.commit()
    
    cursor.close()
    conn.close()
    
    log(f"Backfill complete: {updated} boat(s) updated", "SUCCESS")
    return updated


def main():
    dry_run = '--dry-run' in sys.argv
    
    print("=" * 70)
    print("BACKFILL STOCK IMAGES")
    print("=" * 70)
    print(f"Database: {MYSQL_DB}")
    print(f"Dry run:  {dry_run}")
    print(f"Started:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    updated = backfill_stock_images(dry_run)
    
    print()
    print("=" * 70)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Updated:   {updated} boat(s)")
    print("=" * 70)


if __name__ == '__main__':
    main()
