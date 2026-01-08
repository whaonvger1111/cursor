"""
计算转移动态路径上的加总变量(L,K,Y)
注意：我使用_small和_corp分别表示非企业部门和企业部门的变量
"""
import numpy as np
from fun import Fun
from sub.sub_aggregates_onestep import sub_aggregates_onestep
from compute_cap_adj import compute_cap_adj


def ind2sub(shape, index):
    """将线性索引转换为多维索引"""
    return np.unravel_index(index, shape)


def sub2ind(shape, *indices):
    """将多维索引转换为线性索引"""
    return np.ravel_multi_index(indices, shape)


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from tools.v2struct import pack_to_struct


def fun_aggregates_tran(par, pol_tran, distrib_tran, path, agg_ss, distrib_ss, prices_ss):
    """
    计算转移动态路径上的加总变量
    
    参数:
    par: 参数字典
    pol_tran: 转移动态政策函数字典
    distrib_tran: 转移动态分布字典
    path: 价格路径字典
    agg_ss: 稳态加总变量字典
    distrib_ss: 稳态分布字典
    prices_ss: 稳态价格字典
    
    返回:
    agg_tran: 转移动态加总变量字典
    """
    # 输入检查
    if not isinstance(par, dict):
        raise TypeError("输入<par>在fun_aggregates_tran中必须是字典！")
    if not isinstance(pol_tran, dict):
        raise TypeError("输入<pol_tran>在fun_aggregates_tran中必须是字典！")
    if not isinstance(distrib_tran, dict):
        raise TypeError("输入<distrib_tran>在fun_aggregates_tran中必须是字典！")
    if not isinstance(path, dict):
        raise TypeError("输入<path>在fun_aggregates_tran中必须是字典！")
    if not isinstance(agg_ss, dict):
        raise TypeError("输入<agg_ss>在fun_aggregates_tran中必须是字典！")
    
    # 验证分布
    mu = distrib_tran['mu']
    mu_active = distrib_tran['mu_active']
    assert np.all(np.isfinite(mu)) and np.all(~np.isnan(mu)), "mu包含非有限值或NaN"
    assert np.all(mu >= 0), "mu包含负值"
    assert mu.shape == (par['nk'], par['nb'], par['nx'], par['T'] + 1, par['nn']), \
        f"mu维度错误: {mu.shape}"
    
    # 解包政策
    pol_exit = pol_tran['pol_exit']  # 维度: (nk,nb,nx,T+1,nn)
    pol_entry = pol_tran['pol_entry']  # 维度: (nk,nb,nx,T+1,nn)
    phi_dist = pol_tran['phi_dist']  # 维度: (nk,nb,nx,T+1,nn)
    pol_kp_ind = pol_tran['pol_kp_ind']
    pol_kp = pol_tran['pol_kp']
    
    # 解包分布
    # mu和mu_active已经在上面解包
    
    # 解包价格路径
    wage_path = path['w']
    KL_ratio = path['KL_ratio']
    C_path = path['C']
    
    # 解包参数
    T = par['T']
    T_grant = par.get('T_grant', 0)
    k_grid = par['k_grid']  # 维度 (nk,)
    delta_k = par['delta_k']
    x_grid = par['x_grid']
    mass_vec = par['mass_vec']
    nx = par['nx']
    nb = par['nb']
    nk = par['nk']
    ni = par['ni']
    ns = par['ns']
    nn = par['nn']
    A_small = par['A_small']  # 维度 (T+1,ni)
    A_corp = par['A_corp']
    psi = par['psi']
    
    if par.get('verbose', 0) >= 1:
        print(' ')
        print('Aggregates transition..')
    
    # 定义权重
    # - n_c = 0: impact, grant
    # - n_c = 1: no impact, grant
    # - n_c = 2: impact, no grant
    # - n_c = 3: no impact, no grant
    weights = par['weights']  # 维度:(nk,nx,nn)
    
    # 1. 计算小企业对租赁资本的需求
    # 注意：草稿中的mu ==> 代码中的mu_active
    #       草稿中的mu^0 ==> 代码中的mu
    K_small = np.zeros(T + 1)
    mass_small = np.zeros(T + 1)  # 小企业质量
    mass_small_0 = np.zeros(T + 1)  # 在位小企业质量
    
    weights_arr = np.tile(weights[:, :, :, np.newaxis], (1, 1, 1, nb))
    weights_arr = np.transpose(weights_arr, (0, 3, 1, 2))  # (nk,nb,nx,nn)
    kappa_arr = np.tile(k_grid[:, np.newaxis, np.newaxis, np.newaxis], (1, nb, nx, nn))
    mu_active_p = np.transpose(mu_active, (0, 1, 2, 4, 3))  # (nk,nb,nx,nn,T+1)
    mu_p = np.transpose(mu, (0, 1, 2, 4, 3))  # (nk,nb,nx,nn,T+1)
    
    for t in range(T + 1):
        K_small[t] = np.sum(kappa_arr * weights_arr * mu_active_p[:, :, :, :, t])
        mass_small[t] = np.sum(weights_arr * mu_active_p[:, :, :, :, t])
        mass_small_0[t] = np.sum(weights_arr * mu_p[:, :, :, :, t])
    
    # 2. 计算小企业部门的一些加总变量
    output_small = np.zeros(T + 1)
    Y_small = np.zeros(T + 1)  # 等于output_small-cost_adj+liq-entry
    entry_vec = np.zeros(T + 1)
    entry_rate_vec = np.zeros(T + 1)
    entry_cost_vec = np.zeros(T + 1)
    liq_vec = np.zeros(T + 1)
    exit_vec = np.zeros(T + 1)
    exit_rate_vec = np.zeros(T + 1)
    L_small = np.zeros(T + 1)
    cost_adj = np.zeros(T + 1)
    capadj = np.zeros((T + 1, 4))  # 四种类型的资本调整
    exit_emp_vec = np.zeros(T + 1)  # 排除微型企业的退出
    exit_rate_emp_vec = np.zeros(T + 1)  # 排除微型企业的退出率
    wage_t0 = prices_ss.get('wage', prices_ss.get('w', 1.0))  # 上一期的工资
    A_small_t0 = np.ones(2)
    
    for t in range(T + 1):
        # t时的潜在进入者质量
        mass = mass_vec[t]
        # 重置临时变量
        output = np.zeros(nn)
        c_adj = np.zeros(nn)
        entry = np.zeros(nn)
        entry_cost = np.zeros(nn)
        exit_rate = np.zeros(nn)
        liq = np.zeros(nn)
        empl = np.zeros(nn)
        exits_emp = np.zeros(nn)
        mass_emp = np.zeros(nn)
        capadj_vec = np.zeros((4, nn))
        
        for n_c in range(nn):
            i_c, _ = ind2sub([ni, ns], n_c)  # i_c = 受冲击指标; s_c = 补助指标
            
            weights_n = weights[:, :, n_c]
            weights_nn = np.transpose(np.tile(weights_n[:, :, np.newaxis], (1, 1, nb)), (0, 2, 1))
            mu_temp = weights_nn * mu[:, :, :, t, n_c]
            mu_active_temp = weights_nn * mu_active[:, :, :, t, n_c]
            phi_dist_temp = weights_nn * phi_dist[:, :, :, t, n_c]
            # exit_all_n: 总退出率包括外生和内生退出
            exit_all_n = psi + (1 - psi) * pol_exit[:, :, :, t, n_c]
            # 小企业加总变量
            entry_cost[n_c], output[n_c], liq[n_c], empl[n_c], c_adj[n_c], \
            exit_rate[n_c], entry[n_c] = sub_aggregates_onestep(
                mu_temp, mu_active_temp, pol_kp_ind[:, :, :, t, n_c],
                pol_entry[:, :, :, t, n_c], exit_all_n, phi_dist_temp,
                wage_path[t], mass, A_small[t, i_c], par)
            # 资本调整变量
            capadj_vec[:, n_c] = compute_cap_adj(
                pol_kp[:, :, :, t, n_c], mu_temp, mu_active_temp, phi_dist_temp,
                pol_entry[:, :, :, t, n_c], pol_exit[:, :, :, t, n_c],
                mass, k_grid, delta_k, psi)
            # 排除微型企业的退出率
            exits_temp = 0
            mass_temp = 0
            for x_c in range(nx):
                x_val = x_grid[x_c]
                for k_c in range(nk):
                    kappa = k_grid[k_c]
                    l_opt = Fun.fun_l(x_val, prices_ss.get('wage', prices_ss.get('w', 1.0)), 
                                     kappa, par)
                    
                    if l_opt > par.get('emp_min', 0):
                        exits_temp += np.sum(exit_all_n[k_c, :, x_c] * mu_temp[k_c, :, x_c])
                        mass_temp += np.sum(mu_temp[k_c, :, x_c])
            exits_emp[n_c] = exits_temp
            mass_emp[n_c] = mass_temp
        
        entry_cost_vec[t] = np.sum(entry_cost)  # 进入成本
        entry_vec[t] = np.sum(entry)  # 进入者测度
        if mass_small[t] > 0:
            entry_rate_vec[t] = np.sum(entry) / mass_small[t]
        liq_vec[t] = np.sum(liq)
        cost_adj[t] = np.sum(c_adj)
        exit_vec[t] = np.sum(exit_rate)  # 退出企业测度
        if mass_small_0[t] > 0:
            exit_rate_vec[t] = np.sum(exit_rate) / mass_small_0[t]
        output_small[t] = np.sum(output)  # 小企业产出
        L_small[t] = np.sum(empl)  # 小企业就业
        # Y_small是小企业产出减去折旧加上退出减去进入
        Y_small[t] = output_small[t] - cost_adj[t] + liq_vec[t] - entry_cost_vec[t]
        capadj[t, :] = np.sum(capadj_vec, axis=1)
        # 排除微型企业的退出
        exit_emp_vec[t] = np.sum(exits_emp)
        if np.sum(mass_emp) > 0:
            exit_rate_emp_vec[t] = np.sum(exits_emp) / np.sum(mass_emp)
        # 更新上一期的A_small和wage
        wage_t0 = wage_path[t]
        A_small_t0 = A_small[t, :]
    
    # 3. 计算企业部门的劳动和产出以及K的投资
    L_corp = np.zeros(T + 1)
    Y_corp = np.zeros(T + 1)
    K_corp = np.zeros(T + 1)
    InvK_corp = np.zeros(T + 1)  # 企业投资
    
    # 资本是预定的
    K_corp[0] = agg_ss['K_corp']
    
    for t in range(T + 1):
        L_corp[t] = K_corp[t] / KL_ratio[t] if KL_ratio[t] > 0 else 0
        if K_corp[t] > 0:
            Y_corp[t] = A_corp[t] * Fun.prod_corp(KL_ratio[t], L_corp[t], par)
        else:
            Y_corp[t] = 0
        
        InvK_corp[t] = Y_small[t] + Y_corp[t] - C_path[t]
        if t < T:
            K_corp[t + 1] = (1 - delta_k) * K_corp[t] + InvK_corp[t]
    
    K_agg = K_corp + K_small
    
    Y_agg = Y_corp + output_small
    L_agg = L_corp + L_small
    
    # 经济范围的资本和投资
    InvK = InvK_corp + entry_cost_vec - liq_vec + cost_adj
    
    # 补助政策的成本
    tot_grant = 0
    for i_c in range(ni):
        n_c = sub2ind([ni, ns], i_c, 0)  # s_c=0表示有补助
        for t in range(T_grant):
            for k_c in range(nk):
                for x_c in range(nx):
                    # 所有退出
                    exit_all_b = psi + (1 - psi) * pol_exit[k_c, :, x_c, t, n_c]
                    tot_grant += (pol_tran['grant_vec'][k_c, x_c, t, 0] * 
                                 weights[k_c, x_c, n_c] *
                                 np.sum((1 - exit_all_b) * mu[k_c, :, x_c, t, n_c]))
    
    agg_tran = pack_to_struct(
        Y_agg=Y_agg, Y_corp=Y_corp, Y_small=Y_small, output_small=output_small,
        K_small=K_small, K_corp=K_corp, K_agg=K_agg, InvK=InvK, InvK_corp=InvK_corp,
        L_agg=L_agg, L_corp=L_corp, L_small=L_small, mass_small=mass_small,
        mass_small_0=mass_small_0,
        entry_vec=entry_vec, entry_cost_vec=entry_cost_vec, entry_rate_vec=entry_rate_vec,
        liq_vec=liq_vec, exit_rate_vec=exit_rate_vec, exit_vec=exit_vec,
        cost_adj=cost_adj, tot_grant=tot_grant, capadj=capadj,
        exit_emp_vec=exit_emp_vec, exit_rate_emp_vec=exit_rate_emp_vec
    )
    
    return agg_tran

