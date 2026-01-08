"""
单步加总计算
这个子函数被fun_aggregates和fun_aggregates_tran调用
注意：A是标量，等于生产率冲击。在稳态中，A=1由构造决定
"""
import numpy as np
from fun import Fun


def sub_aggregates_onestep(mu, mu_active, pol_kp_ind, pol_entry, exit_all,
                           phi_dist, wage, mass, A, par):
    """
    单步加总计算
    
    参数:
    mu: 分布
    mu_active: 活跃企业分布
    pol_kp_ind: 资本政策索引
    pol_entry: 进入政策
    exit_all: 总退出率
    phi_dist: 进入者分布
    wage: 工资
    mass: 潜在进入者质量
    A: 生产率冲击（标量）
    par: 参数字典
    
    返回:
    entry: 进入成本
    output_small: 小企业产出
    liq: 清算
    L_small: 小企业就业
    cost_adj: 资本调整成本
    exit_rate: 退出率
    entry_rate: 进入率
    """
    # 解包
    k_grid = par['k_grid']
    x_grid = par['x_grid']
    fixcost = par['fixcost']
    cost_e = par['cost_e']
    theta = par['theta']
    delta_k = par['delta_k']
    nb = par['nb']
    nx = par['nx']
    nk = par['nk']
    
    # 确保k_grid是一维数组（处理可能的(nk,1)形状）
    k_grid = k_grid.flatten() if k_grid.ndim > 1 else k_grid
    
    kappa = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
    c = np.tile(fixcost[:, np.newaxis, np.newaxis], (1, nb, nx))
    # 关键修复：prod_small和fun_l函数内部都已经乘以par['A']
    # 与fun_vfi1.py中profit_mat的计算保持一致（直接使用x_grid，不乘以A）
    # 注意：参数A是小企业部门的生产率冲击，但在稳态中A=1
    # 如果这里乘以A，会导致双重计算，因为prod_small内部已经乘以par['A']
    x_val = np.tile(x_grid[np.newaxis, np.newaxis, :], (nk, nb, 1))
    
    l_opt = Fun.fun_l(x_val, wage, kappa, par)  # (nk,nb,nx)
    y_opt = Fun.prod_small(x_val, kappa, l_opt, c, par)  # (nk,nb,nx)
    
    L_small = np.sum(l_opt * mu_active)  # 标量
    output_small = np.sum(y_opt * mu_active)  # 标量
    liq = np.sum(theta * (1 - delta_k) * kappa * exit_all * mu)  # 标量
    # entry是进入的总成本
    entry = np.sum(mass * (kappa + cost_e) * pol_entry * phi_dist)  # 标量
    # entry_rate是进入者的测度
    entry_rate = np.sum(mass * pol_entry * phi_dist)  # 标量
    # exit_rate是退出企业的测度
    exit_rate = np.sum(exit_all * mu)  # 标量
    
    cost_adj = 0  # 资本调整成本（小企业）
    
    for x_c in range(nx):
        for b_c in range(nb):
            k_val = k_grid  # (nk,)
            kp_val = k_grid[pol_kp_ind[:, b_c, x_c].astype(int)]
            temp = Fun.adjcost(kp_val, k_val, theta, delta_k) * mu_active[:, b_c, x_c]
            cost_adj += np.sum(temp)
    
    return entry, output_small, liq, L_small, cost_adj, exit_rate, entry_rate
