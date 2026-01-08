"""
生成进入者的初始分布Phi(k,b,x)
"""
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from find_loc_vec import find_loc_vec


def find_loc(x_grid, xi):
    """
    找到jl使得x_grid(jl)<=xi<x_grid(jl+1)
    这是find_loc_vec的标量版本
    
    参数:
    x_grid: 严格递增的列向量
    xi: 标量
    
    返回:
    jl: 左点（标量）
    omega: 左点的权重（标量）
    """
    x_grid = np.asarray(x_grid).flatten()
    nx = len(x_grid)
    
    # 使用digitize找到位置
    jl = np.digitize([xi], x_grid)[0] - 1
    jl = max(min(jl, nx - 2), 0)
    
    # x_grid(j)上的权重
    omega = (x_grid[jl + 1] - xi) / (x_grid[jl + 1] - x_grid[jl])
    
    return jl, omega


def gen_phi_dist(bk0_vec, bk0_prob, k_grid, b_grid, x0_prob, prob_k):
    """
    创建进入者的初始分布Phi(k,b,x)
    
    参数:
    bk0_vec: 3*1向量，初始债务资产比的值
    bk0_prob: 3*1向量，初始债务资产比的概率
    k_grid: 资本网格
    b_grid: 债务网格，维度(nk,nb)
    x0_prob: x的分布
    prob_k: k的分布
    
    返回:
    phi_dist: 3维数组，进入者在(k,b,x)上的初始概率
    """
    nk = k_grid.shape[0] if k_grid.ndim > 1 else len(k_grid)
    nb = b_grid.shape[1]
    nx = len(x0_prob)
    nbk = len(bk0_vec)
    
    if nbk != len(bk0_prob):
        raise ValueError('bk0_vec和bk0_prob大小不同！')
    
    chk = np.sum(bk0_prob)
    if abs(chk - 1) > 1e-10:
        raise ValueError('bk0_prob和不等于1！')
    
    phi_dist = np.zeros((nk, nb, nx))
    
    # b0（标量）是进入者的初始债务水平
    for k_c in range(nk):
        b_gridk = b_grid[k_c, :]
        kappa = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
        
        for x_c in range(nx):
            for bk_c in range(nbk):
                bk0 = bk0_vec[bk_c]
                b0 = bk0 * kappa
                b0_ind, omega = find_loc(b_gridk, b0)
                
                # 无约束新进入者
                b0_ind = int(np.clip(b0_ind, 0, nb - 2))
                phi_dist[k_c, b0_ind, x_c] += omega * bk0_prob[bk_c] * x0_prob[x_c]
                if b0_ind + 1 < nb:
                    phi_dist[k_c, b0_ind + 1, x_c] += (1 - omega) * bk0_prob[bk_c] * x0_prob[x_c]
        
        # 归一化
        phi_dist_sum = np.sum(phi_dist[k_c, :, :])
        if phi_dist_sum > 0:
            phi_dist[k_c, :, :] = prob_k[k_c] * phi_dist[k_c, :, :] / phi_dist_sum
    
    phi_dist = phi_dist / np.sum(phi_dist)
    
    # 验证
    assert np.all(np.isfinite(phi_dist)) and np.all(~np.isnan(phi_dist)), "phi_dist包含非有限值或NaN"
    assert np.all(phi_dist >= 0), "phi_dist包含负值"
    assert phi_dist.shape == (nk, nb, nx), f"phi_dist维度错误: {phi_dist.shape}"
    
    return phi_dist

