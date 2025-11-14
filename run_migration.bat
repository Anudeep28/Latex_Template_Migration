@echo off
REM LaTeX Migration Script - Granular Mode
REM This batch file runs the migration with the granular configuration

echo ================================================
echo LaTeX Template Migration - Granular Mode
echo ================================================
echo.

REM Activate virtual environment
call myenv\Scripts\activate.bat

REM Run the migration script
python latex_migration.py -c migration_config_granular.json -o example_old_for_granular.tex -n example_new_with_structure.tex -out Anudeep_test_level_2.tex -v

echo.
echo ================================================
echo Migration completed!
echo ================================================
echo.
echo Output file: Anudeep_test_level_2.tex
echo.

pause
