"""
深入调查output_small过大问题
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))
from fun import Fun


def analyze_output_small_calculation():
    """分析output_small的计算过程"""
    
    print('='*80)
    print('output_small计算过程详细分析')
    print('='*80)
    print('')
    
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
            
            print('1. 基本参数')
            print('-'*80)
            print(f'A (稳态中=1): {A}')
            print(f'wage: {wage:.6f}')
            print(f'k_grid范围: [{np.min(k_grid):.6f}, {np.max(k_grid):.6f}]')
            print(f'x_grid范围: [{np.min(x_grid):.6f}, {np.max(x_grid):.6f}]')
            print(f'fixcost范围: [{np.min(fixcost):.6f}, {np.max(fixcost):.6f}]')
            print(f'mu_active总和: {np.sum(mu_active):.6f}')
            print('')
            
            # 创建网格
            kappa = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
            c = np.tile(fixcost[:, np.newaxis, np.newaxis], (1, nb, nx))
            x_val = np.tile((A * x_grid)[np.newaxis, np.newaxis, :], (nk, nb, 1))
            
            # 计算劳动需求
            print('2. 计算劳动需求 l_opt')
            print('-'*80)
            l_opt = Fun.fun_l(x_val, wage, kappa, par)
            print(f'l_opt范围: [{np.min(l_opt):.6f}, {np.max(l_opt):.6f}]')
            print(f'l_opt平均值: {np.mean(l_opt):.6f}')
            print(f'l_opt中位数: {np.median(l_opt):.6f}')
            print('')
            
            # 计算产出
            print('3. 计算产出 y_opt')
            print('-'*80)
            y_opt = Fun.prod_small(x_val, kappa, l_opt, c, par)
            print(f'y_opt范围: [{np.min(y_opt):.6f}, {np.max(y_opt):.6f}]')
            print(f'y_opt平均值: {np.mean(y_opt):.6f}')
            print(f'y_opt中位数: {np.median(y_opt):.6f}')
            print(f'y_opt正值数量: {np.sum(y_opt > 0)}')
            print(f'y_opt负值数量: {np.sum(y_opt < 0)}')
            print('')
            
            # 计算output_small
            print('4. 计算output_small')
            print('-'*80)
            contribution = y_opt * mu_active
            output_small = np.sum(contribution)
            print(f'output_small = sum(y_opt * mu_active) = {output_small:.6f}')
            print(f'contribution范围: [{np.min(contribution):.6f}, {np.max(contribution):.6f}]')
            print(f'contribution平均值: {np.mean(contribution):.6f}')
            print('')
            
            # 分析贡献最大的点
            print('5. 贡献最大的前20个点')
            print('-'*80)
            contribution_flat = contribution.flatten()
            top20_idx = np.argsort(np.abs(contribution_flat))[-20:][::-1]
            
            total_top20 = 0
            for i, idx in enumerate(top20_idx):
                contrib_val = contribution_flat[idx]
                total_top20 += contrib_val
                k_idx, b_idx, x_idx = np.unravel_index(idx, contribution.shape)
                y_val = y_opt[k_idx, b_idx, x_idx]
                mu_val = mu_active[k_idx, b_idx, x_idx]
                kappa_val = kappa[k_idx, b_idx, x_idx]
                x_val_val = x_val[k_idx, b_idx, x_idx]
                l_val = l_opt[k_idx, b_idx, x_idx]
                c_val = c[k_idx, b_idx, x_idx]
                
                print(f'{i+1:2d}. (k={k_idx:2d}, b={b_idx:2d}, x={x_idx:2d}): '
                      f'贡献={contrib_val:.6f}, '
                      f'y_opt={y_val:.2f}, '
                      f'mu_active={mu_val:.6e}, '
                      f'kappa={kappa_val:.2f}, '
                      f'x={x_val_val:.3f}, '
                      f'l={l_val:.2f}, '
                      f'c={c_val:.3f}')
            
            print(f'\n前20个点的总贡献: {total_top20:.6f}')
            print(f'占总output_small的比例: {total_top20 / output_small * 100:.2f}%')
            print('')
            
            # 分析y_opt的分布
            print('6. y_opt分布分析')
            print('-'*80)
            y_opt_flat = y_opt.flatten()
            y_opt_sorted = np.sort(y_opt_flat)[::-1]
            
            print(f'y_opt前10个最大值: {y_opt_sorted[:10]}')
            print(f'y_opt前10个最大值的平均值: {np.mean(y_opt_sorted[:10]):.6f}')
            
            # 检查是否有异常大的y_opt值
            if np.max(y_opt) > 50:
                print(f'\n[WARN] y_opt最大值 ({np.max(y_opt):.6f}) 很大')
                max_y_idx = np.unravel_index(np.argmax(y_opt), y_opt.shape)
                print(f'最大值位置: (k={max_y_idx[0]}, b={max_y_idx[1]}, x={max_y_idx[2]})')
                print(f'  kappa: {kappa[max_y_idx]:.6f}')
                print(f'  x_val: {x_val[max_y_idx]:.6f}')
                print(f'  l_opt: {l_opt[max_y_idx]:.6f}')
                print(f'  c: {c[max_y_idx]:.6f}')
                
                # 手动验证
                kappa_val = kappa[max_y_idx]
                x_val_val = x_val[max_y_idx]
                l_val = l_opt[max_y_idx]
                c_val = c[max_y_idx]
                
                inner = (kappa_val ** par['gamma1']) * (l_val ** (1 - par['gamma1']))
                y_manual = par['A'] * x_val_val * (inner ** par['gamma2']) - c_val
                print(f'\n手动验证:')
                print(f'  inner = ({kappa_val:.6f}^{par["gamma1"]:.4f}) * ({l_val:.6f}^{1-par["gamma1"]:.4f}) = {inner:.6f}')
                print(f'  y = {par["A"]:.6f} * {x_val_val:.6f} * ({inner:.6f}^{par["gamma2"]:.2f}) - {c_val:.6f}')
                print(f'  y = {y_manual:.6f}')
                print(f'  与y_opt的差异: {abs(y_manual - y_opt[max_y_idx]):.2e}')
            
            # 分析mu_active的分布
            print(f'\n7. mu_active分布分析')
            print('-'*80)
            mu_active_flat = mu_active.flatten()
            mu_active_sorted = np.sort(mu_active_flat)[::-1]
            
            print(f'mu_active前10个最大值: {mu_active_sorted[:10]}')
            print(f'mu_active前10个最大值的总和: {np.sum(mu_active_sorted[:10]):.6f}')
            print(f'占总mu_active的比例: {np.sum(mu_active_sorted[:10]) / np.sum(mu_active) * 100:.2f}%')
            
            # 检查高产出企业的mu_active
            high_y_mask = y_opt > np.percentile(y_opt[y_opt > 0], 90)
            high_y_mu_active = np.sum(mu_active[high_y_mask])
            print(f'\n高产出企业(y_opt > 90分位数)的mu_active总和: {high_y_mu_active:.6f}')
            print(f'占总mu_active的比例: {high_y_mu_active / np.sum(mu_active) * 100:.2f}%')
            
            # 对比MATLAB
            print(f'\n8. 与MATLAB对比')
            print('-'*80)
            matlab_output_small = 0.0639
            print(f'Python output_small: {output_small:.6f}')
            print(f'MATLAB output_small: {matlab_output_small:.6f}')
            print(f'差异: {output_small - matlab_output_small:.6f}')
            print(f'差异倍数: {output_small / matlab_output_small:.2f}倍')
            
            # 如果MATLAB的mu_active总和已知，可以计算平均产出
            # 假设MATLAB的mu_active总和与Python相似
            python_mu_active_sum = np.sum(mu_active)
            python_avg_output = output_small / python_mu_active_sum
            matlab_avg_output_est = matlab_output_small / python_mu_active_sum
            print(f'\n平均每个企业的产出:')
            print(f'  Python: {python_avg_output:.6f}')
            print(f'  MATLAB(估算): {matlab_avg_output_est:.6f}')
            print(f'  差异倍数: {python_avg_output / matlab_avg_output_est:.2f}倍')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()


def check_prod_small_parameters():
    """检查prod_small函数的参数值"""
    
    print('\n' + '='*80)
    print('prod_small函数参数检查')
    print('='*80)
    print('')
    
    par = {
        'A': 0.25,
        'gamma1': 0.3182,
        'gamma2': 0.88,
    }
    
    print('参数值:')
    print('-'*80)
    print(f'A = {par["A"]:.6f}')
    print(f'gamma1 = {par["gamma1"]:.6f}')
    print(f'gamma2 = {par["gamma2"]:.6f}')
    print('')
    
    print('公式: y = A * x * ((kappa^gamma1) * (labor^(1-gamma1)))^gamma2 - c')
    print('')
    
    # 测试不同规模的企业
    print('不同规模企业的产出测试:')
    print('-'*80)
    
    test_cases = [
        {'name': '小企业', 'kappa': 0.5, 'x': 1.0, 'wage': 0.275008},
        {'name': '中等企业', 'kappa': 5.0, 'x': 1.5, 'wage': 0.275008},
        {'name': '大企业', 'kappa': 20.0, 'x': 2.0, 'wage': 0.275008},
        {'name': '超大企业', 'kappa': 100.0, 'x': 3.0, 'wage': 0.275008},
        {'name': '最大企业', 'kappa': 200.0, 'x': 3.5, 'wage': 0.275008},
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
        print(f'  kappa={kappa:.1f}, x={x:.1f}, l={l:.2f}, c={c:.3f}')
        print(f'  y={y:.6f}')
        
        if 0.5 < y < 5.0:
            print(f'  [OK] 产出值在合理范围内')
        elif y > 10:
            print(f'  [WARN] 产出值较大')
        print('')


if __name__ == '__main__':
    analyze_output_small_calculation()
    check_prod_small_parameters()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要发现:')
    print('  1. 需要检查y_opt值是否合理')
    print('  2. 需要检查mu_active分布是否合理')
    print('  3. 需要对比MATLAB的实现')
    print('  4. 需要检查是否有参数缩放问题')













