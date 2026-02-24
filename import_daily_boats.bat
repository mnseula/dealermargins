@echo off
REM Daily Boat Import Pipeline
REM Loads CPQ data from Infor APIs, then imports today's invoiced boats from ERP

pushd \\ELK1ITSQVP001\Qlikview\Python_Dealer_Portal
python import_daily_boats.py
popd
