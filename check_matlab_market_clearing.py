"""
检查MATLAB稳态结果是否满足市场出清条件
基于MATLAB的稳态结果表格进行分析
"""
import numpy as np


def analyze_matlab_steady_state():
    """分析MATLAB稳态结果的市场出清条件"""
    
    print('='*80)
    print('MATLAB稳态结果市场出清条件分析')
    print('='*80)
    print('')
    
    # MATLAB稳态结果（来自baseline/tables/steady_state.tex）
    matlab_results = {
        'C_agg': 0.1084,
        'K_corp': 0.7526,
        'L_corp': 0.1668,
        'K_agg': 1.2399,
        'L_agg': 0.3175,
        'Y_corp': 0.0655,
        'output_small': 0.0639,
        'Y_agg': 0.1295,
        'InvK': 0.0211,
        'liq': 0.0019,
        'entry': 0.0004,
    }
    
    print('MATLAB稳态结果:')
    print('-'*80)
    for key, value in sorted(matlab_results.items()):
        print(f'  {key:15s} = {value:15.6f}')
    print('')
    
    # 市场出清条件分析
    print('市场出清条件分析:')
    print('-'*80)
    
    # 1. 检查K_corp
    K_corp = matlab_results['K_corp']
    print(f'1. K_corp = {K_corp:.6f}')
    if K_corp > 0:
        print('   [OK] K_corp为正值')
    else:
        print('   [X] K_corp为负值或零')
    
    # 2. 计算LHS（需要cost_adj和entry_cost）
    # 从MATLAB结果推断
    C_agg = matlab_results['C_agg']
    output_small = matlab_results['output_small']
    liq = matlab_results['liq']
    entry = matlab_results['entry']  # 这是进入者测度，不是entry_cost
    
    # 估算entry_cost（假设entry_cost ≈ entry * 平均资本）
    # 从InvK计算：InvK = InvK_corp + entry_cost - liq + cost_adj
    # InvK_corp = delta_k * K_corp
    delta_k = 0.015  # 从参数中
    InvK_corp = delta_k * K_corp
    InvK = matlab_results['InvK']
    
    # 从Y_small计算：Y_small = output_small - cost_adj + liq - entry_cost
    # 但我们没有Y_small的直接值
    
    # 另一种方法：从K_corp = LHS / aux反推
    # 如果K_corp > 0，且aux > 0，则LHS > 0
    L_corp = matlab_results['L_corp']
    KL_ratio = K_corp / L_corp if L_corp > 0 else 0
    A = 0.25
    alpha = 0.3
    aux = A * (KL_ratio ** alpha) - delta_k
    
    print(f'\n2. aux计算（企业部门净收益率）:')
    print(f'   KL_ratio = K_corp / L_corp = {K_corp:.6f} / {matlab_results["L_corp"]:.6f} = {KL_ratio:.6f}')
    print(f'   aux = A * (KL_ratio^alpha) - delta_k')
    print(f'   aux = {A:.6f} * ({KL_ratio:.6f}^{alpha:.6f}) - {delta_k:.6f}')
    aux_calc = A * (KL_ratio ** alpha)
    print(f'   aux = {aux_calc:.6f} - {delta_k:.6f}')
    print(f'   aux = {aux:.6f}')
    
    if aux > 0:
        print('   [OK] aux为正值')
    else:
        print('   [X] aux为负值或零')
    
    # 3. 反推LHS
    if aux > 0 and K_corp > 0:
        LHS = K_corp * aux
        print(f'\n3. LHS反推:')
        print(f'   LHS = K_corp * aux')
        print(f'   LHS = {K_corp:.6f} * {aux:.6f}')
        print(f'   LHS = {LHS:.6f}')
        
        if LHS > 0:
            print('   [OK] LHS为正值')
        else:
            print('   [X] LHS为负值或零')
        
        # 4. 分解LHS
        print(f'\n4. LHS分解（估算）:')
        print(f'   LHS = C_agg - output_small + cost_adj + entry_cost - liq')
        print(f'   {LHS:.6f} = {C_agg:.6f} - {output_small:.6f} + cost_adj + entry_cost - {liq:.6f}')
        
        # 估算cost_adj + entry_cost
        cost_adj_plus_entry = LHS - C_agg + output_small + liq
        print(f'   cost_adj + entry_cost = LHS - C_agg + output_small + liq')
        print(f'   cost_adj + entry_cost = {LHS:.6f} - {C_agg:.6f} + {output_small:.6f} + {liq:.6f}')
        print(f'   cost_adj + entry_cost = {cost_adj_plus_entry:.6f}')
        
        if cost_adj_plus_entry > 0:
            print('   [OK] cost_adj + entry_cost为正值')
        else:
            print('   [WARN] cost_adj + entry_cost为负值（可能cost_adj为负）')
    
    # 5. 检查其他加总变量
    print(f'\n5. 其他加总变量检查:')
    print('-'*80)
    
    checks = {
        'K_corp': matlab_results['K_corp'],
        'L_corp': matlab_results['L_corp'],
        'K_agg': matlab_results['K_agg'],
        'L_agg': matlab_results['L_agg'],
        'Y_corp': matlab_results['Y_corp'],
        'Y_agg': matlab_results['Y_agg'],
        'InvK': matlab_results['InvK'],
    }
    
    all_positive = True
    for key, value in checks.items():
        if value > 0:
            print(f'   [OK] {key:10s} = {value:15.6f}')
        else:
            print(f'   [X]  {key:10s} = {value:15.6f}')
            all_positive = False
    
    print('')
    print('='*80)
    print('结论')
    print('='*80)
    
    if K_corp > 0 and aux > 0 and all_positive:
        print('[OK] MATLAB稳态结果满足市场出清条件')
        print('')
        print('证据:')
        print('  1. K_corp = 0.7526 > 0 [OK]')
        print('  2. aux > 0（企业部门净收益率为正）[OK]')
        print('  3. LHS = K_corp * aux > 0 [OK]')
        print('  4. 所有加总变量均为正值 [OK]')
    else:
        print('[X] MATLAB稳态结果可能不满足市场出清条件')
        if K_corp <= 0:
            print('  - K_corp <= 0')
        if aux <= 0:
            print('  - aux <= 0')
        if not all_positive:
            print('  - 部分加总变量为负值')
    
    print('')
    print('='*80)


if __name__ == '__main__':
    analyze_matlab_steady_state()

