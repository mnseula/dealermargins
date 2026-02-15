#!/usr/bin/env python3
"""
Test GET_CPQ_STANDARD_FEATURES stored procedure
Verifies if stored procedure exists and returns correct data for model 22MSB year 2026
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def test_stored_procedure():
    """Test GET_CPQ_STANDARD_FEATURES procedure"""

    print("=" * 100)
    print("TESTING GET_CPQ_STANDARD_FEATURES STORED PROCEDURE")
    print("=" * 100)
    print()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    try:
        # Test 1: Check if stored procedure exists
        print("Test 1: Checking if stored procedure exists...")
        cursor.execute("""
            SELECT ROUTINE_NAME, ROUTINE_TYPE, ROUTINE_DEFINITION
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = 'warrantyparts_test'
              AND ROUTINE_NAME = 'GET_CPQ_STANDARD_FEATURES'
        """)
        proc = cursor.fetchone()

        if proc:
            print(f"✅ Stored procedure EXISTS: {proc['ROUTINE_NAME']} ({proc['ROUTINE_TYPE']})")
            print()
        else:
            print("❌ STORED PROCEDURE DOES NOT EXIST!")
            print()
            print("Checking all stored procedures in database:")
            cursor.execute("""
                SELECT ROUTINE_NAME
                FROM information_schema.ROUTINES
                WHERE ROUTINE_SCHEMA = 'warrantyparts_test'
                ORDER BY ROUTINE_NAME
            """)
            procs = cursor.fetchall()
            for p in procs:
                print(f"  - {p['ROUTINE_NAME']}")
            print()
            return

        # Test 2: Call the stored procedure
        print("Test 2: Calling stored procedure with model_id='22MSB', year=2026...")
        cursor.callproc('GET_CPQ_STANDARD_FEATURES', ('22MSB', 2026))
        results = cursor.fetchall()

        print(f"✅ Query returned {len(results)} features")
        print()

        if len(results) > 0:
            print("Feature breakdown by area:")
            print("-" * 100)

            # Group by area
            by_area = {}
            for row in results:
                area = row['area']
                if area not in by_area:
                    by_area[area] = []
                by_area[area].append(row)

            for area in ['Interior Features', 'Exterior Features', 'Console Features', 'Warranty']:
                if area in by_area:
                    print(f"\n{area}: {len(by_area[area])} features")
                    print("-" * 100)
                    for feat in by_area[area][:5]:  # Show first 5
                        print(f"  • {feat['feature_code']}: {feat['description']}")
                    if len(by_area[area]) > 5:
                        print(f"  ... and {len(by_area[area]) - 5} more")
                else:
                    print(f"\n{area}: 0 features")

            print()
            print("=" * 100)
            print(f"TOTAL: {len(results)} features")
            print("=" * 100)
        else:
            print("❌ NO FEATURES RETURNED!")
            print()
            print("Let's check if the data exists in the tables...")

            # Check ModelStandardFeatures table
            cursor.execute("""
                SELECT model_id, year, COUNT(*) as count
                FROM warrantyparts_test.ModelStandardFeatures
                WHERE model_id = '22MSB' AND year = 2026
                GROUP BY model_id, year
            """)
            msf_count = cursor.fetchone()

            if msf_count:
                print(f"ModelStandardFeatures: {msf_count['count']} records for 22MSB / 2026")
            else:
                print("ModelStandardFeatures: NO records for 22MSB / 2026")

            # Check what model IDs exist
            cursor.execute("""
                SELECT DISTINCT model_id, year
                FROM warrantyparts_test.ModelStandardFeatures
                WHERE model_id LIKE '%22%MSB%' OR model_id LIKE '%M%'
                ORDER BY year DESC, model_id
                LIMIT 10
            """)
            similar_models = cursor.fetchall()

            if similar_models:
                print("\nSimilar model IDs in database:")
                for m in similar_models:
                    print(f"  - {m['model_id']} (year {m['year']})")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    test_stored_procedure()
