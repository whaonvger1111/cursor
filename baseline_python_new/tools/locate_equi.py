"""
等间距网格的定位函数
与locate相同，但假设网格是等间距的
如果xgrid(1)<= xi<=xgrid(N)，总是返回{1,...,N-1}中的索引
如果xi<xgrid(1)，则jl=1
如果xi>xgrid(N)，则jl=N-1
"""
import numpy as np


def locate_equi(xgrid, xi):
    """
    在等间距网格中定位
    
    参数:
    xgrid: 等间距网格
    xi: 查询值
    
    返回:
    jl: 位置索引
    """
    nx = len(xgrid)
    
    step = xgrid[1] - xgrid[0]
    xi_min = xi - xgrid[0]
    
    jl = min(nx - 1, max(1, int(np.floor(xi_min / step)) + 1))
    
    return jl

