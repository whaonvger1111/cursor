"""
对比MATLAB和Python的参数设置，特别是网格和容差
"""
import numpy as np
import pickle
import scipy.io
import os
import sys


def extract_matlab_param(mat_data, param_name):
    """从MATLAB结构数组中提取参数值"""
    if 'par' not in mat_data:
        return None
    
    mat_par = mat_data['par']
    if not isinstance(mat_par, np.ndarray) or not mat_par.dtype.names:
        return None
    
    if param_name not in mat_par.dtype.names:
        return None
    
    val = mat_par[param_name][0, 0]
    # 提取标量值
    if isinstance(val, np.ndarray):
        if val.size == 1:
            return float(val.item())
        else:
            return val
    else:
        return float(val) if isinstance(val, (int, float, np.number)) else val


def compare_parameters(matlab_file=None, python_file=None):
    """
    对比参数设置
    
    参数:
    matlab_file: MATLAB .mat文件路径
    python_file: Python .pkl文件路径
    """
    # 默认文件路径
    if matlab_file is None:
        possible_matlab_files = [
            '../baseline_python/steady_state_results_fortran.mat',
            '../alternative/mat/ss.mat',
            'steady_state_results.mat'
        ]
        for f in possible_matlab_files:
            if os.path.exists(f):
                matlab_file = f
                break
    
    if python_file is None:
        possible_python_files = [
            'steady_state_results_new.pkl',
            '../baseline_python/steady_state_results_fortran.pkl',
            '../baseline_python/steady_state_results.pkl'
        ]
        for f in possible_python_files:
            if os.path.exists(f):
                python_file = f
                break
    
    if matlab_file is None or not os.path.exists(matlab_file):
        print("错误: 找不到MATLAB结果文件")
        return
    
    if python_file is None or not os.path.exists(python_file):
        print("错误: 找不到Python结果文件")
        return
    
    print("="*80)
    print("参数设置对比: MATLAB vs Python")
    print("="*80)
    print(f"MATLAB文件: {matlab_file}")
    print(f"Python文件: {python_file}")
    print("="*80)
    
    # 加载数据
    try:
        mat_data = scipy.io.loadmat(matlab_file)
    except Exception as e:
        print(f"无法加载MATLAB文件: {e}")
        return
    
    try:
        with open(python_file, 'rb') as f:
            py_data = pickle.load(f)
    except Exception as e:
        print(f"无法加载Python文件: {e}")
        return
    
    # 提取参数
    mat_par = {}
    py_par = py_data.get('par', {}) if isinstance(py_data, dict) else {}
    
    # 关键参数列表
    key_params = {
        '网格设置': ['nx', 'nb', 'nk'],
        '容差设置': ['tol_vfi', 'tol_vfi_u', 'tol_bhat', 'tol_dist'],
        '迭代设置': ['max_iter', 'maxiter_dist', 'n_howard', 'do_howard'],
        '经济参数': ['beta', 'sigma', 'alpha', 'delta_k', 'gamma1', 'gamma2', 'A', 'lambda0', 'theta', 'psi', 'zeta'],
        '生产率参数': ['x0', 'xi', 'epsx', 'rhox', 'x_process'],
        '资本参数': ['k_min', 'k_max', 'k_alpha', 'k_distrib'],
        '其他参数': ['mass', 'fixcost1', 'fixcost2', 'cost_e']
    }
    
    # 从MATLAB提取参数
    for category, params in key_params.items():
        for param_name in params:
            val = extract_matlab_param(mat_data, param_name)
            if val is not None:
                mat_par[param_name] = val
    
    print("\n" + "="*80)
    print("参数对比详情")
    print("="*80)
    
    all_match = True
    
    for category, params in key_params.items():
        print(f"\n【{category}】")
        print(f"{'参数':<20} {'MATLAB值':<25} {'Python值':<25} {'匹配':<10} {'说明'}")
        print("-" * 100)
        
        for param_name in params:
            mat_val = mat_par.get(param_name)
            py_val = py_par.get(param_name)
            
            # 格式化值
            if mat_val is None:
                mat_str = "缺失"
            elif isinstance(mat_val, np.ndarray):
                mat_str = f"array{mat_val.shape}"
            else:
                mat_str = f"{mat_val:.10f}" if isinstance(mat_val, (int, float, np.number)) else str(mat_val)
            
            if py_val is None:
                py_str = "缺失"
            elif isinstance(py_val, np.ndarray):
                py_str = f"array{py_val.shape}"
            else:
                py_str = f"{py_val:.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
            
            # 判断是否匹配
            if mat_val is None or py_val is None:
                match = "?"
                note = "一方缺失"
            elif isinstance(mat_val, np.ndarray) or isinstance(py_val, np.ndarray):
                match = "?"
                note = "数组类型"
            else:
                # 数值比较
                if isinstance(mat_val, (int, float, np.number)) and isinstance(py_val, (int, float, np.number)):
                    if abs(mat_val - py_val) < 1e-10:
                        match = "[OK]"
                        note = "完全匹配"
                    else:
                        match = "[DIFF]"
                        diff = abs(mat_val - py_val)
                        rel_diff = diff / (abs(mat_val) + 1e-10)
                        note = f"差异={diff:.2e} ({rel_diff*100:.2f}%)"
                        all_match = False
                else:
                    match = "?"
                    note = "类型不匹配"
            
            print(f"{param_name:<20} {mat_str:<25} {py_str:<25} {match:<10} {note}")
    
    # 特别检查网格和容差
    print("\n" + "="*80)
    print("关键差异总结")
    print("="*80)
    
    critical_params = {
        '网格大小': ['nx', 'nb', 'nk'],
        '容差': ['tol_vfi', 'tol_vfi_u', 'tol_bhat', 'tol_dist'],
        '迭代次数': ['max_iter', 'maxiter_dist', 'n_howard']
    }
    
    has_critical_diff = False
    for category, params in critical_params.items():
        print(f"\n{category}:")
        for param_name in params:
            mat_val = mat_par.get(param_name)
            py_val = py_par.get(param_name)
            
            if mat_val is not None and py_val is not None:
                if isinstance(mat_val, (int, float, np.number)) and isinstance(py_val, (int, float, np.number)):
                    if abs(mat_val - py_val) > 1e-10:
                        diff = abs(mat_val - py_val)
                        rel_diff = diff / (abs(mat_val) + 1e-10) * 100
                        print(f"  {param_name}: MATLAB={mat_val}, Python={py_val}, 差异={diff:.2e} ({rel_diff:.1f}%)")
                        has_critical_diff = True
    
    if not has_critical_diff:
        print("  所有关键参数完全匹配！")
    
    # 检查其他重要参数
    print("\n其他重要参数:")
    other_params = ['beta', 'sigma', 'alpha', 'delta_k', 'gamma1', 'gamma2', 'A', 'lambda0', 'theta', 'psi', 'zeta', 'mass']
    for param_name in other_params:
        mat_val = mat_par.get(param_name)
        py_val = py_par.get(param_name)
        
        if mat_val is not None and py_val is not None:
            if isinstance(mat_val, (int, float, np.number)) and isinstance(py_val, (int, float, np.number)):
                if abs(mat_val - py_val) > 1e-10:
                    diff = abs(mat_val - py_val)
                    rel_diff = diff / (abs(mat_val) + 1e-10) * 100
                    print(f"  {param_name}: MATLAB={mat_val:.10f}, Python={py_val:.10f}, 差异={diff:.2e} ({rel_diff:.2f}%)")
                    all_match = False
    
    print("\n" + "="*80)
    if all_match:
        print("所有参数完全匹配！")
    else:
        print("发现参数差异，这可能导致结果不同")
    print("="*80)
    
    # 保存详细对比到文件
    output_file = 'parameter_comparison.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("参数设置对比: MATLAB vs Python\n")
        f.write("="*80 + "\n")
        f.write(f"MATLAB文件: {matlab_file}\n")
        f.write(f"Python文件: {python_file}\n")
        f.write("="*80 + "\n\n")
        
        for category, params in key_params.items():
            f.write(f"\n【{category}】\n")
            f.write(f"{'参数':<20} {'MATLAB值':<25} {'Python值':<25} {'匹配':<10} {'说明'}\n")
            f.write("-" * 100 + "\n")
            
            for param_name in params:
                mat_val = mat_par.get(param_name)
                py_val = py_par.get(param_name)
                
                if mat_val is None:
                    mat_str = "缺失"
                elif isinstance(mat_val, np.ndarray):
                    mat_str = f"array{mat_val.shape}"
                else:
                    mat_str = f"{mat_val:.10f}" if isinstance(mat_val, (int, float, np.number)) else str(mat_val)
                
                if py_val is None:
                    py_str = "缺失"
                elif isinstance(py_val, np.ndarray):
                    py_str = f"array{py_val.shape}"
                else:
                    py_str = f"{py_val:.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
                
                if mat_val is None or py_val is None:
                    match = "?"
                    note = "一方缺失"
                elif isinstance(mat_val, np.ndarray) or isinstance(py_val, np.ndarray):
                    match = "?"
                    note = "数组类型"
                else:
                    if isinstance(mat_val, (int, float, np.number)) and isinstance(py_val, (int, float, np.number)):
                        if abs(mat_val - py_val) < 1e-10:
                            match = "[OK]"
                            note = "完全匹配"
                        else:
                            match = "[DIFF]"
                            diff = abs(mat_val - py_val)
                            rel_diff = diff / (abs(mat_val) + 1e-10)
                            note = f"差异={diff:.2e} ({rel_diff*100:.2f}%)"
                    else:
                        match = "?"
                        note = "类型不匹配"
                
                f.write(f"{param_name:<20} {mat_str:<25} {py_str:<25} {match:<10} {note}\n")
    
    print(f"\n详细对比结果已保存到: {output_file}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='对比MATLAB和Python的参数设置')
    parser.add_argument('--matlab', type=str, help='MATLAB .mat文件路径')
    parser.add_argument('--python', type=str, help='Python .pkl文件路径')
    
    args = parser.parse_args()
    
    compare_parameters(args.matlab, args.python)

