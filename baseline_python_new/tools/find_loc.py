"""
找到位置：标量版本
找到jl使得x_grid(jl)<=xi<x_grid(jl+1)
"""
import numpy as np


def locate(x_grid, xi):
    """
    找到xi在x_grid中的位置
    
    参数:
    x_grid: 严格递增的向量
    xi: 标量
    
    返回:
    位置索引
    """
    x_grid = np.asarray(x_grid).flatten()
    return np.searchsorted(x_grid, xi, side='right') - 1


def find_loc(x_grid, xi):
    """
    找到jl使得x_grid(jl)<=xi<x_grid(jl+1)
    
    参数:
    x_grid: 严格递增的列向量
    xi: 标量
    
    返回:
    jl: 左点（标量）
    omega: 左点的权重（标量）
    """
    x_grid = np.asarray(x_grid).flatten()
    nx = len(x_grid)
    
    jl = max(min(locate(x_grid, xi), nx - 2), 0)
    
    # x_grid(j)上的权重
    omega = (x_grid[jl + 1] - xi) / (x_grid[jl + 1] - x_grid[jl])
    
    return jl, omega

