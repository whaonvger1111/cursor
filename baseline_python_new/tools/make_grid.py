"""
生成网格
"""
import numpy as np


def make_grid(a_min, a_max, n, curv=1, method=1, growth=None):
    """
    生成离散网格
    
    参数:
    a_min, a_max: 网格的下界和上界
    n: 网格点数
    curv: 曲率参数
         方法1：如果curv=1，网格是等间距的
               如果curv>1，则更接近a_min的点更多
         方法2：curv有不同的解释！
    method: 1 = 标准方法，2 = Kindermann方法
    growth: 增长率（方法2需要）
    
    返回:
    a_grid: 离散网格（列向量）
    """
    if method == 1:
        # 标准方法
        a_grid = np.zeros(n)
        for i in range(n):
            a_grid[i] = a_min + ((i) / (n - 1)) ** curv * (a_max - a_min)
    elif method == 2:
        # Kindermann方法
        if growth is None:
            raise ValueError('方法2需要growth参数')
        a_grid = np.full(n, np.nan)
        # 计算因子
        h = (a_max - a_min) / ((1 + growth) ** n - 1)
        for i in range(2, n + 2):
            a_grid[i - 2] = h * ((1 + growth) ** (i - 1) - 1) + a_min
    else:
        raise ValueError(f'未知的方法: {method}')
    
    return a_grid.reshape(-1, 1)

