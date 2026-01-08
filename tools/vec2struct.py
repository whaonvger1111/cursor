"""
将向量添加到结构体中
"""
import numpy as np


def vec2struct(pvec, parnames, pstruct):
    """
    将向量pvec的每个元素添加到结构体pstruct中，使用parnames中的元素作为字段名
    
    参数:
    pvec: 数值向量
    parnames: 字符串列表
    pstruct: 字典
    
    返回:
    pstruct: 更新的字典
    """
    pvec = np.asarray(pvec).flatten()
    n = len(parnames)
    
    for i in range(n):
        pstruct[parnames[i]] = pvec[i]
    
    return pstruct

