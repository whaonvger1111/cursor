"""
计算稳态的加总变量(C,N等)
"""
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from fun import Fun
from sub.sub_aggregates_onestep import sub_aggregates_onestep
from compute_cap_adj import compute_cap_adj
from tools.v2struct import pack_to_struct


def fun_aggregates(par, sol, distribS, phi_dist, prices):
    """
    计算稳态的加总变量
    
    参数:
    par: 参数字典
    sol: 解字典
    distribS: 分布字典
    phi_dist: 进入者分布
    prices: 价格字典
    
    返回:
    agg: 加总变量字典
    """
    # 输入检查
    if not isinstance(par, dict):
        raise TypeError("输入<par>在fun_aggregates中必须是字典！")
    if not isinstance(sol, dict):
        raise TypeError("输入<sol>在fun_aggregates中必须是字典！")
    if not isinstance(prices, dict):
        raise TypeError("输入<prices>在fun_aggregates中必须是字典！")
    
    # 解包SOL
    # 注意: (1-psi)(1-d^l)=1-(psi+(1-psi)d^l)
    pol_exit = sol['pol_exit']
    pol_entry = sol['pol_entry']
    pol_kp_ind = sol['pol_kp_ind']
    pol_kp = sol['pol_kp']
    
    # 解包distribS
    mu = distribS['mu']
    mu_active = distribS['mu_active']
    entry_vec = distribS['entry_vec']
    
    # 解包参数
    delta_k = par['delta_k']
    x_grid = par['x_grid']
    k_grid = par['k_grid']
    mass = par['mass']
    psi = par['psi']
    
    # 解包价格
    wage = prices['wage']
    KL_ratio = prices['KL_ratio']
    
    C_agg = Fun.C_foc_labor(wage, par)  # 总消费，来自FOC
    
    # kappa的边际分布，mu(k,b,x)
    mu_kappa = np.sum(mu_active, axis=(1, 2))
    
    # 小企业质量
    mass_small = np.sum(mu_active)
    # 小企业资本
    K_small = np.dot(k_grid.flatten(), mu_kappa)
    
    # 活跃企业和进入者的测度
    Mactive = np.sum(mu_active)
    Mentr = np.sum(entry_vec)
    
    # 我们包括外生退出
    exit_all = psi + (1 - psi) * pol_exit  # 维度: (nk,nb,nx)
    
    # 计算进入、产出（小企业）、清算（小企业）和就业（小企业）的加总值
    A = 1  # 稳态中生产率冲击等于1
    entry_cost, output_small, liq, L_small, cost_adj, exit, entry = \
        sub_aggregates_onestep(mu, mu_active, pol_kp_ind, pol_entry, exit_all,
                              phi_dist, wage, mass, A, par)
    
    # 通过在位企业测度归一化得到退出率
    exit_rate = exit / np.sum(mu) if np.sum(mu) > 0 else 0
    # 通过活跃企业测度归一化得到进入率
    entry_rate = entry / np.sum(mu_active) if np.sum(mu_active) > 0 else 0
    
    # 计算按类型分类的资本调整
    capadj = compute_cap_adj(pol_kp, mu, mu_active, phi_dist,
                            pol_entry, pol_exit, mass, k_grid, delta_k, psi)
    
    # 计算排除微型企业的退出
    exits_temp = 0
    mass_temp = 0
    for x_c in range(par['nx']):
        # 这里我们不乘以A_small
        x_val = x_grid[x_c]
        for k_c in range(par['nk']):
            kappa = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
            l_opt = Fun.fun_l(x_val, wage, kappa, par)
            if l_opt > par.get('emp_min', 0):
                exits_temp += np.sum(exit_all[k_c, :, x_c] * mu[k_c, :, x_c])
                mass_temp += np.sum(mu[k_c, :, x_c])
    
    exit_emp = exits_temp
    exit_rate_emp = exits_temp / mass_temp if mass_temp > 0 else 0
    
    # 市场出清方程的左端（第49页）
    LHS = C_agg - output_small + cost_adj + entry_cost - liq
    aux = Fun.prod_corp(KL_ratio, 1 / KL_ratio, par) - delta_k
    
    # 企业部门资本
    K_corp = LHS / aux if aux != 0 else 0
    # 企业部门就业
    L_corp = K_corp / KL_ratio if KL_ratio > 0 else 0
    # 企业部门产出
    Y_corp = Fun.prod_corp(KL_ratio, L_corp, par)
    
    # 总就业：企业部门加上小企业
    L_agg = L_corp + L_small
    
    # Y_small是小企业产出，包括清算、进入和调整成本
    Y_small = output_small - cost_adj + liq - entry_cost
    
    # 总产出
    Y_agg = Y_corp + output_small
    
    # 家庭拥有的资本（租赁给企业部门和小企业）
    K_agg = K_corp + K_small
    
    # 稳态中家庭资本投资
    InvK_corp = delta_k * K_corp
    
    # 经济中的所有投资（论文中的\tilde{I}）
    InvK = InvK_corp + entry_cost - liq + cost_adj
    
    # 将加总变量打包到字典中
    agg = pack_to_struct(
        C_agg=C_agg, K_agg=K_agg, K_corp=K_corp, K_small=K_small, mass_small=mass_small,
        L_agg=L_agg, L_corp=L_corp, L_small=L_small, Y_agg=Y_agg, Y_corp=Y_corp,
        Y_small=Y_small, output_small=output_small, liq=liq, entry=entry, entry_rate=entry_rate,
        entry_cost=entry_cost, Mactive=Mactive, Mentr=Mentr, InvK=InvK, InvK_corp=InvK_corp,
        exit_rate=exit_rate, exit=exit, cost_adj=cost_adj, capadj=capadj,
        exit_emp=exit_emp, exit_rate_emp=exit_rate_emp
    )
    
    return agg

