"""
快速独立同分布模拟
从离散分布模拟随机抽取
"""
import numpy as np
from tools.locate import locate


def simulate_iid_fast(z_grid, z_prob, dbg=0):
    """
    从离散分布模拟随机抽取
    
    参数:
    z_grid: 冲击z的离散网格
    z_prob: z的离散概率向量，必须>=0且和为1
    dbg: 调试标志
    
    返回:
    ind_sim: 抽取的索引（整数）
    val_sim: z_grid[ind_sim]的实际值
    """
    n = len(z_grid)
    
    if dbg:
        if np.any(z_prob < 0) or np.any(z_prob > 1):
            raise ValueError('概率必须在[0,1]之间')
        if abs(np.sum(z_prob) - 1) > 1e-5:
            raise ValueError('初始概率和不等于1')
    
    # 抽取随机数（这可以在函数外部完成）
    u = np.random.rand()
    
    z_prob_cum = np.cumsum(z_prob)
    
    ind_sim = locate(z_prob_cum, u) + 1
    
    if ind_sim < 1 or ind_sim > n:
        print(f'ind_sim = {ind_sim}')
        raise ValueError('结果超出范围')
    
    val_sim = z_grid[ind_sim - 1]  # Python索引从0开始
    
    return ind_sim, val_sim

