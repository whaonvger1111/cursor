"""
详细检查output_small的计算，找出与MATLAB差异的原因
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))
from fun import Fun


def check_output_small_detailed():
    """详细检查output_small的计算"""
    
    print('='*80)
    print('output_small计算详细检查')
    print('='*80)
    print('')
    
    # 尝试加载稳态结果
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        print('成功加载稳态结果')
        print('-'*80)
        
        # 提取数据
        if 'distribS' in ss_results:
            mu_active = ss_results['distribS']['mu_active']
            print(f'mu_active形状: {mu_active.shape}')
            print(f'mu_active总和: {np.sum(mu_active):.6f}')
            print(f'mu_active最大值: {np.max(mu_active):.6e}')
            print(f'mu_active最小值: {np.min(mu_active):.6e}')
            print(f'mu_active非零元素数量: {np.sum(mu_active > 0)}')
            print(f'mu_active负值数量: {np.sum(mu_active < 0)}')
        
        if 'par' in ss_results:
            par = ss_results['par']
            print(f'\n参数值:')
            print(f'  A = {par.get("A", "N/A")}')
            print(f'  gamma1 = {par.get("gamma1", "N/A")}')
            print(f'  gamma2 = {par.get("gamma2", "N/A")}')
            print(f'  nx = {par.get("nx", "N/A")}')
            print(f'  nb = {par.get("nb", "N/A")}')
            print(f'  nk = {par.get("nk", "N/A")}')
            
            if 'x_grid' in par:
                print(f'\nx_grid范围: [{np.min(par["x_grid"]):.6f}, {np.max(par["x_grid"]):.6f}]')
            if 'k_grid' in par:
                print(f'k_grid范围: [{np.min(par["k_grid"]):.6f}, {np.max(par["k_grid"]):.6f}]')
            if 'fixcost' in par:
                print(f'fixcost范围: [{np.min(par["fixcost"]):.6f}, {np.max(par["fixcost"]):.6f}]')
        
        if 'prices' in ss_results:
            prices = ss_results['prices']
            print(f'\n价格:')
            print(f'  wage = {prices.get("wage", "N/A")}')
            print(f'  KL_ratio = {prices.get("KL_ratio", "N/A")}')
        
        if 'agg' in ss_results:
            agg = ss_results['agg']
            print(f'\n加总变量:')
            print(f'  output_small = {agg.get("output_small", "N/A")}')
            print(f'  L_small = {agg.get("L_small", "N/A")}')
            print(f'  mu_active总和 = {np.sum(mu_active):.6f}')
            
            # 手动计算output_small
            if 'distribS' in ss_results and 'par' in ss_results and 'prices' in ss_results:
                print('\n手动计算output_small:')
                print('-'*80)
                
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
                
                # 创建网格
                kappa = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
                c = np.tile(fixcost[:, np.newaxis, np.newaxis], (1, nb, nx))
                x_val = np.tile((A * x_grid)[np.newaxis, np.newaxis, :], (nk, nb, 1))
                
                # 计算劳动需求
                l_opt = Fun.fun_l(x_val, wage, kappa, par)
                print(f'l_opt范围: [{np.min(l_opt):.6f}, {np.max(l_opt):.6f}]')
                print(f'l_opt平均值: {np.mean(l_opt):.6f}')
                
                # 计算产出
                y_opt = Fun.prod_small(x_val, kappa, l_opt, c, par)
                print(f'y_opt范围: [{np.min(y_opt):.6f}, {np.max(y_opt):.6f}]')
                print(f'y_opt平均值: {np.mean(y_opt):.6f}')
                print(f'y_opt正值数量: {np.sum(y_opt > 0)}')
                print(f'y_opt负值数量: {np.sum(y_opt < 0)}')
                
                # 计算output_small
                output_small_calc = np.sum(y_opt * mu_active)
                print(f'\n计算的output_small: {output_small_calc:.6f}')
                print(f'agg中的output_small: {agg.get("output_small", "N/A")}')
                
                # 分析贡献最大的点
                contribution = y_opt * mu_active
                max_contrib_idx_flat = np.argmax(np.abs(contribution))
                max_contrib_idx = np.unravel_index(max_contrib_idx_flat, contribution.shape)
                print(f'\n贡献最大的点索引: {max_contrib_idx}')
                print(f'contribution形状: {contribution.shape}')
                print(f'mu_active形状: {mu_active.shape}')
                
                if len(max_contrib_idx) == 3:
                    k_idx, b_idx, x_idx = max_contrib_idx
                    print(f'\n贡献最大的点 (k_idx, b_idx, x_idx): ({k_idx}, {b_idx}, {x_idx})')
                    print(f'  贡献值: {contribution[k_idx, b_idx, x_idx]:.6f}')
                    print(f'  y_opt值: {y_opt[k_idx, b_idx, x_idx]:.6f}')
                    print(f'  mu_active值: {mu_active[k_idx, b_idx, x_idx]:.6e}')
                    print(f'  kappa值: {kappa[k_idx, b_idx, x_idx]:.6f}')
                    print(f'  x_val值: {x_val[k_idx, b_idx, x_idx]:.6f}')
                    print(f'  l_opt值: {l_opt[k_idx, b_idx, x_idx]:.6f}')
                    print(f'  c值: {c[k_idx, b_idx, x_idx]:.6f}')
                else:
                    print(f'警告: max_contrib_idx有{len(max_contrib_idx)}个维度，期望3个')
                
                # 检查前10个最大贡献点
                print(f'\n前10个最大贡献点:')
                flat_contrib = contribution.flatten()
                top10_idx = np.argsort(np.abs(flat_contrib))[-10:][::-1]
                for i, idx in enumerate(top10_idx):
                    k_idx, b_idx, x_idx = np.unravel_index(idx, contribution.shape)
                    print(f'  {i+1}. (k={k_idx}, b={b_idx}, x={x_idx}): '
                          f'贡献={contribution[k_idx, b_idx, x_idx]:.6f}, '
                          f'y_opt={y_opt[k_idx, b_idx, x_idx]:.6f}, '
                          f'mu_active={mu_active[k_idx, b_idx, x_idx]:.6e}')
        
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
        print('使用当前终端输出的值进行分析')
        
        # 使用终端输出的值
        print('\n使用终端输出的值:')
        print('-'*80)
        print('output_small = 54.779965')
        print('mu_active总和 = 0.050691')
        print('\n平均每个企业的产出:')
        print('  54.779965 / 0.050691 = 1080.5')
        print('\n这非常大！')
        print('MATLAB的平均产出:')
        print('  0.0639 / (未知mu_active总和) ≈ 小得多')
        
        print('\n可能的问题:')
        print('  1. mu_active分布可能集中在高产出企业')
        print('  2. 生产函数计算可能有问题')
        print('  3. 参数值可能不同')


def check_prod_small_formula():
    """检查prod_small公式"""
    
    print('\n' + '='*80)
    print('prod_small公式检查')
    print('='*80)
    
    # 测试几个样本点
    par = {
        'A': 0.25,
        'gamma1': 0.3182,
        'gamma2': 0.88,
    }
    
    # 样本点1：小值
    x1 = 1.0
    kappa1 = 1.0
    labor1 = 1.0
    c1 = 0.1
    
    y1 = Fun.prod_small(x1, kappa1, labor1, c1, par)
    print(f'\n样本点1: x={x1}, kappa={kappa1}, labor={labor1}, c={c1}')
    print(f'  y = {y1:.6f}')
    
    # 样本点2：中等值
    x2 = 2.0
    kappa2 = 10.0
    labor2 = 5.0
    c2 = 0.2
    
    y2 = Fun.prod_small(x2, kappa2, labor2, c2, par)
    print(f'\n样本点2: x={x2}, kappa={kappa2}, labor={labor2}, c={c2}')
    print(f'  y = {y2:.6f}')
    
    # 样本点3：大值
    x3 = 4.0
    kappa3 = 100.0
    labor3 = 50.0
    c3 = 1.0
    
    y3 = Fun.prod_small(x3, kappa3, labor3, c3, par)
    print(f'\n样本点3: x={x3}, kappa={kappa3}, labor={labor3}, c={c3}')
    print(f'  y = {y3:.6f}')
    
    print('\n公式验证:')
    print('  y = A * x * ((kappa^gamma1) * (labor^(1-gamma1)))^gamma2 - c')
    print(f'  样本点1: y = 0.25 * 1.0 * ((1.0^0.3182) * (1.0^0.6818))^0.88 - 0.1')
    print(f'          = 0.25 * 1.0 * (1.0)^0.88 - 0.1')
    print(f'          = 0.25 - 0.1 = 0.15')
    print(f'  实际计算: {y1:.6f}')


if __name__ == '__main__':
    check_output_small_detailed()
    check_prod_small_formula()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要发现:')
    print('  1. output_small = 54.78 (Python) vs 0.0639 (MATLAB) - 857倍差异')
    print('  2. 需要检查:')
    print('     - mu_active分布是否正确')
    print('     - prod_small和fun_l函数实现是否正确')
    print('     - 参数值是否正确')
    print('     - 网格值是否正确')

