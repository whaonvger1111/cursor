"""
计算新进入者的x分布（生产率由xi转移）
"""
import numpy as np


def fun_x_entrants(x_grid, x_prob, epsx, rhox, mean_x, xi):
    """
    计算新进入者的x分布（生产率由xi转移）
    
    参数:
    x_grid: x网格
    x_prob: x的稳态分布
    epsx: x创新的标准差
    rhox: x的持续性
    mean_x: x的均值
    xi: 进入者相对于在位者的生产率差距
    
    返回:
    x0_prob: 进入者的x分布
    """
    nx = len(x_grid)
    
    var_x = epsx**2 / (1 - rhox**2)
    
    x0_prob = x_prob.copy()
    mean_x_exp = np.exp(mean_x / (1 - rhox))
    
    for x_c in range(1, nx - 1):
        x_val = x_grid[x_c]
        x1_val = x_grid[x_c + 1]
        x0_val = x_grid[x_c - 1]
        x0_prob[x_c] = (np.exp(-(np.log(x_val) - np.log(xi * mean_x_exp))**2 / 2 / var_x) / 
                       x_val / np.sqrt(var_x) / np.sqrt(2 * np.pi) * (x1_val - x0_val) / 2)
    
    x0_prob[0] = (np.exp(-(np.log(x_grid[0]) - np.log(xi * mean_x_exp))**2 / 2 / var_x) / 
                 x_grid[0] / np.sqrt(var_x) / np.sqrt(2 * np.pi) * (x_grid[1] - x_grid[0]) / 2)
    x0_prob[nx - 1] = (np.exp(-(np.log(x_grid[nx - 1]) - np.log(xi * mean_x_exp))**2 / 2 / var_x) / 
                      x_grid[nx - 1] / np.sqrt(var_x) / np.sqrt(2 * np.pi) * 
                      (x_grid[nx - 1] - x_grid[nx - 2]) / 2)
    
    x0_prob = x0_prob / np.sum(x0_prob)
    
    return x0_prob

