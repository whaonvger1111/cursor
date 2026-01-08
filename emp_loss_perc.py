"""
计算就业损失百分比
"""
import numpy as np


def emp_loss_perc(L_tran, L_ss):
    """
    计算转移动态相对于稳态的就业损失百分比
    
    参数:
    L_tran: 转移动态就业路径
    L_ss: 稳态就业
    
    返回:
    emp_loss: 就业损失百分比
    """
    emp_loss = (L_ss - L_tran) / L_ss * 100 if L_ss > 0 else 0
    return emp_loss

