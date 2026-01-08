"""
诊断稳态计算结果中的负值问题
"""
import numpy as np
import pickle
import os
from fun import Fun

def diagnose_steady_state(filename='steady_state_results.pkl'):
    """
    诊断稳态结果中的负值问题
    """
    if not os.path.exists(filename):
        print(f"错误：未找到稳态结果文件 {filename}")
        return
    
    print("="*80)
    print("诊断稳态计算结果中的负值问题")
    print("="*80)
    
    with open(filename, 'rb') as f:
        ss_results = pickle.load(f)
    
    agg = ss_results.get('agg')
    prices = ss_results.get('prices')
    par = ss_results.get('par')
    
    if agg is None or prices is None or par is None:
        print("错误：缺少必要的计算结果")
        return
    
    # 提取关键变量
    C_agg = agg.get('C_agg', 0)
    output_small = agg.get('output_small', 0)
    cost_adj = agg.get('cost_adj', 0)
    entry_cost = agg.get('entry_cost', 0)
    liq = agg.get('liq', 0)
    K_corp = agg.get('K_corp', 0)
    K_small = agg.get('K_small', 0)
    L_corp = agg.get('L_corp', 0)
    L_small = agg.get('L_small', 0)
    
    wage = prices.get('wage', 0)
    KL_ratio = prices.get('KL_ratio', 0)
    delta_k = par.get('delta_k', 0.015)
    
    print("\n1. 市场出清方程分析")
    print("-"*80)
    print(f"C_agg (总消费)        = {C_agg:15.6f}")
    print(f"output_small (小企业产出) = {output_small:15.6f}")
    print(f"cost_adj (调整成本)    = {cost_adj:15.6f}")
    print(f"entry_cost (进入成本) = {entry_cost:15.6f}")
    print(f"liq (清算)            = {liq:15.6f}")
    
    LHS = C_agg - output_small + cost_adj + entry_cost - liq
    print(f"\nLHS = C_agg - output_small + cost_adj + entry_cost - liq")
    print(f"LHS = {C_agg:.6f} - {output_small:.6f} + {cost_adj:.6f} + {entry_cost:.6f} - {liq:.6f}")
    print(f"LHS = {LHS:.6f}")
    
    if LHS < 0:
        print(f"\n[问题] LHS为负值！")
        print(f"  这意味着：C_agg + cost_adj + entry_cost < output_small + liq")
        print(f"  即：消费+调整成本+进入成本 < 小企业产出+清算")
        print(f"  这可能表明小企业产出过大或消费过小")
    
    print(f"\n2. 企业部门资本计算")
    print("-"*80)
    print(f"KL_ratio (资本劳动比) = {KL_ratio:.6f}")
    
    # 计算aux
    prod_corp_val = Fun.prod_corp(KL_ratio, 1 / KL_ratio, par)
    print(f"Fun.prod_corp(KL_ratio, 1/KL_ratio) = {prod_corp_val:.6f}")
    print(f"delta_k (折旧率)      = {delta_k:.6f}")
    
    aux = prod_corp_val - delta_k
    print(f"aux = Fun.prod_corp(KL_ratio, 1/KL_ratio) - delta_k")
    print(f"aux = {prod_corp_val:.6f} - {delta_k:.6f} = {aux:.6f}")
    
    if aux <= 0:
        print(f"\n[问题] aux <= 0！")
        print(f"  这意味着：企业部门净收益率 <= 0")
        print(f"  这会导致K_corp计算出现问题")
    
    print(f"\nK_corp = LHS / aux")
    print(f"K_corp = {LHS:.6f} / {aux:.6f} = {K_corp:.6f}")
    
    if K_corp < 0:
        print(f"\n[问题] K_corp为负值！")
        if LHS < 0 and aux > 0:
            print(f"  原因：LHS为负值")
        elif LHS > 0 and aux < 0:
            print(f"  原因：aux为负值（企业部门净收益率 < 0）")
        elif LHS < 0 and aux < 0:
            print(f"  原因：LHS和aux都为负值，但K_corp = LHS/aux > 0（这不应该发生）")
    
    print(f"\n3. 其他关键变量")
    print("-"*80)
    print(f"K_small (小企业资本) = {K_small:15.6f}")
    print(f"L_corp (企业部门就业) = {L_corp:15.6f}")
    print(f"L_small (小企业就业)  = {L_small:15.6f}")
    
    if K_small < 0:
        print(f"[问题] K_small为负值")
    if L_corp < 0:
        print(f"[问题] L_corp为负值（因为K_corp为负）")
    if L_small < 0:
        print(f"[问题] L_small为负值")
    
    print(f"\n4. 可能的原因分析")
    print("-"*80)
    if LHS < 0:
        print("  - LHS为负值，可能原因：")
        print("    1. 小企业产出output_small过大")
        print("    2. 清算liq过大")
        print("    3. 消费C_agg过小")
        print("    4. 调整成本cost_adj或进入成本entry_cost过小")
    
    if aux <= 0:
        print("  - aux <= 0，可能原因：")
        print("    1. 企业部门生产率参数A过小")
        print("    2. 折旧率delta_k过大")
        print("    3. KL_ratio设置不合理")
    
    print(f"\n5. 建议")
    print("-"*80)
    if K_corp < 0:
        print("  - 检查参数设置，特别是：")
        print("    * 企业部门生产率A")
        print("    * 折旧率delta_k")
        print("    * 固定成本参数fixcost1, fixcost2")
        print("    * 进入成本cost_e")
        print("  - 可能需要重新校准参数")
        print("  - 或者检查小企业产出的计算是否正确")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    diagnose_steady_state()


















