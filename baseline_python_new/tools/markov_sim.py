"""
Markov链模拟
基于CompEcon工具箱
"""
import numpy as np


def markov_sim(nInd, T, prob0V, trProbM, rvInM, dbg=0):
    """
    模拟Markov链历史
    
    参数:
    nInd: 要模拟的个体数量
    T: 历史长度
    prob0V: 日期1时每个状态的概率
    trProbM(s', s): 转移矩阵
    rvInM: 均匀随机变量，按[ind, t]
    dbg: 调试标志
    
    返回:
    idxM(ind, t): 模拟的索引
    """
    ns = len(prob0V)
    
    if dbg:
        # 验证转移矩阵
        if np.any(trProbM < 0) or np.any(trProbM > 1):
            raise ValueError('转移概率必须在[0,1]之间')
        prSumV = np.sum(trProbM, axis=0)
        if np.max(np.abs(prSumV - 1)) > 1e-5:
            raise ValueError('概率和不等于1')
        
        # 验证初始概率
        if np.any(prob0V < 0) or np.any(prob0V > 1):
            raise ValueError('初始概率必须在[0,1]之间')
        if abs(np.sum(prob0V) - 1) > 1e-5:
            raise ValueError('初始概率和不等于1')
        
        # 验证随机数
        if np.any(rvInM < 0) or np.any(rvInM > 1):
            raise ValueError('随机数必须在[0,1]之间')
    
    # 对于每个状态，找到下一期的累积概率分布
    cumTrProbM = np.cumsum(trProbM, axis=0)
    cumTrProbM[-1, :] = 1
    
    # 需要转置这个用于下面的公式
    # 现在按[s, s']
    cumTrProbM = cumTrProbM.T
    
    # 迭代日期
    idxM = np.zeros((nInd, T), dtype=int)
    
    # 抽取t=1
    cumprob0 = np.cumsum(prob0V)
    for i in range(nInd):
        u = rvInM[i, 0]
        idxM[i, 0] = np.searchsorted(cumprob0, u)
    
    # 后续状态
    for t in range(T - 1):
        for i in range(nInd):
            u = rvInM[i, t + 1]
            x_prev = idxM[i, t]
            idxM[i, t + 1] = np.searchsorted(cumTrProbM[x_prev, :], u)
    
    return idxM

