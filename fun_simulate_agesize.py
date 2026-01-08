"""
模拟稳态模型的firm面板
从稳态分布模拟firm面板
"""
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from fun import Fun
from tools.find_loc import find_loc


def ind2sub(shape, index):
    """
    将线性索引转换为下标
    """
    indices = np.unravel_index(index, shape)
    return indices[0], indices[1]


def fun_simulate_agesize(sol, prices, par, distrib, b_grid, N_sim, T_sim):
    """
    模拟稳态模型的firm面板
    
    参数:
    sol, prices, par, distrib: 稳态字典
    b_grid: 2维数组(nk,nb)
    N_sim, T_sim: 标量
    
    返回:
    sim: 包含字段的字典：
    - k_sim, b_sim, x_sim: 模拟的索引
    - k_sim_val, x_sim_val: 模拟的值
    b_sim_val缺失
    """
    # 解包
    nk = par['nk']
    nb = par['nb']
    pi_x = par['pi_x']  # 外生冲击的转移矩阵(x,x')
    k_grid = par['k_grid']  # (nk,)
    x_grid = par['x_grid']  # (nx,)
    
    pol_kp_ind = sol['pol_kp_ind']  # 整数, (k,b,x)
    pol_debt = sol['pol_debt']  # (k,b,x)
    pol_exit = sol['pol_exit']  # (k,b,x)
    pol_entry = sol['pol_entry']  # (k,b,x)
    wage = prices['wage']
    mu_active = distrib['mu_active']  # (k,b,x)
    phi_dist = sol['phi_dist']  # (k,b,x)
    
    # 重置随机种子
    np.random.seed(par.get('seed', 12345))
    
    # 从转移矩阵模拟外生随机生产率x
    # x的初始分布：来自mu_active，但只考虑无约束企业
    prob0V = np.sum(phi_dist * pol_entry, axis=(0, 1))
    prob0V = prob0V / np.sum(prob0V)
    unif_rand = np.random.rand(N_sim, T_sim)
    
    # x_sim是(N,T)整数面板{1,2,..,NX}
    try:
        from tools.markov_sim import markov_sim
        x_sim = markov_sim(N_sim, T_sim, prob0V, pi_x.T, unif_rand, 1)
    except ImportError:
        # 如果markov_sim未实现，使用简化版本
        x_sim = np.zeros((N_sim, T_sim), dtype=int)
        for i in range(N_sim):
            # 初始x从prob0V抽取
            x_sim[i, 0] = np.random.choice(len(prob0V), p=prob0V)
            for t in range(1, T_sim):
                # 从转移矩阵抽取下一个x
                x_sim[i, t] = np.random.choice(len(pi_x), p=pi_x[x_sim[i, t-1], :])
    
    x_sim_val = x_grid[x_sim]
    
    # 模拟内生变量k、b和存活
    k_sim = np.ones((N_sim, T_sim), dtype=int)  # 索引
    b_sim = np.ones((N_sim, T_sim), dtype=int)  # 索引
    # 存活到最后的指标。初始化为1，一旦退出为真就切换到0
    surv_sim = np.ones((N_sim, T_sim), dtype=int)
    l_sim = np.zeros((N_sim, T_sim))  # 规模
    
    # 抽取初始k和b
    kb_grid = np.arange(1, nk * nb + 1)
    for i_c in range(N_sim):
        init_mu = phi_dist[:, :, x_sim[i_c, 0]] * pol_entry[:, :, x_sim[i_c, 0]]
        kb_prob = init_mu.flatten() / np.sum(init_mu)
        # simulate_iid_fast的输出是索引
        try:
            from tools.simulate_iid_fast import simulate_iid_fast
            kb_ind, _ = simulate_iid_fast(kb_grid, kb_prob, 0)
            kb_ind = kb_ind - 1  # 转换为0-based索引
        except ImportError:
            # 如果simulate_iid_fast未实现，使用numpy
            kb_ind = np.random.choice(len(kb_grid), p=kb_prob)
        
        k_init, b_init = ind2sub([nk, nb], kb_ind)
        k_sim[i_c, 0] = k_init
        b_sim[i_c, 0] = b_init
        # 计算t_c=1时的企业规模
        l_sim[i_c, 0] = Fun.fun_l(x_grid[x_sim[i_c, 0]], wage, k_grid[k_sim[i_c, 0]], par)
    
    # 模拟t>1
    unif_rand1 = np.random.rand(N_sim, T_sim)
    for i_c in range(N_sim):
        for t_c in range(T_sim - 1):
            if surv_sim[i_c, t_c] == 1:  # 如果企业i_c在t_c存活
                k_sim[i_c, t_c + 1] = pol_kp_ind[k_sim[i_c, t_c], b_sim[i_c, t_c], x_sim[i_c, t_c]]
                # b_next是一个值，不一定在网格上
                b_next = pol_debt[k_sim[i_c, t_c], b_sim[i_c, t_c], x_sim[i_c, t_c]]
                b_grid_temp = b_grid[k_sim[i_c, t_c + 1], :]
                # omega是左网格点的权重
                left_loc, omega = find_loc(b_grid_temp, b_next)
                u = unif_rand1[i_c, t_c]
                # 这是b_next的索引
                b_sim[i_c, t_c + 1] = left_loc + (1 if u > omega else 0)
                # 计算企业规模
                l_sim[i_c, t_c + 1] = Fun.fun_l(x_grid[x_sim[i_c, t_c + 1]], wage,
                                               k_grid[k_sim[i_c, t_c + 1]], par)
                
                surv_sim[i_c, t_c + 1:] = surv_sim[i_c, t_c] * (pol_exit[k_sim[i_c, t_c], b_sim[i_c, t_c], x_sim[i_c, t_c]] == 0)
            else:
                # 一旦企业退出，不需要继续到t=T_sim
                break
    
    k_sim_val = k_grid[k_sim]
    
    sim = {
        'k_sim': k_sim,
        'b_sim': b_sim,
        'x_sim': x_sim,
        'k_sim_val': k_sim_val,
        'x_sim_val': x_sim_val,
        'l_sim': l_sim,
        'surv_sim': surv_sim
    }
    
    return sim

