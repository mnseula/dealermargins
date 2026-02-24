@echo off
REM Daily Boat Import Pipeline
REM Step 1: Load CPQ data (models, pricing, performance, features, dealer margins) from Infor APIs
REM Step 2: Import today's invoiced line items into BoatOptions and SerialNumberMaster

pushd \\ELK1ITSQVP001\Qlikview\Python_Dealer_Portal
python load_cpq_data.py
python import_daily_boats.py
popd
