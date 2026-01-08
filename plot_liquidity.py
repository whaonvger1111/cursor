"""
绘制转移动态中的金融储蓄和债务
"""
import numpy as np

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("警告：matplotlib未安装，绘图功能将不可用")


def plot_liquidity(b_grid, distrib_tran, weights, par):
    """
    绘制转移动态中的平均债务和债务资本比
    
    参数:
    b_grid: 债务网格，维度(nk,nb,T+1,nn)
    distrib_tran: 转移动态分布字典
    weights: 权重，维度(nk,nx,nn)
    par: 参数字典
    
    返回:
    ave_b: 平均债务，维度(T+1,)
    ave_bk: 平均债务资本比，维度(T+1,)
    """
    T = par['T']
    nk = par['nk']
    nb = par['nb']
    nx = par['nx']
    nn = par['nn']
    k_grid = par['k_grid']
    mu_active = distrib_tran['mu_active']  # 维度(nk,nb,nx,T+1,nn)
    
    ave_b = np.zeros(T + 1)
    ave_bk = np.zeros(T + 1)
    
    for t in range(T + 1):
        b_sum = 0
        bk_sum = 0
        mass_sum = 0
        
        for n_c in range(nn):
            for k_c in range(nk):
                kappa = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
                for x_c in range(nx):
                    weight_val = weights[k_c, x_c, n_c]
                    for b_c in range(nb):
                        b_val = b_grid[k_c, b_c, t, n_c]
                        mu_val = mu_active[k_c, b_c, x_c, t, n_c]
                        
                        b_sum += weight_val * b_val * mu_val
                        bk_sum += weight_val * (b_val / kappa) * mu_val if kappa > 0 else 0
                        mass_sum += weight_val * mu_val
        
        if mass_sum > 0:
            ave_b[t] = b_sum / mass_sum
            ave_bk[t] = bk_sum / mass_sum
    
    return ave_b, ave_bk

