"""
计算新进入者的k分布（Pareto分布）
"""
import numpy as np


def fun_k_entrants_pareto(k_grid, k_min, k_alpha):
    """
    计算新进入者的k分布（Pareto分布）
    
    参数:
    k_grid: k网格
    k_min: Pareto分布的最小值
    k_alpha: Pareto分布的曲率参数
    
    返回:
    k_prob: 新进入者的k分布
    """
    # k_alpha 和 k_min 必须为正
    if k_alpha <= 0 or k_min <= 0:
        raise ValueError("输入<k_alpha>和<k_min>必须严格为正！")
    
    nk = len(k_grid)
    k_prob = np.zeros(nk)
    
    for k_c in range(nk):
        k_val = k_grid[k_c]
        if k_val >= k_min:
            # 这是Pareto分布的p.d.f.
            k_prob[k_c] = k_alpha * (k_min ** k_alpha) / (k_val ** (1 + k_alpha))
    
    # k_prob必须归一化为1
    k_prob = k_prob / np.sum(k_prob)
    
    return k_prob


