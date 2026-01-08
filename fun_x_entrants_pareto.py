"""
计算新进入者的x分布（有界Pareto分布）
"""
import numpy as np
from tools.paretojo import paretojo


def fun_x_entrants_pareto(x_grid, x_prob, x_shape, x_rho):
    """
    计算新进入者的x分布（有界Pareto分布）
    
    参数:
    x_grid: x网格
    x_prob: x的稳态分布
    x_shape: Pareto形状参数
    x_rho: 持续性参数
    
    返回:
    x0_prob: 进入者的x分布
    """
    # 使用paretojo计算分布
    x0_prob, _ = paretojo(len(x_grid), x_grid, x_shape, x_rho)
    x0_prob = x0_prob.flatten()
    
    # 归一化
    x0_prob = x0_prob / np.sum(x0_prob)
    
    return x0_prob

