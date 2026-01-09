"""
对比MATLAB和Python版本的稳态结果
"""
import numpy as np
import pickle
import scipy.io
import os
import sys


def load_matlab_results(mat_file):
    """加载MATLAB的.mat文件"""
    try:
        mat_data = scipy.io.loadmat(mat_file)
        return mat_data
    except Exception as e:
        print(f"无法加载MATLAB文件 {mat_file}: {e}")
        return None


def load_python_results(pkl_file):
    """加载Python的.pkl文件"""
    try:
        with open(pkl_file, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        print(f"无法加载Python文件 {pkl_file}: {e}")
        return None


def compare_values(name, val_matlab, val_python, tol=1e-6):
    """对比两个值"""
    if val_matlab is None or val_python is None:
        return False, "值缺失"
    
    # 转换为numpy数组
    val_matlab = np.asarray(val_matlab)
    val_python = np.asarray(val_python)
    
    # 检查形状
    if val_matlab.shape != val_python.shape:
        return False, f"形状不匹配: MATLAB {val_matlab.shape} vs Python {val_python.shape}"
    
    # 计算差异
    diff = np.abs(val_matlab - val_python)
    max_diff = np.max(diff)
    rel_diff = max_diff / (np.abs(val_matlab).max() + 1e-10)
    
    match = max_diff < tol or rel_diff < tol
    
    return match, {
        'max_abs_diff': max_diff,
        'max_rel_diff': rel_diff,
        'matlab_value': val_matlab,
        'python_value': val_python
    }


def compare_steady_state(matlab_file=None, python_file=None):
    """
    对比稳态结果
    
    参数:
    matlab_file: MATLAB .mat文件路径
    python_file: Python .pkl文件路径
    """
    # 默认文件路径
    if matlab_file is None:
        # 查找MATLAB文件
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
        # 查找Python文件
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
    print("稳态结果对比: MATLAB vs Python")
    print("="*80)
    print(f"MATLAB文件: {matlab_file}")
    print(f"Python文件: {python_file}")
    print("="*80)
    
    # 加载数据
    mat_data = load_matlab_results(matlab_file)
    py_data = load_python_results(python_file)
    
    if mat_data is None or py_data is None:
        return
    
    # 打印MATLAB文件中的变量
    print("\nMATLAB文件中的变量:")
    for key in mat_data.keys():
        if not key.startswith('__'):
            val = mat_data[key]
            if isinstance(val, np.ndarray):
                print(f"  {key}: shape={val.shape}, dtype={val.dtype}")
            else:
                print(f"  {key}: {type(val)}")
    
    print("\nPython文件中的变量:")
    if isinstance(py_data, dict):
        for key in py_data.keys():
            val = py_data[key]
            if isinstance(val, np.ndarray):
                print(f"  {key}: shape={val.shape}, dtype={val.dtype}")
            elif isinstance(val, dict):
                print(f"  {key}: dict with {len(val)} keys")
            else:
                print(f"  {key}: {type(val)}")
    
    print("\n" + "="*80)
    print("关键指标对比")
    print("="*80)
    
    # 对比价格
    print("\n【价格】")
    if 'prices' in mat_data:
        mat_prices = mat_data['prices']
        if isinstance(mat_prices, np.ndarray) and mat_prices.dtype.names:
            # 结构数组
            for name in mat_prices.dtype.names:
                mat_val_arr = mat_prices[name][0, 0]
                # 提取标量值
                if isinstance(mat_val_arr, np.ndarray):
                    mat_val = float(mat_val_arr.item()) if mat_val_arr.size == 1 else mat_val_arr
                else:
                    mat_val = float(mat_val_arr)
                
                py_val = py_data.get('prices', {}).get(name) if isinstance(py_data.get('prices'), dict) else None
                if py_val is not None:
                    match, info = compare_values(f"prices.{name}", mat_val, py_val)
                    status = "[OK]" if match else "[DIFF]"
                    mat_val_str = f"{mat_val:15.10f}" if isinstance(mat_val, (int, float, np.number)) else str(mat_val)
                    py_val_str = f"{py_val:15.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
                    print(f"  {status} {name:20s}: MATLAB={mat_val_str:>15}, Python={py_val_str:>15}, diff={info['max_abs_diff']:.2e}")
    elif 'prices' in py_data:
        py_prices = py_data['prices']
        if isinstance(py_prices, dict):
            for name in ['q', 'wage', 'KL_ratio', 'rental']:
                mat_val = None
                if 'prices' in mat_data:
                    mat_p = mat_data['prices']
                    if isinstance(mat_p, np.ndarray) and mat_p.dtype.names:
                        if name in mat_p.dtype.names:
                            mat_val_arr = mat_p[name][0, 0]
                            if isinstance(mat_val_arr, np.ndarray):
                                mat_val = float(mat_val_arr.item()) if mat_val_arr.size == 1 else mat_val_arr
                            else:
                                mat_val = float(mat_val_arr)
                
                py_val = py_prices.get(name)
                if py_val is not None:
                    if mat_val is not None:
                        match, info = compare_values(f"prices.{name}", mat_val, py_val)
                        status = "[OK]" if match else "[DIFF]"
                        mat_val_str = f"{mat_val:15.10f}" if isinstance(mat_val, (int, float, np.number)) else str(mat_val)
                        py_val_str = f"{py_val:15.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
                        print(f"  {status} {name:20s}: MATLAB={mat_val_str:>15}, Python={py_val_str:>15}, diff={info['max_abs_diff']:.2e}")
                    else:
                        py_val_str = f"{py_val:15.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
                        print(f"  ? {name:20s}: Python={py_val_str:>15} (MATLAB值缺失)")
    
    # 对比加总变量
    print("\n【加总变量】")
    agg_keys = ['C_agg', 'K_corp', 'K_agg', 'L_agg', 'L_corp', 'Y_corp', 'output_small', 
                'exit_rate', 'entry_rate']
    
    for key in agg_keys:
        mat_val = None
        py_val = None
        
        # 从MATLAB获取
        if 'agg' in mat_data:
            mat_agg = mat_data['agg']
            if isinstance(mat_agg, np.ndarray) and mat_agg.dtype.names:
                if key in mat_agg.dtype.names:
                    mat_val_arr = mat_agg[key][0, 0]
                    if isinstance(mat_val_arr, np.ndarray):
                        mat_val = float(mat_val_arr.item()) if mat_val_arr.size == 1 else mat_val_arr
                    else:
                        mat_val = float(mat_val_arr)
        
        # 从Python获取
        if 'agg' in py_data and isinstance(py_data['agg'], dict):
            py_val = py_data['agg'].get(key)
        
        if mat_val is not None and py_val is not None:
            match, info = compare_values(f"agg.{key}", mat_val, py_val)
            status = "[OK]" if match else "[DIFF]"
            mat_val_str = f"{mat_val:15.10f}" if isinstance(mat_val, (int, float, np.number)) else str(mat_val)
            py_val_str = f"{py_val:15.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
            print(f"  {status} {key:20s}: MATLAB={mat_val_str:>15}, Python={py_val_str:>15}, diff={info['max_abs_diff']:.2e}")
        elif py_val is not None:
            py_val_str = f"{py_val:15.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
            print(f"  ? {key:20s}: Python={py_val_str:>15} (MATLAB值缺失)")
        elif mat_val is not None:
            mat_val_str = f"{mat_val:15.10f}" if isinstance(mat_val, (int, float, np.number)) else str(mat_val)
            print(f"  ? {key:20s}: MATLAB={mat_val_str:>15} (Python值缺失)")
    
    # 对比模型矩
    print("\n【模型矩】")
    mom_keys = ['avefirmsize', 'empshare_small', 'exitrate', 'avefirmsize_age0', 
                'autocorr_emp', 'fixedcost_to_rev', 'hasNetDebt']
    
    for key in mom_keys:
        mat_val = None
        py_val = None
        
        # 从MATLAB获取
        if 'model_mom' in mat_data:
            mat_mom = mat_data['model_mom']
            if isinstance(mat_mom, np.ndarray) and mat_mom.dtype.names:
                if key in mat_mom.dtype.names:
                    mat_val_arr = mat_mom[key][0, 0]
                    if isinstance(mat_val_arr, np.ndarray):
                        mat_val = float(mat_val_arr.item()) if mat_val_arr.size == 1 else mat_val_arr
                    else:
                        mat_val = float(mat_val_arr)
        
        # 从Python获取
        if 'model_mom' in py_data and isinstance(py_data['model_mom'], dict):
            py_val = py_data['model_mom'].get(key)
        
        if mat_val is not None and py_val is not None:
            match, info = compare_values(f"model_mom.{key}", mat_val, py_val, tol=1e-4)
            status = "[OK]" if match else "[DIFF]"
            mat_val_str = f"{mat_val:15.10f}" if isinstance(mat_val, (int, float, np.number)) else str(mat_val)
            py_val_str = f"{py_val:15.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
            print(f"  {status} {key:20s}: MATLAB={mat_val_str:>15}, Python={py_val_str:>15}, diff={info['max_abs_diff']:.2e}")
        elif py_val is not None:
            py_val_str = f"{py_val:15.10f}" if isinstance(py_val, (int, float, np.number)) else str(py_val)
            print(f"  ? {key:20s}: Python={py_val_str:>15} (MATLAB值缺失)")
        elif mat_val is not None:
            mat_val_str = f"{mat_val:15.10f}" if isinstance(mat_val, (int, float, np.number)) else str(mat_val)
            print(f"  ? {key:20s}: MATLAB={mat_val_str:>15} (Python值缺失)")
    
    # 对比分布统计
    print("\n【分布统计】")
    if 'distribS' in py_data and isinstance(py_data['distribS'], dict):
        py_distrib = py_data['distribS']
        if 'mu' in py_distrib:
            py_mu = py_distrib['mu']
            print(f"  Python mu: sum={np.sum(py_mu):.10f}, min={np.min(py_mu):.10e}, max={np.max(py_mu):.10e}")
            print(f"  Python mu: 负值数量={np.sum(py_mu < 0)}")
        
        if 'mu_active' in py_distrib:
            py_mu_active = py_distrib['mu_active']
            print(f"  Python mu_active: sum={np.sum(py_mu_active):.10f}, min={np.min(py_mu_active):.10e}, max={np.max(py_mu_active):.10e}")
            print(f"  Python mu_active: 负值数量={np.sum(py_mu_active < 0)}")
    
    if 'mu' in mat_data:
        mat_mu = mat_data['mu']
        print(f"  MATLAB mu: sum={np.sum(mat_mu):.10f}, min={np.min(mat_mu):.10e}, max={np.max(mat_mu):.10e}")
        print(f"  MATLAB mu: 负值数量={np.sum(mat_mu < 0)}")
    
    print("\n" + "="*80)
    print("对比完成")
    print("="*80)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='对比MATLAB和Python的稳态结果')
    parser.add_argument('--matlab', type=str, help='MATLAB .mat文件路径')
    parser.add_argument('--python', type=str, help='Python .pkl文件路径')
    
    args = parser.parse_args()
    
    compare_steady_state(args.matlab, args.python)

