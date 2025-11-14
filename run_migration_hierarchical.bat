@echo off
REM LaTeX Migration Script - Hierarchical Mode
REM This batch file runs the migration with the hierarchical configuration

echo ================================================
echo LaTeX Template Migration - Hierarchical Mode
echo ================================================
echo.

REM Activate virtual environment
call myenv\Scripts\activate.bat

REM Run the migration script
python latex_migration.py -c migration_config_hierarchical.json -o example_old_hierarchical.tex -n example_new_hierarchical.tex -out output_hierarchical.tex -v

echo.
echo ================================================
echo Migration completed!
echo ================================================
echo.
echo Output file: output_hierarchical.tex
echo.

pause
