"""
检查entry_cost和liq的计算，对比Python和MATLAB
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))


def check_entry_cost_calculation():
    """检查entry_cost的计算"""
    
    print('='*80)
    print('entry_cost计算检查')
    print('='*80)
    print('')
    
    print('Python计算方式 (sub_aggregates_onestep.py 第58行):')
    print('  entry = sum(mass * (kappa + cost_e) * pol_entry * phi_dist)')
    print('')
    print('公式解释:')
    print('  - mass: 潜在进入者质量')
    print('  - kappa: 资本网格')
    print('  - cost_e: 进入的固定成本')
    print('  - pol_entry: 进入政策 (0或1)')
    print('  - phi_dist: 进入者分布')
    print('')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results and 'par' in ss_results and 'sol' in ss_results:
            par = ss_results['par']
            sol = ss_results['sol']
            
            mass = par.get('mass', 0)
            cost_e = par.get('cost_e', 0)
            k_grid = par['k_grid']
            pol_entry = sol['pol_entry']
            phi_dist = sol['phi_dist']
            
            if k_grid.ndim > 1:
                k_grid = k_grid.flatten()
            
            nx = par['nx']
            nb = par['nb']
            nk = par['nk']
            
            # 创建kappa网格
            kappa = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
            
            # 计算entry_cost
            entry_cost = np.sum(mass * (kappa + cost_e) * pol_entry * phi_dist)
            
            print('计算结果:')
            print('-'*80)
            print(f'  mass = {mass:.6f}')
            print(f'  cost_e = {cost_e:.6f}')
            print(f'  kappa范围: [{np.min(kappa):.6f}, {np.max(kappa):.6f}]')
            print(f'  pol_entry总和: {np.sum(pol_entry):.6f}')
            print(f'  phi_dist总和: {np.sum(phi_dist):.6f}')
            print(f'  entry_cost = {entry_cost:.6f}')
            
            # 从终端输出
            print(f'\n从终端输出:')
            print(f'  entry_cost = 3.418883')
            print(f'  差异: {abs(entry_cost - 3.418883):.6f}')
            
            # 检查entry_rate
            entry_rate = np.sum(mass * pol_entry * phi_dist)
            print(f'\n  entry_rate (进入者测度) = {entry_rate:.6f}')
            print(f'  从终端输出: entry = 0.000488')
            print(f'  差异: {abs(entry_rate - 0.000488):.6f}')
            
            # 计算平均进入成本
            if entry_rate > 0:
                avg_entry_cost = entry_cost / entry_rate
                print(f'\n  平均每个进入者的成本 = {avg_entry_cost:.6f}')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def check_liq_calculation():
    """检查liq的计算"""
    
    print('\n' + '='*80)
    print('liq计算检查')
    print('='*80)
    print('')
    
    print('Python计算方式 (sub_aggregates_onestep.py 第56行):')
    print('  liq = sum(theta * (1 - delta_k) * kappa * exit_all * mu)')
    print('')
    print('公式解释:')
    print('  - theta: 转售价值 (0 < theta < 1)')
    print('  - delta_k: 折旧率')
    print('  - kappa: 资本网格')
    print('  - exit_all: 总退出率 (psi + (1-psi)*pol_exit)')
    print('  - mu: 分布')
    print('')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results and 'par' in ss_results and 'sol' in ss_results:
            par = ss_results['par']
            sol = ss_results['sol']
            distribS = ss_results['distribS']
            
            theta = par.get('theta', 0)
            delta_k = par.get('delta_k', 0)
            psi = par.get('psi', 0)
            k_grid = par['k_grid']
            mu = distribS['mu']
            pol_exit = sol['pol_exit']
            
            if k_grid.ndim > 1:
                k_grid = k_grid.flatten()
            
            nx = par['nx']
            nb = par['nb']
            nk = par['nk']
            
            # 创建kappa网格
            kappa = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
            
            # 计算exit_all
            exit_all = psi + (1 - psi) * pol_exit
            
            # 计算liq
            liq = np.sum(theta * (1 - delta_k) * kappa * exit_all * mu)
            
            print('计算结果:')
            print('-'*80)
            print(f'  theta = {theta:.6f}')
            print(f'  delta_k = {delta_k:.6f}')
            print(f'  psi = {psi:.6f}')
            print(f'  kappa范围: [{np.min(kappa):.6f}, {np.max(kappa):.6f}]')
            print(f'  exit_all总和: {np.sum(exit_all * mu):.6f}')
            print(f'  mu总和: {np.sum(mu):.6f}')
            print(f'  liq = {liq:.6f}')
            
            # 从终端输出
            print(f'\n从终端输出:')
            print(f'  liq = 5.502663')
            print(f'  差异: {abs(liq - 5.502663):.6f}')
            
            # MATLAB结果
            print(f'\nMATLAB结果:')
            print(f'  liq = 0.0019')
            print(f'  差异: {abs(liq - 0.0019):.6f}')
            print(f'  差异倍数: {liq / 0.0019:.2f}倍')
            
            # 分析差异
            if liq / 0.0019 > 100:
                print(f'\n⚠️  liq差异很大，可能原因:')
                print(f'  1. exit_all * mu过大')
                print(f'  2. kappa值过大')
                print(f'  3. theta值不同')
                print(f'  4. 计算公式不同')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def check_cost_adj_calculation():
    """检查cost_adj的计算"""
    
    print('\n' + '='*80)
    print('cost_adj计算检查')
    print('='*80)
    print('')
    
    print('Python计算方式 (sub_aggregates_onestep.py 第64-71行):')
    print('  cost_adj = sum(adjcost(kp, k, theta, delta) * mu_active)')
    print('')
    print('公式解释:')
    print('  - adjcost: 资本调整成本函数')
    print('    - 如果 kp >= (1-delta)*k: adjcost = kp - (1-delta)*k')
    print('    - 如果 kp < (1-delta)*k:  adjcost = theta * (kp - (1-delta)*k)')
    print('  - mu_active: 活跃企业分布')
    print('')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results and 'par' in ss_results and 'agg' in ss_results:
            par = ss_results['par']
            agg = ss_results['agg']
            
            cost_adj = agg.get('cost_adj', 0)
            capadj = agg.get('capadj', np.zeros(4))
            
            print('计算结果:')
            print('-'*80)
            print(f'  cost_adj = {cost_adj:.6f}')
            print(f'  capadj[0] (向上调整) = {capadj[0]:.6f}')
            print(f'  capadj[1] (向下调整) = {capadj[1]:.6f}')
            print(f'  capadj[2] (进入者购买) = {capadj[2]:.6f}')
            print(f'  capadj[3] (退出者出售) = {capadj[3]:.6f}')
            
            # 从终端输出
            print(f'\n从终端输出:')
            print(f'  cost_adj = 2.203993')
            print(f'  capadj[0] = 134.745508')
            print(f'  capadj[1] = 179.579801')
            print(f'  capadj[2] = 3.418883')
            print(f'  capadj[3] = 6.142620')
            
            # 注意：cost_adj不等于capadj的总和
            # cost_adj是调整成本（考虑theta），而capadj是资本调整量
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')


def compare_all_components():
    """对比所有LHS组成部分"""
    
    print('\n' + '='*80)
    print('LHS组成部分对比')
    print('='*80)
    print('')
    
    # Python结果（从终端输出）
    python_results = {
        'C_agg': 0.108363,
        'output_small': 54.779965,
        'cost_adj': 2.203993,
        'entry_cost': 3.418883,
        'liq': 5.502663,
        'LHS': -54.551389,
    }
    
    # MATLAB结果（从文档）
    matlab_results = {
        'C_agg': 0.1084,
        'output_small': 0.0639,
        'liq': 0.0019,
        'entry': 0.0004,  # 这是进入者测度，不是entry_cost
        'LHS': 0.284386,
    }
    
    # 估算MATLAB的cost_adj + entry_cost
    # LHS = C_agg - output_small + cost_adj + entry_cost - liq
    # cost_adj + entry_cost = LHS - C_agg + output_small + liq
    matlab_cost_adj_plus_entry = (matlab_results['LHS'] - matlab_results['C_agg'] + 
                                  matlab_results['output_small'] + matlab_results['liq'])
    
    print('Python结果:')
    print('-'*80)
    for key, value in python_results.items():
        print(f'  {key:15s} = {value:15.6f}')
    
    print('\nMATLAB结果:')
    print('-'*80)
    for key, value in matlab_results.items():
        print(f'  {key:15s} = {value:15.6f}')
    print(f'  {"cost_adj+entry_cost":15s} = {matlab_cost_adj_plus_entry:15.6f} (估算)')
    
    print('\n差异分析:')
    print('-'*80)
    print(f'  C_agg:      Python={python_results["C_agg"]:.6f}, MATLAB={matlab_results["C_agg"]:.6f}, 差异={abs(python_results["C_agg"]-matlab_results["C_agg"]):.6f}')
    print(f'  output_small: Python={python_results["output_small"]:.6f}, MATLAB={matlab_results["output_small"]:.6f}, 差异={python_results["output_small"]/matlab_results["output_small"]:.2f}倍')
    print(f'  liq:        Python={python_results["liq"]:.6f}, MATLAB={matlab_results["liq"]:.6f}, 差异={python_results["liq"]/matlab_results["liq"]:.2f}倍')
    print(f'  cost_adj+entry_cost: Python={python_results["cost_adj"]+python_results["entry_cost"]:.6f}, MATLAB(估算)={matlab_cost_adj_plus_entry:.6f}, 差异={(python_results["cost_adj"]+python_results["entry_cost"])/matlab_cost_adj_plus_entry:.2f}倍')
    
    print('\n主要问题:')
    print('-'*80)
    print('  1. output_small差异最大 (857倍)')
    print('  2. liq差异很大 (2896倍)')
    print('  3. cost_adj+entry_cost差异较大 (23倍)')


if __name__ == '__main__':
    check_entry_cost_calculation()
    check_liq_calculation()
    check_cost_adj_calculation()
    compare_all_components()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要发现:')
    print('  1. entry_cost和liq的计算公式看起来正确')
    print('  2. 但数值差异很大，可能与output_small问题相关')
    print('  3. 需要进一步检查这些值的合理性')













