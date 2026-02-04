#!/usr/bin/env python3
"""
Check if invoiced CPQ orders have serial numbers in MSSQL
"""
import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

def main():
    print("="*80)
    print("CHECKING SERIAL NUMBERS IN MSSQL FOR CPQ ORDERS")
    print("="*80)

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)

        # Check the specific orders we imported
        query = """
        SELECT
            coi.co_num,
            coi.co_line,
            coi.item,
            coi.description,
            coi.Uf_BENN_BoatSerialNumber,
            coi.Uf_BENN_BoatModel,
            coi.Uf_BENN_BoatWebOrderNumber,
            coi.config_id,
            coi.qty_invoiced,
            iim.inv_num,
            ser.ser_num
        FROM [CSISTG].[dbo].[coitem_mst] coi
        LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
            ON coi.co_num = iim.co_num
            AND coi.co_line = iim.co_line
            AND coi.co_release = iim.co_release
            AND coi.site_ref = iim.site_ref
        LEFT JOIN [CSISTG].[dbo].[serial_mst] ser
            ON coi.co_num = ser.ref_num
            AND coi.co_line = ser.ref_line
            AND coi.co_release = ser.ref_release
            AND coi.item = ser.item
            AND coi.site_ref = ser.site_ref
            AND ser.ref_type = 'O'
        WHERE coi.co_num IN ('SO00936047', 'SO00936067')
            AND coi.site_ref = 'BENN'
        ORDER BY coi.co_num, coi.co_line
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"\nFound {len(rows)} rows in MSSQL\n")

        if len(rows) == 0:
            print("❌ No rows found for these orders!")
            return

        # Show all rows with serial info
        print(f"{'Order':<15} {'Line':<5} {'Item':<20} {'BoatSerial (Uf_)':<20} {'ser_num':<20} {'Invoice':<15} {'ConfigID':<20}")
        print("-"*150)

        for row in rows:
            order = row.get('co_num') or ''
            line = str(row.get('co_line') or '')
            item = (row.get('item') or '')[:20]
            boat_serial = (row.get('Uf_BENN_BoatSerialNumber') or '[EMPTY]')[:20]
            ser_num = (row.get('ser_num') or '[EMPTY]')[:20]
            invoice = (row.get('inv_num') or '[NONE]')[:15]
            config_id = (row.get('config_id') or '[NONE]')[:20]

            print(f"{order:<15} {line:<5} {item:<20} {boat_serial:<20} {ser_num:<20} {invoice:<15} {config_id:<20}")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)

        orders = {}
        for row in rows:
            order = row.get('co_num')
            if order not in orders:
                orders[order] = {
                    'lines': 0,
                    'with_boat_serial': 0,
                    'with_ser_num': 0,
                    'invoiced': 0,
                    'with_config': 0
                }

            orders[order]['lines'] += 1

            if row.get('Uf_BENN_BoatSerialNumber'):
                orders[order]['with_boat_serial'] += 1

            if row.get('ser_num'):
                orders[order]['with_ser_num'] += 1

            if row.get('inv_num'):
                orders[order]['invoiced'] += 1

            if row.get('config_id'):
                orders[order]['with_config'] += 1

        for order, stats in orders.items():
            print(f"\n{order}:")
            print(f"  Total lines: {stats['lines']}")
            print(f"  With Uf_BENN_BoatSerialNumber: {stats['with_boat_serial']}")
            print(f"  With ser_num (serial_mst): {stats['with_ser_num']}")
            print(f"  Invoiced: {stats['invoiced']}")
            print(f"  With ConfigID: {stats['with_config']}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
