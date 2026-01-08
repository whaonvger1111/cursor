"""
检查稳态计算是否使用了校准后的参数值
对比校准前后的参数值
"""
import os
import sys
from datetime import datetime

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

def read_params_from_file(filepath):
    """从文件读取参数值"""
    params = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2:
                    name = parts[0]
                    try:
                        value = float(parts[1])
                        params[name] = value
                    except ValueError:
                        pass
    return params


def check_calibration_usage():
    """检查校准参数的使用情况"""
    
    print('='*80)
    print('检查稳态计算是否使用校准后的参数值')
    print('='*80)
    print('')
    
    file_params = 'estim_params.txt'
    filepath = os.path.join('inputs', file_params)
    
    # 读取当前参数文件中的值
    current_params = read_params_from_file(filepath)
    
    if not current_params:
        print(f'[ERROR] 无法读取参数文件: {filepath}')
        return
    
    print('当前参数文件中的值:')
    print('-'*80)
    for name, value in sorted(current_params.items()):
        print(f'  {name:12s} = {value:15.10f}')
    print('')
    
    # 检查是否有备份文件（校准前的值）
    backup_file = os.path.join('inputs', 'estim_params_backup.txt')
    if os.path.exists(backup_file):
        backup_params = read_params_from_file(backup_file)
        
        print('校准前的参数值（备份文件）:')
        print('-'*80)
        for name, value in sorted(backup_params.items()):
            print(f'  {name:12s} = {value:15.10f}')
        print('')
        
        # 对比校准前后的值
        print('对比校准前后的参数值:')
        print('-'*80)
        
        calib_names = ['mass', 'fixcost1', 'fixcost2', 'theta', 'psi',
                      'k_alpha', 'x0', 'epsx', 'rhox', 'zeta']
        
        has_changes = False
        for name in calib_names:
            if name in backup_params and name in current_params:
                old_val = backup_params[name]
                new_val = current_params[name]
                diff = abs(new_val - old_val)
                rel_diff = diff / abs(old_val) * 100 if old_val != 0 else 0
                
                if diff > 1e-10:
                    has_changes = True
                    print(f'  [CHANGED] {name:12s}:')
                    print(f'    校准前: {old_val:15.10f}')
                    print(f'    校准后: {new_val:15.10f}')
                    print(f'    变化:   {diff:.2e} ({rel_diff:.6f}%)')
                else:
                    print(f'  [SAME]    {name:12s}: {old_val:15.10f} (未变化)')
        
        print('')
        
        if has_changes:
            print('[OK] 结论: 参数文件包含校准后的值')
            print('      稳态计算会使用这些校准后的值')
        else:
            print('[INFO] 结论: 参数值未变化（可能校准未完成或参数未改变）')
            print('       稳态计算会使用初始参数值')
    else:
        print('[INFO] 未找到备份文件，无法对比校准前后的值')
        print('       当前参数值可能是初始值或校准后的值')
        print('')
        print('[INFO] 提示: 如果运行过校准，备份文件应该存在')
        print('       如果未运行过校准，当前值就是初始值')
    
    print('')
    print('='*80)
    
    # 保存检查结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'calibration_usage_check_{timestamp}.txt'
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('='*80 + '\n')
        f.write('校准参数使用情况检查报告\n')
        f.write(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('='*80 + '\n\n')
        
        f.write('当前参数文件中的值:\n')
        for name, value in sorted(current_params.items()):
            f.write(f'  {name:12s} = {value:15.10f}\n')
        f.write('\n')
        
        if os.path.exists(backup_file):
            backup_params = read_params_from_file(backup_file)
            f.write('校准前的参数值（备份文件）:\n')
            for name, value in sorted(backup_params.items()):
                f.write(f'  {name:12s} = {value:15.10f}\n')
            f.write('\n')
            
            f.write('对比结果:\n')
            calib_names = ['mass', 'fixcost1', 'fixcost2', 'theta', 'psi',
                          'k_alpha', 'x0', 'epsx', 'rhox', 'zeta']
            for name in calib_names:
                if name in backup_params and name in current_params:
                    old_val = backup_params[name]
                    new_val = current_params[name]
                    diff = abs(new_val - old_val)
                    rel_diff = diff / abs(old_val) * 100 if old_val != 0 else 0
                    if diff > 1e-10:
                        f.write(f'  {name:12s}: {old_val:15.10f} -> {new_val:15.10f} '
                               f'(变化: {diff:.2e}, {rel_diff:.6f}%)\n')
                    else:
                        f.write(f'  {name:12s}: {old_val:15.10f} (未变化)\n')
    
    print(f'检查结果已保存到: {log_file}')


if __name__ == '__main__':
    check_calibration_usage()













