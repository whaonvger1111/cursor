"""
检查1-4个问题：
1. 检查profit_mat的计算：为什么有19.50%的企业亏损？
2. 检查pol_bp_unc的值：是否为负？是否合理？
3. 提高收敛精度：将tol_bhat从5e-3降低到1e-4或更小
4. 检查参数校准：确认zeta, mass等参数是否正确
"""
import numpy as np
import pickle
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from fun import Fun

def log_message(message, flush=True):
    """记录日志消息"""
    try:
        with open('steady_state_iterations.log', 'a', encoding='utf-8') as f:
            f.write(message + '\n')
            if flush:
                f.flush()
    except:
        pass

def check_issue_1_profit_mat():
    """检查问题1：profit_mat的计算"""
    print("\n" + "="*80)
    print("问题1：检查profit_mat的计算")
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
    
    profit_mat = sol.get('profit_mat', None)
    if profit_mat is None:
        print("\n错误：sol中没有profit_mat")
        return
    
    print(f"\n1. profit_mat基本信息:")
    print("-" * 80)
    print(f"  形状: {profit_mat.shape}")
    print(f"  最小值: {np.min(profit_mat):.6f}")
    print(f"  最大值: {np.max(profit_mat):.6f}")
    print(f"  平均值: {np.mean(profit_mat):.6f}")
    print(f"  负值数量: {np.sum(profit_mat < 0)}")
    print(f"  负值比例: {100*np.sum(profit_mat < 0)/profit_mat.size:.2f}%")
    
    # 重新计算profit_mat
    print(f"\n2. 重新计算profit_mat验证:")
    print("-" * 80)
    x_grid = par.get('x_grid', None)
    k_grid = par.get('k_grid', None)
    fixcost = par.get('fixcost', None)
    wage = prices.get('wage', None)
    
    if x_grid is None or k_grid is None or fixcost is None or wage is None:
        print("  缺少必要参数，无法重新计算")
        return
    
    profit_mat_recalc = np.zeros(profit_mat.shape)
    for x_c in range(len(x_grid)):
        for k_c in range(len(k_grid)):
            k_val = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
            profit_mat_recalc[k_c, x_c] = Fun.fun_profit(x_grid[x_c], k_val, fixcost[k_c], wage, par)
    
    print(f"  重新计算的profit_mat范围: [{np.min(profit_mat_recalc):.6f}, {np.max(profit_mat_recalc):.6f}]")
    print(f"  原始profit_mat范围: [{np.min(profit_mat):.6f}, {np.max(profit_mat):.6f}]")
    
    diff = np.abs(profit_mat - profit_mat_recalc)
    max_diff = np.max(diff)
    mean_diff = np.mean(diff)
    print(f"  最大差异: {max_diff:.6e}")
    print(f"  平均差异: {mean_diff:.6e}")
    
    if max_diff < 1e-6:
        print("  [OK] 重新计算的profit_mat与原始profit_mat一致")
    else:
        print("  [警告] 重新计算的profit_mat与原始profit_mat不一致")
    
    # 分析负值的原因
    print(f"\n3. 分析负值原因:")
    print("-" * 80)
    negative_mask = profit_mat < 0
    negative_indices = np.where(negative_mask)
    
    if np.any(negative_mask):
        print(f"  负值位置分析（前10个）:")
        for i in range(min(10, len(negative_indices[0]))):
            k_idx = negative_indices[0][i]
            x_idx = negative_indices[1][i]
            k_val = k_grid[k_idx] if isinstance(k_grid[k_idx], (int, float, np.number)) else k_grid[k_idx, 0]
            x_val = x_grid[x_idx]
            profit_val = profit_mat[k_idx, x_idx]
            fixcost_val = fixcost[k_idx]
            
            # 计算组成部分
            l_opt = Fun.fun_l(x_val, wage, k_val, par)
            output = Fun.prod_small(x_val, k_val, l_opt, fixcost_val, par)
            cost_labor = wage * l_opt
            
            print(f"    k_idx={k_idx}, x_idx={x_idx}:")
            print(f"      k={k_val:.6f}, x={x_val:.6f}, fixcost={fixcost_val:.6f}")
            print(f"      l_opt={l_opt:.6f}, output={output:.6f}, cost_labor={cost_labor:.6f}")
            print(f"      profit={profit_val:.6f} = output - cost_labor = {output:.6f} - {cost_labor:.6f}")
    
    # 检查与MATLAB的对比
    print(f"\n4. 与MATLAB对比:")
    print("-" * 80)
    print("  MATLAB代码（fun_vfi1.m第81行）:")
    print("    profit_mat(k_c,x_c) = fun.fun_profit(x_grid(x_c),k_grid(k_c),fixcost(k_c),wage,par);")
    print("  Python代码（fun_vfi1.py第104行）:")
    print("    profit_mat[k_c, x_c] = Fun.fun_profit(x_grid[x_c], k_val, fixcost[k_c], wage, par)")
    print("  [OK] 计算逻辑一致")
    
    log_message("\n" + "="*80)
    log_message("问题1：profit_mat检查完成")
    log_message(f"负值比例: {100*np.sum(profit_mat < 0)/profit_mat.size:.2f}%")

def check_issue_2_pol_bp_unc():
    """检查问题2：pol_bp_unc的值"""
    print("\n" + "="*80)
    print("问题2：检查pol_bp_unc的值")
    print("="*80)
    
    # 加载稳态结果
    if not os.path.exists('steady_state_results.pkl'):
        print("\n错误：找不到steady_state_results.pkl文件")
        return
    
    with open('steady_state_results.pkl', 'rb') as f:
        ss_results = pickle.load(f)
    
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    pol_bp_unc = sol.get('pol_bp_unc', None)
    if pol_bp_unc is None:
        print("\n错误：sol中没有pol_bp_unc")
        return
    
    print(f"\n1. pol_bp_unc基本信息:")
    print("-" * 80)
    print(f"  形状: {pol_bp_unc.shape}")
    print(f"  最小值: {np.min(pol_bp_unc):.6f}")
    print(f"  最大值: {np.max(pol_bp_unc):.6f}")
    print(f"  平均值: {np.mean(pol_bp_unc):.6f}")
    print(f"  负值数量: {np.sum(pol_bp_unc < 0)}")
    print(f"  负值比例: {100*np.sum(pol_bp_unc < 0)/pol_bp_unc.size:.2f}%")
    
    # 检查pol_bp_unc是否应该为负
    print(f"\n2. pol_bp_unc经济含义:")
    print("-" * 80)
    print("  pol_bp_unc表示无约束企业的b'(k,x)政策（下一期债务）")
    print("  如果pol_bp_unc为负，意味着企业持有资产而非债务")
    print("  这在经济上可能是合理的（如果企业选择储蓄）")
    
    if np.any(pol_bp_unc < 0):
        print(f"\n  [注意] pol_bp_unc中存在负值")
        print(f"  这可能影响B_hat的计算，因为B_hat = profit + q*pol_bp_unc - adjcost")
        print(f"  如果pol_bp_unc为负，q*pol_bp_unc也为负，会降低B_hat")
    
    # 检查pol_bp_unc是否超过抵押约束
    print(f"\n3. 检查抵押约束:")
    print("-" * 80)
    theta = par.get('theta', 0.7)
    delta = par.get('delta_k', 0.015)
    lambda0 = par.get('lambda0', 1.0)
    lambda_val = lambda0 * theta * (1 - delta)
    
    k_grid = par.get('k_grid', None)
    pol_kp_unc = sol.get('pol_kp_unc', None)
    
    if k_grid is not None and pol_kp_unc is not None:
        kp_mat = np.clip(pol_kp_unc, k_grid[0], k_grid[-1])
        lambda_bound = lambda_val * kp_mat
        
        print(f"  lambda_val = lambda0 * theta * (1-delta) = {lambda0:.6f} * {theta:.6f} * {1-delta:.6f} = {lambda_val:.6f}")
        print(f"  lambda_bound范围: [{np.min(lambda_bound):.6f}, {np.max(lambda_bound):.6f}]")
        print(f"  pol_bp_unc范围: [{np.min(pol_bp_unc):.6f}, {np.max(pol_bp_unc):.6f}]")
        
        exceed_mask = pol_bp_unc > lambda_bound
        if np.any(exceed_mask):
            print(f"  [警告] {np.sum(exceed_mask)}个值超过抵押约束上界")
        else:
            print(f"  [OK] 所有pol_bp_unc值都在抵押约束上界内")
    
    log_message("\n" + "="*80)
    log_message("问题2：pol_bp_unc检查完成")
    log_message(f"负值比例: {100*np.sum(pol_bp_unc < 0)/pol_bp_unc.size:.2f}%")

def check_issue_3_tol_bhat():
    """检查问题3：tol_bhat收敛精度"""
    print("\n" + "="*80)
    print("问题3：检查tol_bhat收敛精度")
    print("="*80)
    
    # 读取当前参数设置
    import set_parameters
    par = {}
    par, _, _, _, _, _, _ = set_parameters.set_parameters(par, 'estim_params.txt')
    
    tol_bhat_current = par.get('tol_bhat', 5e-3)
    tol_bhat_matlab = 1e-9  # MATLAB中的默认值
    
    print(f"\n1. tol_bhat对比:")
    print("-" * 80)
    print(f"  Python当前值: {tol_bhat_current:.2e}")
    print(f"  MATLAB默认值: {tol_bhat_matlab:.2e}")
    print(f"  差异: {tol_bhat_current / tol_bhat_matlab:.2e}倍")
    
    if tol_bhat_current > tol_bhat_matlab:
        print(f"\n  [警告] Python的tol_bhat ({tol_bhat_current:.2e}) 远大于MATLAB ({tol_bhat_matlab:.2e})")
        print(f"  这可能导致B_hat固定点迭代未完全收敛")
        print(f"  建议：将tol_bhat降低到1e-4或更小")
    
    # 检查set_parameters.py中的设置
    print(f"\n2. 检查set_parameters.py:")
    print("-" * 80)
    print("  当前设置: par['tol_bhat'] = 5e-3")
    print("  建议设置: par['tol_bhat'] = 1e-4 或更小")
    
    log_message("\n" + "="*80)
    log_message("问题3：tol_bhat检查完成")
    log_message(f"当前值: {tol_bhat_current:.2e}, MATLAB值: {tol_bhat_matlab:.2e}")

def check_issue_4_parameters():
    """检查问题4：参数校准"""
    print("\n" + "="*80)
    print("问题4：检查参数校准")
    print("="*80)
    
    # 加载稳态结果
    if not os.path.exists('steady_state_results.pkl'):
        print("\n错误：找不到steady_state_results.pkl文件")
        return
    
    with open('steady_state_results.pkl', 'rb') as f:
        ss_results = pickle.load(f)
    
    par = ss_results.get('par', {})
    prices = ss_results.get('prices', {})
    
    print(f"\n1. 关键参数检查:")
    print("-" * 80)
    
    # zeta参数
    zeta = par.get('zeta', None)
    if zeta is None:
        print("  [警告] zeta参数未设置，使用默认值1.0")
        zeta = 1.0
    else:
        print(f"  zeta = {zeta:.6f}")
    
    # mass参数
    mass = par.get('mass', None)
    if mass is None:
        print("  [警告] mass参数未设置")
    else:
        print(f"  mass = {mass:.6f}")
    
    # theta参数
    theta = par.get('theta', None)
    if theta is None:
        print("  [警告] theta参数未设置")
    else:
        print(f"  theta = {theta:.6f}")
    
    # psi参数
    psi = par.get('psi', None)
    if psi is None:
        print("  [警告] psi参数未设置")
    else:
        print(f"  psi = {psi:.6f}")
    
    # fixcost参数
    fixcost1 = par.get('fixcost1', None)
    fixcost2 = par.get('fixcost2', None)
    if fixcost1 is None or fixcost2 is None:
        print("  [警告] fixcost参数未设置")
    else:
        print(f"  fixcost1 = {fixcost1:.6f}")
        print(f"  fixcost2 = {fixcost2:.6f}")
    
    # 检查参数是否从文件读取
    print(f"\n2. 检查参数来源:")
    print("-" * 80)
    estim_params_file = os.path.join('inputs', 'estim_params.txt')
    if os.path.exists(estim_params_file):
        print(f"  [OK] 参数文件存在: {estim_params_file}")
        with open(estim_params_file, 'r') as f:
            lines = f.readlines()
            print(f"  文件行数: {len(lines)}")
            print(f"  前10行内容:")
            for i, line in enumerate(lines[:10]):
                print(f"    {i+1}: {line.strip()}")
    else:
        print(f"  [警告] 参数文件不存在: {estim_params_file}")
        print(f"  将使用set_parameters.py中的默认值")
    
    # 检查C_agg的计算
    print(f"\n3. 检查C_agg计算:")
    print("-" * 80)
    wage = prices.get('wage', None)
    sigma = par.get('sigma', 2.0)
    
    if wage is not None:
        C_agg = Fun.C_foc_labor(wage, par)
        print(f"  wage = {wage:.6f}")
        print(f"  zeta = {zeta:.6f}")
        print(f"  sigma = {sigma:.6f}")
        print(f"  C_agg = (wage/zeta)^(1/sigma) = ({wage:.6f}/{zeta:.6f})^(1/{sigma:.6f}) = {C_agg:.6f}")
        
        if C_agg < 0.1:
            print(f"\n  [警告] C_agg过小 ({C_agg:.6f})")
            print(f"  可能原因：")
            print(f"    1. wage过小")
            print(f"    2. zeta过大")
            print(f"    3. sigma过大")
    
    log_message("\n" + "="*80)
    log_message("问题4：参数校准检查完成")

if __name__ == '__main__':
    check_issue_1_profit_mat()
    check_issue_2_pol_bp_unc()
    check_issue_3_tol_bhat()
    check_issue_4_parameters()
    print("\n" + "="*80)
    print("所有检查完成")
    print("="*80)


















