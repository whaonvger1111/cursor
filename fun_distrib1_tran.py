"""
计算转移动态路径上的分布mu_0(k,b,x)（退出前）
和活跃企业分布mu_active
从前向迭代开始，从稳态的mu_0和mu_active开始
"""
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'sub'))

from find_loc_vec import find_loc_vec
from sub.sub_mu_onestep import sub_mu_onestep


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from tools.v2struct import pack_to_struct


def fun_distrib1_tran(par, pol_tran, distrib_ss, sol_ss):
    """
    计算转移动态路径上的分布
    
    参数:
    par: 参数字典
    pol_tran: 转移动态政策函数字典
    distrib_ss: 稳态分布字典
    sol_ss: 稳态解字典
    
    返回:
    distrib_tran: 转移动态分布字典
    """
    # 输入检查
    if not isinstance(par, dict):
        raise TypeError("输入<par>在fun_distrib1_tran中必须是字典！")
    if not isinstance(pol_tran, dict):
        raise TypeError("输入<pol_tran>在fun_distrib1_tran中必须是字典！")
    if not isinstance(distrib_ss, dict):
        raise TypeError("输入<distrib_ss>在fun_distrib1_tran中必须是字典！")
    
    # 解包所有t的政策函数
    pol_debt = pol_tran['pol_debt']  # 维度:(nk,nb,nx,T+1,nn)
    pol_exit = pol_tran['pol_exit']  # 维度:(nk,nb,nx,T+1,nn)
    pol_entry = pol_tran['pol_entry']  # 维度:(nk,nb,nx,T+1,nn)
    pol_kp_ind = pol_tran['pol_kp_ind']  # 维度:(nk,nb,nx,T+1,nn)
    b_grid = pol_tran['b_grid']  # 维度:(nk,nb,T+1,nn)
    phi_dist = pol_tran['phi_dist']  # 维度:(nk,nb,nx,T+1,nn)
    
    # 解包稳态分布 --> 初始条件
    # 字典包含 = {mu,mu_active,entry_vec}
    mu_init = distrib_ss['mu']
    
    # 验证mu_init
    assert np.all(np.isfinite(mu_init)) and np.all(~np.isnan(mu_init)), "mu_init包含非有限值或NaN"
    assert np.all(mu_init >= 0), "mu_init包含负值"
    assert mu_init.shape == (par['nk'], par['nb'], par['nx']), f"mu_init维度错误: {mu_init.shape}"
    
    # 解包参数
    T = par['T']
    nx = par['nx']
    nb = par['nb']
    nk = par['nk']
    nn = par['nn']  # nn = ni x ns
    pi_x = par['pi_x']  # x的转移矩阵
    mass_vec = par['mass_vec']  # 潜在进入者质量, 维度 (T+1,)
    psi = par['psi']
    verbose = par.get('verbose', 1)
    
    if phi_dist.shape != (nk, nb, nx, T + 1, nn):
        raise ValueError(f'phi_dist维度不正确: {phi_dist.shape}, 期望 ({nk},{nb},{nx},{T+1},{nn})')
    
    # 计算mu^0，退出和进入前的分布
    mu = np.zeros((nk, nb, nx, T + 1, nn))  # 维度: (k,b,x,time,impact x grant)
    
    # 初始条件：第一期的在位者分布是稳态分布
    for n_c in range(nn):  # 受冲击 vs 未受冲击 x 有补助 vs 无补助
        mu[:, :, :, 0, n_c] = mu_init
    
    if verbose >= 1:
        print('Start distribution..')
    
    for n_c in range(nn):
        for t in range(1, T + 1):
            # t时的潜在进入者质量
            mass = mass_vec[t]
            # 要传递给子函数的时间t政策函数
            pol_debt_t = pol_debt[:, :, :, t - 1, n_c]  # (k,b,x)
            pol_exit_t = pol_exit[:, :, :, t - 1, n_c]  # (k,b,x)
            pol_entry_t = pol_entry[:, :, :, t - 1, n_c]  # (k,b,x)
            pol_kp_ind_t = pol_kp_ind[:, :, :, t - 1, n_c]  # (k,b,x)
            phi_dist_t = phi_dist[:, :, :, t - 1, n_c]  # (k,b,x)
            b_grid_t = b_grid[:, :, t - 1, n_c]  # (k,b)
            
            b_min_all = np.min(b_grid_t[:, 0])  # 标量
            b_max_all = np.max(b_grid_t[:, nb - 1])  # 标量
            b_grid_all = np.linspace(b_min_all, b_max_all, nb)
            
            bopt = pol_debt_t  # 维度是 (nk,nb,nx)
            b_min = b_grid_t[pol_kp_ind_t, 0].reshape(nk, nb, nx)
            b_max = b_grid_t[pol_kp_ind_t, nb - 1].reshape(nk, nb, nx)
            
            # 避免除零
            b_range = b_max - b_min
            b_range[b_range == 0] = 1e-10
            
            bopt_new = ((bopt - b_min) / b_range * (b_max_all - b_min_all) + 
                       b_min_all)  # 维度是 (nk,nb,nx)
            
            loc_vec, omega_vec = find_loc_vec(b_grid_all, bopt_new.flatten())  # 维度是 (nk*nb*nx,)
            
            left_loc_arr = loc_vec.reshape(nk, nb, nx)
            omega_arr = omega_vec.reshape(nk, nb, nx)
            
            # 在分布方程上前向迭代
            mu[:, :, :, t, n_c] = sub_mu_onestep(mu[:, :, :, t - 1, n_c], phi_dist_t,
                                                 pol_kp_ind_t, pol_exit_t, pol_entry_t,
                                                 left_loc_arr, omega_arr, pi_x, mass, psi)
            
            if verbose >= 2:
                print(f'iter = {t} ; n_c = {n_c}')
    
    # 验证mu
    assert np.all(np.isfinite(mu)) and np.all(~np.isnan(mu)), "mu包含非有限值或NaN"
    assert np.all(mu >= 0), "mu包含负值"
    
    # 计算mu，活跃企业
    # 活跃企业的测度（见方程5）
    mu_active = np.zeros((nk, nb, nx, T + 1, nn))  # 维度:(k,b,x,time,impact x grant)
    
    for n_c in range(nn):
        for t in range(T + 1):
            for x_c in range(nx):
                for b_c in range(nb):
                    for k_c in range(nk):
                        mu_active[k_c, b_c, x_c, t, n_c] = (
                            (1 - psi) * (1 - pol_exit[k_c, b_c, x_c, t, n_c]) * 
                            mu[k_c, b_c, x_c, t, n_c] +
                            mass_vec[t] * pol_entry[k_c, b_c, x_c, t, n_c] * 
                            phi_dist[k_c, b_c, x_c, t, n_c])
    
    # 验证mu_active
    assert np.all(np.isfinite(mu_active)) and np.all(~np.isnan(mu_active)), "mu_active包含非有限值或NaN"
    assert np.all(mu_active >= 0), "mu_active包含负值"
    
    # 将输出打包到字典中
    distrib_tran = pack_to_struct(mu=mu, mu_active=mu_active)
    
    return distrib_tran

