"""
等间距网格的一维插值
"""
import numpy as np


def myinterp1_equi(x, y, xi, extrap=1):
    """
    等间距网格的一维插值
    
    参数:
    x: N*1向量，必须单调递增
    y: N*1向量
    xi: 查询点，必须是标量
    extrap: 0-1整数，是否外推。建议设置为1！
    
    返回:
    yi: 在查询点xi处的插值函数值
    """
    n = len(x)
    if len(y) != n:
        raise ValueError('myinterp1_equi: x和y必须是相同长度的向量！')
    
    step = x[1] - x[0]
    
    # 找到x(j)<= xi <x(j+1)，对于j=1,..,n-1
    j = max(min(int(np.ceil((xi - x[0]) / step)), n - 1), 1)
    
    # xi在x(j)和x(j+1)之间
    slope = (y[j] - y[j - 1]) / (x[j] - x[j - 1])
    yi = y[j - 1] + (xi - x[j - 1]) * slope
    
    # 对于超出x范围的xi值，给出NaN
    if extrap == 0:
        if xi < x[0] or xi > x[-1]:
            yi = np.nan
    
    return yi

