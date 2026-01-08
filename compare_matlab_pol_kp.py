"""
对比MATLAB和Python的pol_kp相关结果
"""
import numpy as np
import pickle
import sys
import os

try:
    import scipy.io as sio
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("警告：scipy未安装，无法读取MATLAB .mat文件")

sys.path.append(os.path.dirname(__file__))


def load_python_results():
    """加载Python的稳态结果"""
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        return ss_results
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        return None


def load_matlab_results():
    """加载MATLAB的稳态结果"""
    if not HAS_SCIPY:
        return None
    
    matlab_paths = [
        '../alternative/mat/ss.mat',
        'mat/ss.mat',
        '../mat/ss.mat'
    ]
    
    for path in matlab_paths:
        if os.path.exists(path):
            try:
                print(f'尝试加载MATLAB文件: {path}')
                mat_data = sio.loadmat(path)
                print(f'成功加载MATLAB文件: {path}')
                return mat_data
            except Exception as e:
                print(f'加载{path}失败: {e}')
                continue
    
    print('未找到MATLAB的ss.mat文件')
    return None


def compare_V1():
    """对比V1"""
    
    print('='*80)
    print('V1对比（无约束企业的价值函数）')
    print('='*80)
    print('')
    
    py_results = load_python_results()
    if py_results is None:
        return
    
    mat_results = load_matlab_results()
    if mat_results is None:
        print('无法加载MATLAB结果，跳过对比')
        return
    
    py_sol = py_results.get('sol', {})
    py_V1 = py_sol.get('V1', None)
    
    if py_V1 is None:
        print('Python结果中没有V1')
        return
    
    # MATLAB的sol是结构体，需要访问sol['V1']
    mat_V1 = None
    mat_key = None
    
    if 'sol' in mat_results:
        sol_struct = mat_results['sol']
        # MATLAB结构体是numpy的structured array
        if isinstance(sol_struct, np.ndarray) and sol_struct.dtype.names:
            if 'V1' in sol_struct.dtype.names:
                mat_V1 = sol_struct['V1'][0, 0]  # MATLAB结构体通常是(1,1)形状
                mat_key = 'sol.V1'
    
    if mat_V1 is None:
        print('未在MATLAB结果中找到V1')
        if 'sol' in mat_results:
            sol_struct = mat_results['sol']
            if isinstance(sol_struct, np.ndarray) and sol_struct.dtype.names:
                print('MATLAB sol结构体中的字段:')
                for name in sol_struct.dtype.names:
                    print(f'  {name}')
        return
    
    print(f'找到MATLAB的V1: {mat_key}')
    print('')
    
    print('V1统计对比:')
    print('-'*80)
    print(f'  Python V1:')
    print(f'    形状: {py_V1.shape}')
    print(f'    最小值: {np.min(py_V1):.6f}')
    print(f'    最大值: {np.max(py_V1):.6f}')
    print(f'    平均值: {np.mean(py_V1):.6f}')
    print(f'  MATLAB V1:')
    print(f'    形状: {mat_V1.shape}')
    print(f'    最小值: {np.min(mat_V1):.6f}')
    print(f'    最大值: {np.max(mat_V1):.6f}')
    print(f'    平均值: {np.mean(mat_V1):.6f}')
    print('')
    
    # 计算差异
    if py_V1.shape == mat_V1.shape:
        diff = np.abs(py_V1 - mat_V1)
        print('V1差异:')
        print('-'*80)
        print(f'  最大差异: {np.max(diff):.6f}')
        print(f'  平均差异: {np.mean(diff):.6f}')
        print(f'  相对差异（平均）: {np.mean(diff) / np.mean(np.abs(mat_V1)) * 100:.2f}%')
        print(f'  差异>1e-3的点数: {np.sum(diff > 1e-3)} ({np.sum(diff > 1e-3)/diff.size*100:.2f}%)')
        print('')
        
        if np.max(diff) > 1:
            print('警告：V1差异较大！')
    else:
        print('警告：V1形状不匹配，无法直接对比')


def compare_pol_kp_unc():
    """对比pol_kp_unc"""
    
    print('\n' + '='*80)
    print('pol_kp_unc对比（无约束企业的资本政策）')
    print('='*80)
    print('')
    
    py_results = load_python_results()
    if py_results is None:
        return
    
    mat_results = load_matlab_results()
    if mat_results is None:
        print('无法加载MATLAB结果，跳过对比')
        return
    
    py_sol = py_results.get('sol', {})
    py_pol_kp_unc = py_sol.get('pol_kp_unc', None)
    
    if py_pol_kp_unc is None:
        print('Python结果中没有pol_kp_unc')
        return
    
    # MATLAB的pol_kp_unc在sol结构体中
    mat_pol_kp_unc = None
    mat_key = None
    
    if 'sol' in mat_results:
        sol_struct = mat_results['sol']
        if isinstance(sol_struct, np.ndarray) and sol_struct.dtype.names:
            if 'pol_kp_unc' in sol_struct.dtype.names:
                mat_pol_kp_unc = sol_struct['pol_kp_unc'][0, 0]
                mat_key = 'sol.pol_kp_unc'
    
    if mat_pol_kp_unc is None:
        print('未在MATLAB结果中找到pol_kp_unc')
        print('MATLAB结果中形状匹配的数组:')
        for key in mat_results.keys():
            if not key.startswith('__'):
                data = mat_results[key]
                if isinstance(data, np.ndarray) and len(data.shape) == 2:
                    print(f'  {key}: shape={data.shape}')
        return
    
    print(f'找到MATLAB的pol_kp_unc: {mat_key}')
    print('')
    
    print('pol_kp_unc统计对比:')
    print('-'*80)
    print(f'  Python pol_kp_unc:')
    print(f'    形状: {py_pol_kp_unc.shape}')
    print(f'    最小值: {np.min(py_pol_kp_unc):.6f}')
    print(f'    最大值: {np.max(py_pol_kp_unc):.6f}')
    print(f'    平均值: {np.mean(py_pol_kp_unc):.6f}')
    print(f'  MATLAB pol_kp_unc:')
    print(f'    形状: {mat_pol_kp_unc.shape}')
    print(f'    最小值: {np.min(mat_pol_kp_unc):.6f}')
    print(f'    最大值: {np.max(mat_pol_kp_unc):.6f}')
    print(f'    平均值: {np.mean(mat_pol_kp_unc):.6f}')
    print('')
    
    # 计算差异
    if py_pol_kp_unc.shape == mat_pol_kp_unc.shape:
        diff = np.abs(py_pol_kp_unc - mat_pol_kp_unc)
        print('pol_kp_unc差异:')
        print('-'*80)
        print(f'  最大差异: {np.max(diff):.6f}')
        print(f'  平均差异: {np.mean(diff):.6f}')
        print(f'  相对差异（平均）: {np.mean(diff) / np.mean(np.abs(mat_pol_kp_unc)) * 100:.2f}%')
        print(f'  差异>1e-3的点数: {np.sum(diff > 1e-3)} ({np.sum(diff > 1e-3)/diff.size*100:.2f}%)')
        print(f'  差异>1的点数: {np.sum(diff > 1)} ({np.sum(diff > 1)/diff.size*100:.2f}%)')
        print('')
        
        # 找出差异最大的点
        max_diff_idx = np.unravel_index(np.argmax(diff), diff.shape)
        print('差异最大的点:')
        print('-'*80)
        print(f'  位置: k_idx={max_diff_idx[0]}, x_idx={max_diff_idx[1]}')
        print(f'  Python值: {py_pol_kp_unc[max_diff_idx]:.6f}')
        print(f'  MATLAB值: {mat_pol_kp_unc[max_diff_idx]:.6f}')
        print(f'  差异: {diff[max_diff_idx]:.6f}')
        print('')
        
        if np.max(diff) > 1:
            print('警告：pol_kp_unc差异很大！')
    else:
        print('警告：pol_kp_unc形状不匹配，无法直接对比')


def compare_pol_kp():
    """对比pol_kp"""
    
    print('\n' + '='*80)
    print('pol_kp对比（所有企业的资本政策）')
    print('='*80)
    print('')
    
    py_results = load_python_results()
    if py_results is None:
        return
    
    mat_results = load_matlab_results()
    if mat_results is None:
        print('无法加载MATLAB结果，跳过对比')
        return
    
    py_sol = py_results.get('sol', {})
    py_pol_kp = py_sol.get('pol_kp', None)
    
    if py_pol_kp is None:
        print('Python结果中没有pol_kp')
        return
    
    # MATLAB的pol_kp在sol结构体中
    mat_pol_kp = None
    mat_key = None
    
    if 'sol' in mat_results:
        sol_struct = mat_results['sol']
        if isinstance(sol_struct, np.ndarray) and sol_struct.dtype.names:
            if 'pol_kp' in sol_struct.dtype.names:
                mat_pol_kp = sol_struct['pol_kp'][0, 0]
                mat_key = 'sol.pol_kp'
    
    if mat_pol_kp is None:
        print('未在MATLAB结果中找到pol_kp')
        print('MATLAB结果中形状匹配的3D数组:')
        for key in mat_results.keys():
            if not key.startswith('__'):
                data = mat_results[key]
                if isinstance(data, np.ndarray) and len(data.shape) == 3:
                    print(f'  {key}: shape={data.shape}')
        return
    
    print(f'找到MATLAB的pol_kp: {mat_key}')
    print('')
    
    print('pol_kp统计对比:')
    print('-'*80)
    print(f'  Python pol_kp:')
    print(f'    形状: {py_pol_kp.shape}')
    print(f'    最小值: {np.min(py_pol_kp):.6f}')
    print(f'    最大值: {np.max(py_pol_kp):.6f}')
    print(f'    平均值: {np.mean(py_pol_kp):.6f}')
    print(f'  MATLAB pol_kp:')
    print(f'    形状: {mat_pol_kp.shape}')
    print(f'    最小值: {np.min(mat_pol_kp):.6f}')
    print(f'    最大值: {np.max(mat_pol_kp):.6f}')
    print(f'    平均值: {np.mean(mat_pol_kp):.6f}')
    print('')
    
    # 计算差异
    if py_pol_kp.shape == mat_pol_kp.shape:
        diff = np.abs(py_pol_kp - mat_pol_kp)
        print('pol_kp差异:')
        print('-'*80)
        print(f'  最大差异: {np.max(diff):.6f}')
        print(f'  平均差异: {np.mean(diff):.6f}')
        print(f'  相对差异（平均）: {np.mean(diff) / np.mean(np.abs(mat_pol_kp)) * 100:.2f}%')
        print(f'  差异>1e-3的点数: {np.sum(diff > 1e-3)} ({np.sum(diff > 1e-3)/diff.size*100:.2f}%)')
        print(f'  差异>1的点数: {np.sum(diff > 1)} ({np.sum(diff > 1)/diff.size*100:.2f}%)')
        print('')
        
        # 计算投资方向
        py_par = py_results.get('par', {})
        py_k_grid = py_par.get('k_grid', None)
        if py_k_grid is not None:
            if py_k_grid.ndim > 1:
                py_k_grid = py_k_grid.flatten()
            delta = py_par.get('delta_k', 0.015)
            
            k_arr = np.tile(py_k_grid[:, np.newaxis, np.newaxis], (1, py_pol_kp.shape[1], py_pol_kp.shape[2]))
            py_investment = py_pol_kp - (1 - delta) * k_arr
            mat_investment = mat_pol_kp - (1 - delta) * k_arr
            
            print('投资方向对比:')
            print('-'*80)
            py_up = np.sum(py_investment > 0)
            py_down = np.sum(py_investment < 0)
            mat_up = np.sum(mat_investment > 0)
            mat_down = np.sum(mat_investment < 0)
            
            print(f'  Python:')
            print(f'    向上调整: {py_up} ({py_up/py_investment.size*100:.2f}%)')
            print(f'    向下调整: {py_down} ({py_down/py_investment.size*100:.2f}%)')
            print(f'  MATLAB:')
            print(f'    向上调整: {mat_up} ({mat_up/mat_investment.size*100:.2f}%)')
            print(f'    向下调整: {mat_down} ({mat_down/mat_investment.size*100:.2f}%)')
            print('')
        
        if np.max(diff) > 1:
            print('警告：pol_kp差异很大！')
    else:
        print('警告：pol_kp形状不匹配，无法直接对比')


if __name__ == '__main__':
    if not HAS_SCIPY:
        print('错误：需要安装scipy来读取MATLAB文件')
        print('请运行: pip install scipy')
        sys.exit(1)
    
    compare_V1()
    compare_pol_kp_unc()
    compare_pol_kp()
    
    print('\n' + '='*80)
    print('对比完成')
    print('='*80)

