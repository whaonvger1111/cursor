"""
计算有界Pareto分布的遍历分布和转移矩阵
"""
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bddparetocdf import bddparetocdf


def paretojo(neps, eps, shape, rhoeps):
    """
    计算有界Pareto分布的遍历分布和转移矩阵
    
    参数:
    neps: epsilon值的数量
    eps: epsilon值的网格
    shape: Pareto分布的形状参数
    rhoeps: 持续性参数
    
    返回:
    ergoeps: 遍历分布
    pie: 转移矩阵
    """
    ergoeps = np.zeros(neps)
    pie = np.zeros((neps, neps))
    
    # emin和emax是连续分布的假想端点
    emin = eps[0] - (eps[1] - eps[0]) / 2
    emax = eps[neps - 1] + (eps[neps - 1] - eps[neps - 2]) / 2
    
    mideps = np.zeros(neps - 1)
    for i in range(neps - 1):
        mideps[i] = (eps[i] + eps[i + 1]) / 2
    
    # 计算每个epsilon点的密度或质量
    ergoeps[0] = bddparetocdf(emin, emax, shape, mideps[0])
    for i in range(1, neps - 1):
        mass = bddparetocdf(emin, emax, shape, mideps[i - 1])
        ergoeps[i] = bddparetocdf(emin, emax, shape, mideps[i]) - mass
    ergoeps[neps - 1] = 1.0 - bddparetocdf(emin, emax, shape, mideps[neps - 2])
    
    # 给定rhoeps的转移矩阵
    for i in range(neps):
        pie[i, i] = rhoeps
        pie[i, :] = pie[i, :] + (1.0 - rhoeps) * ergoeps
    
    return ergoeps, pie

