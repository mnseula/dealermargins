@echo off
REM CPQ Order to Quote Number Export - JAMS Job
REM Uses Infor CPQ API to fetch order/quote number mapping

REM Set paths
set SCRIPT_DIR=%~dp0
set OUTPUT_DIR=%SCRIPT_DIR%output
set PYTHON_SCRIPT=%SCRIPT_DIR%export_cpq_quote_numbers.py
set OUTPUT_CSV=%OUTPUT_DIR%\cpq_order_quote_numbers.csv

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Run Python script
pushd "%SCRIPT_DIR%"
@REM E:\Python\python.exe -u "%PYTHON_SCRIPT%" --since 2025-12-15 --output "%OUTPUT_CSV%"
E:\Python\python.exe -u "%PYTHON_SCRIPT%" --today --output "%OUTPUT_CSV%"
set EXIT_CODE=%ERRORLEVEL%
popd

REM Exit with Python script's exit code
exit /b %EXIT_CODE%
