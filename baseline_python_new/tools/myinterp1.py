"""
一维插值函数
优化版本：使用手动插值方法（与MATLAB interp1一致）
支持向量化操作，性能接近np.interp，且结果与MATLAB一致
"""
import numpy as np


def myinterp1(x_grid, y_grid, xi, extrapolate_flag=0):
    """
    一维插值（与MATLAB interp1一致）
    使用向量化手动插值方法，避免scipy.interpolate.interp1d的性能问题和结果差异
    
    参数:
    x_grid: 网格点（必须严格递增）
    y_grid: 网格值
    xi: 要插值的点（可以是标量或数组）
    extrapolate_flag: 外推标志
        0: 使用边界值（y_grid[0] 或 y_grid[-1]）
        1: 线性外推
    
    返回:
    插值结果（标量或数组，与xi的形状一致）
    """
    x_grid = np.asarray(x_grid).flatten()
    y_grid = np.asarray(y_grid).flatten()
    xi = np.asarray(xi)
    
    # 确保xi是标量或1D数组
    if xi.ndim > 1:
        xi = xi.flatten()
    
    # 处理边界情况
    if len(x_grid) == 0 or len(y_grid) == 0:
        raise ValueError("x_grid和y_grid不能为空")
    
    if len(x_grid) != len(y_grid):
        raise ValueError(f"x_grid长度({len(x_grid)})必须等于y_grid长度({len(y_grid)})")
    
    if len(x_grid) == 1:
        # 如果只有一个点，返回该点的值
        if np.isscalar(xi) or (xi.ndim == 0):
            return float(y_grid[0])
        return np.full_like(xi, y_grid[0], dtype=y_grid.dtype)
    
    # 记录xi是否为标量
    xi_was_scalar = np.isscalar(xi) or (xi.ndim == 0)
    
    nx = len(x_grid)
    
    # 优化：标量调用使用快速路径，避免数组转换开销
    if xi_was_scalar:
        xi_val = float(xi)
        
        # 处理边界情况
        if xi_val <= x_grid[0]:
            if extrapolate_flag == 1:
                if nx > 1:
                    slope = (y_grid[1] - y_grid[0]) / (x_grid[1] - x_grid[0])
                    return float(y_grid[0] + slope * (xi_val - x_grid[0]))
                return float(y_grid[0])
            return float(y_grid[0])
        elif xi_val >= x_grid[-1]:
            if extrapolate_flag == 1:
                if nx > 1:
                    slope = (y_grid[-1] - y_grid[-2]) / (x_grid[-1] - x_grid[-2])
                    return float(y_grid[-1] + slope * (xi_val - x_grid[-1]))
                return float(y_grid[-1])
            return float(y_grid[-1])
        else:
            # 内部点：使用searchsorted快速查找
            jl = np.searchsorted(x_grid, xi_val, side='right') - 1
            jl = max(min(jl, nx - 2), 0)
            
            # 计算插值权重
            omega = (x_grid[jl + 1] - xi_val) / (x_grid[jl + 1] - x_grid[jl])
            
            # 线性插值
            return float(omega * y_grid[jl] + (1 - omega) * y_grid[jl + 1])
    
    # 向量化版本：批量处理所有插值点
    # 使用searchsorted批量查找位置（与locate函数一致）
    jl = np.searchsorted(x_grid, xi, side='right') - 1
    
    # 处理边界情况
    jl[xi <= x_grid[0]] = 0
    jl[xi >= x_grid[-1]] = nx - 2
    
    # 确保jl在有效范围内
    jl = np.clip(jl, 0, nx - 2)
    
    # 向量化计算插值权重
    omega = (x_grid[jl + 1] - xi) / (x_grid[jl + 1] - x_grid[jl])
    
    # 向量化线性插值
    result = omega * y_grid[jl] + (1 - omega) * y_grid[jl + 1]
    
    # 处理边界情况
    left_mask = xi <= x_grid[0]
    right_mask = xi >= x_grid[-1]
    
    if np.any(left_mask):
        if extrapolate_flag == 1:
            # 线性外推
            if nx > 1:
                slope = (y_grid[1] - y_grid[0]) / (x_grid[1] - x_grid[0])
                result[left_mask] = y_grid[0] + slope * (xi[left_mask] - x_grid[0])
            else:
                result[left_mask] = y_grid[0]
        else:
            # 使用边界值
            result[left_mask] = y_grid[0]
    
    if np.any(right_mask):
        if extrapolate_flag == 1:
            # 线性外推
            if nx > 1:
                slope = (y_grid[-1] - y_grid[-2]) / (x_grid[-1] - x_grid[-2])
                result[right_mask] = y_grid[-1] + slope * (xi[right_mask] - x_grid[-1])
            else:
                result[right_mask] = y_grid[-1]
        else:
            # 使用边界值
            result[right_mask] = y_grid[-1]
    
    return result

