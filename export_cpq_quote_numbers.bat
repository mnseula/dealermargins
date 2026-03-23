@echo off
REM CPQ Order to Quote Number Export - JAMS Job
REM Daily mode (JAMS):   export_cpq_quote_numbers.bat
REM Backfill mode:       export_cpq_quote_numbers.bat --since 2025-12-15
REM Custom output:       export_cpq_quote_numbers.bat --since 2025-12-15 --output C:\path\file.csv

set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%export_cpq_quote_numbers.py
set OUTPUT_CSV=\\elk1itsqvp001\qlik\Common\SourceData-CSV\CPQOrderQuoteNumbers\cpq_order_quote_numbers.csv

pushd "%SCRIPT_DIR%"

REM If arguments were passed (e.g. --since), use them. Otherwise default to --today --append.
if "%~1"=="" (
    E:\Python\python.exe "%PYTHON_SCRIPT%" --today --append --output "%OUTPUT_CSV%"
) else (
    E:\Python\python.exe "%PYTHON_SCRIPT%" %* --output "%OUTPUT_CSV%"
)

set EXIT_CODE=%ERRORLEVEL%
popd

exit /b %EXIT_CODE%
