"""
计算救援政策相对于"无补助"经济的消费等价变化(CEV)
"""
import numpy as np
from fun import Fun


def fun_welfare(par, C_ss, L_ss, C_baseline, L_baseline, C_nogrant, L_nogrant,
               C_targslim, L_targslim, margutil, lsupply):
    """
    计算救援政策的消费等价变化
    
    参数:
    C_ss,L_ss: 稳态中的消费和劳动
    C_baseline,L_baseline: 转移动态基准补助中的C和L, (T+1,)
    C_nogrant,L_nogrant: 转移动态无补助中的C和L, (T+1,)
    C_targslim,L_targslim: 转移动态定向补助中的C和L, (T+1,)
    margutil,lsupply: 需求和劳动供给冲击的路径, (T+1,)
    
    返回:
    CEV_baseline: 基准补助相对于无补助的CEV
    CEV_targslim: 定向补助相对于无补助的CEV
    """
    if not isinstance(par, dict):
        raise TypeError('输入参数par必须是字典')
    
    if len(C_baseline) != par['T'] + 1:
        raise ValueError('C_baseline必须是长度为T+1的向量')
    
    # 计算代表性家庭的价值函数
    V_baseline = 0
    V_nogrant = 0
    V_targslim = 0
    V_nogrant_cons = 0
    
    for t in range(par['T'] + 1):
        V_baseline = V_baseline + par['beta'] ** t * \
            Fun.utility(C_baseline[t], margutil[t], L_baseline[t], lsupply[t], par)
        V_nogrant = V_nogrant + par['beta'] ** t * \
            Fun.utility(C_nogrant[t], margutil[t], L_nogrant[t], lsupply[t], par)
        V_targslim = V_targslim + par['beta'] ** t * \
            Fun.utility(C_targslim[t], margutil[t], L_targslim[t], lsupply[t], par)
        # 这里我们只考虑前四个季度的价值函数的消费部分
        if t < 4:
            V_nogrant_cons = V_nogrant_cons + par['beta'] ** t * \
                Fun.utility_consumption(C_nogrant[t], margutil[t], par)
    
    # 计算T+1期之后的延续价值。注意在稳态中冲击等于1。
    V_ss = 1 / (1 - par['beta']) * Fun.utility(C_ss, 1, L_ss, 1, par)
    
    # 添加延续价值
    V_baseline = V_baseline + par['beta'] ** (par['T'] + 1) * V_ss
    V_nogrant = V_nogrant + par['beta'] ** (par['T'] + 1) * V_ss
    V_targslim = V_targslim + par['beta'] ** (par['T'] + 1) * V_ss
    
    # 计算CEV
    CEV_baseline = ((V_baseline - V_nogrant) / (V_nogrant_cons + 1e-20) + 1) ** (1 / (1 - par['sigma'])) - 1
    CEV_targslim = ((V_targslim - V_nogrant) / (V_nogrant_cons + 1e-20) + 1) ** (1 / (1 - par['sigma'])) - 1
    
    return CEV_baseline, CEV_targslim

