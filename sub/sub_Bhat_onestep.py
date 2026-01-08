"""
通过迭代方程(21)和(22)（固定点迭代）找到B_hat(k,x)，与非负股息一致的最高债务水平
还返回借款政策b'(k,x)
"""
import numpy as np
from scipy.interpolate import interp1d
from fun import Fun


def myinterp1q(x_grid, y_grid, x_val):
    """
    一维插值函数（替代MATLAB的myinterp1q）
    
    参数:
    x_grid: 网格点
    y_grid: 网格值（可以是多维）
    x_val: 要插值的点
    
    返回:
    插值结果
    """
    x_grid = np.asarray(x_grid).flatten()
    x_val = np.asarray(x_val).flatten()
    
    if y_grid.ndim == 1:
        # 一维情况
        f = interp1d(x_grid, y_grid, kind='linear', 
                     bounds_error=False, fill_value='extrapolate')
        return f(x_val)
    else:
        # 多维情况：对每一列进行插值
        result = np.zeros((len(x_val), y_grid.shape[1]))
        for i in range(y_grid.shape[1]):
            f = interp1d(x_grid, y_grid[:, i], kind='linear',
                        bounds_error=False, fill_value='extrapolate')
            result[:, i] = f(x_val)
        return result


def sub_Bhat_onestep(B_hat, pol_kp_unc, profit_mat, x_tilde_val, k_grid, x_grid, 
                     q, theta, delta, lambda_val):
    """
    找到B_hat(k,x)，与非负股息一致的最高债务水平
    
    参数:
    B_hat: 初始最大债务, 维度: (nk,nx)
    pol_kp_unc: 无约束企业的k'(k,x)政策, 维度: (nk,nx)
    profit_mat: 静态利润, 维度: (nk,nx)
    x_tilde_val: 退出截断值, 维度: (nk,1)
    k_grid: 资本的固定网格, 维度: (nk,1)
    x_grid: 生产率的网格
    q,theta,delta,lambda_val: 标量参数
    
    返回:
    B_hat_new: 更新的B_hat, 维度: (nk,nx)
    pol_bp_unc: 无约束企业的b'(k,x)政策, 维度: (nk,nx)
    """
    nk, nx = B_hat.shape
    
    k_min = k_grid[0]
    k_max = k_grid[-1]
    
    pol_bp_unc = np.zeros((nk, nx))
    
    kp_mat = np.clip(pol_kp_unc, k_min, k_max)
    
    for x_c in range(nx):
        kp_val = kp_mat[:, x_c]  # 维度: (nk,)
        B_hat_interp = myinterp1q(k_grid.flatten(), B_hat, kp_val)  # 维度: (nk,nx)
        x_cut = myinterp1q(k_grid.flatten(), x_tilde_val.flatten(), kp_val)  # (nk,)
        viable_x = x_grid >= x_cut[:, np.newaxis]  # (nk,nx)
        B_hat_interp[~viable_x] = np.nan
        pol_bp_unc[:, x_c] = np.minimum(lambda_val * kp_val, 
                                        np.nanmin(B_hat_interp, axis=1))
    
    # 处理NaN值
    nan_mask = np.isnan(pol_bp_unc)
    if np.any(nan_mask):
        pol_bp_unc[nan_mask] = np.clip(lambda_val * pol_kp_unc[nan_mask], k_min, k_max)
    
    B_hat_new = profit_mat + q * pol_bp_unc - Fun.adjcost(kp_mat, k_grid, theta, delta)
    
    return B_hat_new, pol_bp_unc

