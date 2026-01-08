"""
计算无约束企业的投资政策
这需要计算k_star1和k_star2
"""
import numpy as np


def sub_investment_onestep(V1, k_grid, pi_x, theta, delta, q, psi):
    """
    计算无约束企业的投资政策
    
    参数:
    V1: 无约束企业的价值V(k,x), 维度: (nk,nx)
    k_grid: 资本网格
    pi_x: 冲击x的转移矩阵, 维度: (nx,nx)
    theta,delta,q,psi: 标量参数
    
    返回:
    pol_kp_unc: k'(k,x)对于无约束企业。这是值（不是索引），不在网格k_grid上
    """
    nk = len(k_grid)
    nx = pi_x.shape[0]
    
    aux1 = -(1 - q * psi * theta * (1 - delta))
    aux2 = -(1 - q * psi * (1 - delta)) * theta
    
    k_star1 = np.zeros(nx)
    k_star2 = np.zeros(nx)
    kprime_vec = k_grid.flatten()
    
    for x_c in range(nx):
        EVx = np.zeros(nk)
        for xp_c in range(nx):
            EVx = EVx + pi_x[x_c, xp_c] * np.maximum(theta * (1 - delta) * kprime_vec, 
                                                     V1[:, xp_c])
        RHS1 = aux1 * kprime_vec + q * (1 - psi) * EVx
        RHS2 = aux2 * kprime_vec + q * (1 - psi) * EVx
        max_ind1 = np.argmax(RHS1)
        max_ind2 = np.argmax(RHS2)
        k_star1[x_c] = k_grid[max_ind1]
        k_star2[x_c] = k_grid[max_ind2]
    
    # 计算k'(k,x)，无约束企业的资本投资
    pol_kp_unc = np.zeros((nk, nx))  # 值
    for x_c in range(nx):
        for k_c in range(nk):
            k_val = k_grid[k_c]
            if (1 - delta) * k_val > k_star2[x_c]:
                pol_kp_unc[k_c, x_c] = k_star2[x_c]
            elif (1 - delta) * k_val >= k_star1[x_c] and (1 - delta) * k_val <= k_star2[x_c]:
                pol_kp_unc[k_c, x_c] = (1 - delta) * k_val
            else:
                pol_kp_unc[k_c, x_c] = k_star1[x_c]
    
    return pol_kp_unc

