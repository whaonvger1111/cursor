"""
自动保存代码到Git的脚本
使用方法：python auto_save_to_git.py [提交信息]
"""
import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd):
    """执行git命令"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def auto_save(commit_message=None):
    """自动保存到Git"""
    if commit_message is None:
        commit_message = f"Auto save: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print("="*60)
    print("自动保存到Git")
    print("="*60)
    
    # 1. 检查状态
    print("\n1. 检查更改...")
    success, stdout, stderr = run_command("git status --short")
    if not success:
        print(f"错误: {stderr}")
        return False
    
    if not stdout.strip():
        print("没有需要提交的更改")
        return True
    
    print("发现以下更改:")
    print(stdout)
    
    # 2. 添加所有更改
    print("\n2. 添加更改...")
    success, stdout, stderr = run_command("git add .")
    if not success:
        print(f"错误: {stderr}")
        return False
    print("✓ 文件已添加到暂存区")
    
    # 3. 提交
    print(f"\n3. 提交更改: {commit_message}")
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if not success:
        if "nothing to commit" in stderr.lower():
            print("没有需要提交的更改")
            return True
        print(f"错误: {stderr}")
        return False
    print("✓ 提交成功")
    print(stdout)
    
    # 4. 推送到远程
    print("\n4. 推送到远程仓库...")
    success, stdout, stderr = run_command("git push")
    if not success:
        print(f"错误: {stderr}")
        return False
    print("✓ 推送成功")
    print(stdout)
    
    print("\n" + "="*60)
    print("保存完成！")
    print("="*60)
    return True

if __name__ == "__main__":
    commit_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    auto_save(commit_msg)

