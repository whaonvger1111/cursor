"""
计算转移动态期间进入企业的分布Phi(b,x,kappa)
"""
import numpy as np
from scipy.interpolate import interp1d


def fun_phi_tran(phi_dist_ss, b_grid_ss, b_grid, b_tilde, par):
    """
    计算转移动态期间进入企业的分布
    
    参数:
    phi_dist_ss: 稳态分布, 维度: (nk,nb,nx)
    b_grid_ss: 稳态债务网格, 维度: (nk,nb)
    b_grid: 转移动态债务网格, 维度: (nk,nb,T+1,nn)
    b_tilde: 截断值, 维度: (nk,T+1,nn)
    par: 参数字典
    
    返回:
    phi_dist: 转移动态分布, 维度: (nk,nb,nx,T+1,nn)
    """
    T = par['T']
    nx = par['nx']
    nb = par['nb']
    nk = par['nk']
    nn = par['nn']
    lambda_val = par.get('lambda', par.get('lambda0', 1))
    k_grid = par['k_grid']
    
    phi_dist = np.zeros((nk, nb, nx, T + 1, nn))
    
    # 简化版本：将稳态分布投影到转移动态网格
    for n_c in range(nn):
        for t in range(T + 1):
            for k_c in range(nk):
                kappa = k_grid[k_c]
                if b_tilde[k_c, t, n_c] >= lambda_val * kappa:
                    for x_c in range(nx):
                        phi_dist[k_c, 0, x_c, t, n_c] = np.sum(phi_dist_ss[k_c, :, x_c])
                else:
                    # 插值到新的网格
                    for x_c in range(nx):
                        b_grid_ss_k = b_grid_ss[k_c, :]
                        phi_ss_k = phi_dist_ss[k_c, :, x_c]
                        b_grid_t_k = b_grid[k_c, :, t, n_c]
                        
                        # 使用线性插值
                        valid_mask = b_grid_ss_k <= b_tilde[k_c, t, n_c]
                        if np.any(valid_mask):
                            f = interp1d(b_grid_ss_k[valid_mask], phi_ss_k[valid_mask],
                                        kind='linear', bounds_error=False, 
                                        fill_value=0.0)
                            phi_dist[k_c, :, x_c, t, n_c] = f(b_grid_t_k)
                        else:
                            phi_dist[k_c, 0, x_c, t, n_c] = np.sum(phi_ss_k)
    
    return phi_dist

