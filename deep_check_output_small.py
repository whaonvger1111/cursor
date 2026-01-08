"""
深入检查output_small过大的原因
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))
from fun import Fun


def check_prod_small_scaling():
    """检查prod_small是否有缩放问题"""
    
    print('='*80)
    print('prod_small缩放检查')
    print('='*80)
    print('')
    
    par = {
        'A': 0.25,
        'gamma1': 0.3182,
        'gamma2': 0.88,
    }
    
    # 检查不同规模企业的产出
    print('不同规模企业的产出检查:')
    print('-'*80)
    
    # 模拟典型的企业规模
    test_cases = [
        {'name': '小企业', 'kappa': 1.0, 'x': 1.0, 'wage': 0.275008},
        {'name': '中等企业', 'kappa': 10.0, 'x': 2.0, 'wage': 0.275008},
        {'name': '大企业', 'kappa': 100.0, 'x': 3.0, 'wage': 0.275008},
        {'name': '超大企业', 'kappa': 200.0, 'x': 3.5, 'wage': 0.275008},
    ]
    
    for case in test_cases:
        kappa = case['kappa']
        x = case['x']
        wage = case['wage']
        name = case['name']
        
        # 计算固定成本（假设fixcost1=0.165, fixcost2=0.0047）
        fixcost1 = 0.1652544033
        fixcost2 = 0.0047081982
        c = fixcost1 + fixcost2 * kappa
        
        # 计算劳动需求
        l = Fun.fun_l(x, wage, kappa, par)
        
        # 计算产出
        y = Fun.prod_small(x, kappa, l, c, par)
        
        print(f'{name}:')
        print(f'  kappa={kappa:.1f}, x={x:.1f}, l={l:.2f}, c={c:.3f}')
        print(f'  y={y:.6f}')
        print('')
    
    print('需要检查:')
    print('  1. 产出值是否合理')
    print('  2. 是否有单位转换问题')
    print('  3. 是否有参数缩放问题')


def check_mu_active_distribution():
    """详细检查mu_active分布"""
    
    print('\n' + '='*80)
    print('mu_active分布详细检查')
    print('='*80)
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results and 'par' in ss_results:
            mu_active = ss_results['distribS']['mu_active']
            par = ss_results['par']
            
            k_grid = par['k_grid']
            x_grid = par['x_grid']
            
            # 确保k_grid是一维的
            if k_grid.ndim > 1:
                k_grid = k_grid.flatten()
            
            nx = par['nx']
            nb = par['nb']
            nk = par['nk']
            
            print('\n分布按k维度汇总:')
            print('-'*80)
            mu_k = np.sum(mu_active, axis=(1, 2))  # (nk,)
            print(f'k维度总和: {np.sum(mu_k):.6f}')
            print(f'k维度最大值位置: k_idx={np.argmax(mu_k)}, k_val={k_grid[np.argmax(mu_k)]:.6f}')
            print(f'k维度最大值: {np.max(mu_k):.6e}')
            
            print('\n分布按x维度汇总:')
            print('-'*80)
            mu_x = np.sum(mu_active, axis=(0, 1))  # (nx,)
            print(f'x维度总和: {np.sum(mu_x):.6f}')
            print(f'x维度最大值位置: x_idx={np.argmax(mu_x)}, x_val={x_grid[np.argmax(mu_x)]:.6f}')
            print(f'x维度最大值: {np.max(mu_x):.6e}')
            
            print('\n分布按(k,x)维度汇总:')
            print('-'*80)
            mu_kx = np.sum(mu_active, axis=1)  # (nk, nx)
            max_kx_idx = np.unravel_index(np.argmax(mu_kx), mu_kx.shape)
            print(f'(k,x)维度最大值位置: k_idx={max_kx_idx[0]}, x_idx={max_kx_idx[1]}')
            print(f'  k_val={k_grid[max_kx_idx[0]]:.6f}, x_val={x_grid[max_kx_idx[1]]:.6f}')
            print(f'  最大值: {np.max(mu_kx):.6e}')
            
            # 检查高资本企业的分布
            print('\n高资本企业(k接近最大值)的分布:')
            print('-'*80)
            k_max_idx = nk - 1
            mu_k_max = mu_active[k_max_idx, :, :]  # (nb, nx)
            print(f'k_idx={k_max_idx}, k_val={k_grid[k_max_idx]:.6f}')
            print(f'  总和: {np.sum(mu_k_max):.6e}')
            print(f'  最大值: {np.max(mu_k_max):.6e}')
            print(f'  非零元素数量: {np.sum(mu_k_max > 0)}')
            
            # 检查高生产率企业的分布
            print('\n高生产率企业(x接近最大值)的分布:')
            print('-'*80)
            x_max_idx = nx - 1
            mu_x_max = mu_active[:, :, x_max_idx]  # (nk, nb)
            print(f'x_idx={x_max_idx}, x_val={x_grid[x_max_idx]:.6f}')
            print(f'  总和: {np.sum(mu_x_max):.6e}')
            print(f'  最大值: {np.max(mu_x_max):.6e}')
            print(f'  非零元素数量: {np.sum(mu_x_max > 0)}')
            
            # 检查最高产出企业的分布
            print('\n最高产出企业(k最大且x最大)的分布:')
            print('-'*80)
            mu_kx_max = mu_active[k_max_idx, :, x_max_idx]  # (nb,)
            print(f'k_idx={k_max_idx}, x_idx={x_max_idx}')
            print(f'  总和: {np.sum(mu_kx_max):.6e}')
            print(f'  最大值: {np.max(mu_kx_max):.6e}')
            print(f'  非零元素数量: {np.sum(mu_kx_max > 0)}')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def check_y_opt_values():
    """检查y_opt的值是否合理"""
    
    print('\n' + '='*80)
    print('y_opt值合理性检查')
    print('='*80)
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results and 'par' in ss_results and 'prices' in ss_results:
            mu_active = ss_results['distribS']['mu_active']
            par = ss_results['par']
            prices = ss_results['prices']
            
            k_grid = par['k_grid']
            x_grid = par['x_grid']
            fixcost = par['fixcost']
            wage = prices['wage']
            A = 1  # 稳态中A=1
            
            nx = par['nx']
            nb = par['nb']
            nk = par['nk']
            
            # 确保k_grid是一维的
            if k_grid.ndim > 1:
                k_grid = k_grid.flatten()
            if fixcost.ndim > 1:
                fixcost = fixcost.flatten()
            
            # 创建网格
            kappa = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
            c = np.tile(fixcost[:, np.newaxis, np.newaxis], (1, nb, nx))
            x_val = np.tile((A * x_grid)[np.newaxis, np.newaxis, :], (nk, nb, 1))
            
            # 计算产出
            l_opt = Fun.fun_l(x_val, wage, kappa, par)
            y_opt = Fun.prod_small(x_val, kappa, l_opt, c, par)
            
            print('\ny_opt统计:')
            print('-'*80)
            print(f'  平均值: {np.mean(y_opt):.6f}')
            print(f'  中位数: {np.median(y_opt):.6f}')
            print(f'  最大值: {np.max(y_opt):.6f}')
            print(f'  最小值: {np.min(y_opt):.6f}')
            print(f'  标准差: {np.std(y_opt):.6f}')
            print(f'  正值数量: {np.sum(y_opt > 0)}')
            print(f'  负值数量: {np.sum(y_opt < 0)}')
            
            # 检查最大值的位置
            max_y_idx = np.unravel_index(np.argmax(y_opt), y_opt.shape)
            print(f'\n最大值位置: (k={max_y_idx[0]}, b={max_y_idx[1]}, x={max_y_idx[2]})')
            print(f'  kappa: {kappa[max_y_idx]:.6f}')
            print(f'  x_val: {x_val[max_y_idx]:.6f}')
            print(f'  l_opt: {l_opt[max_y_idx]:.6f}')
            print(f'  c: {c[max_y_idx]:.6f}')
            print(f'  y_opt: {y_opt[max_y_idx]:.6f}')
            
            # 手动验证最大值
            print(f'\n手动验证最大值计算:')
            kappa_val = kappa[max_y_idx]
            x_val_val = x_val[max_y_idx]
            l_opt_val = l_opt[max_y_idx]
            c_val = c[max_y_idx]
            
            inner = (kappa_val ** par['gamma1']) * (l_opt_val ** (1 - par['gamma1']))
            y_manual = par['A'] * x_val_val * (inner ** par['gamma2']) - c_val
            print(f'  inner = ({kappa_val:.6f}^{par["gamma1"]:.4f}) * ({l_opt_val:.6f}^{1-par["gamma1"]:.4f})')
            print(f'  inner = {inner:.6f}')
            print(f'  y = {par["A"]:.6f} * {x_val_val:.6f} * ({inner:.6f}^{par["gamma2"]:.2f}) - {c_val:.6f}')
            print(f'  y = {y_manual:.6f}')
            print(f'  与y_opt的差异: {abs(y_manual - y_opt[max_y_idx]):.2e}')
            
            # 检查y_opt的分布
            print(f'\ny_opt分布分析:')
            print('-'*80)
            y_opt_flat = y_opt.flatten()
            y_opt_sorted = np.sort(y_opt_flat)[::-1]
            print(f'  前10个最大值: {y_opt_sorted[:10]}')
            print(f'  前10个最大值的平均值: {np.mean(y_opt_sorted[:10]):.6f}')
            
            # 检查y_opt与mu_active的乘积
            contribution = y_opt * mu_active
            print(f'\ncontribution = y_opt * mu_active统计:')
            print('-'*80)
            print(f'  总和: {np.sum(contribution):.6f}')
            print(f'  平均值: {np.mean(contribution):.6f}')
            print(f'  最大值: {np.max(contribution):.6f}')
            print(f'  最小值: {np.min(contribution):.6f}')
            
            # 检查贡献最大的点
            max_contrib_idx = np.unravel_index(np.argmax(np.abs(contribution)), contribution.shape)
            print(f'\n最大贡献点: (k={max_contrib_idx[0]}, b={max_contrib_idx[1]}, x={max_contrib_idx[2]})')
            print(f'  y_opt: {y_opt[max_contrib_idx]:.6f}')
            print(f'  mu_active: {mu_active[max_contrib_idx]:.6e}')
            print(f'  contribution: {contribution[max_contrib_idx]:.6f}')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def check_parameter_scaling():
    """检查是否有参数缩放问题"""
    
    print('\n' + '='*80)
    print('参数缩放检查')
    print('='*80)
    
    # 检查关键参数
    params_to_check = {
        'A': 0.25,
        'gamma1': 0.3182,
        'gamma2': 0.88,
        'alpha': 0.3,
        'delta_k': 0.015,
    }
    
    print('\n关键参数值:')
    print('-'*80)
    for key, value in params_to_check.items():
        print(f'  {key:10s} = {value:.6f}')
    
    print('\n检查是否有单位转换问题:')
    print('-'*80)
    print('  1. 检查A是否应该乘以某个缩放因子')
    print('  2. 检查kappa和labor的单位是否一致')
    print('  3. 检查x_grid的值是否合理')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'par' in ss_results:
            par = ss_results['par']
            
            print('\n网格值检查:')
            print('-'*80)
            if 'k_grid' in par:
                k_grid = par['k_grid']
                if k_grid.ndim > 1:
                    k_grid = k_grid.flatten()
                print(f'  k_grid范围: [{np.min(k_grid):.6f}, {np.max(k_grid):.6f}]')
                print(f'  k_grid平均值: {np.mean(k_grid):.6f}')
            
            if 'x_grid' in par:
                x_grid = par['x_grid']
                print(f'  x_grid范围: [{np.min(x_grid):.6f}, {np.max(x_grid):.6f}]')
                print(f'  x_grid平均值: {np.mean(x_grid):.6f}')
            
            if 'fixcost' in par:
                fixcost = par['fixcost']
                if fixcost.ndim > 1:
                    fixcost = fixcost.flatten()
                print(f'  fixcost范围: [{np.min(fixcost):.6f}, {np.max(fixcost):.6f}]')
                print(f'  fixcost平均值: {np.mean(fixcost):.6f}')
            
            if 'prices' in ss_results:
                prices = ss_results['prices']
                if 'wage' in prices:
                    print(f'  wage: {prices["wage"]:.6f}')
    
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def compare_with_matlab_expected():
    """与MATLAB预期值对比"""
    
    print('\n' + '='*80)
    print('与MATLAB预期值对比')
    print('='*80)
    
    # MATLAB结果
    matlab_output_small = 0.0639
    matlab_mu_active_sum = None  # 未知
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results and 'agg' in ss_results:
            mu_active = ss_results['distribS']['mu_active']
            output_small = ss_results['agg']['output_small']
            
            python_mu_active_sum = np.sum(mu_active)
            
            print('\n对比结果:')
            print('-'*80)
            print(f'  output_small:')
            print(f'    Python: {output_small:.6f}')
            print(f'    MATLAB: {matlab_output_small:.6f}')
            print(f'    差异: {output_small - matlab_output_small:.6f}')
            print(f'    差异倍数: {output_small / matlab_output_small:.2f}倍')
            
            print(f'\n  mu_active总和:')
            print(f'    Python: {python_mu_active_sum:.6f}')
            print(f'    MATLAB: 未知')
            
            if python_mu_active_sum > 0:
                avg_output_python = output_small / python_mu_active_sum
                print(f'\n  平均每个企业的产出:')
                print(f'    Python: {avg_output_python:.6f}')
                if matlab_output_small > 0:
                    # 假设MATLAB的mu_active总和与Python相似
                    avg_output_matlab_est = matlab_output_small / python_mu_active_sum
                    print(f'    MATLAB(估算): {avg_output_matlab_est:.6f}')
                    print(f'    差异倍数: {avg_output_python / avg_output_matlab_est:.2f}倍')
            
            # 分析差异
            print(f'\n差异分析:')
            print('-'*80)
            if output_small / matlab_output_small > 10:
                print('  output_small差异很大，可能原因:')
                print('    1. y_opt值过大')
                print('    2. mu_active分布集中在高产出企业')
                print('    3. 参数值不同')
                print('    4. 函数实现不同')
    
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


if __name__ == '__main__':
    check_prod_small_scaling()
    check_mu_active_distribution()
    check_y_opt_values()
    check_parameter_scaling()
    compare_with_matlab_expected()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要发现:')
    print('  1. 需要检查y_opt的值是否合理')
    print('  2. 需要检查mu_active分布是否合理')
    print('  3. 需要检查是否有参数缩放问题')
    print('  4. 需要对比MATLAB的mu_active分布和y_opt值')













