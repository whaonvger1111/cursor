"""
重新计算稳态的脚本
应用所有修复后重新计算稳态
"""
import os
import shutil
from datetime import datetime

# 备份旧的稳态结果文件
steady_state_file = 'steady_state_results.pkl'
if os.path.exists(steady_state_file):
    backup_name = f'steady_state_results_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
    shutil.copy2(steady_state_file, backup_name)
    print(f"已备份旧稳态结果文件到: {backup_name}")

# 备份旧的日志文件
log_file = 'steady_state_iterations.log'
if os.path.exists(log_file):
    backup_log = f'steady_state_iterations_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    shutil.copy2(log_file, backup_log)
    print(f"已备份旧日志文件到: {backup_log}")

# 清空日志文件
with open(log_file, 'w', encoding='utf-8') as f:
    f.write('='*80 + '\n')
    f.write('稳态计算迭代日志（重新计算）\n')
    f.write('='*80 + '\n')
    f.write(f'开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    f.write('='*80 + '\n\n')
    f.write('应用修复：\n')
    f.write('  1. tol_bhat从5e-3降低到1e-4\n')
    f.write('  2. pol_bp_unc已保存到sol字典\n')
    f.write('='*80 + '\n\n')

print("\n" + "="*80)
print("准备重新计算稳态")
print("="*80)
print("\n应用的修复：")
print("  1. tol_bhat: 5e-3 -> 1e-4 (提高收敛精度)")
print("  2. pol_bp_unc: 已保存到sol字典")
print("\n开始运行main.py...")
print("="*80 + "\n")

# 运行main.py
import main


















