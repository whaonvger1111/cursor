"""
计算四种类型的资本调整
1. 活跃企业的向上调整
2. 活跃企业的向下调整
3. 进入者购买的资本
4. 退出者出售的资本
"""
import numpy as np


def compute_cap_adj(pol_kp, mu, mu_active, phi_dist, pol_entry, pol_exit,
                    mass, k_grid, delta, psi):
    """
    计算资本调整
    
    参数:
    pol_kp: 下一期资本政策, 维度 (nk,nb,nx)
    mu, mu_active, phi_dist: 分布（在位者、活跃企业、进入者）, 维度 (nk,nb,nx)
    pol_entry, pol_exit: 进入和退出政策, 维度 (nk,nb,nx)
    mass: 标量，潜在进入者质量
    k_grid: 维度 nk
    delta: 标量，资本折旧率
    psi: 标量，外生退出率
    
    返回:
    capadj: 向量 4x1
    """
    _, nb, nx = pol_kp.shape
    
    k_arr = np.tile(k_grid[:, np.newaxis, np.newaxis], (1, nb, nx))
    
    up_active = np.maximum(pol_kp - (1 - delta) * k_arr, 0)
    down_active = np.maximum((1 - delta) * k_arr - pol_kp, 0)
    
    capadj = np.zeros(4)
    # 1. 活跃企业的向上调整
    capadj[0] = np.sum(up_active * mu_active)
    
    # 2. 活跃企业的向下调整
    capadj[1] = np.sum(down_active * mu_active)
    
    # 3. 进入者购买的资本
    capadj[2] = np.sum(mass * k_arr * pol_entry * phi_dist)
    
    # 4. 退出者出售的资本
    exit_all = psi + (1 - psi) * pol_exit
    capadj[3] = np.sum(k_arr * exit_all * mu)
    
    return capadj

