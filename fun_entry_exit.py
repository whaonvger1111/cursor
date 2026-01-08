"""
计算(k,b,x)上的进入和退出政策函数
"""
import numpy as np


def fun_entry_exit(val, profit_mat, b_grid, k_grid, theta, delta, cost_e):
    """
    计算进入和退出政策函数
    
    参数:
    val: 价值函数, 维度: (nk,nb,nx)
    profit_mat: 利润矩阵, 维度: (nk,nx)
    b_grid: 债务网格, 维度: (nk,nb)
    k_grid: 资本网格
    theta,delta,cost_e: 标量参数
    
    返回:
    pol_entry: 进入政策, 维度: (nk,nb,nx)
    pol_exit: 退出政策, 维度: (nk,nb,nx)
    pol_exit_forced: 强制清算政策, 维度: (nk,nb,nx)
    pol_exit_vol: 自愿清算政策, 维度: (nk,nb,nx)
    """
    nk, nb, nx = val.shape
    
    # 进入政策 d^e(k,b,x)
    pol_entry = np.zeros((nk, nb, nx))
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                k_val = k_grid[k_c]
                b_val = b_grid[k_c, b_c]
                aux1 = val[k_c, b_c, x_c] >= cost_e + k_val - b_val
                pol_entry[k_c, b_c, x_c] = float(aux1)
    
    # 退出政策 d^l(x,b)
    pol_exit = np.zeros((nk, nb, nx))
    pol_exit_vol = np.zeros((nk, nb, nx))
    pol_exit_forced = np.zeros((nk, nb, nx))
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                kappa = k_grid[k_c]
                b_val = b_grid[k_c, b_c]
                # 强制清算
                aux1 = profit_mat[k_c, x_c] - b_val + theta * (1 - delta) * kappa < 0
                pol_exit_forced[k_c, b_c, x_c] = float(aux1)
                # 自愿清算
                aux2 = val[k_c, b_c, x_c] < theta * (1 - delta) * kappa - b_val
                pol_exit_vol[k_c, b_c, x_c] = float(aux2)
                aux = (aux1 or aux2)
                pol_exit[k_c, b_c, x_c] = float(aux)
    
    return pol_entry, pol_exit, pol_exit_forced, pol_exit_vol

