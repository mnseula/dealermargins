#!/usr/bin/env python3
"""
Check Model Length Data

Verifies that the Models table has length data populated.

Usage:
    python3 check_model_length.py [model_id]

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector
import sys

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    model_id = sys.argv[1] if len(sys.argv) > 1 else None

    print("="*80)
    print("MODEL LENGTH DATA CHECK")
    print("="*80)
    print()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if model_id:
            # Check specific model
            print(f"Checking model: {model_id}")
            print()

            cursor.execute("""
                SELECT
                    model_id,
                    model_name,
                    series_id,
                    length_feet,
                    loa_str,
                    beam_str,
                    floorplan_desc
                FROM Models
                WHERE model_id = %s
            """, (model_id,))

            row = cursor.fetchone()

            if not row:
                print(f"❌ Model {model_id} not found in Models table")
                return 1

            print(f"Model: {row['model_id']} - {row['model_name']}")
            print(f"Series: {row['series_id']}")
            print(f"Floorplan: {row['floorplan_desc']}")
            print()
            print("Length Data:")
            print(f"  length_feet: {row['length_feet']}")
            print(f"  loa_str: {row['loa_str']}")
            print(f"  beam_str: {row['beam_str']}")
            print()

            if row['loa_str']:
                print("✅ Length data is populated")
            else:
                print("❌ Length data is MISSING (NULL)")
                print()
                print("This model needs to be updated with length information.")

        else:
            # Check all models
            cursor.execute("""
                SELECT
                    model_id,
                    model_name,
                    series_id,
                    length_feet,
                    loa_str,
                    beam_str
                FROM Models
                ORDER BY series_id, length_feet
            """)

            rows = cursor.fetchall()

            print(f"Total models: {len(rows)}")
            print()

            missing_length = []
            has_length = []

            for row in rows:
                if row['loa_str']:
                    has_length.append(row)
                else:
                    missing_length.append(row)

            print(f"✅ Models with length data: {len(has_length)}")
            print(f"❌ Models missing length data: {len(missing_length)}")
            print()

            if missing_length:
                print("Models missing length data:")
                for row in missing_length:
                    print(f"  - {row['model_id']:12s} {row['model_name']}")
                print()

            if has_length:
                print("Sample models with length data:")
                for row in has_length[:5]:
                    print(f"  ✅ {row['model_id']:12s} {row['model_name']:40s} LOA: {row['loa_str']}")

        print("="*80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
