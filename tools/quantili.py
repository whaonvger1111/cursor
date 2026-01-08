"""
计算加权分位数
作者：Cagetti和De Nardi (2006)
计算x的q分位数，权重为w
w是离散概率函数
不需要排序或归一化
"""
import numpy as np
from tools.myinterp1 import myinterp1


def quantili(x, w, q):
    """
    计算加权分位数
    
    参数:
    x: 数据向量
    w: 权重向量（离散概率函数）
    q: 分位数向量
    
    返回:
    y: 分位数值
    """
    x = np.asarray(x).flatten()
    w = np.asarray(w).flatten()
    q = np.asarray(q).flatten()
    
    # 按升序排序向量x
    ix = np.argsort(x)
    xs = x[ix]
    
    # 相应地排序分布w
    ws = w[ix]
    ws = ws / np.sum(ws)
    cums = np.cumsum(ws)
    
    # 找到唯一值（最后一个索引）
    xs_u, ind_u = np.unique(xs, return_index=True)
    # MATLAB的unique(...,'last')返回最后一个索引
    # 我们需要找到每个唯一值的最后一个出现位置
    ind_u_last = []
    for val in xs_u:
        indices = np.where(xs == val)[0]
        if len(indices) > 0:
            ind_u_last.append(indices[-1])
    ind_u_last = np.array(ind_u_last)
    cums_u = cums[ind_u_last]
    
    y = np.zeros(len(q))
    for i in range(len(q)):
        y[i] = myinterp1(cums_u, xs_u, q[i], extrap=1)
    
    return y

