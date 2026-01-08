"""
监控稳态计算使用的参数值
检查是否使用了校准后的参数值
"""
import os
import sys
import numpy as np
from datetime import datetime

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from set_parameters import set_parameters
from fun_steady_state import fun_steady_state


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


def monitor_steady_state_calculation():
    """监控稳态计算使用的参数值"""
    
    print('='*80)
    print('监控稳态计算使用的参数值')
    print('='*80)
    print('')
    
    # 1. 读取参数文件中的值
    file_params = 'estim_params.txt'
    filepath = os.path.join('inputs', file_params)
    
    print(f'步骤1: 读取参数文件 "{filepath}"')
    print('-'*80)
    
    params_from_file = read_params_from_file(filepath)
    
    if not params_from_file:
        print(f'[ERROR] 错误：无法读取参数文件 "{filepath}"')
        return
    
    print('参数文件中的值:')
    for name, value in sorted(params_from_file.items()):
        print(f'  {name:12s} = {value:15.10f}')
    print('')
    
    # 2. 设置参数并记录实际使用的值
    print('步骤2: 调用 set_parameters() 设置参数')
    print('-'*80)
    
    par = {}
    par['do_calib'] = 0  # 稳态计算模式
    par['InpDir'] = os.path.join('inputs')
    par['TabDir'] = 'tables'
    par['do_table'] = 0
    par['do_tex'] = 0
    par['verbose'] = 1
    
    # 记录校准参数名称（这些是会被校准的参数）
    calib_names = [
        'mass', 'fixcost1', 'fixcost2', 'theta', 'psi',
        'k_alpha', 'x0', 'epsx', 'rhox', 'zeta'
    ]
    
    par, guess, bounds, calibNames, dispNames, description, ExoNames = \
        set_parameters(par, file_params)
    
    print('set_parameters() 设置后的参数值:')
    params_after_set = {}
    for name in calib_names:
        if name in par:
            value = par[name]
            params_after_set[name] = value
            print(f'  {name:12s} = {value:15.10f}')
    print('')
    
    # 3. 对比参数文件值和实际使用的值
    print('步骤3: 对比参数文件值和实际使用的值')
    print('-'*80)
    
    differences = []
    for name in calib_names:
        file_value = params_from_file.get(name, None)
        used_value = params_after_set.get(name, None)
        
        if file_value is None:
            print(f'  [WARN] {name:12s}: 参数文件中不存在')
            continue
        
        if used_value is None:
            print(f'  [WARN] {name:12s}: set_parameters() 后不存在')
            continue
        
        diff = abs(file_value - used_value)
        rel_diff = diff / abs(file_value) * 100 if file_value != 0 else 0
        
        if diff < 1e-10:
            status = '[OK] 一致'
        else:
            status = f'[X] 不一致 (差异: {diff:.2e}, {rel_diff:.6f}%)'
            differences.append((name, file_value, used_value, diff, rel_diff))
        
        print(f'  {status} {name:12s}: 文件={file_value:15.10f}, 使用={used_value:15.10f}')
    
    print('')
    
    # 4. 检查是否有差异
    if differences:
        print('[WARN] 发现参数值不一致！')
        print('-'*80)
        for name, file_val, used_val, diff, rel_diff in differences:
            print(f'  {name:12s}:')
            print(f'    文件值: {file_val:15.10f}')
            print(f'    使用值: {used_val:15.10f}')
            print(f'    差异:   {diff:.2e} ({rel_diff:.6f}%)')
        print('')
        print('[X] 结论: 稳态计算使用的参数值与文件中的值不一致！')
    else:
        print('[OK] 结论: 稳态计算使用的参数值与文件中的值完全一致！')
        print('')
        print('这意味着:')
        print('  - 如果参数文件包含校准后的值，稳态计算会使用校准后的值')
        print('  - 如果参数文件包含初始值，稳态计算会使用初始值')
    
    print('')
    print('='*80)
    
    # 5. 可选：运行稳态计算并记录使用的参数值
    print('')
    print('步骤4: 运行稳态计算（可选）')
    print('-'*80)
    print('是否运行稳态计算？这可能需要较长时间。')
    print('如果要运行，请取消下面的注释。')
    print('')
    
    # 取消注释以运行稳态计算
    # print('开始运行稳态计算...')
    # try:
    #     sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par_final = \
    #         fun_steady_state(par)
    #     
    #     if flag_ss >= 0:
    #         print('✅ 稳态计算成功完成')
    #         print('')
    #         print('稳态计算中使用的参数值（最终）:')
    #         for name in calib_names:
    #             if name in par_final:
    #                 value = par_final[name]
    #                 print(f'  {name:12s} = {value:15.10f}')
    #     else:
    #         print('❌ 稳态计算失败')
    # except Exception as e:
    #     print(f'❌ 稳态计算出错: {e}')
    #     import traceback
    #     traceback.print_exc()
    
    # 6. 保存监控结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'steady_state_params_monitor_{timestamp}.txt'
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('='*80 + '\n')
        f.write('稳态计算参数监控报告\n')
        f.write(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('='*80 + '\n\n')
        
        f.write('参数文件中的值:\n')
        for name, value in sorted(params_from_file.items()):
            f.write(f'  {name:12s} = {value:15.10f}\n')
        f.write('\n')
        
        f.write('set_parameters() 设置后的参数值:\n')
        for name, value in sorted(params_after_set.items()):
            f.write(f'  {name:12s} = {value:15.10f}\n')
        f.write('\n')
        
        if differences:
            f.write('[WARN] 发现参数值不一致:\n')
            for name, file_val, used_val, diff, rel_diff in differences:
                f.write(f'  {name:12s}: 文件={file_val:15.10f}, 使用={used_val:15.10f}, '
                       f'差异={diff:.2e} ({rel_diff:.6f}%)\n')
        else:
            f.write('[OK] 所有参数值一致\n')
    
    print(f'监控结果已保存到: {log_file}')
    print('')


if __name__ == '__main__':
    monitor_steady_state_calculation()

