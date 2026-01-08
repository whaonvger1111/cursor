"""
综合检查所有可能的问题
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))
from fun import Fun


def check_unit_scaling():
    """检查是否有单位缩放问题"""
    
    print('='*80)
    print('单位缩放检查')
    print('='*80)
    print('')
    
    # 检查关键变量的数量级
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'par' in ss_results and 'prices' in ss_results and 'agg' in ss_results:
            par = ss_results['par']
            prices = ss_results['prices']
            agg = ss_results['agg']
            
            print('关键变量的数量级:')
            print('-'*80)
            print(f'  wage: {prices.get("wage", 0):.6f}')
            print(f'  C_agg: {agg.get("C_agg", 0):.6f}')
            print(f'  output_small: {agg.get("output_small", 0):.6f}')
            print(f'  K_small: {agg.get("K_small", 0):.6f}')
            print(f'  L_small: {agg.get("L_small", 0):.6f}')
            
            # 检查比例关系
            if agg.get('output_small', 0) > 0 and agg.get('K_small', 0) > 0:
                output_per_k = agg.get('output_small', 0) / agg.get('K_small', 0)
                print(f'\n  output_small / K_small = {output_per_k:.6f}')
            
            if agg.get('output_small', 0) > 0 and agg.get('L_small', 0) > 0:
                output_per_l = agg.get('output_small', 0) / agg.get('L_small', 0)
                print(f'  output_small / L_small = {output_per_l:.6f}')
            
            # MATLAB对比
            print(f'\nMATLAB对比:')
            print(f'  output_small / K_small ≈ 0.0639 / (未知K_small)')
            print(f'  output_small / L_small ≈ 0.0639 / (未知L_small)')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def check_prod_small_with_matlab_values():
    """使用MATLAB的典型值检查prod_small"""
    
    print('\n' + '='*80)
    print('使用MATLAB典型值检查prod_small')
    print('='*80)
    
    par = {
        'A': 0.25,
        'gamma1': 0.3182,
        'gamma2': 0.88,
    }
    
    # 假设MATLAB的典型企业规模
    # 从MATLAB结果推断：output_small = 0.0639, mu_active总和未知
    # 假设平均企业产出约为1-2
    
    print('\n假设MATLAB的典型企业:')
    print('-'*80)
    
    # 尝试不同的企业规模
    test_cases = [
        {'name': '小企业', 'kappa': 0.5, 'x': 1.0, 'wage': 0.275008},
        {'name': '中等企业', 'kappa': 2.0, 'x': 1.5, 'wage': 0.275008},
        {'name': '大企业', 'kappa': 10.0, 'x': 2.0, 'wage': 0.275008},
    ]
    
    for case in test_cases:
        kappa = case['kappa']
        x = case['x']
        wage = case['wage']
        name = case['name']
        
        # 计算固定成本
        fixcost1 = 0.1652544033
        fixcost2 = 0.0047081982
        c = fixcost1 + fixcost2 * kappa
        
        # 计算劳动需求
        l = Fun.fun_l(x, wage, kappa, par)
        
        # 计算产出
        y = Fun.prod_small(x, kappa, l, c, par)
        
        print(f'{name}:')
        print(f'  kappa={kappa:.1f}, x={x:.1f}, l={l:.3f}, c={c:.4f}')
        print(f'  y={y:.6f}')
        
        if 0.5 < y < 5.0:
            print(f'  [OK] 产出值在合理范围内')
        elif y > 10:
            print(f'  [WARN] 产出值较大')
        print('')
    
    print('如果MATLAB的平均企业产出约为1-2，')
    print('那么Python的y_opt平均值9.24可能过大')


def check_mu_active_normalization():
    """检查mu_active的归一化"""
    
    print('\n' + '='*80)
    print('mu_active归一化检查')
    print('='*80)
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results:
            mu_active = ss_results['distribS']['mu_active']
            mu = ss_results['distribS']['mu']
            
            print('\n分布统计:')
            print('-'*80)
            print(f'mu_active总和: {np.sum(mu_active):.6f}')
            print(f'mu总和: {np.sum(mu):.6f}')
            print(f'mu_active / mu = {np.sum(mu_active) / np.sum(mu):.6f}')
            
            # 检查是否有归一化问题
            print('\n归一化检查:')
            print('-'*80)
            print('mu_active应该 <= mu (活跃企业 <= 总企业)')
            violations = np.sum(mu_active > mu + 1e-10)
            print(f'违反mu_active <= mu的点数: {violations}')
            
            if violations > 0:
                print(f'\n[WARN] 警告: 有{violations}个点违反mu_active <= mu')
                max_violation_idx = np.unravel_index(np.argmax(mu_active - mu), mu_active.shape)
                print(f'最大违反点: (k={max_violation_idx[0]}, b={max_violation_idx[1]}, x={max_violation_idx[2]})')
                print(f'  mu_active = {mu_active[max_violation_idx]:.6e}')
                print(f'  mu = {mu[max_violation_idx]:.6e}')
                print(f'  差异 = {mu_active[max_violation_idx] - mu[max_violation_idx]:.6e}')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def check_k_grid_scaling():
    """检查k_grid的缩放"""
    
    print('\n' + '='*80)
    print('k_grid缩放检查')
    print('='*80)
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'par' in ss_results:
            par = ss_results['par']
            k_grid = par['k_grid']
            
            if k_grid.ndim > 1:
                k_grid = k_grid.flatten()
            
            print('\nk_grid统计:')
            print('-'*80)
            print(f'  最小值: {np.min(k_grid):.6f}')
            print(f'  最大值: {np.max(k_grid):.6f}')
            print(f'  平均值: {np.mean(k_grid):.6f}')
            print(f'  中位数: {np.median(k_grid):.6f}')
            print(f'  网格点数: {len(k_grid)}')
            
            # 检查是否有缩放问题
            print('\n缩放检查:')
            print('-'*80)
            print('如果k_grid的值过大，可能导致产出过大')
            print('需要对比MATLAB的k_grid范围')
            
            # 检查k_grid的最大值是否合理
            if np.max(k_grid) > 1000:
                print(f'\n⚠️  警告: k_grid最大值 ({np.max(k_grid):.6f}) 很大')
            elif np.max(k_grid) > 100:
                print(f'\n[INFO] k_grid最大值 ({np.max(k_grid):.6f}) 较大')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def check_x_grid_scaling():
    """检查x_grid的缩放"""
    
    print('\n' + '='*80)
    print('x_grid缩放检查')
    print('='*80)
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'par' in ss_results:
            par = ss_results['par']
            x_grid = par['x_grid']
            
            print('\nx_grid统计:')
            print('-'*80)
            print(f'  最小值: {np.min(x_grid):.6f}')
            print(f'  最大值: {np.max(x_grid):.6f}')
            print(f'  平均值: {np.mean(x_grid):.6f}')
            print(f'  中位数: {np.median(x_grid):.6f}')
            print(f'  网格点数: {len(x_grid)}')
            
            # 检查x0参数
            if 'x0' in par:
                print(f'\n  x0参数: {par["x0"]:.6f}')
                print(f'  x_grid平均值 / x0 = {np.mean(x_grid) / par["x0"]:.6f}')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def check_A_parameter():
    """检查A参数的使用"""
    
    print('\n' + '='*80)
    print('A参数检查')
    print('='*80)
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'par' in ss_results:
            par = ss_results['par']
            
            print('\nA参数值:')
            print('-'*80)
            print(f'  A (企业部门TFP) = {par.get("A", "N/A")}')
            
            # 检查prod_small中A的使用
            print('\nprod_small中A的使用:')
            print('-'*80)
            print('  y = A * x * ((kappa^gamma1) * (labor^(1-gamma1)))^gamma2 - c')
            print('  其中A = 0.25')
            print('')
            print('需要检查:')
            print('  1. MATLAB是否使用相同的A值')
            print('  2. 是否有A的缩放因子')
            print('  3. 是否有单位转换问题')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


if __name__ == '__main__':
    check_unit_scaling()
    check_prod_small_with_matlab_values()
    check_mu_active_normalization()
    check_k_grid_scaling()
    check_x_grid_scaling()
    check_A_parameter()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要发现:')
    print('  1. 需要检查是否有单位缩放问题')
    print('  2. 需要检查k_grid和x_grid的值是否合理')
    print('  3. 需要检查A参数的使用是否正确')
    print('  4. 需要对比MATLAB的所有相关值')

