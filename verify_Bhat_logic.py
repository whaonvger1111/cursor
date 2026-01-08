"""
验证B_hat的计算逻辑是否与MATLAB一致
"""
import numpy as np
import pickle
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from fun import Fun

def verify_Bhat_logic():
    """验证B_hat的计算逻辑"""
    print("\n" + "="*80)
    print("B_hat计算逻辑验证")
    print("="*80)
    
    # 加载稳态结果
    if not os.path.exists('steady_state_results.pkl'):
        print("\n错误：找不到steady_state_results.pkl文件")
        return
    
    with open('steady_state_results.pkl', 'rb') as f:
        ss_results = pickle.load(f)
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    prices = ss_results.get('prices', {})
    
    if 'B_hat' not in sol:
        print("\n错误：sol中没有B_hat")
        return
    
    B_hat = sol['B_hat']
    pol_bp_unc = sol.get('pol_bp_unc', None)
    pol_kp_unc = sol.get('pol_kp_unc', None)
    profit_mat = sol.get('profit_mat', None)
    
    print(f"\n1. B_hat基本信息:")
    print("-" * 80)
    print(f"  形状: {B_hat.shape}")
    print(f"  最小值: {np.min(B_hat):.6f}")
    print(f"  最大值: {np.max(B_hat):.6f}")
    print(f"  平均值: {np.mean(B_hat):.6f}")
    print(f"  负值数量: {np.sum(B_hat < 0)}")
    print(f"  负值比例: {100*np.sum(B_hat < 0)/B_hat.size:.2f}%")
    
    if np.all(B_hat < 0):
        print("\n  [严重问题] B_hat全部为负值！")
        print("  B_hat应该表示与非负股息一致的最高债务水平，通常应该为非负值。")
    
    # 检查B_hat的计算公式
    print(f"\n2. B_hat计算公式验证:")
    print("-" * 80)
    print("  根据代码，B_hat的计算公式为：")
    print("  B_hat_new = profit_mat + q * pol_bp_unc - adjcost(kp_mat, k_grid, theta, delta)")
    print("\n  其中：")
    print("    - profit_mat: 静态利润")
    print("    - q: 金融贴现因子")
    print("    - pol_bp_unc: 无约束企业的b'(k,x)政策")
    print("    - adjcost: 资本调整成本")
    
    k_grid = par.get('k_grid', None)
    
    if profit_mat is not None and pol_bp_unc is not None and pol_kp_unc is not None and k_grid is not None:
        q = prices.get('q', par.get('beta', 0.989))
        theta = par.get('theta', 0.7)
        delta = par.get('delta_k', 0.015)
        
        if k_grid is not None:
            # 重新计算B_hat
            kp_mat = np.clip(pol_kp_unc, k_grid[0], k_grid[-1])
            adjcost_val = Fun.adjcost(kp_mat, k_grid, theta, delta)
            B_hat_recalc = profit_mat + q * pol_bp_unc - adjcost_val
            
            print(f"\n  重新计算B_hat:")
            print(f"    profit_mat范围: [{np.min(profit_mat):.6f}, {np.max(profit_mat):.6f}]")
            print(f"    pol_bp_unc范围: [{np.min(pol_bp_unc):.6f}, {np.max(pol_bp_unc):.6f}]")
            print(f"    adjcost范围: [{np.min(adjcost_val):.6f}, {np.max(adjcost_val):.6f}]")
            print(f"    q = {q:.6f}")
            print(f"    B_hat_recalc范围: [{np.min(B_hat_recalc):.6f}, {np.max(B_hat_recalc):.6f}]")
            print(f"    B_hat原始范围: [{np.min(B_hat):.6f}, {np.max(B_hat):.6f}]")
            
            # 检查是否一致
            diff = np.abs(B_hat - B_hat_recalc)
            max_diff = np.max(diff)
            mean_diff = np.mean(diff)
            print(f"\n  与原始B_hat的差异:")
            print(f"    最大差异: {max_diff:.6e}")
            print(f"    平均差异: {mean_diff:.6e}")
            
            if max_diff < 1e-6:
                print("    [OK] 重新计算的B_hat与原始B_hat一致")
            else:
                print("    [警告] 重新计算的B_hat与原始B_hat不一致")
    
    # 检查pol_bp_unc的计算
    print(f"\n3. pol_bp_unc计算验证:")
    print("-" * 80)
    if pol_bp_unc is not None:
        print(f"  pol_bp_unc范围: [{np.min(pol_bp_unc):.6f}, {np.max(pol_bp_unc):.6f}]")
        print(f"  负值数量: {np.sum(pol_bp_unc < 0)}")
        print(f"  负值比例: {100*np.sum(pol_bp_unc < 0)/pol_bp_unc.size:.2f}%")
        
        lambda_val = par.get('lambda0', 1.0) * theta * (1 - delta)
        print(f"\n  根据代码，pol_bp_unc的计算公式为：")
        print(f"  pol_bp_unc = min(lambda_val * kp_val, min(B_hat_interp))")
        print(f"  其中 lambda_val = lambda0 * theta * (1-delta) = {lambda_val:.6f}")
        
        if pol_kp_unc is not None:
            lambda_bound = lambda_val * pol_kp_unc
            print(f"  lambda_val * kp范围: [{np.min(lambda_bound):.6f}, {np.max(lambda_bound):.6f}]")
            
            # 检查pol_bp_unc是否超过lambda_bound
            exceed_mask = pol_bp_unc > lambda_bound
            if np.any(exceed_mask):
                print(f"  [警告] {np.sum(exceed_mask)}个值超过lambda_bound上界")
            else:
                print(f"  [OK] 所有pol_bp_unc值都在lambda_bound上界内")
    
    # 检查B_hat的经济含义
    print(f"\n4. B_hat经济含义检查:")
    print("-" * 80)
    print("  B_hat应该表示：与非负股息一致的最高债务水平")
    print("  这意味着：")
    print("    - B_hat应该 >= 0（债务不能为负）")
    print("    - B_hat应该 <= lambda_val * k（抵押约束）")
    print("    - B_hat应该使得股息非负：profit + q*b' - adjcost >= 0")
    
    if np.all(B_hat < 0):
        print("\n  [严重问题] B_hat全部为负值，这不符合经济含义！")
        print("  可能的原因：")
        print("    1. profit_mat过小或为负")
        print("    2. adjcost过大")
        print("    3. pol_bp_unc为负（企业持有资产而非债务）")
        print("    4. 计算公式有误")
    
    # 检查profit_mat
    print(f"\n5. profit_mat检查:")
    print("-" * 80)
    if profit_mat is not None:
        print(f"  profit_mat范围: [{np.min(profit_mat):.6f}, {np.max(profit_mat):.6f}]")
        print(f"  负值数量: {np.sum(profit_mat < 0)}")
        print(f"  负值比例: {100*np.sum(profit_mat < 0)/profit_mat.size:.2f}%")
        
        if np.any(profit_mat < 0):
            print("  [警告] profit_mat中存在负值（企业亏损）")
    
    # 检查adjcost
    print(f"\n6. adjcost检查:")
    print("-" * 80)
    k_grid = par.get('k_grid', None)
    if pol_kp_unc is not None and k_grid is not None:
        theta = par.get('theta', 0.7)
        delta = par.get('delta_k', 0.015)
        kp_mat = np.clip(pol_kp_unc, k_grid[0], k_grid[-1])
        adjcost_val = Fun.adjcost(kp_mat, k_grid, theta, delta)
        print(f"  adjcost范围: [{np.min(adjcost_val):.6f}, {np.max(adjcost_val):.6f}]")
        print(f"  负值数量: {np.sum(adjcost_val < 0)}")
        print(f"  负值比例: {100*np.sum(adjcost_val < 0)/adjcost_val.size:.2f}%")
        
        if np.any(adjcost_val < 0):
            print("  [注意] adjcost中存在负值（向下调整，企业收缩资本）")
    
    # 记录到日志
    def log_message(msg):
        try:
            with open('steady_state_iterations.log', 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except:
            pass
    
    log_message("\n" + "="*80)
    log_message("B_hat计算逻辑验证")
    log_message("="*80)
    log_message(f"\nB_hat范围: [{np.min(B_hat):.6f}, {np.max(B_hat):.6f}]")
    log_message(f"负值数量: {np.sum(B_hat < 0)}/{B_hat.size}")
    if np.all(B_hat < 0):
        log_message("[严重问题] B_hat全部为负值！")

if __name__ == '__main__':
    verify_Bhat_logic()

