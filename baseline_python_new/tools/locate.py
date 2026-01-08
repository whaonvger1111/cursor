"""
定位函数：找到x在xx中的位置
x在xx(jl)和xx(jl+1)之间
jl总是在{1,2,..,n-1}中
xx假设为单调递增
"""
import numpy as np


def locate(xx, x):
    """
    找到x在xx中的位置
    
    参数:
    xx: 单调递增的向量
    x: 要查找的值
    
    返回:
    jl: 位置索引（1-based转换为0-based）
    """
    n = len(xx)
    
    if x < xx[0]:
        jl = -1  # 小于最小值
    elif x > xx[n - 1]:
        jl = n  # 大于最大值
    else:
        jl = 0
        ju = n - 1
        while ju - jl > 1:
            jm = (ju + jl) // 2
            if x >= xx[jm]:
                jl = jm
            else:
                ju = jm
    
    # 转换为0-based索引，并限制在[0, n-2]范围内
    jl = min(n - 2, max(0, jl))
    
    return jl

