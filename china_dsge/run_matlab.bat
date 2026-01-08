@echo off
chcp 65001 >nul
echo ========================================
echo   China 42-Sector DSGE Model
echo   Government Spending Multiplier Study
echo ========================================
echo.
echo Starting MATLAB...
echo.

cd /d "%~dp0"

matlab -nosplash -nodesktop -r "cd('%~dp0'); Run_China_DSGE; pause"

pause





















