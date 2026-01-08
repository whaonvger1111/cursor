"""
无约束企业价值函数V(k,x)的单步Bellman算子
转移动态期间，设置do_howard=0
"""
import numpy as np
from fun import Fun


def sub_V1_onestep(V1, pi_x, profit_mat, k_grid, q, theta, delta, psi, do_howard):
    """
    无约束企业价值函数V(k,x)的单步Bellman算子
    
    参数:
    V1: 价值函数V(k,x), 维度: (nk,nx)
    pi_x: 转移概率矩阵prob(x,x'), 维度: (nx,nx)
    profit_mat: 静态利润pi(k,x), 维度: (nk,nx)
    k_grid: 资本的固定网格, 维度: (nk,1)
    q,theta,delta,psi: 参数, 标量
    do_howard: 是否使用Howard加速
    
    返回:
    V2: 价值函数V(k,x), 维度: (nk,nx)
    """
    n_howard = 50
    
    nk, nx = V1.shape
    
    V2 = np.zeros((nk, nx))
    kpol_ind = np.ones((nk, nx), dtype=int)  # 政策函数k'(k,x)，索引
    kprime = k_grid.flatten()  # 下一期资本：我们对k'向量化。维度:(nk,)
    k_today = k_grid.flatten()  # 当期资本
    
    # 计算期望值
    V1_max = np.maximum(theta * (1 - delta) * kprime[:, np.newaxis], V1)  # 维度: (nk,nx)
    EV = V1_max @ pi_x.T  # 维度: (nk,nx)，对x'积分
    
    # 进行最大化
    for x_c in range(nx):
        EV_x = EV[:, x_c]
        profit_x = profit_mat[:, x_c]
        
        # 关键修复：确保adjcost返回(nk,nk)矩阵
        # MATLAB中：kprime是(nk,1)，k_today是(1,nk)，adjcost返回(nk,nk)
        kprime_col = kprime[:, np.newaxis]  # (nk,1) - 列向量
        k_today_row = k_today[np.newaxis, :]  # (1,nk) - 行向量
        adjcost_mat = Fun.adjcost(kprime_col, k_today_row, theta, delta)  # (nk,nk)
        
        # 构建RHS矩阵：(nk,nk)
        # profit_x需要广播到(nk,nk)
        profit_mat_broadcast = profit_x[:, np.newaxis]  # (nk,1)
        EV_x_broadcast = EV_x[:, np.newaxis]  # (nk,1)
        kprime_broadcast = kprime_col  # (nk,1)
        
        RHS = (profit_mat_broadcast - 
               adjcost_mat + 
               q * (psi * theta * (1 - delta) * kprime_broadcast + 
                    (1 - psi) * EV_x_broadcast))
        
        # 找到最大值及其索引
        # max(RHS, axis=0) 沿着第0维（行）取最大值，返回(nk,)的最大值和索引
        max_indices = np.argmax(RHS, axis=0)  # (nk,) - 每列的最大值索引
        V2[:, x_c] = RHS[max_indices, np.arange(nk)]
        kpol_ind[:, x_c] = max_indices
    
    # Howard加速
    # 在不进行最大化的情况下多次更新V2
    if do_howard == 1:
        for h_c in range(n_howard):
            # 计算期望值
            EVh = np.maximum(theta * (1 - delta) * kprime[:, np.newaxis], V2) @ pi_x.T
            for x_c in range(nx):
                EV_x = EVh[:, x_c]
                for k_c in range(nk):
                    k_val = k_grid[k_c]
                    kopt_ind = kpol_ind[k_c, x_c]
                    V2[k_c, x_c] = (profit_mat[k_c, x_c] - 
                                   Fun.adjcost_scal(k_grid[kopt_ind], k_val, theta, delta) + 
                                   q * (psi * theta * (1 - delta) * k_grid[kopt_ind] + 
                                        (1 - psi) * EV_x[kopt_ind]))
    
    return V2

