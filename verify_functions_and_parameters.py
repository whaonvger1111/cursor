"""
验证prod_small和fun_l函数的实现，以及参数值
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))
from fun import Fun


def verify_parameters():
    """验证参数值"""
    
    print('='*80)
    print('参数值验证')
    print('='*80)
    print('')
    
    # 从set_parameters.py中提取的参数
    params = {
        'A': 0.25,
        'gamma1': 0.3182,
        'gamma2': 0.88,
        'alpha': 0.3,
        'delta_k': 0.015,
    }
    
    print('Python参数值:')
    print('-'*80)
    for key, value in params.items():
        print(f'  {key:10s} = {value:.6f}')
    
    # 计算aux相关值
    aux = (1 - params['gamma1']) * params['gamma2']
    aux_minus_one = aux - 1
    print(f'\nfun_l函数中的辅助值:')
    print(f'  aux = (1 - gamma1) * gamma2 = (1 - {params["gamma1"]:.4f}) * {params["gamma2"]:.4f}')
    print(f'  aux = {aux:.6f}')
    print(f'  aux_minus_one = aux - 1 = {aux_minus_one:.6f}')
    
    print('\n' + '='*80)
    print('MATLAB参数值（从文档推断）')
    print('-'*80)
    print('  应该与Python相同（因为参数文件相同）')
    
    return params


def verify_prod_small():
    """验证prod_small函数实现"""
    
    print('\n' + '='*80)
    print('prod_small函数验证')
    print('='*80)
    
    par = {
        'A': 0.25,
        'gamma1': 0.3182,
        'gamma2': 0.88,
    }
    
    # 测试几个样本点
    test_cases = [
        {'x': 1.0, 'kappa': 1.0, 'labor': 1.0, 'c': 0.1, 'name': '小值'},
        {'x': 2.0, 'kappa': 10.0, 'labor': 5.0, 'c': 0.2, 'name': '中等值'},
        {'x': 4.0, 'kappa': 100.0, 'labor': 50.0, 'c': 1.0, 'name': '大值'},
    ]
    
    print('\nPython实现:')
    print('  y = A * x * ((kappa^gamma1) * (labor^(1-gamma1)))^gamma2 - c')
    print('')
    
    for case in test_cases:
        x = case['x']
        kappa = case['kappa']
        labor = case['labor']
        c = case['c']
        name = case['name']
        
        # Python计算
        y_python = Fun.prod_small(x, kappa, labor, c, par)
        
        # 手动计算验证
        inner = (kappa ** par['gamma1']) * (labor ** (1 - par['gamma1']))
        y_manual = par['A'] * x * (inner ** par['gamma2']) - c
        
        print(f'{name}测试点:')
        print(f'  x={x:.1f}, kappa={kappa:.1f}, labor={labor:.1f}, c={c:.1f}')
        print(f'  Python结果: {y_python:.6f}')
        print(f'  手动计算: {y_manual:.6f}')
        print(f'  差异: {abs(y_python - y_manual):.2e}')
        
        if abs(y_python - y_manual) < 1e-10:
            print('  [OK] 验证通过')
        else:
            print('  [X] 验证失败')
        print('')
    
    print('需要检查:')
    print('  1. 公式是否正确（与MATLAB一致）')
    print('  2. 参数值是否正确')


def verify_fun_l():
    """验证fun_l函数实现"""
    
    print('\n' + '='*80)
    print('fun_l函数验证')
    print('='*80)
    
    par = {
        'A': 0.25,
        'gamma1': 0.3182,
        'gamma2': 0.88,
    }
    
    wage = 0.275008  # 从之前的输出
    
    # 计算辅助值
    aux = (1 - par['gamma1']) * par['gamma2']
    aux_minus_one = aux - 1
    
    print(f'\n辅助值:')
    print(f'  aux = (1 - {par["gamma1"]:.4f}) * {par["gamma2"]:.4f} = {aux:.6f}')
    print(f'  aux_minus_one = {aux_minus_one:.6f}')
    
    # 测试几个样本点
    test_cases = [
        {'x': 1.0, 'k': 1.0, 'name': '小值'},
        {'x': 2.0, 'k': 10.0, 'name': '中等值'},
        {'x': 4.0, 'k': 100.0, 'name': '大值'},
    ]
    
    print('\nPython实现:')
    print('  l = (wage / (A * x * aux))^(1/aux_minus_one) * k^(-gamma1*gamma2/aux_minus_one)')
    print('')
    
    for case in test_cases:
        x = case['x']
        k = case['k']
        name = case['name']
        
        # Python计算
        l_python = Fun.fun_l(x, wage, k, par)
        
        # 手动计算验证
        denominator = par['A'] * x * aux
        exponent1 = 1 / aux_minus_one
        exponent2 = -par['gamma1'] * par['gamma2'] / aux_minus_one
        l_manual = (wage / denominator) ** exponent1 * (k ** exponent2)
        
        print(f'{name}测试点:')
        print(f'  x={x:.1f}, k={k:.1f}, wage={wage:.6f}')
        print(f'  Python结果: {l_python:.6f}')
        print(f'  手动计算: {l_manual:.6f}')
        print(f'  差异: {abs(l_python - l_manual):.2e}')
        
        if abs(l_python - l_manual) < 1e-10:
            print('  [OK] 验证通过')
        else:
            print('  [X] 验证失败')
        print('')
    
    print('需要检查:')
    print('  1. 公式是否正确（与MATLAB一致）')
    print('  2. 参数值是否正确')
    print('  3. 边界情况处理是否正确（aux_minus_one接近0的情况）')


def check_mu_active_calculation():
    """检查mu_active的计算"""
    
    print('\n' + '='*80)
    print('mu_active分布检查')
    print('='*80)
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results:
            mu_active = ss_results['distribS']['mu_active']
            mu = ss_results['distribS']['mu']
            
            print('\n分布统计:')
            print('-'*80)
            print(f'mu_active形状: {mu_active.shape}')
            print(f'mu_active总和: {np.sum(mu_active):.6f}')
            print(f'mu_active最大值: {np.max(mu_active):.6e}')
            print(f'mu_active最小值: {np.min(mu_active):.6e}')
            print(f'mu_active非零元素数量: {np.sum(mu_active > 0)}')
            print(f'mu_active负值数量: {np.sum(mu_active < 0)}')
            
            print(f'\nmu形状: {mu.shape}')
            print(f'mu总和: {np.sum(mu):.6f}')
            print(f'mu最大值: {np.max(mu):.6e}')
            print(f'mu最小值: {np.min(mu):.6e}')
            print(f'mu非零元素数量: {np.sum(mu > 0)}')
            print(f'mu负值数量: {np.sum(mu < 0)}')
            
            # 检查mu_active和mu的关系
            print(f'\nmu_active vs mu:')
            print(f'  mu_active总和 / mu总和 = {np.sum(mu_active) / np.sum(mu):.6f}')
            print(f'  mu_active <= mu: {np.all(mu_active <= mu + 1e-10)}')
            
            # 检查分布的主要集中区域
            print(f'\n分布的主要集中区域:')
            mu_active_flat = mu_active.flatten()
            sorted_idx = np.argsort(mu_active_flat)[::-1]
            top10_sum = np.sum(mu_active_flat[sorted_idx[:10]])
            print(f'  前10个最大值的总和: {top10_sum:.6f}')
            print(f'  占总和的比例: {top10_sum / np.sum(mu_active):.2%}')
            
            # 检查是否有异常大的值
            if np.max(mu_active) > 0.01:
                print(f'\n[WARN] 警告: mu_active最大值 ({np.max(mu_active):.6e}) 较大')
                max_idx = np.unravel_index(np.argmax(mu_active), mu_active.shape)
                print(f'  最大值位置: (k={max_idx[0]}, b={max_idx[1]}, x={max_idx[2]})')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        print('无法检查mu_active分布')


def check_output_small_scaling():
    """检查output_small的缩放问题"""
    
    print('\n' + '='*80)
    print('output_small缩放问题检查')
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
            
            # 计算output_small
            output_small = np.sum(y_opt * mu_active)
            
            print(f'\n计算结果:')
            print(f'  output_small = {output_small:.6f}')
            print(f'  mu_active总和 = {np.sum(mu_active):.6f}')
            print(f'  平均每个企业的产出 = {output_small / np.sum(mu_active):.6f}')
            
            print(f'\ny_opt统计:')
            print(f'  y_opt平均值 = {np.mean(y_opt):.6f}')
            print(f'  y_opt最大值 = {np.max(y_opt):.6f}')
            print(f'  y_opt最小值 = {np.min(y_opt):.6f}')
            print(f'  y_opt正值数量 = {np.sum(y_opt > 0)}')
            print(f'  y_opt负值数量 = {np.sum(y_opt < 0)}')
            
            # 检查贡献最大的点
            contribution = y_opt * mu_active
            contribution_flat = contribution.flatten()
            top10_idx = np.argsort(np.abs(contribution_flat))[-10:][::-1]
            
            print(f'\n前10个最大贡献点:')
            total_contrib = 0
            for i, idx in enumerate(top10_idx):
                contrib_val = contribution_flat[idx]
                total_contrib += contrib_val
                k_idx, b_idx, x_idx = np.unravel_index(idx, contribution.shape)
                print(f'  {i+1}. (k={k_idx:2d}, b={b_idx:2d}, x={x_idx:2d}): '
                      f'贡献={contrib_val:.6f}, '
                      f'y_opt={y_opt[k_idx, b_idx, x_idx]:.6f}, '
                      f'mu_active={mu_active[k_idx, b_idx, x_idx]:.6e}')
            
            print(f'\n前10个点的总贡献: {total_contrib:.6f}')
            print(f'占总output_small的比例: {total_contrib / output_small:.2%}')
            
            # 检查是否有异常大的y_opt值
            if np.max(y_opt) > 100:
                print(f'\n[WARN] 警告: y_opt最大值 ({np.max(y_opt):.6f}) 非常大')
                max_y_idx = np.unravel_index(np.argmax(y_opt), y_opt.shape)
                print(f'  最大值位置: (k={max_y_idx[0]}, b={max_y_idx[1]}, x={max_y_idx[2]})')
                print(f'  对应的kappa: {kappa[max_y_idx]:.6f}')
                print(f'  对应的x_val: {x_val[max_y_idx]:.6f}')
                print(f'  对应的l_opt: {l_opt[max_y_idx]:.6f}')
                print(f'  对应的c: {c[max_y_idx]:.6f}')
                print(f'  对应的mu_active: {mu_active[max_y_idx]:.6e}')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        print('无法检查output_small缩放问题')


if __name__ == '__main__':
    params = verify_parameters()
    verify_prod_small()
    verify_fun_l()
    check_mu_active_calculation()
    check_output_small_scaling()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要发现:')
    print('  1. 参数值: A=0.25, gamma1=0.3182, gamma2=0.88')
    print('  2. prod_small和fun_l函数的实现需要与MATLAB对比')
    print('  3. output_small过大可能是由于:')
    print('     - mu_active分布集中在高产出企业')
    print('     - y_opt值过大')
    print('     - 生产函数计算错误')
    print('\n建议:')
    print('  1. 对比MATLAB代码中的prod_small和fun_l实现')
    print('  2. 检查参数值是否与MATLAB一致')
    print('  3. 检查mu_active分布的计算是否正确')

