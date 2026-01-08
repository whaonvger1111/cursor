"""
对比MATLAB和Python的参数值与稳态结果
检查参数合理性
"""
import os
import sys
import numpy as np

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from set_parameters import set_parameters
from fun_steady_state import fun_steady_state


def read_matlab_params():
    """读取MATLAB的参数文件"""
    matlab_file = r'C:\Users\Administrator\Desktop\Rescue-Policies-COVID-main\baseline\inputs\estim_params.txt'
    params = {}
    
    if os.path.exists(matlab_file):
        with open(matlab_file, 'r') as f:
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


def read_python_params():
    """读取Python的参数文件"""
    python_file = os.path.join('inputs', 'estim_params.txt')
    params = {}
    
    if os.path.exists(python_file):
        with open(python_file, 'r') as f:
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


def read_matlab_steady_state():
    """尝试读取MATLAB的稳态结果（从表格文件）"""
    matlab_table = r'C:\Users\Administrator\Desktop\Rescue-Policies-COVID-main\baseline\tables\steady_state.tex'
    results = {}
    
    if os.path.exists(matlab_table):
        with open(matlab_table, 'r', encoding='utf-8') as f:
            content = f.read()
            # 尝试解析LaTeX表格
            # 这里需要根据实际格式解析
            pass
    
    return results


def compare_parameters():
    """对比MATLAB和Python的参数值"""
    print('='*80)
    print('MATLAB vs Python 参数值对比')
    print('='*80)
    print('')
    
    matlab_params = read_matlab_params()
    python_params = read_python_params()
    
    if not matlab_params:
        print('[ERROR] 无法读取MATLAB参数文件')
        return
    
    if not python_params:
        print('[ERROR] 无法读取Python参数文件')
        return
    
    calib_names = ['mass', 'fixcost1', 'fixcost2', 'theta', 'psi',
                   'k_alpha', 'x0', 'epsx', 'rhox', 'zeta']
    
    print('参数值对比:')
    print('-'*80)
    print(f'{"参数":<12s} {"MATLAB":>20s} {"Python":>20s} {"差异":>20s} {"相对差异":>15s}')
    print('-'*80)
    
    differences = []
    for name in calib_names:
        matlab_val = matlab_params.get(name, None)
        python_val = python_params.get(name, None)
        
        if matlab_val is None or python_val is None:
            print(f'{name:<12s} {"N/A":>20s} {"N/A":>20s}')
            continue
        
        diff = abs(python_val - matlab_val)
        rel_diff = diff / abs(matlab_val) * 100 if matlab_val != 0 else 0
        
        if diff < 1e-10:
            status = '[OK]'
        else:
            status = '[DIFF]'
            differences.append((name, matlab_val, python_val, diff, rel_diff))
        
        print(f'{status} {name:<10s} {matlab_val:>20.10f} {python_val:>20.10f} '
              f'{diff:>20.2e} {rel_diff:>15.6f}%')
    
    print('-'*80)
    print('')
    
    if differences:
        print('[WARN] 发现参数值差异:')
        for name, matlab_val, python_val, diff, rel_diff in differences:
            print(f'  {name:12s}: MATLAB={matlab_val:15.10f}, Python={python_val:15.10f}, '
                  f'差异={diff:.2e} ({rel_diff:.6f}%)')
    else:
        print('[OK] 所有参数值完全一致')
    
    print('')
    return matlab_params, python_params


def compare_steady_state_results():
    """对比MATLAB和Python的稳态结果"""
    print('='*80)
    print('MATLAB vs Python 稳态结果对比')
    print('='*80)
    print('')
    
    # 读取MATLAB稳态结果（如果可用）
    matlab_table = r'C:\Users\Administrator\Desktop\Rescue-Policies-COVID-main\baseline\tables\steady_state.tex'
    matlab_results = {}
    
    if os.path.exists(matlab_table):
        print('尝试读取MATLAB稳态结果...')
        try:
            with open(matlab_table, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单的解析（根据实际格式调整）
                import re
                # 查找数值模式
                patterns = {
                    'K_corp': r'Capital \(corporate\)[^&]*&[^&]*([0-9.]+)',
                    'C_agg': r'Aggregate consumption[^&]*&[^&]*([0-9.]+)',
                    'L_agg': r'Employment \(total\)[^&]*&[^&]*([0-9.]+)',
                }
                for key, pattern in patterns.items():
                    match = re.search(pattern, content)
                    if match:
                        try:
                            matlab_results[key] = float(match.group(1))
                        except:
                            pass
        except Exception as e:
            print(f'  警告: 解析MATLAB表格文件失败: {e}')
    
    # 计算Python稳态结果
    print('计算Python稳态结果...')
    print('-'*80)
    
    par = {}
    par['do_calib'] = 0  # 稳态计算模式
    par['InpDir'] = os.path.join('inputs')
    par['TabDir'] = 'tables'
    par['do_table'] = 0
    par['do_tex'] = 0
    par['verbose'] = 0  # 减少输出
    
    file_params = 'estim_params.txt'
    
    try:
        par, guess, bounds, calibNames, dispNames, description, ExoNames = \
            set_parameters(par, file_params)
        
        sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par_final = \
            fun_steady_state(par)
        
        if flag_ss < 0:
            print('[ERROR] Python稳态计算失败')
            return
        
        python_results = {
            'K_corp': agg.get('K_corp', np.nan),
            'C_agg': agg.get('C_agg', np.nan),
            'L_agg': agg.get('L_agg', np.nan),
            'LHS': agg.get('LHS', np.nan),
            'output_small': agg.get('output_small', np.nan),
            'cost_adj': agg.get('cost_adj', np.nan),
            'wage': prices.get('wage', np.nan),
        }
        
        print('Python稳态结果:')
        for key, value in python_results.items():
            if not np.isnan(value):
                print(f'  {key:15s} = {value:15.6f}')
        print('')
        
        # 对比结果
        if matlab_results:
            print('稳态结果对比:')
            print('-'*80)
            print(f'{"变量":<15s} {"MATLAB":>20s} {"Python":>20s} {"差异":>20s}')
            print('-'*80)
            
            for key in python_results.keys():
                if key in matlab_results:
                    matlab_val = matlab_results[key]
                    python_val = python_results[key]
                    if not np.isnan(python_val):
                        diff = abs(python_val - matlab_val)
                        print(f'{key:<15s} {matlab_val:>20.6f} {python_val:>20.6f} {diff:>20.6f}')
        else:
            print('[INFO] 无法读取MATLAB稳态结果，仅显示Python结果')
        
        # 检查合理性
        print('')
        print('参数合理性检查:')
        print('-'*80)
        
        issues = []
        
        if python_results['K_corp'] < 0:
            issues.append(f"K_corp为负值: {python_results['K_corp']:.6f}")
        
        if python_results['LHS'] < 0:
            issues.append(f"LHS为负值: {python_results['LHS']:.6f}")
        
        if python_results['C_agg'] < 0.1:
            issues.append(f"C_agg过小: {python_results['C_agg']:.6f}")
        
        if python_results['output_small'] > 100:
            issues.append(f"output_small过大: {python_results['output_small']:.6f}")
        
        if issues:
            print('[WARN] 发现以下问题:')
            for issue in issues:
                print(f'  - {issue}')
        else:
            print('[OK] 所有检查通过')
        
    except Exception as e:
        print(f'[ERROR] 计算Python稳态结果时出错: {e}')
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    # 1. 对比参数值
    matlab_params, python_params = compare_parameters()
    
    print('')
    print('='*80)
    print('')
    
    # 2. 对比稳态结果
    compare_steady_state_results()
    
    print('')
    print('='*80)
    print('对比完成')
    print('='*80)


if __name__ == '__main__':
    main()













