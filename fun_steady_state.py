"""
求解稳态模型
给定参数值par（包括网格等）求解稳态模型

概述:
    Step 0: 给定par，设置网格等
    Step 1: 给定价格(q,w,R)，求解企业的动态规划问题
    Step 2: 恢复企业的价值函数、进入和退出规则
    Step 3: 计算平稳分布mu（草稿中的mu0）和mu_active（草稿中的mu）
    Step 4: 市场出清以找到加总变量
    Step 5: 计算模型矩

注意:
    关于求解稳态的数值算法的解释，请阅读论文的附录F
"""
import numpy as np
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'sub'))

from fun import Fun
from fun_prices import fun_prices
from fun_x_entrants import fun_x_entrants
from fun_k_entrants_pareto import fun_k_entrants_pareto
from fun_k_entrants_uniform import fun_k_entrants_uniform
from tools.markovapprox import markovapprox
from tools.paretojo import paretojo


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from tools.v2struct import pack_to_struct


def fun_steady_state(par):
    """
    求解稳态模型
    
    参数:
    par: 参数字典（包括网格等）
    
    返回:
    sol: 解字典
    agg: 加总变量字典
    b_grid: 债务网格
    distribS: 分布字典
    prices: 价格字典
    model_mom: 模型矩字典
    flag_ss: 收敛标志
    par: 更新的参数字典
    """
    # 输入检查
    if not isinstance(par, dict):
        raise TypeError('输入par在fun_solve_model中必须是字典！')
    
    flag_ss = 0  # 到目前为止一切正常
    verbose = par.get('verbose', 1)
    
    # Step 0a: 设置x网格、x的转移矩阵和x的平稳分布
    if par['x_process'] == 1:
        # AR1
        # 辅助参数
        par['mean_x'] = (1 - par['rhox']) * np.log(par['x0'])
        Tran, log_x_grid, _, _, _ = markovapprox(par['rhox'], par['epsx'], par['mean_x'], 
                                        par.get('cover', 3.5), par['nx'], disp_on_screen=False)
        par['pi_x'] = Tran
        par['x_grid'] = np.exp(log_x_grid)
        
        # 计算Markov链x'|x的平稳分布并称为x_prob
        eig_values, eig_vectors = np.linalg.eig(par['pi_x'].T)
        arg = np.argmin(np.abs(eig_values - 1))
        unit_eig_vector = eig_vectors[:, arg]
        par['x_prob'] = unit_eig_vector / np.sum(unit_eig_vector)
        
        # 计算新进入者的x分布（生产率由xi转移，草稿中称为x0）
        par['x0_prob'] = fun_x_entrants(par['x_grid'], par['x_prob'], par['epsx'], 
                                        par['rhox'], par['mean_x'], par['xi'])
    
    elif par['x_process'] == 2:
        # 有界Pareto带持续性
        par['x_grid'] = np.linspace(par['x_lb'], par['x_ub'], par['nx'])
        ergoeps, pie = paretojo(par['nx'], par['x_grid'], par['x_shape'], par['x_rho'])
        par['x_prob'] = ergoeps
        par['pi_x'] = pie
        # TODO: 如何转移进入者的分布？？
        par['x0_prob'] = par['x_prob']
    else:
        raise ValueError('fun_steady_state: x_process无效！')
    
    # Step 0b: 设置资本网格和初始k的概率分布
    # par.k_grid在set_parameters.m中创建
    
    # 计算新进入者的k分布
    if par['k_distrib'] == 1:  # 均匀分布
        par['prob_k'] = fun_k_entrants_uniform(par['k_grid'].flatten(), 
                                               par['k_min'], par['k_max'])
    elif par['k_distrib'] == 2:  # pareto分布
        par['prob_k'] = fun_k_entrants_pareto(par['k_grid'].flatten(), 
                                             par['k_min'], par['k_alpha'])
    else:
        raise ValueError('fun_steady_state: k_distrib无效！')
    
    # Step 0c: 设置辅助参数
    par['lambda'] = par['lambda0'] * par['theta'] * (1 - par['delta_k'])
    
    # Step 0d: 设置固定成本向量（依赖于kappa）
    par['fixcost'] = np.zeros(par['nk'])
    for k_c in range(par['nk']):
        k_val = par['k_grid'][k_c]
        par['fixcost'][k_c] = Fun.fun_fixcost(k_val, par['fixcost1'], par['fixcost2'], par)
    
    if verbose >= 1:
        print(' ')
        print('--------------------------------------------')
        print('Grid dimensions')
        print('--------------------------------------------')
        print(f'nb:   {par["nb"]}')
        print(f'nx:   {par["nx"]}')
        print(f'nk:   {par["nk"]}')
        print(' ')
    
    # Step 1: 价格
    prices = fun_prices(par)
    
    # Step 2: 价值函数迭代
    # 注意：fun_vfi1需要实现
    if verbose >= 1:
        start_time = time.time()
    
    try:
        from fun_vfi1 import fun_vfi1
        sol, b_grid, phi_dist, flag_vf = fun_vfi1(prices, par)
    except ImportError:
        print("警告: fun_vfi1未实现，使用占位符")
        sol = {}
        b_grid = np.zeros((par['nk'], par['nb']))
        phi_dist = np.zeros((par['nk'], par['nb'], par['nx']))
        flag_vf = -1
    
    if verbose >= 1:
        elapsed = time.time() - start_time
        print(f'Time to do VFI: {elapsed:8.4f}')
        print(' ')
    
    if flag_vf < 0:
        print('警告：fun_vfi1中发生了一些错误')
        flag_ss = -1
        return None, None, None, None, None, None, flag_ss, par
    
    if np.any(np.isnan(phi_dist)) or np.any(np.isinf(phi_dist)):
        print('警告：phi_dist有NaN/Inf值')
        flag_ss = -1
        return None, None, None, None, None, None, flag_ss, par
    
    # 分布
    if verbose >= 1:
        start_time = time.time()
    
    try:
        from fun_distrib1 import fun_distrib1
        mu, mu_active, entry_vec, flag_mu, dist, iter_mu = fun_distrib1(par, sol, b_grid, phi_dist)
    except ImportError:
        print("警告: fun_distrib1未实现，使用占位符")
        mu = np.zeros((par['nk'], par['nb'], par['nx']))
        mu_active = np.zeros((par['nk'], par['nb'], par['nx']))
        entry_vec = np.zeros(par['nx'])
        flag_mu = -1
        dist = 1.0
        iter_mu = 0
    
    if verbose >= 1:
        elapsed = time.time() - start_time
        print(f'Time to do DISTRIBUTION: {elapsed:8.4f}')
    
    if flag_mu < 0:
        print('警告：分布未收敛！')
        print(f'到目前为止的迭代 = {iter_mu}')
        print(f'最后的误差    = {dist:.15f}')
        flag_ss = -1
        # 继续执行而不是返回
    
    # 将分布的输出分组到字典中
    distribS = pack_to_struct(mu=mu, mu_active=mu_active, entry_vec=entry_vec)
    
    # 加总变量和模型矩
    if verbose >= 1:
        start_time = time.time()
    
    try:
        from fun_aggregates import fun_aggregates
        agg = fun_aggregates(par, sol, distribS, phi_dist, prices)
    except ImportError:
        print("警告: fun_aggregates未实现，使用占位符")
        agg = {'K_corp': 0, 'K_agg': 0, 'C_agg': 1.0}
    
    if verbose >= 1:
        elapsed = time.time() - start_time
        print(f'Time to do aggregates: {elapsed:8.4f}')
        print(' ')
    
    # 将phi_dist添加到<sol>字典
    sol['phi_dist'] = phi_dist
    
    # 计算模型矩（除了<agg>）
    if verbose >= 1:
        start_time = time.time()
    
    try:
        from fun_targets import fun_targets
        model_mom = fun_targets(sol, distribS, par, prices, agg, b_grid)
    except ImportError:
        print("警告: fun_targets未实现，使用占位符")
        model_mom = {}
    
    if verbose >= 1:
        elapsed = time.time() - start_time
        print(f'Time to do targets: {elapsed:8.4f}')
        print(' ')
    
    if not isinstance(sol, dict):
        raise TypeError('输出<sol>必须是字典')
    if not isinstance(agg, dict):
        raise TypeError('输出<agg>必须是字典')
    if not isinstance(distribS, dict):
        raise TypeError('输出<distribS>必须是字典')
    
    return sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par

