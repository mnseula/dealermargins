@echo off
REM Daily Boat Import Pipeline
REM Imports today's invoiced line items into BoatOptions and SerialNumberMaster

pushd \\ELK1ITSQVP001\Qlikview\Python_Dealer_Portal
python import_daily_boats.py
popd
