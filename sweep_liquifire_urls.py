#!/usr/bin/env python3
"""
sweep_liquifire_urls.py

Nightly sweep for CPQ boats with missing or low-quality Liquifire image URLs.
Designed to be triggered by JAMS as a scheduled nightly job.

Targets:
  - LiquifireImageUrl = '' / NULL  — never populated or timed out
  - LiquifireMethod   = 'stock-bare' — no colors applied; retry in case
                                        CPQ config is now available

Usage:
    python3 sweep_liquifire_urls.py                        # full sweep (all missing)
    python3 sweep_liquifire_urls.py --today                # only boats imported today (JAMS nightly)
    python3 sweep_liquifire_urls.py --today --no-verify    # skip Liquifire render test (use when Liquifire unreachable)
    python3 sweep_liquifire_urls.py --dry-run              # print what would be processed, no writes
"""

import sys
import mysql.connector
import build_liquifire_url as blu

DRY_RUN   = '--dry-run'   in sys.argv
TODAY     = '--today'     in sys.argv
NO_VERIFY = '--no-verify' in sys.argv


def get_sweep_serials(cur):
    date_filter = "AND DATE(snm.createdate) = CURDATE()" if TODAY else ""
    cur.execute(f"""
        SELECT DISTINCT snm.Boat_SerialNo
        FROM SerialNumberMaster snm
        JOIN warrantyparts.BoatOptions26 bo ON bo.BoatSerialNo = snm.Boat_SerialNo
        WHERE bo.BoatModelNo IS NOT NULL
          AND bo.BoatModelNo NOT IN ('', 'Base Boat')
          AND (
            snm.LiquifireImageUrl IS NULL
            OR snm.LiquifireImageUrl = ''
            OR snm.LiquifireMethod   = 'stock-bare'
          )
          {date_filter}
        ORDER BY snm.Boat_SerialNo
    """)
    return [r[0] for r in cur.fetchall()]


def main():
    scope = 'today' if TODAY else 'all missing'
    print(f'=== Liquifire URL Sweep ({scope}) ===\n')
    if NO_VERIFY:
        print('  [--no-verify] skipping Liquifire render test — storing built URL directly\n')

    token = blu.get_trn_token()
    matrices = blu.load_matrices(token)

    prod_conn = mysql.connector.connect(
        database='warrantyparts',
        client_flags=[mysql.connector.constants.ClientFlag.FOUND_ROWS],
        **blu.DB
    )
    test_conn = mysql.connector.connect(
        database='warrantyparts_test',
        client_flags=[mysql.connector.constants.ClientFlag.FOUND_ROWS],
        **blu.DB
    )

    if not DRY_RUN:
        blu.ensure_snm_method_column(prod_conn)
        blu.ensure_snm_method_column(test_conn)

    prod_cur = prod_conn.cursor()
    serials = get_sweep_serials(prod_cur)
    print(f'Found {len(serials)} boat(s) needing URL sweep\n')

    if not serials:
        print('Nothing to do.')
        prod_conn.close()
        test_conn.close()
        return

    if DRY_RUN:
        print('[--dry-run] no writes will be made\n')

    results = {'ok': 0, 'failed': 0, 'skipped': 0}

    for serial in serials:
        config, model, series = blu.get_boat_config(prod_cur, serial)

        if not model:
            print(f'  {serial}: SKIP — no model in BoatOptions26 or BoatOptions25')
            results['skipped'] += 1
            continue

        from_snm = False
        if not config:
            config, from_snm = blu.get_snm_config(prod_cur, serial, matrices)
            if from_snm:
                print(f'  {serial}: built config from SNM colors ({len(config)} keys)')

        _, was_fixed = blu.normalize_asset(model)
        if was_fixed:
            normalized_asset, _ = blu.normalize_asset(model)
            print(f'  {serial}: asset normalized {model} → {normalized_asset}')

        if NO_VERIFY:
            url = blu.build_url(serial, config, model, series, matrices)
            size, method = 0, 'no-verify'
            if not url:
                print(f'  {serial} ({model}): SKIP — could not build URL')
                results['skipped'] += 1
                continue
        else:
            url, size, method = blu.build_and_test_url(
                serial, config, model, series, matrices, from_snm=from_snm
            )

        if not url:
            print(f'  {serial} ({model}): FAIL — URL did not render')
            results['failed'] += 1
            continue

        if DRY_RUN:
            print(f'  {serial} ({model}): OK [{method}] ({size:,} bytes) [dry-run]')
        else:
            n_prod = blu.store_url(prod_conn, serial, url, method)
            n_test = blu.store_url(test_conn, serial, url, method)
            print(f'  {serial} ({model}): OK [{method}] ({size:,} bytes) — stored prod={n_prod} test={n_test}')

        results['ok'] += 1

    prod_conn.close()
    test_conn.close()
    print(f'\nSweep complete. ok={results["ok"]} failed={results["failed"]} skipped={results["skipped"]}')


if __name__ == '__main__':
    main()
