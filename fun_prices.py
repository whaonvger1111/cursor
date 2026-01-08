"""
计算稳态价格(q,w,R)
"""
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from fun import Fun
from tools.v2struct import pack_to_struct


def fun_prices(par):
    """
    计算稳态价格
    
    参数:
    par: 参数字典
    
    返回:
    prices: 价格字典
    """
    if not isinstance(par, dict):
        raise TypeError('输入par在fun_prices中必须是字典！')
    
    q = par['beta']  # 金融贴现因子
    FK = 1 / q + par['delta_k'] - 1  # 企业部门MPK
    rental = FK  # 租金率
    KL_ratio = Fun.optimal_KL(rental, par)  # 企业部门资本劳动比
    wage = Fun.marg_prod_labor(KL_ratio, par)  # 实际工资
    
    # 将输出打包到字典中
    prices = pack_to_struct(q=q, rental=rental, wage=wage, KL_ratio=KL_ratio)
    
    if not isinstance(prices, dict):
        raise TypeError('输出<prices>必须是字典')
    
    if par.get('verbose', 0) >= 1:
        print(' ')
        print('--------------------------------------------')
        print('Prices')
        print('--------------------------------------------')
        print(f'q:                         {q:.6f}')
        print(f'K-L Ratio:                 {KL_ratio:.6f}')
        print(f'Wage:                      {wage:.6f}')
        print(' ')
    
    return prices

