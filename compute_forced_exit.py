"""
计算强制退出
"""
import numpy as np


def compute_forced_exit(pol_exit_forced, mu, par):
    """
    计算强制退出
    
    参数:
    pol_exit_forced: 强制退出政策函数
    mu: 分布
    par: 参数字典
    
    返回:
    forced_exit_rate: 强制退出率
    """
    forced_exit = np.sum(pol_exit_forced * mu)
    total_mass = np.sum(mu)
    forced_exit_rate = forced_exit / total_mass if total_mass > 0 else 0
    
    return forced_exit_rate

