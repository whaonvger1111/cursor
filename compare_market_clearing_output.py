"""
对比Python和MATLAB的市场出清方程和output_small计算
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))
from fun import Fun


def analyze_python_calculations():
    """分析Python的计算方式"""
    
    print('='*80)
    print('Python计算方式分析')
    print('='*80)
    print('')
    
    # 从终端输出中提取的值
    python_results = {
        'C_agg': 0.108363,
        'output_small': 54.779965,
        'cost_adj': 2.203993,
        'entry_cost': 3.418883,
        'liq': 5.502663,
        'LHS': -54.551389,
        'aux': 0.072074,
        'K_corp': -756.875176,
        'KL_ratio': 4.511862,
        'wage': 0.275008,
        'mu_sum': 0.051080,
        'mu_active_sum': 0.050691,
    }
    
    # MATLAB结果（来自文档）
    matlab_results = {
        'C_agg': 0.1084,
        'output_small': 0.0639,
        'K_corp': 0.7526,
        'L_corp': 0.1668,
        'KL_ratio': 4.511990,  # 从K_corp/L_corp计算
        'aux': 0.377871,  # 从文档中
        'LHS': 0.284386,  # 从K_corp * aux计算
        'liq': 0.0019,
        'entry': 0.0004,
    }
    
    print('1. 市场出清方程 (LHS) 计算对比')
    print('-'*80)
    print('\nPython计算:')
    print(f'  LHS = C_agg - output_small + cost_adj + entry_cost - liq')
    print(f'  LHS = {python_results["C_agg"]:.6f} - {python_results["output_small"]:.6f} + '
          f'{python_results["cost_adj"]:.6f} + {python_results["entry_cost"]:.6f} - {python_results["liq"]:.6f}')
    print(f'  LHS = {python_results["LHS"]:.6f}')
    
    print('\nMATLAB结果（从K_corp反推）:')
    print(f'  LHS = K_corp * aux')
    print(f'  LHS = {matlab_results["K_corp"]:.6f} * {matlab_results["aux"]:.6f}')
    print(f'  LHS = {matlab_results["LHS"]:.6f}')
    
    # 反推MATLAB的cost_adj + entry_cost
    matlab_cost_adj_plus_entry = (matlab_results["LHS"] - matlab_results["C_agg"] + 
                                  matlab_results["output_small"] + matlab_results["liq"])
    print(f'\nMATLAB的 cost_adj + entry_cost (反推):')
    print(f'  cost_adj + entry_cost = LHS - C_agg + output_small + liq')
    print(f'  cost_adj + entry_cost = {matlab_results["LHS"]:.6f} - {matlab_results["C_agg"]:.6f} + '
          f'{matlab_results["output_small"]:.6f} + {matlab_results["liq"]:.6f}')
    print(f'  cost_adj + entry_cost = {matlab_cost_adj_plus_entry:.6f}')
    
    python_cost_adj_plus_entry = python_results["cost_adj"] + python_results["entry_cost"]
    print(f'\nPython的 cost_adj + entry_cost:')
    print(f'  cost_adj + entry_cost = {python_results["cost_adj"]:.6f} + {python_results["entry_cost"]:.6f}')
    print(f'  cost_adj + entry_cost = {python_cost_adj_plus_entry:.6f}')
    
    print('\n' + '='*80)
    print('2. output_small 计算对比')
    print('-'*80)
    
    print('\nPython计算方式 (sub_aggregates_onestep.py):')
    print('  output_small = sum(y_opt * mu_active)')
    print('  其中:')
    print('    y_opt = Fun.prod_small(x_val, kappa, l_opt, c, par)')
    print('    l_opt = Fun.fun_l(x_val, wage, kappa, par)')
    print('    x_val = A * x_grid (A=1在稳态中)')
    print('    kappa = k_grid (资本网格)')
    print('    c = fixcost (固定成本)')
    print('    mu_active = 活跃企业分布')
    print(f'\n  Python结果: output_small = {python_results["output_small"]:.6f}')
    print(f'  MATLAB结果: output_small = {matlab_results["output_small"]:.6f}')
    print(f'  差异: {python_results["output_small"] / matlab_results["output_small"]:.2f}倍')
    
    print('\n' + '='*80)
    print('3. 关键差异分析')
    print('-'*80)
    
    print('\n3.1 output_small差异:')
    print(f'  Python: {python_results["output_small"]:.6f}')
    print(f'  MATLAB: {matlab_results["output_small"]:.6f}')
    print(f'  差异倍数: {python_results["output_small"] / matlab_results["output_small"]:.2f}倍')
    print(f'  差异绝对值: {python_results["output_small"] - matlab_results["output_small"]:.6f}')
    
    print('\n3.2 LHS差异:')
    print(f'  Python: {python_results["LHS"]:.6f} (负值)')
    print(f'  MATLAB: {matlab_results["LHS"]:.6f} (正值)')
    print(f'  差异: {python_results["LHS"] - matlab_results["LHS"]:.6f}')
    
    print('\n3.3 aux差异:')
    print(f'  Python: {python_results["aux"]:.6f}')
    print(f'  MATLAB: {matlab_results["aux"]:.6f}')
    print(f'  差异: {python_results["aux"] - matlab_results["aux"]:.6f}')
    print(f'  差异倍数: {matlab_results["aux"] / python_results["aux"]:.2f}倍')
    
    print('\n3.4 KL_ratio差异:')
    print(f'  Python: {python_results["KL_ratio"]:.6f}')
    print(f'  MATLAB: {matlab_results["KL_ratio"]:.6f}')
    print(f'  差异: {abs(python_results["KL_ratio"] - matlab_results["KL_ratio"]):.6f}')
    
    print('\n' + '='*80)
    print('4. 可能的原因')
    print('-'*80)
    
    print('\n4.1 output_small过大的可能原因:')
    print('  a) 分布mu_active过大')
    print(f'     Python: mu_active总和 = {python_results["mu_active_sum"]:.6f}')
    print('     MATLAB: 未知（需要对比）')
    print('  b) 生产函数计算错误')
    print('     - prod_small函数实现可能不同')
    print('     - fun_l函数实现可能不同')
    print('     - 参数值可能不同')
    print('  c) 网格或分布计算不准确')
    print('     - 分布未充分收敛')
    print('     - 网格太粗糙')
    
    print('\n4.2 aux差异的可能原因:')
    print('  aux = A * (KL_ratio^alpha) - delta_k')
    print(f'  Python KL_ratio = {python_results["KL_ratio"]:.6f}')
    print(f'  MATLAB KL_ratio = {matlab_results["KL_ratio"]:.6f}')
    print('  差异很小，但aux差异很大')
    print('  可能原因:')
    print('    - KL_ratio的计算方式不同')
    print('    - 或者KL_ratio本身的计算依赖于LHS/K_corp')
    
    print('\n4.3 LHS为负的可能原因:')
    print('  LHS = C_agg - output_small + cost_adj + entry_cost - liq')
    print(f'  Python: {python_results["C_agg"]:.6f} - {python_results["output_small"]:.6f} + '
          f'{python_results["cost_adj"]:.6f} + {python_results["entry_cost"]:.6f} - {python_results["liq"]:.6f}')
    print(f'  = {python_results["LHS"]:.6f}')
    print('  主要问题: output_small过大 (54.78 vs 0.0639)')
    print('  导致: C_agg - output_small 为很大的负值')
    
    print('\n' + '='*80)
    print('5. 建议检查点')
    print('-'*80)
    
    print('\n5.1 检查output_small计算:')
    print('  - 检查prod_small函数实现')
    print('  - 检查fun_l函数实现')
    print('  - 检查mu_active分布是否正确')
    print('  - 检查x_grid, k_grid, fixcost的值')
    
    print('\n5.2 检查市场出清方程:')
    print('  - 检查LHS计算公式是否正确')
    print('  - 检查cost_adj计算是否正确')
    print('  - 检查entry_cost计算是否正确')
    print('  - 检查liq计算是否正确')
    
    print('\n5.3 检查aux计算:')
    print('  - 检查KL_ratio的计算方式')
    print('  - 检查prod_corp函数实现')
    print('  - 检查参数A, alpha, delta_k的值')
    
    print('\n' + '='*80)


def check_prod_small_implementation():
    """检查prod_small函数的实现"""
    
    print('\n' + '='*80)
    print('prod_small函数实现检查')
    print('='*80)
    
    # 读取fun.py中的prod_small实现
    print('\nPython实现 (fun.py):')
    print('  def prod_small(x, kappa, labor, c, par):')
    print('      A = par["A"]')
    print('      gamma1 = par["gamma1"]')
    print('      gamma2 = par["gamma2"]')
    print('      return A * x * ((kappa ** gamma1) * (labor ** (1 - gamma1))) ** gamma2 - c')
    
    print('\n公式:')
    print('  y = A * x * ((kappa^gamma1) * (labor^(1-gamma1)))^gamma2 - c')
    print('  其中:')
    print('    A = 企业部门TFP')
    print('    x = 生产率')
    print('    kappa = 资本')
    print('    labor = 劳动')
    print('    c = 固定成本')
    
    print('\n需要检查:')
    print('  1. 公式是否正确（与MATLAB一致）')
    print('  2. 参数值是否正确')
    print('  3. 输入值是否正确（x, kappa, labor, c）')


def check_fun_l_implementation():
    """检查fun_l函数的实现"""
    
    print('\n' + '='*80)
    print('fun_l函数实现检查')
    print('='*80)
    
    print('\nPython实现 (fun.py):')
    print('  def fun_l(x, wage, k, par):')
    print('      gamma1 = par["gamma1"]')
    print('      gamma2 = par["gamma2"]')
    print('      aux = (1 - gamma1) * gamma2')
    print('      aux_minus_one = aux - 1')
    print('      denominator = par["A"] * x * aux')
    print('      return (wage / denominator) ** (1 / aux_minus_one) * (k ** (-gamma1 * gamma2 / aux_minus_one))')
    
    print('\n公式:')
    print('  l = (wage / (A * x * (1-gamma1) * gamma2))^(1/((1-gamma1)*gamma2 - 1)) * k^(-gamma1*gamma2/((1-gamma1)*gamma2 - 1))')
    
    print('\n需要检查:')
    print('  1. 公式是否正确（与MATLAB一致）')
    print('  2. 参数值是否正确')
    print('  3. 输入值是否正确（x, wage, k）')


if __name__ == '__main__':
    analyze_python_calculations()
    check_prod_small_implementation()
    check_fun_l_implementation()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要问题:')
    print('  1. output_small过大 (54.78 vs 0.0639) - 857倍差异')
    print('  2. LHS为负值 (-54.55 vs 0.284)')
    print('  3. aux较小 (0.072 vs 0.378) - 5.2倍差异')
    print('\n需要进一步检查:')
    print('  - prod_small和fun_l函数的实现是否与MATLAB一致')
    print('  - mu_active分布是否正确')
    print('  - 参数值是否正确')
    print('  - 市场出清方程的计算公式是否正确')












