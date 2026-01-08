"""
深入检查pol_kp问题的根本原因
检查V1、k_star1、k_star2等关键变量
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))


def load_results():
    """加载稳态结果"""
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        return ss_results
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        return None


def check_V1():
    """检查V1（无约束企业的价值函数）"""
    
    print('='*80)
    print('V1检查（无约束企业的价值函数）')
    print('='*80)
    print('')
    
    ss_results = load_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    if 'V1' not in sol:
        print('❌ sol中没有V1')
        return
    
    V1 = sol['V1']
    k_grid = par.get('k_grid', None)
    x_grid = par.get('x_grid', None)
    
    if k_grid is None or x_grid is None:
        print('❌ 缺少k_grid或x_grid')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    if x_grid.ndim > 1:
        x_grid = x_grid.flatten()
    
    nk, nx = V1.shape
    print(f'V1维度: ({nk}, {nx})')
    print('')
    
    print('V1统计信息:')
    print('-'*80)
    print(f'  V1最小值: {np.min(V1):.6f}')
    print(f'  V1最大值: {np.max(V1):.6f}')
    print(f'  V1平均值: {np.mean(V1):.6f}')
    print(f'  V1中位数: {np.median(V1):.6f}')
    print(f'  负值数量: {np.sum(V1 < 0)} ({np.sum(V1 < 0)/(nk*nx)*100:.2f}%)')
    print(f'  正值数量: {np.sum(V1 > 0)} ({np.sum(V1 > 0)/(nk*nx)*100:.2f}%)')
    print('')
    
    # 检查V1的分布
    print('V1按x（生产率）的统计:')
    print('-'*80)
    for x_c in range(min(5, nx)):  # 只显示前5个
        print(f'  x={x_c} (x_val={x_grid[x_c]:.6f}):')
        print(f'    V1范围: [{np.min(V1[:, x_c]):.6f}, {np.max(V1[:, x_c]):.6f}]')
        print(f'    V1平均值: {np.mean(V1[:, x_c]):.6f}')
    
    if nx > 5:
        print(f'  ... (共{nx}个x值)')
    print('')
    
    # 找出V1最大和最小的点
    max_idx = np.unravel_index(np.argmax(V1), V1.shape)
    min_idx = np.unravel_index(np.argmin(V1), V1.shape)
    
    print('V1极值点:')
    print('-'*80)
    print(f'  最大值点: k_idx={max_idx[0]}, x_idx={max_idx[1]}')
    print(f'    k={k_grid[max_idx[0]]:.6f}, x={x_grid[max_idx[1]]:.6f}')
    print(f'    V1={V1[max_idx]:.6f}')
    print(f'  最小值点: k_idx={min_idx[0]}, x_idx={min_idx[1]}')
    print(f'    k={k_grid[min_idx[0]]:.6f}, x={x_grid[min_idx[1]]:.6f}')
    print(f'    V1={V1[min_idx]:.6f}')
    print('')


def check_k_star():
    """检查k_star1和k_star2的计算"""
    
    print('\n' + '='*80)
    print('k_star1和k_star2检查')
    print('='*80)
    print('')
    
    ss_results = load_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    if 'V1' not in sol:
        print('❌ sol中没有V1')
        return
    
    V1 = sol['V1']
    k_grid = par.get('k_grid', None)
    x_grid = par.get('x_grid', None)
    pi_x = par.get('pi_x', None)
    
    if k_grid is None or x_grid is None or pi_x is None:
        print('❌ 缺少必要参数')
        return
    
    # 获取参数
    theta = par.get('theta', 0.7)
    delta = par.get('delta_k', 0.015)
    q = par.get('q', 0.99)
    psi = par.get('psi', 0.002)
    
    print('使用的参数:')
    print('-'*80)
    print(f'  theta = {theta:.6f}')
    print(f'  delta = {delta:.6f}')
    print(f'  q = {q:.6f}')
    print(f'  psi = {psi:.6f}')
    print('')
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    if x_grid.ndim > 1:
        x_grid = x_grid.flatten()
    
    nk = len(k_grid)
    nx = len(x_grid)
    
    # 重新计算k_star1和k_star2（与sub_investment_onestep相同）
    aux1 = -(1 - q * psi * theta * (1 - delta))
    aux2 = -(1 - q * psi * (1 - delta)) * theta
    
    print('辅助变量:')
    print('-'*80)
    print(f'  aux1 = {aux1:.6f}')
    print(f'  aux2 = {aux2:.6f}')
    print('')
    
    k_star1 = np.zeros(nx)
    k_star2 = np.zeros(nx)
    kprime_vec = k_grid.flatten()
    
    for x_c in range(nx):
        EVx = np.zeros(nk)
        for xp_c in range(nx):
            EVx = EVx + pi_x[x_c, xp_c] * np.maximum(theta * (1 - delta) * kprime_vec, 
                                                     V1[:, xp_c])
        RHS1 = aux1 * kprime_vec + q * (1 - psi) * EVx
        RHS2 = aux2 * kprime_vec + q * (1 - psi) * EVx
        max_ind1 = np.argmax(RHS1)
        max_ind2 = np.argmax(RHS2)
        k_star1[x_c] = k_grid[max_ind1]
        k_star2[x_c] = k_grid[max_ind2]
    
    print('k_star1和k_star2统计:')
    print('-'*80)
    print(f'  k_star1最小值: {np.min(k_star1):.6f}')
    print(f'  k_star1最大值: {np.max(k_star1):.6f}')
    print(f'  k_star1平均值: {np.mean(k_star1):.6f}')
    print(f'  k_star2最小值: {np.min(k_star2):.6f}')
    print(f'  k_star2最大值: {np.max(k_star2):.6f}')
    print(f'  k_star2平均值: {np.mean(k_star2):.6f}')
    print('')
    
    print('k_star1 vs k_star2:')
    print('-'*80)
    print(f'  k_star1 < k_star2的点数: {np.sum(k_star1 < k_star2)} ({np.sum(k_star1 < k_star2)/nx*100:.2f}%)')
    print(f'  k_star1 = k_star2的点数: {np.sum(k_star1 == k_star2)} ({np.sum(k_star1 == k_star2)/nx*100:.2f}%)')
    print(f'  k_star1 > k_star2的点数: {np.sum(k_star1 > k_star2)} ({np.sum(k_star1 > k_star2)/nx*100:.2f}%)')
    print('')
    
    # 检查k_star与k_grid的关系
    k_min = np.min(k_grid)
    k_max = np.max(k_grid)
    
    print('k_star与k_grid的关系:')
    print('-'*80)
    print(f'  k_grid范围: [{k_min:.6f}, {k_max:.6f}]')
    print(f'  k_star1在k_grid范围内的点数: {np.sum((k_star1 >= k_min) & (k_star1 <= k_max))} ({nx})')
    print(f'  k_star2在k_grid范围内的点数: {np.sum((k_star2 >= k_min) & (k_star2 <= k_max))} ({nx})')
    print('')
    
    # 显示前几个x的k_star值
    print('前5个x的k_star值:')
    print('-'*80)
    for x_c in range(min(5, nx)):
        print(f'  x={x_c} (x_val={x_grid[x_c]:.6f}):')
        print(f'    k_star1={k_star1[x_c]:.6f}')
        print(f'    k_star2={k_star2[x_c]:.6f}')
        print(f'    k_star1/k_star2={k_star1[x_c]/k_star2[x_c]:.6f}' if k_star2[x_c] != 0 else '    k_star2=0')
    print('')


def check_pol_kp_unc_logic():
    """检查pol_kp_unc的计算逻辑"""
    
    print('\n' + '='*80)
    print('pol_kp_unc计算逻辑检查')
    print('='*80)
    print('')
    
    ss_results = load_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    if 'pol_kp_unc' not in sol or 'V1' not in sol:
        print('❌ 缺少pol_kp_unc或V1')
        return
    
    pol_kp_unc = sol['pol_kp_unc']
    V1 = sol['V1']
    k_grid = par.get('k_grid', None)
    x_grid = par.get('x_grid', None)
    pi_x = par.get('pi_x', None)
    
    if k_grid is None or x_grid is None or pi_x is None:
        print('❌ 缺少必要参数')
        return
    
    delta = par.get('delta_k', 0.015)
    theta = par.get('theta', 0.7)
    q = par.get('q', 0.99)
    psi = par.get('psi', 0.002)
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    if x_grid.ndim > 1:
        x_grid = x_grid.flatten()
    
    nk, nx = pol_kp_unc.shape
    
    # 重新计算k_star1和k_star2
    aux1 = -(1 - q * psi * theta * (1 - delta))
    aux2 = -(1 - q * psi * (1 - delta)) * theta
    kprime_vec = k_grid.flatten()
    
    k_star1 = np.zeros(nx)
    k_star2 = np.zeros(nx)
    
    for x_c in range(nx):
        EVx = np.zeros(nk)
        for xp_c in range(nx):
            EVx = EVx + pi_x[x_c, xp_c] * np.maximum(theta * (1 - delta) * kprime_vec, 
                                                     V1[:, xp_c])
        RHS1 = aux1 * kprime_vec + q * (1 - psi) * EVx
        RHS2 = aux2 * kprime_vec + q * (1 - psi) * EVx
        max_ind1 = np.argmax(RHS1)
        max_ind2 = np.argmax(RHS2)
        k_star1[x_c] = k_grid[max_ind1]
        k_star2[x_c] = k_grid[max_ind2]
    
    # 统计三种情况
    case1_count = 0  # (1-delta)*k > k_star2
    case2_count = 0  # k_star1 <= (1-delta)*k <= k_star2
    case3_count = 0  # (1-delta)*k < k_star1
    
    case1_investment = []  # 投资变化
    case2_investment = []
    case3_investment = []
    
    for x_c in range(nx):
        for k_c in range(nk):
            k_val = k_grid[k_c]
            k_depreciated = (1 - delta) * k_val
            pol_kp_val = pol_kp_unc[k_c, x_c]
            investment_change = pol_kp_val - k_depreciated
            
            if k_depreciated > k_star2[x_c]:
                case1_count += 1
                case1_investment.append(investment_change)
            elif k_depreciated >= k_star1[x_c] and k_depreciated <= k_star2[x_c]:
                case2_count += 1
                case2_investment.append(investment_change)
            else:
                case3_count += 1
                case3_investment.append(investment_change)
    
    print('pol_kp_unc三种情况的统计:')
    print('-'*80)
    print(f'  情况1 (k_dep > k_star2): {case1_count} ({case1_count/(nk*nx)*100:.2f}%)')
    print(f'    平均投资变化: {np.mean(case1_investment):.6f}' if case1_investment else '    无数据')
    print(f'  情况2 (k_star1 <= k_dep <= k_star2): {case2_count} ({case2_count/(nk*nx)*100:.2f}%)')
    print(f'    平均投资变化: {np.mean(case2_investment):.6f}' if case2_investment else '    无数据')
    print(f'  情况3 (k_dep < k_star1): {case3_count} ({case3_count/(nk*nx)*100:.2f}%)')
    print(f'    平均投资变化: {np.mean(case3_investment):.6f}' if case3_investment else '    无数据')
    print('')
    
    # 检查每种情况下的pol_kp_unc值
    print('每种情况下pol_kp_unc的值:')
    print('-'*80)
    if case1_count > 0:
        case1_pol_kp = []
        for x_c in range(nx):
            for k_c in range(nk):
                k_val = k_grid[k_c]
                k_depreciated = (1 - delta) * k_val
                if k_depreciated > k_star2[x_c]:
                    case1_pol_kp.append(pol_kp_unc[k_c, x_c])
        print(f'  情况1: pol_kp_unc应该等于k_star2')
        print(f'    实际平均值: {np.mean(case1_pol_kp):.6f}')
        print(f'    k_star2平均值: {np.mean(k_star2):.6f}')
        print(f'    差异: {np.mean(case1_pol_kp) - np.mean(k_star2):.6f}')
    
    if case2_count > 0:
        case2_pol_kp = []
        for x_c in range(nx):
            for k_c in range(nk):
                k_val = k_grid[k_c]
                k_depreciated = (1 - delta) * k_val
                if k_depreciated >= k_star1[x_c] and k_depreciated <= k_star2[x_c]:
                    case2_pol_kp.append(pol_kp_unc[k_c, x_c])
        print(f'  情况2: pol_kp_unc应该等于(1-delta)*k')
        print(f'    实际平均值: {np.mean(case2_pol_kp):.6f}')
        print(f'    (1-delta)*k平均值: {np.mean([(1-delta)*k_grid[k_c] for k_c in range(nk)]):.6f}')
    
    if case3_count > 0:
        case3_pol_kp = []
        for x_c in range(nx):
            for k_c in range(nk):
                k_val = k_grid[k_c]
                k_depreciated = (1 - delta) * k_val
                if k_depreciated < k_star1[x_c]:
                    case3_pol_kp.append(pol_kp_unc[k_c, x_c])
        print(f'  情况3: pol_kp_unc应该等于k_star1')
        print(f'    实际平均值: {np.mean(case3_pol_kp):.6f}')
        print(f'    k_star1平均值: {np.mean(k_star1):.6f}')
        print(f'    差异: {np.mean(case3_pol_kp) - np.mean(k_star1):.6f}')
    print('')


def check_RHS_values():
    """检查RHS1和RHS2的值"""
    
    print('\n' + '='*80)
    print('RHS1和RHS2检查')
    print('='*80)
    print('')
    
    ss_results = load_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    if 'V1' not in sol:
        print('❌ sol中没有V1')
        return
    
    V1 = sol['V1']
    k_grid = par.get('k_grid', None)
    x_grid = par.get('x_grid', None)
    pi_x = par.get('pi_x', None)
    
    if k_grid is None or x_grid is None or pi_x is None:
        print('❌ 缺少必要参数')
        return
    
    theta = par.get('theta', 0.7)
    delta = par.get('delta_k', 0.015)
    q = par.get('q', 0.99)
    psi = par.get('psi', 0.002)
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    if x_grid.ndim > 1:
        x_grid = x_grid.flatten()
    
    nk = len(k_grid)
    nx = len(x_grid)
    
    aux1 = -(1 - q * psi * theta * (1 - delta))
    aux2 = -(1 - q * psi * (1 - delta)) * theta
    kprime_vec = k_grid.flatten()
    
    # 检查第一个x的RHS值
    x_c = 0
    EVx = np.zeros(nk)
    for xp_c in range(nx):
        EVx = EVx + pi_x[x_c, xp_c] * np.maximum(theta * (1 - delta) * kprime_vec, 
                                                 V1[:, xp_c])
    RHS1 = aux1 * kprime_vec + q * (1 - psi) * EVx
    RHS2 = aux2 * kprime_vec + q * (1 - psi) * EVx
    
    print(f'对于x={x_c} (x_val={x_grid[x_c]:.6f}):')
    print('-'*80)
    print(f'  RHS1统计:')
    print(f'    最小值: {np.min(RHS1):.6f}')
    print(f'    最大值: {np.max(RHS1):.6f}')
    print(f'    平均值: {np.mean(RHS1):.6f}')
    print(f'    最大值位置: k_idx={np.argmax(RHS1)}, k={k_grid[np.argmax(RHS1)]:.6f}')
    print(f'  RHS2统计:')
    print(f'    最小值: {np.min(RHS2):.6f}')
    print(f'    最大值: {np.max(RHS2):.6f}')
    print(f'    平均值: {np.mean(RHS2):.6f}')
    print(f'    最大值位置: k_idx={np.argmax(RHS2)}, k={k_grid[np.argmax(RHS2)]:.6f}')
    print('')


if __name__ == '__main__':
    check_V1()
    check_k_star()
    check_pol_kp_unc_logic()
    check_RHS_values()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要检查项:')
    print('  1. V1的值和分布')
    print('  2. k_star1和k_star2的计算')
    print('  3. pol_kp_unc的计算逻辑')
    print('  4. RHS1和RHS2的值')
    print('\n如果发现异常，需要对比MATLAB代码和结果')




