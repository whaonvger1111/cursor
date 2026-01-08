"""
更新政策函数：债务、资本和政策索引
"""
import numpy as np
from fun import Fun


def fun_pol_update(val, val_unc, pol_bp_unc, pol_kp_unc, pol_kp_ind_con, 
                   profit_mat, B_hat, k_grid, b_grid, q, theta, delta):
    """
    更新政策函数
    
    参数:
    val: 价值函数, 维度: (nk,nb,nx)
    val_unc: 无约束企业的价值函数, 维度: (nk,nb,nx)
    pol_bp_unc: 无约束企业的债务政策, 维度: (nk,nx)
    pol_kp_unc: 无约束企业的资本政策, 维度: (nk,nx)
    pol_kp_ind_con: 约束企业的资本政策索引, 维度: (nk,nb,nx)
    profit_mat: 利润矩阵, 维度: (nk,nx)
    B_hat: 最大债务, 维度: (nk,nx)
    k_grid: 资本网格
    b_grid: 债务网格, 维度: (nk,nb)
    q,theta,delta: 标量参数
    
    返回:
    pol_debt: 债务政策, 维度: (nk,nb,nx)
    pol_kp: 资本政策, 维度: (nk,nb,nx)
    pol_kp_ind: 资本政策索引, 维度: (nk,nb,nx)
    val: 更新的价值函数, 维度: (nk,nb,nx)
    """
    nk, nb, nx = val.shape
    
    # 确保k_grid是一维数组
    k_grid_flat = np.asarray(k_grid).flatten()
    if len(k_grid_flat) != nk:
        raise ValueError(f'k_grid长度 {len(k_grid_flat)} 与 nk {nk} 不匹配')
    
    # 计算由方程(25)隐含的最优债务政策
    pol_debt = np.zeros((nk, nb, nx))
    pol_kp = np.zeros((nk, nb, nx))
    pol_kp_ind = np.ones((nk, nb, nx), dtype=int)
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                k_val = k_grid_flat[k_c]
                b_val = b_grid[k_c, b_c]
                profit_val = profit_mat[k_c, x_c]
                
                if b_val <= B_hat[k_c, x_c]:  # 企业无约束
                    val[k_c, b_c, x_c] = val_unc[k_c, b_c, x_c]
                    pol_debt[k_c, b_c, x_c] = pol_bp_unc[k_c, x_c]
                    pol_kp[k_c, b_c, x_c] = pol_kp_unc[k_c, x_c]
                    # 最近的网格点
                    pol_kp_ind[k_c, b_c, x_c] = np.argmin(np.abs(k_grid_flat - pol_kp[k_c, b_c, x_c]))
                else:  # 企业有约束
                    kp_ind = int(pol_kp_ind_con[k_c, b_c, x_c])
                    # 确保索引在有效范围内
                    kp_ind = np.clip(kp_ind, 0, nk - 1)
                    kprime = k_grid_flat[kp_ind]
                    # 确保b_grid索引有效
                    bprime_lb = b_grid[kp_ind, 0] if kp_ind < nk else b_grid[0, 0]
                    bprime = np.maximum(bprime_lb,
                                       (1 / q) * (b_val - profit_val + 
                                                 Fun.adjcost_scal(kprime, k_val, theta, delta)))
                    pol_debt[k_c, b_c, x_c] = bprime
                    pol_kp[k_c, b_c, x_c] = kprime
                    pol_kp_ind[k_c, b_c, x_c] = kp_ind
    
    return pol_debt, pol_kp, pol_kp_ind, val

