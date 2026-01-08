@echo off
chcp 65001 >nul
echo ========================================
echo 快速保存代码到Git
echo ========================================
echo.

python auto_save_to_git.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ 保存成功！
) else (
    echo.
    echo ✗ 保存失败，请检查错误信息
)

echo.
pause

