"""
检查sub_V1_onestep中RHS的维度计算
这是关键！MATLAB和Python的维度可能不同
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))


def check_RHS_dimension():
    """检查RHS的维度"""
    
    print('='*80)
    print('检查sub_V1_onestep中RHS的维度')
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
    profit_mat = sol.get('profit_mat', None)
    pi_x = par.get('pi_x', None)
    
    if V1 is None or k_grid is None or profit_mat is None or pi_x is None:
        print('缺少必要数据')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    
    nk, nx = V1.shape
    theta = par.get('theta', 0.7)
    delta = par.get('delta_k', 0.015)
    q = par.get('q', 0.99)
    psi = par.get('psi', 0.002)
    
    print('MATLAB代码分析:')
    print('-'*80)
    print('MATLAB第45-47行:')
    print('  profit_x = profit_mat(:,x_c)\'  % 转置，维度(1,nk)')
    print('  k_today = k_grid\'              % 转置，维度(1,nk)')
    print('  kprime = k_grid                 % 维度(nk,1)')
    print('  RHS = profit_x - fun.adjcost(kprime,k_today,...) + ...')
    print('  说明: RHS应该是(nk,nk)矩阵')
    print('  [V2(:,x_c),kpol_ind(:,x_c)] = max(RHS,[],1)')
    print('  说明: 沿着第1维（列）取最大值，返回(nk,1)的最大值和索引')
    print('')
    
    print('Python代码分析:')
    print('-'*80)
    print('Python第41-44行:')
    print('  profit_x = profit_mat[:, x_c]      % 维度(nk,)')
    print('  k_today = k_grid.flatten()          % 维度(nk,)')
    print('  kprime = k_grid.flatten()          % 维度(nk,)')
    print('  RHS = profit_x[:, np.newaxis] - ...')
    print('  说明: RHS应该是(nk,nk)矩阵')
    print('  max_indices = np.argmax(RHS, axis=0)')
    print('  说明: 沿着axis=0（行）取最大值索引，返回(nk,)的索引')
    print('')
    
    # 实际测试
    x_c = 0
    print(f'实际测试x={x_c}:')
    print('-'*80)
    
    # Python的计算方式
    EV_x = np.zeros(nk)  # 简化，实际需要计算EV
    profit_x = profit_mat[:, x_c]
    kprime = k_grid.flatten()
    k_today = k_grid.flatten()
    
    # 检查Fun.adjcost的维度
    from fun import Fun
    adjcost_result = Fun.adjcost(kprime, k_today, theta, delta)
    print(f'  Fun.adjcost(kprime, k_today, ...)的形状: {adjcost_result.shape}')
    print(f'  kprime形状: {kprime.shape}')
    print(f'  k_today形状: {k_today.shape}')
    print('')
    
    # 构建RHS（Python方式）
    profit_x_col = profit_x[:, np.newaxis]  # (nk,1)
    adjcost_col = adjcost_result[:, np.newaxis] if adjcost_result.ndim == 1 else adjcost_result
    kprime_col = kprime[:, np.newaxis]  # (nk,1)
    EV_x_col = EV_x[:, np.newaxis]  # (nk,1)
    
    RHS_python = (profit_x_col - adjcost_col + 
                  q * (psi * theta * (1 - delta) * kprime_col + 
                       (1 - psi) * EV_x_col))
    
    print(f'  RHS (Python方式)形状: {RHS_python.shape}')
    print(f'  预期形状: (nk, nk) = ({nk}, {nk})')
    
    if RHS_python.shape != (nk, nk):
        print('  警告：RHS形状不正确！')
        print(f'  实际形状: {RHS_python.shape}')
        print(f'  预期形状: ({nk}, {nk})')
    else:
        print('  RHS形状正确')
    print('')
    
    # 检查max的操作
    if RHS_python.shape == (nk, nk):
        max_indices_python = np.argmax(RHS_python, axis=0)
        print(f'  np.argmax(RHS, axis=0)形状: {max_indices_python.shape}')
        print(f'  预期形状: (nk,) = ({nk},)')
        print(f'  前5个索引值: {max_indices_python[:5]}')
        print('')
        
        # 检查索引范围
        if np.any(max_indices_python < 0) or np.any(max_indices_python >= nk):
            print('  警告：索引超出范围！')
        else:
            print('  索引范围检查通过')
    print('')


def check_adjcost_dimension():
    """检查adjcost函数的维度"""
    
    print('\n' + '='*80)
    print('检查adjcost函数的维度')
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
    
    theta = par.get('theta', 0.7)
    delta = par.get('delta_k', 0.015)
    
    from fun import Fun
    
    # 测试不同形状的输入
    kprime = k_grid[:5]  # (5,)
    k_today = k_grid[:5]  # (5,)
    
    print('测试adjcost函数:')
    print('-'*80)
    print(f'  输入: kprime形状={kprime.shape}, k_today形状={k_today.shape}')
    
    result = Fun.adjcost(kprime, k_today, theta, delta)
    print(f'  输出形状: {result.shape}')
    print('')
    
    # MATLAB中adjcost应该返回什么？
    print('MATLAB中adjcost的预期行为:')
    print('-'*80)
    print('  fun.adjcost(kprime, k_today, ...)')
    print('  kprime: (nk,1)')
    print('  k_today: (1,nk)')
    print('  应该返回: (nk,nk)矩阵')
    print('')
    
    # 测试广播
    kprime_col = kprime[:, np.newaxis]  # (5,1)
    k_today_row = k_today[np.newaxis, :]  # (1,5)
    
    print('测试广播:')
    print('-'*80)
    print(f'  kprime_col形状: {kprime_col.shape}')
    print(f'  k_today_row形状: {k_today_row.shape}')
    
    # 手动计算adjcost看看维度
    diff = kprime_col - k_today_row  # (5,5)
    print(f'  kprime_col - k_today_row形状: {diff.shape}')
    print('')


if __name__ == '__main__':
    check_RHS_dimension()
    check_adjcost_dimension()
    
    print('\n' + '='*80)
    print('关键发现')
    print('='*80)
    print('\n需要检查:')
    print('  1. Fun.adjcost函数的维度是否正确')
    print('  2. RHS的构建是否正确')
    print('  3. max操作的方向是否正确（axis=0 vs axis=1）')



