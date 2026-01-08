"""
向量化的位置查找函数
找到jl使得x_grid(jl)<=xi<x_grid(jl+1)
"""
import numpy as np


def find_loc_vec(x_grid, xi):
    """
    找到位置和权重用于插值
    
    参数:
    x_grid: 严格递增的列向量(nx,1)
    xi: 可以是N维数组，维度(s1,s2,...)
    
    返回:
    jl: 左点位置，与xi相同大小
    omega: 左点的权重，与xi相同大小
    """
    nx = len(x_grid)
    xi = np.asarray(xi)
    
    # 对于每个'xi'，获取边界它的'x'元素的位置
    # 使用searchsorted代替histc
    jl = np.searchsorted(x_grid, xi, side='right') - 1
    
    # 处理边界情况
    jl[xi <= x_grid[0]] = 0
    jl[xi >= x_grid[nx - 1]] = nx - 2
    
    # 确保jl在有效范围内
    jl = np.clip(jl, 0, nx - 2)
    
    # 左点的权重
    omega = (x_grid[jl + 1] - xi) / (x_grid[jl + 1] - x_grid[jl])
    omega = np.clip(omega, 0, 1)
    
    return jl, omega
