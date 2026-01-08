"""
计算约束企业k'的上界
"""
import numpy as np


def sub_kp_onestep(profit_mat, b_grid, k_grid, q, theta, delta, lambda_val):
    """
    计算约束企业k'的上界
    
    参数:
    profit_mat: 利润矩阵, 维度: (nk,nx)
    b_grid: 债务网格, 维度: (nk,nb)
    k_grid: 资本网格, 维度: (nk,)
    q,theta,delta,lambda_val: 标量参数
    
    返回:
    kp_bar: k'的上界, 维度: (nk,nb,nx)
    """
    nk, nx = profit_mat.shape
    nb = b_grid.shape[1]
    
    kp_bar = np.zeros((nk, nb, nx))
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                k_val = k_grid[k_c]
                b_val = b_grid[k_c, b_c]
                profit_val = profit_mat[k_c, x_c]
                # 如果k'>=(1-delta)*k
                kp_bar_up = (profit_val + (1 - delta) * k_val - b_val) / (1 - q * lambda_val)
                # 如果k'<(1-delta)*k
                kp_bar_down = (profit_val + theta * (1 - delta) * k_val - b_val) / (theta - q * lambda_val)
                if profit_val + q * lambda_val * (1 - delta) * k_val - b_val >= 0:
                    kp_bar[k_c, b_c, x_c] = kp_bar_up
                else:
                    kp_bar[k_c, b_c, x_c] = kp_bar_down
    
    return kp_bar

