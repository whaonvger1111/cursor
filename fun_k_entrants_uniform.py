"""
计算新进入者的k分布（均匀分布）
"""
import numpy as np


def fun_k_entrants_uniform(k_grid, k_min, k_max):
    """
    计算新进入者的k分布
    
    参数:
    k_grid: k的网格
    k_min: 下界
    k_max: 上界
    
    返回:
    k_prob: k的概率分布
    """
    if k_min <= 0 or k_max <= 0:
        raise ValueError("输入<k_min>和<k_max>必须严格为正！")
    
    nk = len(k_grid)
    k_prob = np.zeros(nk)
    
    for k_c in range(nk):
        k_val = k_grid[k_c]
        if k_val >= k_min and k_val <= k_max:
            k_prob[k_c] = 1
    
    # k_prob必须和为1
    k_prob = k_prob / np.sum(k_prob)
    
    return k_prob

