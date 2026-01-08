"""
检查fun_vfi1.py中pol_kp_unc和pol_kp的计算过程
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))


def load_results():
    """加载结果"""
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        return ss_results
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        return None


def check_fun_vfi1_pol_kp_unc():
    """检查fun_vfi1中pol_kp_unc的计算"""
    
    print('='*80)
    print('检查fun_vfi1.py中pol_kp_unc的计算')
    print('='*80)
    print('')
    
    ss_results = load_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    # 获取关键变量
    V1 = sol.get('V1', None)
    pol_kp_unc = sol.get('pol_kp_unc', None)
    k_grid = par.get('k_grid', None)
    x_grid = par.get('x_grid', None)
    pi_x = par.get('pi_x', None)
    
    if V1 is None or pol_kp_unc is None:
        print('缺少V1或pol_kp_unc')
        return
    
    # 获取参数
    theta = par.get('theta', 0.7)
    delta = par.get('delta_k', 0.015)
    q = par.get('q', 0.99)
    psi = par.get('psi', 0.002)
    
    print('参数值:')
    print('-'*80)
    print(f'  theta = {theta:.6f}')
    print(f'  delta_k = {delta:.6f}')
    print(f'  q = {q:.6f}')
    print(f'  psi = {psi:.6f}')
    print('')
    
    print('V1统计:')
    print('-'*80)
    print(f'  形状: {V1.shape}')
    print(f'  范围: [{np.min(V1):.6f}, {np.max(V1):.6f}]')
    print(f'  平均值: {np.mean(V1):.6f}')
    print('')
    
    print('pol_kp_unc统计:')
    print('-'*80)
    print(f'  形状: {pol_kp_unc.shape}')
    print(f'  范围: [{np.min(pol_kp_unc):.6f}, {np.max(pol_kp_unc):.6f}]')
    print(f'  平均值: {np.mean(pol_kp_unc):.6f}')
    print('')
    
    # 重新计算pol_kp_unc
    from sub.sub_investment_onestep import sub_investment_onestep
    
    if k_grid is None or x_grid is None or pi_x is None:
        print('缺少k_grid、x_grid或pi_x')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    if x_grid.ndim > 1:
        x_grid = x_grid.flatten()
    
    print('重新计算pol_kp_unc...')
    pol_kp_unc_recalc = sub_investment_onestep(V1, k_grid, pi_x, theta, delta, q, psi)
    
    print('重新计算的pol_kp_unc统计:')
    print('-'*80)
    print(f'  形状: {pol_kp_unc_recalc.shape}')
    print(f'  范围: [{np.min(pol_kp_unc_recalc):.6f}, {np.max(pol_kp_unc_recalc):.6f}]')
    print(f'  平均值: {np.mean(pol_kp_unc_recalc):.6f}')
    print('')
    
    # 对比
    diff = np.abs(pol_kp_unc - pol_kp_unc_recalc)
    print('保存的vs重新计算的差异:')
    print('-'*80)
    print(f'  最大差异: {np.max(diff):.6f}')
    print(f'  平均差异: {np.mean(diff):.6f}')
    print(f'  差异>1e-3的点数: {np.sum(diff > 1e-3)} ({np.sum(diff > 1e-3)/diff.size*100:.2f}%)')
    print('')


def check_pol_kp_details():
    """检查pol_kp的详细信息"""
    
    print('\n' + '='*80)
    print('检查pol_kp的详细信息')
    print('='*80)
    print('')
    
    ss_results = load_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    distribS = ss_results.get('distribS', {})
    
    pol_kp = sol.get('pol_kp', None)
    pol_kp_unc = sol.get('pol_kp_unc', None)
    B_hat = sol.get('B_hat', None)
    b_grid = ss_results.get('b_grid', None)
    
    if pol_kp is None:
        print('缺少pol_kp')
        return
    
    k_grid = par.get('k_grid', None)
    if k_grid is None:
        print('缺少k_grid')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    
    nk, nb, nx = pol_kp.shape
    delta = par.get('delta_k', 0.015)
    mu_active = distribS.get('mu_active', None)
    
    print('pol_kp统计:')
    print('-'*80)
    print(f'  形状: {pol_kp.shape}')
    print(f'  范围: [{np.min(pol_kp):.6f}, {np.max(pol_kp):.6f}]')
    print(f'  平均值: {np.mean(pol_kp):.6f}')
    print('')
    
    # 计算投资变化
    k_arr = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
    investment_change = pol_kp - (1 - delta) * k_arr
    
    print('投资变化统计:')
    print('-'*80)
    print(f'  最小值: {np.min(investment_change):.6f}')
    print(f'  最大值: {np.max(investment_change):.6f}')
    print(f'  平均值: {np.mean(investment_change):.6f}')
    print('')
    
    up_count = np.sum(investment_change > 0)
    down_count = np.sum(investment_change < 0)
    no_change = np.sum(investment_change == 0)
    
    print('投资方向:')
    print('-'*80)
    print(f'  向上调整: {up_count} ({up_count/(nk*nb*nx)*100:.2f}%)')
    print(f'  向下调整: {down_count} ({down_count/(nk*nb*nx)*100:.2f}%)')
    print(f'  无变化: {no_change} ({no_change/(nk*nb*nx)*100:.2f}%)')
    print('')
    
    # 如果有mu_active，计算加权统计
    if mu_active is not None:
        weighted_up = np.sum(np.maximum(investment_change, 0) * mu_active)
        weighted_down = np.sum(np.maximum(-investment_change, 0) * mu_active)
        
        print('加权投资变化:')
        print('-'*80)
        print(f'  加权向上: {weighted_up:.6f}')
        print(f'  加权向下: {weighted_down:.6f}')
        print(f'  净投资: {weighted_up - weighted_down:.6f}')
        print('')
    
    # 检查无约束企业的pol_kp
    if pol_kp_unc is not None and B_hat is not None and b_grid is not None:
        print('无约束企业的pol_kp检查:')
        print('-'*80)
        
        unconstrained_count = 0
        differences = []
        
        for k_c in range(nk):
            for b_c in range(nb):
                for x_c in range(nx):
                    b_val = b_grid[k_c, b_c]
                    if b_val <= B_hat[k_c, x_c]:
                        unconstrained_count += 1
                        diff = abs(pol_kp[k_c, b_c, x_c] - pol_kp_unc[k_c, x_c])
                        differences.append(diff)
        
        print(f'  无约束企业数量: {unconstrained_count} / {nk*nb*nx}')
        if differences:
            differences = np.array(differences)
            print(f'  pol_kp与pol_kp_unc的最大差异: {np.max(differences):.6f}')
            print(f'  平均差异: {np.mean(differences):.6f}')
            print(f'  差异>1e-3的点数: {np.sum(differences > 1e-3)}')
        print('')


def check_pol_kp_ind_con():
    """检查pol_kp_ind_con（约束企业的资本政策索引）"""
    
    print('\n' + '='*80)
    print('检查pol_kp_ind_con')
    print('='*80)
    print('')
    
    ss_results = load_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    # pol_kp_ind_con不在sol中，需要从sub_vfi_onestep的输出中获取
    # 但我们可以检查pol_kp_ind
    pol_kp_ind = sol.get('pol_kp_ind', None)
    pol_kp = sol.get('pol_kp', None)
    
    if pol_kp_ind is None or pol_kp is None:
        print('缺少pol_kp_ind或pol_kp')
        return
    
    k_grid = par.get('k_grid', None)
    if k_grid is None:
        print('缺少k_grid')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    
    print('pol_kp_ind统计:')
    print('-'*80)
    print(f'  形状: {pol_kp_ind.shape}')
    print(f'  范围: [{np.min(pol_kp_ind)}, {np.max(pol_kp_ind)}]')
    print(f'  平均值: {np.mean(pol_kp_ind):.6f}')
    print('')
    
    # 检查pol_kp_ind与pol_kp的一致性
    pol_kp_from_ind = k_grid[pol_kp_ind]
    diff = np.abs(pol_kp - pol_kp_from_ind)
    
    print('pol_kp_ind与pol_kp的一致性:')
    print('-'*80)
    print(f'  最大差异: {np.max(diff):.6f}')
    print(f'  平均差异: {np.mean(diff):.6f}')
    print(f'  差异>1e-3的点数: {np.sum(diff > 1e-3)} ({np.sum(diff > 1e-3)/diff.size*100:.2f}%)')
    print(f'  差异>1的点数: {np.sum(diff > 1)} ({np.sum(diff > 1)/diff.size*100:.2f}%)')
    print('')
    
    if np.max(diff) > 1:
        print('警告：pol_kp_ind与pol_kp不一致！')
        print('  这可能是因为pol_kp_unc不在k_grid上，需要投影到最近的网格点')


if __name__ == '__main__':
    check_fun_vfi1_pol_kp_unc()
    check_pol_kp_details()
    check_pol_kp_ind_con()
    
    print('\n' + '='*80)
    print('检查完成')
    print('='*80)




