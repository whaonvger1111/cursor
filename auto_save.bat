@echo off
REM 自动保存代码到Git的批处理脚本
REM 使用方法：双击运行或在命令行输入 auto_save.bat [提交信息]

python auto_save_to_git.py %*

pause

