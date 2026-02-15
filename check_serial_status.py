#!/usr/bin/env python3
"""Check if boat exists in both SerialNumberMaster and Status tables"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_serial_status():
    """Check boat in SerialNumberMaster and SerialNumberRegistrationStatus"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        test_serial = 'ETWS0837A626'

        print("\n" + "="*80)
        print(f"CHECKING {test_serial} IN SERIALNUMBERMASTER")
        print("="*80 + "\n")

        cursor.execute("""
            SELECT *
            FROM SerialNumberMaster
            WHERE Boat_SerialNo = %s
        """, (test_serial,))

        snm_result = cursor.fetchone()

        if snm_result:
            print(f"✅ FOUND in SerialNumberMaster:")
            for key, value in snm_result.items():
                if value is not None:
                    print(f"  {key}: {value}")
            print()
        else:
            print(f"❌ NOT FOUND in SerialNumberMaster\n")

        print("="*80)
        print(f"CHECKING {test_serial} IN SERIALNUMBERREGISTRATIONSTATUS")
        print("="*80 + "\n")

        cursor.execute("""
            SELECT *
            FROM SerialNumberRegistrationStatus
            WHERE Boat_SerialNo = %s
        """, (test_serial,))

        status_result = cursor.fetchone()

        if status_result:
            print(f"✅ FOUND in SerialNumberRegistrationStatus:")
            for key, value in status_result.items():
                if value is not None:
                    print(f"  {key}: {value}")
            print()
        else:
            print(f"❌ NOT FOUND in SerialNumberRegistrationStatus")
            print("\n⚠️  This might prevent the boat from being accessible!\n")

        # Check a working boat for comparison (the 20SSR that works)
        print("="*80)
        print("COMPARISON: CHECKING WORKING 20SSR BOAT (ETWS2842L425)")
        print("="*80 + "\n")

        working_serial = 'ETWS2842L425'

        cursor.execute("""
            SELECT Boat_SerialNo, DealerNumber, DealerName
            FROM SerialNumberMaster
            WHERE Boat_SerialNo = %s
        """, (working_serial,))

        working_snm = cursor.fetchone()

        cursor.execute("""
            SELECT Boat_SerialNo, Status
            FROM SerialNumberRegistrationStatus
            WHERE Boat_SerialNo = %s
        """, (working_serial,))

        working_status = cursor.fetchone()

        if working_snm:
            print(f"SerialNumberMaster: ✅ {working_serial}")
            print(f"  Dealer: {working_snm['DealerName']} (#{working_snm['DealerNumber']})")
        else:
            print(f"SerialNumberMaster: ❌ {working_serial} not found")

        if working_status:
            print(f"SerialNumberRegistrationStatus: ✅ {working_serial}")
            print(f"  Status: {working_status.get('Status', 'N/A')}")
        else:
            print(f"SerialNumberRegistrationStatus: ❌ {working_serial} not found")

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80 + "\n")

        print(f"23SSR (ETWS0837A626):")
        print(f"  SerialNumberMaster: {'✅' if snm_result else '❌'}")
        print(f"  SerialNumberRegistrationStatus: {'✅' if status_result else '❌'}")
        if snm_result:
            print(f"  Dealer #: {snm_result['DealerNumber']}")

        print(f"\n20SSR Working (ETWS2842L425):")
        print(f"  SerialNumberMaster: {'✅' if working_snm else '❌'}")
        print(f"  SerialNumberRegistrationStatus: {'✅' if working_status else '❌'}")
        if working_snm:
            print(f"  Dealer #: {working_snm['DealerNumber']}")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_serial_status()
