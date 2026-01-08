"""
有界Pareto分布的累积分布函数
计算在x处的累积密度（或质量）
用于在(emin,emax)上的离散化有界Pareto分布
作者：In Hwan Jo和Tatsuro Senga，后来由Alessandro Di Nola修改
"""
import numpy as np


def bddparetocdf(emin, emax, shape, x):
    """
    计算有界Pareto分布的累积分布函数
    
    参数:
    emin: 下界
    emax: 上界
    shape: 形状参数
    x: 查询点
    
    返回:
    cdf: 累积分布函数值
    """
    paretocdf = 1.0 - (emin / x) ** shape
    cdf = paretocdf / (1.0 - (emin / emax) ** shape)
    return cdf
