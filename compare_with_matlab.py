"""
对比Python和MATLAB的参数设置和市场出清方程
添加详细诊断信息
"""
import numpy as np
import pickle
import os

def log_message(message, flush=True):
    """记录日志消息"""
    try:
        with open('steady_state_iterations.log', 'a', encoding='utf-8') as f:
            f.write(message + '\n')
            if flush:
                f.flush()
    except:
        pass

def compare_parameters():
    """对比Python和MATLAB的参数设置"""
    print("\n" + "="*80)
    print("参数设置对比（Python vs MATLAB原始值）")
    print("="*80)
    
    # Python当前参数（从set_parameters.py）
    python_params = {
        'nx': 20,  # 当前值（已降低）
        'nb': 30,  # 当前值（已降低）
        'nk': 40,  # 当前值（已降低）
        'tol_bhat': 5e-3,  # 当前值（已提高）
        'tol_vfi': 5e-3,  # 当前值（已提高）
        'tol_vfi_u': 5e-3,  # 当前值（已提高）
        'tol_dist': 1e-2,  # 当前值（已提高）
        'n_howard': 20,  # 当前值（已降低）
        'beta': 0.989,
        'sigma': 2.0,
        'alpha': 0.3,
        'delta_k': 0.015,
        'gamma1': 0.3182,
        'gamma2': 0.88,
        'A': 0.25,
        'lambda0': 1,
        'cost_e': 0,
    }
    
    # MATLAB原始参数（典型值，需要根据实际MATLAB代码确认）
    matlab_params = {
        'nx': 60,  # 典型MATLAB值（更精细的网格）
        'nb': 60,  # 典型MATLAB值
        'nk': 60,  # 典型MATLAB值
        'tol_bhat': 1e-4,  # 典型MATLAB值（更严格的容差）
        'tol_vfi': 1e-4,  # 典型MATLAB值
        'tol_vfi_u': 1e-4,  # 典型MATLAB值
        'tol_dist': 1e-4,  # 典型MATLAB值
        'n_howard': 50,  # 典型MATLAB值
        'beta': 0.989,
        'sigma': 2.0,
        'alpha': 0.3,
        'delta_k': 0.015,
        'gamma1': 0.3182,
        'gamma2': 0.88,
        'A': 0.25,
        'lambda0': 1,
        'cost_e': 0,
    }
    
    print("\n数值参数（网格和容差）:")
    print(f"{'参数':<15} {'Python当前值':<20} {'MATLAB典型值':<20} {'说明':<30}")
    print("-" * 85)
    for key in ['nx', 'nb', 'nk', 'tol_bhat', 'tol_vfi', 'tol_vfi_u', 'tol_dist', 'n_howard']:
        py_val = python_params[key]
        ml_val = matlab_params[key]
        diff = py_val - ml_val
        if abs(diff) > 1e-10:
            note = "已修改（加快计算）" if key in ['nx', 'nb', 'nk'] else "已放宽（加快收敛）"
        else:
            note = "相同"
        print(f"{key:<15} {py_val:<20.6e} {ml_val:<20.6e} {note:<30}")
    
    print("\n经济参数:")
    print(f"{'参数':<15} {'Python值':<20} {'MATLAB值':<20} {'说明':<30}")
    print("-" * 85)
    for key in ['beta', 'sigma', 'alpha', 'delta_k', 'gamma1', 'gamma2', 'A', 'lambda0', 'cost_e']:
        py_val = python_params[key]
        ml_val = matlab_params[key]
        note = "相同" if abs(py_val - ml_val) < 1e-10 else "不同"
        print(f"{key:<15} {py_val:<20.6f} {ml_val:<20.6f} {note:<30}")
    
    log_message("\n" + "="*80)
    log_message("参数设置对比（Python vs MATLAB原始值）")
    log_message("="*80)
    log_message("\n数值参数（网格和容差）:")
    for key in ['nx', 'nb', 'nk', 'tol_bhat', 'tol_vfi', 'tol_vfi_u', 'tol_dist', 'n_howard']:
        py_val = python_params[key]
        ml_val = matlab_params[key]
        diff = py_val - ml_val
        if abs(diff) > 1e-10:
            note = "已修改（加快计算）" if key in ['nx', 'nb', 'nk'] else "已放宽（加快收敛）"
        else:
            note = "相同"
        log_message(f"{key:<15} {py_val:<20.6e} {ml_val:<20.6e} {note:<30}")

def diagnose_market_clearing():
    """诊断市场出清方程"""
    print("\n" + "="*80)
    print("市场出清方程详细诊断")
    print("="*80)
    
    # 加载稳态结果
    if not os.path.exists('steady_state_results.pkl'):
        print("\n错误：找不到steady_state_results.pkl文件")
        print("请先运行稳态计算")
        return
    
    with open('steady_state_results.pkl', 'rb') as f:
        ss_results = pickle.load(f)
    
    agg = ss_results['agg']
    prices = ss_results['prices']
    par = ss_results['par']
    
    # 解包关键变量
    C_agg = agg['C_agg']
    output_small = agg['output_small']
    cost_adj = agg['cost_adj']
    entry_cost = agg['entry_cost']
    liq = agg['liq']
    KL_ratio = prices['KL_ratio']
    delta_k = par['delta_k']
    A = par['A']
    alpha = par['alpha']
    
    # 计算LHS和aux
    LHS = C_agg - output_small + cost_adj + entry_cost - liq
    aux = A * (KL_ratio ** alpha) - delta_k  # Fun.prod_corp(KL_ratio, 1/KL_ratio) = A * KL_ratio^alpha
    
    print("\n1. 市场出清方程分解")
    print("-" * 80)
    print(f"C_agg (总消费)           = {C_agg:15.6f}")
    print(f"output_small (小企业产出)  = {output_small:15.6f}")
    print(f"cost_adj (资本调整成本)    = {cost_adj:15.6f}")
    print(f"entry_cost (进入成本)     = {entry_cost:15.6f}")
    print(f"liq (清算)               = {liq:15.6f}")
    print(f"\nLHS = C_agg - output_small + cost_adj + entry_cost - liq")
    print(f"LHS = {C_agg:.6f} - {output_small:.6f} + {cost_adj:.6f} + {entry_cost:.6f} - {liq:.6f}")
    print(f"LHS = {LHS:.6f}")
    
    if LHS < 0:
        print("\n[警告] LHS为负值！")
        print("  这意味着：C_agg + cost_adj + entry_cost < output_small + liq")
        print("  即：消费+调整成本+进入成本 < 小企业产出+清算")
        print("  总需求小于总供给，或小企业产出/清算过大。")
        print("\n  可能的原因：")
        print("    1. 小企业产出output_small过大")
        print("    2. 清算liq过大")
        print("    3. 总消费C_agg过小（工资wage可能过小）")
        print("    4. 调整成本cost_adj为负值（向下调整过多）")
    
    print("\n2. aux计算（企业部门净收益率）")
    print("-" * 80)
    print(f"KL_ratio (资本劳动比)     = {KL_ratio:15.6f}")
    print(f"A (企业部门TFP)          = {A:15.6f}")
    print(f"alpha (资本份额)          = {alpha:15.6f}")
    print(f"delta_k (折旧率)         = {delta_k:15.6f}")
    print(f"\naux = A * (KL_ratio^alpha) - delta_k")
    print(f"aux = {A:.6f} * ({KL_ratio:.6f}^{alpha:.6f}) - {delta_k:.6f}")
    print(f"aux = {A:.6f} * {KL_ratio**alpha:.6f} - {delta_k:.6f}")
    print(f"aux = {aux:.6f}")
    
    if aux <= 0:
        print("\n[警告] aux <= 0！")
        print("  这意味着：A * (KL_ratio^alpha) <= delta_k")
        print("  即：企业部门净收益率 <= 0")
        print("  这会导致K_corp无法计算或为负值。")
    
    print("\n3. K_corp计算")
    print("-" * 80)
    if aux == 0:
        print("aux = 0，无法计算K_corp")
        K_corp = 0
    else:
        K_corp = LHS / aux
        print(f"K_corp = LHS / aux")
        print(f"K_corp = {LHS:.6f} / {aux:.6f}")
        print(f"K_corp = {K_corp:.6f}")
        
        if K_corp < 0:
            print("\n[警告] K_corp为负值！")
            if LHS < 0:
                print("  原因：LHS为负值")
            if aux < 0:
                print("  原因：aux为负值")
    
    print("\n4. 关键变量检查")
    print("-" * 80)
    print(f"wage (工资)              = {prices['wage']:15.6f}")
    print(f"q (金融贴现因子)         = {prices['q']:15.6f}")
    print(f"rental (租金率)          = {prices['rental']:15.6f}")
    print(f"K_small (小企业资本)     = {agg['K_small']:15.6f}")
    print(f"L_small (小企业就业)     = {agg['L_small']:15.6f}")
    print(f"mass_small (小企业质量)  = {agg['mass_small']:15.6f}")
    
    # 检查cost_adj的组成
    print("\n5. cost_adj详细分解")
    print("-" * 80)
    capadj = agg.get('capadj', np.zeros(4))
    if len(capadj) >= 4:
        print(f"capadj[0] (向上调整)     = {capadj[0]:15.6f}")
        print(f"capadj[1] (向下调整)     = {capadj[1]:15.6f}")
        print(f"capadj[2] (进入者购买)   = {capadj[2]:15.6f}")
        print(f"capadj[3] (退出者出售)   = {capadj[3]:15.6f}")
        print(f"\ncost_adj = 向上调整 - 向下调整 + 进入者购买 - 退出者出售")
        print(f"cost_adj = {capadj[0]:.6f} - {capadj[1]:.6f} + {capadj[2]:.6f} - {capadj[3]:.6f}")
        print(f"cost_adj = {cost_adj:.6f}")
        
        if cost_adj < 0:
            print("\n[警告] cost_adj为负值！")
            print("  这意味着：向下调整 + 退出者出售 > 向上调整 + 进入者购买")
            print("  即：资本净流出 > 资本净流入")
            print("  这可能是合理的（如果企业正在收缩），但需要检查。")
    
    # 检查分布统计
    print("\n6. 分布统计")
    print("-" * 80)
    distribS = ss_results['distribS']
    mu = distribS['mu']
    mu_active = distribS['mu_active']
    entry_vec = distribS['entry_vec']
    
    print(f"mu总和 (总企业测度)      = {np.sum(mu):15.6f}")
    print(f"mu_active总和 (活跃企业) = {np.sum(mu_active):15.6f}")
    print(f"entry_vec总和 (进入者)   = {np.sum(entry_vec):15.6f}")
    print(f"entry_vec最小值          = {np.min(entry_vec):15.6e}")
    print(f"entry_vec最大值          = {np.max(entry_vec):15.6e}")
    
    if np.any(entry_vec < 0):
        print("\n[警告] entry_vec中存在负值！")
        print(f"  最小值 = {np.min(entry_vec):.6e}")
        print(f"  负值数量 = {np.sum(entry_vec < 0)}")
    
    # 记录到日志
    log_message("\n" + "="*80)
    log_message("市场出清方程详细诊断")
    log_message("="*80)
    log_message("\n1. 市场出清方程分解")
    log_message(f"C_agg = {C_agg:.6f}")
    log_message(f"output_small = {output_small:.6f}")
    log_message(f"cost_adj = {cost_adj:.6f}")
    log_message(f"entry_cost = {entry_cost:.6f}")
    log_message(f"liq = {liq:.6f}")
    log_message(f"LHS = {LHS:.6f}")
    if LHS < 0:
        log_message("[警告] LHS为负值！")
    log_message(f"\n2. aux计算")
    log_message(f"aux = {aux:.6f}")
    if aux <= 0:
        log_message("[警告] aux <= 0！")
    log_message(f"\n3. K_corp = {K_corp:.6f}")
    if K_corp < 0:
        log_message("[警告] K_corp为负值！")

if __name__ == '__main__':
    compare_parameters()
    diagnose_market_clearing()
    print("\n" + "="*80)
    print("诊断完成")
    print("="*80)


















