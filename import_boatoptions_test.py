#!/usr/bin/env python3
"""
BoatOptions Import Script - TEST VERSION

Imports INVOICED boat orders from 12/14/2024 onwards to TEST database.
This is for validating the scraping logic before running on production.

Features:
- Only invoiced orders (has invoice number and qty_invoiced > 0)
- Only orders from 2024-12-14 onwards (CPQ go-live date)
- CPQ order detection (routes to BoatOptions26_test)
- Non-CPQ order detection (routes by serial number year)
- Complete field set including MCTDesc from prodcode_mst
- CFG table scraping for configured CPQ items

Usage:
    python3 import_boatoptions_test.py

Author: Claude Code
Date: 2026-02-03
"""

import sys
import csv
import tempfile
import os
from datetime import datetime, date
from typing import List, Dict, Tuple
import pymssql
import mysql.connector
from mysql.connector import Error as MySQLError

# ============================================================================
# DATABASE CONFIGURATIONS
# ============================================================================

# MSSQL (Source - CSI/ERP)
MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

# MySQL (Destination - TEST DATABASE)
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_boatoptions_test',  # TEST DATABASE
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# CPQ Go-Live Date
CPQ_GO_LIVE_DATE = date(2024, 12, 14)
