"""
检查pol_kp与MATLAB的差异
"""
import numpy as np
import pickle
import sys
import os

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


def check_pol_kp_statistics():
    """检查pol_kp的统计信息"""
    
    print('='*80)
    print('pol_kp统计信息检查')
    print('='*80)
    print('')
    
    ss_results = load_python_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    distribS = ss_results.get('distribS', {})
    
    if 'pol_kp' not in sol:
        print('❌ sol中没有pol_kp')
        return
    
    pol_kp = sol['pol_kp']
    k_grid = par.get('k_grid', None)
    mu_active = distribS.get('mu_active', None)
    
    if k_grid is None:
        print('❌ 未找到k_grid')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    
    nk, nb, nx = pol_kp.shape
    print(f'pol_kp维度: ({nk}, {nb}, {nx})')
    print('')
    
    # 计算当前资本
    k_arr = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
    
    # 计算投资变化
    delta_k = par.get('delta_k', 0.015)
    k_next_depreciated = (1 - delta_k) * k_arr
    investment_change = pol_kp - k_next_depreciated
    
    print('pol_kp统计信息:')
    print('-'*80)
    print(f'  pol_kp最小值: {np.min(pol_kp):.6f}')
    print(f'  pol_kp最大值: {np.max(pol_kp):.6f}')
    print(f'  pol_kp平均值: {np.mean(pol_kp):.6f}')
    print(f'  pol_kp中位数: {np.median(pol_kp):.6f}')
    print('')
    
    print('投资变化统计 (pol_kp - (1-delta)*k):')
    print('-'*80)
    print(f'  最小值: {np.min(investment_change):.6f}')
    print(f'  最大值: {np.max(investment_change):.6f}')
    print(f'  平均值: {np.mean(investment_change):.6f}')
    print(f'  中位数: {np.median(investment_change):.6f}')
    print('')
    
    # 统计向上和向下调整
    up_adjust = np.sum(investment_change > 0)
    down_adjust = np.sum(investment_change < 0)
    no_adjust = np.sum(investment_change == 0)
    
    print('投资方向统计:')
    print('-'*80)
    print(f'  向上调整点数: {up_adjust} ({up_adjust/(nk*nb*nx)*100:.2f}%)')
    print(f'  向下调整点数: {down_adjust} ({down_adjust/(nk*nb*nx)*100:.2f}%)')
    print(f'  无调整点数: {no_adjust} ({no_adjust/(nk*nb*nx)*100:.2f}%)')
    print('')
    
    # 如果有mu_active，计算加权统计
    if mu_active is not None:
        print('基于mu_active加权的统计:')
        print('-'*80)
        
        # 计算加权平均投资变化
        total_mass = np.sum(mu_active)
        if total_mass > 0:
            weighted_up = np.sum(np.maximum(investment_change, 0) * mu_active)
            weighted_down = np.sum(np.maximum(-investment_change, 0) * mu_active)
            
            print(f'  加权向上调整: {weighted_up:.6f}')
            print(f'  加权向下调整: {weighted_down:.6f}')
            print(f'  净投资变化: {weighted_up - weighted_down:.6f}')
            print('')
            
            # 找出投资变化最大的点
            abs_change = np.abs(investment_change)
            max_indices = np.unravel_index(np.argmax(abs_change * mu_active), abs_change.shape)
            k_idx, b_idx, x_idx = max_indices
            
            print('投资变化最大的点 (基于mu_active加权):')
            print('-'*80)
            print(f'  索引: (k={k_idx}, b={b_idx}, x={x_idx})')
            print(f'  当前资本 k: {k_arr[k_idx, b_idx, x_idx]:.6f}')
            print(f'  下一期资本 pol_kp: {pol_kp[k_idx, b_idx, x_idx]:.6f}')
            print(f'  投资变化: {investment_change[k_idx, b_idx, x_idx]:.6f}')
            print(f'  mu_active: {mu_active[k_idx, b_idx, x_idx]:.6f}')
            print('')
    
    # 检查pol_kp是否在合理范围内
    k_min = np.min(k_grid)
    k_max = np.max(k_grid)
    
    below_min = np.sum(pol_kp < k_min)
    above_max = np.sum(pol_kp > k_max)
    
    print('pol_kp范围检查:')
    print('-'*80)
    print(f'  k_grid范围: [{k_min:.6f}, {k_max:.6f}]')
    print(f'  小于k_min的点数: {below_min}')
    print(f'  大于k_max的点数: {above_max}')
    if below_min > 0 or above_max > 0:
        print('  ⚠️ 警告：pol_kp超出k_grid范围')
    print('')


def check_pol_kp_unc():
    """检查pol_kp_unc（无约束企业的资本政策）"""
    
    print('\n' + '='*80)
    print('pol_kp_unc检查')
    print('='*80)
    print('')
    
    ss_results = load_python_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    if 'pol_kp_unc' not in sol:
        print('❌ sol中没有pol_kp_unc')
        return
    
    pol_kp_unc = sol['pol_kp_unc']
    k_grid = par.get('k_grid', None)
    
    if k_grid is None:
        print('❌ 未找到k_grid')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    
    nk, nx = pol_kp_unc.shape
    print(f'pol_kp_unc维度: ({nk}, {nx})')
    print('')
    
    print('pol_kp_unc统计信息:')
    print('-'*80)
    print(f'  最小值: {np.min(pol_kp_unc):.6f}')
    print(f'  最大值: {np.max(pol_kp_unc):.6f}')
    print(f'  平均值: {np.mean(pol_kp_unc):.6f}')
    print(f'  中位数: {np.median(pol_kp_unc):.6f}')
    print('')
    
    # 检查与k_grid的关系
    k_arr = np.tile(k_grid[:, np.newaxis], (1, nx))
    delta_k = par.get('delta_k', 0.015)
    k_next_depreciated = (1 - delta_k) * k_arr
    investment_change = pol_kp_unc - k_next_depreciated
    
    print('pol_kp_unc投资变化统计:')
    print('-'*80)
    print(f'  最小值: {np.min(investment_change):.6f}')
    print(f'  最大值: {np.max(investment_change):.6f}')
    print(f'  平均值: {np.mean(investment_change):.6f}')
    print('')
    
    up_adjust = np.sum(investment_change > 0)
    down_adjust = np.sum(investment_change < 0)
    
    print(f'  向上调整点数: {up_adjust} ({up_adjust/(nk*nx)*100:.2f}%)')
    print(f'  向下调整点数: {down_adjust} ({down_adjust/(nk*nx)*100:.2f}%)')
    print('')


def check_pol_kp_vs_pol_kp_unc():
    """对比pol_kp和pol_kp_unc"""
    
    print('\n' + '='*80)
    print('pol_kp vs pol_kp_unc对比')
    print('='*80)
    print('')
    
    ss_results = load_python_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    distribS = ss_results.get('distribS', {})
    
    if 'pol_kp' not in sol or 'pol_kp_unc' not in sol:
        print('❌ 缺少pol_kp或pol_kp_unc')
        return
    
    pol_kp = sol['pol_kp']
    pol_kp_unc = sol['pol_kp_unc']
    B_hat = sol.get('B_hat', None)
    b_grid = ss_results.get('b_grid', None)
    
    if B_hat is None or b_grid is None:
        print('❌ 缺少B_hat或b_grid')
        return
    
    nk, nb, nx = pol_kp.shape
    
    # 检查无约束企业的pol_kp是否等于pol_kp_unc
    differences = []
    unconstrained_count = 0
    
    for k_c in range(nk):
        for b_c in range(nb):
            for x_c in range(nx):
                b_val = b_grid[k_c, b_c]
                if b_val <= B_hat[k_c, x_c]:  # 无约束企业
                    unconstrained_count += 1
                    diff = abs(pol_kp[k_c, b_c, x_c] - pol_kp_unc[k_c, x_c])
                    differences.append(diff)
    
    print(f'无约束企业数量: {unconstrained_count} / {nk*nb*nx}')
    print('')
    
    if differences:
        differences = np.array(differences)
        print('pol_kp与pol_kp_unc的差异（无约束企业）:')
        print('-'*80)
        print(f'  最大差异: {np.max(differences):.6f}')
        print(f'  平均差异: {np.mean(differences):.6f}')
        print(f'  中位数差异: {np.median(differences):.6f}')
        print(f'  差异>1e-6的点数: {np.sum(differences > 1e-6)}')
        print(f'  差异>1e-3的点数: {np.sum(differences > 1e-3)}')
        print('')
        
        if np.max(differences) > 1e-3:
            print('⚠️ 警告：无约束企业的pol_kp与pol_kp_unc差异较大')
            print('  这可能是因为pol_kp_unc不在k_grid上，需要投影到最近的网格点')
    else:
        print('未找到无约束企业')


def check_pol_kp_ind():
    """检查pol_kp_ind（资本政策索引）"""
    
    print('\n' + '='*80)
    print('pol_kp_ind检查')
    print('='*80)
    print('')
    
    ss_results = load_python_results()
    if ss_results is None:
        return
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    if 'pol_kp_ind' not in sol:
        print('❌ sol中没有pol_kp_ind')
        return
    
    pol_kp_ind = sol['pol_kp_ind']
    pol_kp = sol.get('pol_kp', None)
    k_grid = par.get('k_grid', None)
    
    if k_grid is None:
        print('❌ 未找到k_grid')
        return
    
    if k_grid.ndim > 1:
        k_grid = k_grid.flatten()
    
    nk, nb, nx = pol_kp_ind.shape
    print(f'pol_kp_ind维度: ({nk}, {nb}, {nx})')
    print('')
    
    # 检查索引范围
    invalid_low = np.sum(pol_kp_ind < 0)
    invalid_high = np.sum(pol_kp_ind >= nk)
    
    print('pol_kp_ind范围检查:')
    print('-'*80)
    print(f'  有效范围: [0, {nk-1}]')
    print(f'  小于0的点数: {invalid_low}')
    print(f'  大于等于{nk}的点数: {invalid_high}')
    if invalid_low > 0 or invalid_high > 0:
        print('  ⚠️ 警告：pol_kp_ind超出有效范围')
    print('')
    
    # 如果pol_kp存在，检查一致性
    if pol_kp is not None:
        print('pol_kp_ind与pol_kp一致性检查:')
        print('-'*80)
        
        # 从索引恢复pol_kp值
        pol_kp_from_ind = k_grid[pol_kp_ind]
        
        # 计算差异
        differences = np.abs(pol_kp - pol_kp_from_ind)
        
        print(f'  最大差异: {np.max(differences):.6f}')
        print(f'  平均差异: {np.mean(differences):.6f}')
        print(f'  差异>1e-3的点数: {np.sum(differences > 1e-3)}')
        print(f'  差异>1e-1的点数: {np.sum(differences > 1e-1)}')
        print('')
        
        if np.max(differences) > 1e-1:
            print('⚠️ 警告：pol_kp_ind与pol_kp不一致')
            print('  这可能表明索引计算有问题')


if __name__ == '__main__':
    check_pol_kp_statistics()
    check_pol_kp_unc()
    check_pol_kp_vs_pol_kp_unc()
    check_pol_kp_ind()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要检查项:')
    print('  1. pol_kp的统计信息和范围')
    print('  2. pol_kp_unc的统计信息')
    print('  3. pol_kp与pol_kp_unc的一致性（无约束企业）')
    print('  4. pol_kp_ind的有效性和一致性')
    print('\n如果发现异常，需要对比MATLAB代码实现')



