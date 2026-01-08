"""
检查索引问题，特别是1-based vs 0-based的差异
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))


def check_V1_indexing():
    """检查V1的索引使用"""
    
    print('='*80)
    print('检查V1的索引使用')
    print('='*80)
    print('')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    V1 = sol.get('V1', None)
    k_grid = par.get('k_grid', None)
    x_grid = par.get('x_grid', None)
    pi_x = par.get('pi_x', None)
    
    if V1 is None:
        print('缺少V1')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    if x_grid.ndim > 1:
        x_grid = x_grid.flatten()
    
    nk, nx = V1.shape
    
    print(f'V1形状: {V1.shape} (应该是(nk, nx))')
    print(f'k_grid长度: {len(k_grid)} (应该是nk={nk})')
    print(f'x_grid长度: {len(x_grid)} (应该是nx={nx})')
    print('')
    
    # 检查V1的访问方式
    print('检查V1的访问方式:')
    print('-'*80)
    print('MATLAB代码: V1(:,xp_c) - 这是列向量，维度(nk,1)')
    print('Python代码: V1[:, xp_c] - 这也是列向量，维度(nk,)')
    print('')
    
    # 检查V1[:, xp_c]的形状
    for xp_c in range(min(3, nx)):
        v1_col = V1[:, xp_c]
        print(f'V1[:, {xp_c}]形状: {v1_col.shape}, 长度: {len(v1_col)}')
        if len(v1_col) != nk:
            print(f'  警告：长度不匹配！应该是{nk}')
    print('')
    
    # 检查k_grid的索引
    print('检查k_grid的索引:')
    print('-'*80)
    print('MATLAB: k_grid(max_ind1) - max_ind1是1-based索引')
    print('Python: k_grid[max_ind1] - max_ind1是0-based索引')
    print('')
    
    # 测试索引
    test_indices = [0, 1, nk-1]
    print('测试索引访问:')
    for idx in test_indices:
        if idx < len(k_grid):
            print(f'  k_grid[{idx}] = {k_grid[idx]:.6f}')
    print('')


def check_sub_investment_indexing():
    """检查sub_investment_onestep中的索引使用"""
    
    print('\n' + '='*80)
    print('检查sub_investment_onestep中的索引使用')
    print('='*80)
    print('')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    V1 = sol.get('V1', None)
    k_grid = par.get('k_grid', None)
    x_grid = par.get('x_grid', None)
    pi_x = par.get('pi_x', None)
    
    if V1 is None or k_grid is None or x_grid is None or pi_x is None:
        print('缺少必要数据')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    if x_grid.ndim > 1:
        x_grid = x_grid.flatten()
    
    theta = par.get('theta', 0.7)
    delta = par.get('delta_k', 0.015)
    q = par.get('q', 0.99)
    psi = par.get('psi', 0.002)
    
    nk = len(k_grid)
    nx = len(x_grid)
    
    print('关键代码对比:')
    print('-'*80)
    print('MATLAB:')
    print('  [~,max_ind1] = max(RHS1);')
    print('  k_star1(x_c) = k_grid(max_ind1);')
    print('  说明: max_ind1是1-based索引，k_grid(max_ind1)访问第max_ind1个元素')
    print('')
    print('Python:')
    print('  max_ind1 = np.argmax(RHS1)')
    print('  k_star1[x_c] = k_grid[max_ind1]')
    print('  说明: max_ind1是0-based索引，k_grid[max_ind1]访问第max_ind1个元素')
    print('')
    
    # 测试一个x值
    x_c = 0
    print(f'测试x={x_c}的计算:')
    print('-'*80)
    
    aux1 = -(1 - q * psi * theta * (1 - delta))
    aux2 = -(1 - q * psi * (1 - delta)) * theta
    kprime_vec = k_grid.flatten()
    
    EVx = np.zeros(nk)
    for xp_c in range(nx):
        EVx = EVx + pi_x[x_c, xp_c] * np.maximum(theta * (1 - delta) * kprime_vec, 
                                                 V1[:, xp_c])
    
    RHS1 = aux1 * kprime_vec + q * (1 - psi) * EVx
    RHS2 = aux2 * kprime_vec + q * (1 - psi) * EVx
    
    max_ind1 = np.argmax(RHS1)
    max_ind2 = np.argmax(RHS2)
    
    print(f'  RHS1长度: {len(RHS1)} (应该是nk={nk})')
    print(f'  RHS2长度: {len(RHS2)} (应该是nk={nk})')
    print(f'  max_ind1 = {max_ind1} (0-based索引)')
    print(f'  max_ind2 = {max_ind2} (0-based索引)')
    print(f'  k_grid[max_ind1] = {k_grid[max_ind1]:.6f}')
    print(f'  k_grid[max_ind2] = {k_grid[max_ind2]:.6f}')
    print('')
    
    # 检查是否有索引越界
    if max_ind1 >= nk or max_ind2 >= nk:
        print(f'警告：索引越界！max_ind1={max_ind1}, max_ind2={max_ind2}, nk={nk}')
    else:
        print('索引范围检查通过')
    print('')


def check_V1_shape_issue():
    """检查V1的形状是否有问题"""
    
    print('\n' + '='*80)
    print('检查V1的形状和访问')
    print('='*80)
    print('')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    V1 = sol.get('V1', None)
    k_grid = par.get('k_grid', None)
    pi_x = par.get('pi_x', None)
    
    if V1 is None:
        print('缺少V1')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    
    nk, nx = V1.shape
    
    print('V1形状检查:')
    print('-'*80)
    print(f'  V1.shape = {V1.shape}')
    print(f'  V1是2D数组: {V1.ndim == 2}')
    print('')
    
    print('V1[:, xp_c]的访问:')
    print('-'*80)
    for xp_c in range(min(3, nx)):
        v1_slice = V1[:, xp_c]
        print(f'  V1[:, {xp_c}]:')
        print(f'    形状: {v1_slice.shape}')
        print(f'    长度: {len(v1_slice)}')
        print(f'    是否1D: {v1_slice.ndim == 1}')
        print(f'    前3个值: {v1_slice[:3]}')
    print('')
    
    print('关键问题检查:')
    print('-'*80)
    print('MATLAB: V1(:,xp_c) 返回列向量 (nk,1)')
    print('Python: V1[:, xp_c] 返回1D数组 (nk,)')
    print('')
    print('在计算中:')
    print('  MATLAB: max(theta*(1-delta)*kprime_vec, V1(:,xp_c))')
    print('    kprime_vec是(nk,1)，V1(:,xp_c)是(nk,1)，max返回(nk,1)')
    print('')
    print('  Python: np.maximum(theta*(1-delta)*kprime_vec, V1[:, xp_c])')
    print('    kprime_vec是(nk,)，V1[:, xp_c]是(nk,)，max返回(nk,)')
    print('')
    print('这应该是等价的，因为numpy的broadcasting会处理形状差异')
    print('')


def check_k_grid_indexing():
    """检查k_grid的索引是否正确"""
    
    print('\n' + '='*80)
    print('检查k_grid的索引')
    print('='*80)
    print('')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        return
    
    par = ss_results.get('par', {})
    k_grid = par.get('k_grid', None)
    
    if k_grid is None:
        print('缺少k_grid')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    
    nk = len(k_grid)
    
    print('k_grid检查:')
    print('-'*80)
    print(f'  k_grid长度: {nk}')
    print(f'  k_grid范围: [{k_grid[0]:.6f}, {k_grid[-1]:.6f}]')
    print(f'  有效索引范围: [0, {nk-1}] (0-based)')
    print('')
    
    # 检查索引访问
    print('索引访问测试:')
    print('-'*80)
    test_cases = [
        (0, '第一个元素'),
        (1, '第二个元素'),
        (nk-1, '最后一个元素')
    ]
    
    for idx, desc in test_cases:
        if 0 <= idx < nk:
            print(f'  k_grid[{idx}] = {k_grid[idx]:.6f} ({desc})')
        else:
            print(f'  警告：索引{idx}超出范围！')
    print('')


if __name__ == '__main__':
    check_V1_indexing()
    check_sub_investment_indexing()
    check_V1_shape_issue()
    check_k_grid_indexing()
    
    print('\n' + '='*80)
    print('索引检查完成')
    print('='*80)
    print('\n关键发现:')
    print('  1. Python使用0-based索引，MATLAB使用1-based索引')
    print('  2. np.argmax返回0-based索引，MATLAB的max返回1-based索引')
    print('  3. 但k_grid[max_ind1]的访问应该是正确的，因为k_grid也是0-based')
    print('  4. 需要检查是否有其他地方使用了错误的索引')




