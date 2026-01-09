@echo off
echo ========================================
echo 运行MATLAB稳态计算
echo ========================================
echo.

REM 尝试找到MATLAB安装路径
set MATLAB_PATH=
if exist "C:\Program Files\MATLAB\R2025a\bin\matlab.exe" (
    set MATLAB_PATH=C:\Program Files\MATLAB\R2025a\bin\matlab.exe
) else if exist "C:\Program Files\MATLAB\R2024b\bin\matlab.exe" (
    set MATLAB_PATH=C:\Program Files\MATLAB\R2024b\bin\matlab.exe
) else if exist "C:\Program Files\MATLAB\R2024a\bin\matlab.exe" (
    set MATLAB_PATH=C:\Program Files\MATLAB\R2024a\bin\matlab.exe
) else if exist "C:\Program Files\MATLAB\R2023b\bin\matlab.exe" (
    set MATLAB_PATH=C:\Program Files\MATLAB\R2023b\bin\matlab.exe
) else if exist "C:\Program Files\MATLAB\R2019b\bin\matlab.exe" (
    set MATLAB_PATH=C:\Program Files\MATLAB\R2019b\bin\matlab.exe
)

if "%MATLAB_PATH%"=="" (
    echo 错误: 找不到MATLAB安装路径
    echo 请手动设置MATLAB_PATH环境变量或修改此脚本
    pause
    exit /b 1
)

echo 找到MATLAB: %MATLAB_PATH%
echo.

REM 切换到baseline目录
cd /d "C:\Users\Administrator\Desktop\Rescue-Policies-COVID-main\baseline"

REM 运行MATLAB
echo 正在运行MATLAB稳态计算...
echo 这可能需要一些时间，请耐心等待...
echo.

"%MATLAB_PATH%" -batch "cd('C:\Users\Administrator\Desktop\Rescue-Policies-COVID-main\baseline'); addpath(genpath('tools')); run('main.m');"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo MATLAB稳态计算完成！
    echo 结果已保存到: mat\ss.mat
    echo ========================================
) else (
    echo.
    echo ========================================
    echo MATLAB运行出错，错误代码: %ERRORLEVEL%
    echo ========================================
)

pause

