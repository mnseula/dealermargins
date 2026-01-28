#!/usr/bin/env python3
"""
Load stored procedure with EOS fallback into database
"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def load_procedure():
    with open('stored_procedures_with_eos_fallback.sql', 'r') as f:
        sql_script = f.read()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print('Loading stored procedures with EOS fallback...\n')

    # Split by DELIMITER changes
    parts = sql_script.split('DELIMITER')

    for i, part in enumerate(parts):
        if i == 0:
            # Regular SQL statements before first DELIMITER
            statements = part.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--') and not stmt.startswith('/*'):
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        if 'USE' not in stmt and 'DROP' not in stmt:
                            print(f'Warning: {e}')
        elif '//' in part:
            # Procedure definitions (between DELIMITER // and DELIMITER ;)
            procedures = part.split('//')
            for proc in procedures:
                proc = proc.strip()
                if 'CREATE PROCEDURE' in proc:
                    proc_name = proc.split('CREATE PROCEDURE')[1].split('(')[0].strip()
                    try:
                        cursor.execute(proc)
                        print(f'✓ Created procedure: {proc_name}')
                    except Exception as e:
                        print(f'✗ Error creating {proc_name}: {e}')

    conn.commit()
    cursor.close()
    conn.close()

    print('\n✅ Stored procedures loaded successfully')

if __name__ == '__main__':
    load_procedure()
