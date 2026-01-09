"""
计算稳态价格 (q, w, R)
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from fun import Fun
from tools.v2struct import pack_to_struct


def fun_prices(par):
    """
    计算稳态价格 (q, w, R)
    
    参数:
    par: 参数字典
    
    返回:
    prices: 价格字典，包含 q, rental, wage, KL_ratio
    """
    # 输入检查
    if not isinstance(par, dict):
        raise TypeError("输入par在fun_prices中必须是字典！")
    
    # 金融贴现因子
    q = par['beta']
    
    # 企业部门边际资本产出
    FK = 1 / q + par['delta_k'] - 1
    
    # 租金率
    rental = FK
    
    # 资本劳动比（企业部门）
    KL_ratio = Fun.optimal_KL(rental, par)
    
    # 实际工资
    wage = Fun.marg_prod_labor(KL_ratio, par)
    
    # 打包输出为字典
    prices = pack_to_struct(q=q, rental=rental, wage=wage, KL_ratio=KL_ratio)
    
    # 输出检查
    if not isinstance(prices, dict):
        raise TypeError("输出<prices>必须是字典")
    
    # 打印价格信息（如果启用详细输出）
    verbose = par.get('verbose', 1)
    if verbose >= 1:
        print(' ')
        print('--------------------------------------------')
        print('Prices')
        print('--------------------------------------------')
        print(f'q:                         {q:.10f}')
        print(f'K-L Ratio:                 {KL_ratio:.10f}')
        print(f'Wage:                      {wage:.10f}')
        print(' ')
    
    return prices


