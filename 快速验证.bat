@echo off
chcp 65001 >nul
echo ============================================================
echo 快速验证 Fortran 配置
echo ============================================================
echo.

echo 1. 检查 gfortran...
where gfortran >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo    [成功] gfortran 可用
    gfortran --version | findstr "GNU Fortran"
) else (
    echo    [失败] gfortran 未找到
)

echo.
echo 2. 检查 Fortran 模块...
if exist "fortran\vfi_core.pyd" (
    echo    [成功] Fortran 模块已编译
) else (
    echo    [警告] Fortran 模块未编译
    echo    运行: python fortran\setup_fortran.py
)

echo.
echo 3. 测试 Python 导入...
python -c "import sys; sys.path.insert(0, 'fortran'); import vfi_core; print('   [成功] Fortran模块可导入')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo    [警告] Fortran模块导入失败
)

echo.
echo ============================================================
echo 验证完成！
echo ============================================================
echo.
pause

