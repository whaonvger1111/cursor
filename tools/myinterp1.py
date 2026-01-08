"""
一维插值函数
"""
import numpy as np
from scipy.interpolate import interp1d


def myinterp1(x_grid, y_grid, xi, extrapolate_flag=0):
    """
    一维插值
    
    参数:
    x_grid: 网格点
    y_grid: 网格值
    xi: 要插值的点（可以是标量或数组）
    extrapolate_flag: 外推标志
    
    返回:
    插值结果
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
    
    # 如果xi是标量，转换为数组以便处理
    xi_was_scalar = np.isscalar(xi) or (xi.ndim == 0)
    if xi_was_scalar:
        xi = np.array([xi])
    
    try:
        if extrapolate_flag == 1:
            f = interp1d(x_grid, y_grid, kind='linear', 
                         bounds_error=False, fill_value='extrapolate')
        else:
            f = interp1d(x_grid, y_grid, kind='linear', 
                         bounds_error=False, fill_value=(y_grid[0], y_grid[-1]))
        
        result = f(xi)
        
        # 如果输入是标量，返回标量
        if xi_was_scalar:
            return float(result[0])
        return result
    except Exception as e:
        # 如果scipy插值失败，使用简单的线性插值
        result = np.interp(xi, x_grid, y_grid)
        if xi_was_scalar:
            return float(result)
        return result

