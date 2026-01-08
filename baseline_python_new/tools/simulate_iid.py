"""
从离散分布模拟随机抽取
"""
import numpy as np


def simulate_iid(z_grid, z_prob, u, dbg=0):
    """
    从离散分布模拟随机抽取
    
    参数:
    z_grid: 冲击z的离散网格
    z_prob: z的离散概率向量，必须>=0且和为1
    u: 均匀随机数（在函数外部生成）
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
    
    # 遍历累积概率
    for i in range(n - 1):
        # 累积和p1+p2+..+pi
        prob_sum = np.sum(z_prob[:i + 1])
        if u <= prob_sum:
            ind_sim = i + 1  # MATLAB索引从1开始，Python从0开始
            val_sim = z_grid[ind_sim - 1]
            return ind_sim, val_sim
    
    # 否则，选择最后一个值
    ind_sim = n
    val_sim = z_grid[ind_sim - 1]
    return ind_sim, val_sim

