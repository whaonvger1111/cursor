"""
直接测试pol_kp_unc的计算，验证逻辑是否正确
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))
from sub.sub_investment_onestep import sub_investment_onestep


def test_pol_kp_unc():
    """测试pol_kp_unc的计算"""
    
    print('='*80)
    print('直接测试pol_kp_unc计算')
    print('='*80)
    print('')
    
    # 加载数据
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    V1 = sol['V1']
    k_grid = par['k_grid']
    x_grid = par['x_grid']
    pi_x = par['pi_x']
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    if x_grid.ndim > 1:
        x_grid = x_grid.flatten()
    
    theta = par.get('theta', 0.7)
    delta = par.get('delta_k', 0.015)
    q = par.get('q', 0.99)
    psi = par.get('psi', 0.002)
    
    print('参数:')
    print(f'  theta={theta}, delta={delta}, q={q}, psi={psi}')
    print('')
    
    # 重新计算pol_kp_unc
    print('重新计算pol_kp_unc...')
    pol_kp_unc_recalc = sub_investment_onestep(V1, k_grid, pi_x, theta, delta, q, psi)
    
    # 获取保存的pol_kp_unc
    pol_kp_unc_saved = sol.get('pol_kp_unc', None)
    
    if pol_kp_unc_saved is not None:
        print('对比重新计算的和保存的pol_kp_unc:')
        print('-'*80)
        diff = np.abs(pol_kp_unc_recalc - pol_kp_unc_saved)
        print(f'  最大差异: {np.max(diff):.6f}')
        print(f'  平均差异: {np.mean(diff):.6f}')
        print(f'  差异>1e-6的点数: {np.sum(diff > 1e-6)}')
        print(f'  差异>1e-3的点数: {np.sum(diff > 1e-3)}')
        print('')
        
        if np.max(diff) > 1e-3:
            print('警告：重新计算的pol_kp_unc与保存的不一致！')
            print('  可能的原因：')
            print('    1. pol_kp_unc在保存后被修改')
            print('    2. 参数值不同')
            print('    3. V1的值不同')
        else:
            print('重新计算的pol_kp_unc与保存的一致')
    else:
        print('❌ sol中没有pol_kp_unc')
    
    print('')
    
    # 详细检查一个x值
    x_c = 0
    print(f'详细检查x={x_c} (x_val={x_grid[x_c]:.6f}):')
    print('-'*80)
    
    # 计算k_star1和k_star2
    aux1 = -(1 - q * psi * theta * (1 - delta))
    aux2 = -(1 - q * psi * (1 - delta)) * theta
    kprime_vec = k_grid.flatten()
    nk = len(k_grid)
    nx = len(x_grid)
    
    EVx = np.zeros(nk)
    for xp_c in range(nx):
        EVx = EVx + pi_x[x_c, xp_c] * np.maximum(theta * (1 - delta) * kprime_vec, 
                                                 V1[:, xp_c])
    RHS1 = aux1 * kprime_vec + q * (1 - psi) * EVx
    RHS2 = aux2 * kprime_vec + q * (1 - psi) * EVx
    max_ind1 = np.argmax(RHS1)
    max_ind2 = np.argmax(RHS2)
    k_star1 = k_grid[max_ind1]
    k_star2 = k_grid[max_ind2]
    
    print(f'  k_star1 = {k_star1:.6f} (k_idx={max_ind1})')
    print(f'  k_star2 = {k_star2:.6f} (k_idx={max_ind2})')
    print('')
    
    # 检查前几个k值的pol_kp_unc
    print('前10个k值的pol_kp_unc:')
    print('-'*80)
    print('  k_idx | k_val | (1-d)*k | k_star1 | k_star2 | pol_kp_unc | 情况')
    print('-'*80)
    for k_c in range(min(10, nk)):
        k_val = k_grid[k_c]
        k_dep = (1 - delta) * k_val
        pol_kp_val = pol_kp_unc_recalc[k_c, x_c]
        
        if k_dep > k_star2:
            case = '1: k_dep>k_star2, 应该=k_star2'
        elif k_dep >= k_star1 and k_dep <= k_star2:
            case = '2: k_star1<=k_dep<=k_star2, 应该=k_dep'
        else:
            case = '3: k_dep<k_star1, 应该=k_star1'
        
        expected = k_star2 if k_dep > k_star2 else (k_dep if k_dep >= k_star1 and k_dep <= k_star2 else k_star1)
        diff = abs(pol_kp_val - expected)
        
        print(f'  {k_c:5d} | {k_val:6.3f} | {k_dep:7.3f} | {k_star1:7.3f} | {k_star2:7.3f} | {pol_kp_val:10.3f} | {case}')
        if diff > 1e-3:
            print(f'        差异: {diff:.6f}, 应该={expected:.6f}')
    print('')


if __name__ == '__main__':
    test_pol_kp_unc()

