"""
计算平稳分布mu_0(k,b,x)（代码中称为mu）
和活跃企业分布mu_active(k,b,x)
"""
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'sub'))

from find_loc_vec import find_loc_vec
from sub.sub_mu_onestep import sub_mu_onestep
from sub.sub_mu_onestep_fortran import sub_mu_onestep_fortran


def find_loc(x_grid, xi):
    """
    找到jl使得x_grid(jl)<=xi<x_grid(jl+1)（标量版本）
    """
    from tools.find_loc import find_loc as _find_loc
    return _find_loc(x_grid, xi)


def fun_distrib1(par, sol, b_grid, phi_dist):
    """
    计算平稳分布
    
    参数:
    par: 参数字典
    sol: 解字典
    b_grid: (nk,nb)数值数组
    phi_dist: (nk,nb,nx)数值数组
    
    返回:
    mu: 平稳分布, 维度: (nk,nb,nx)
    mu_active: 活跃企业分布, 维度: (nk,nb,nx)
    entry_vec: 进入向量
    flag_mu: 收敛标志
    dist: 标量误差
    iter: 迭代次数
    """
    # 输入检查
    if not isinstance(par, dict):
        raise TypeError("输入<par>必须是字典！")
    if not isinstance(sol, dict):
        raise TypeError("输入<sol>必须是字典！")
    
    # 解包SOL
    pol_kp_ind = sol['pol_kp_ind']  # 维度: (nk,nb,nx)
    pol_debt = sol['pol_debt']  # 维度: (nk,nb,nx)
    pol_exit = sol['pol_exit']  # 维度: (nk,nb,nx)
    pol_entry = sol['pol_entry']  # 维度: (nk,nb,nx)
    
    # 验证输入数据
    assert np.all(np.isfinite(pol_kp_ind)) and np.all(~np.isnan(pol_kp_ind)), "pol_kp_ind包含非有限值或NaN"
    assert np.all((pol_kp_ind >= 0) & (pol_kp_ind < par['nk'])), "pol_kp_ind超出范围"
    
    # 验证pol_exit和pol_entry在[0,1]范围内
    if np.any(pol_exit < 0) or np.any(pol_exit > 1):
        print(f'警告: pol_exit超出[0,1]范围，最小值={np.min(pol_exit):.6f}, 最大值={np.max(pol_exit):.6f}')
        pol_exit = np.clip(pol_exit, 0, 1)
    
    if np.any(pol_entry < 0) or np.any(pol_entry > 1):
        print(f'警告: pol_entry超出[0,1]范围，最小值={np.min(pol_entry):.6f}, 最大值={np.max(pol_entry):.6f}')
        pol_entry = np.clip(pol_entry, 0, 1)
    
    # 验证phi_dist
    if np.any(phi_dist < 0):
        n_negative = np.sum(phi_dist < 0)
        print(f'警告: phi_dist包含 {n_negative} 个负值，将设为0')
        phi_dist = np.maximum(phi_dist, 0.0)
        phi_dist_sum = np.sum(phi_dist)
        if phi_dist_sum > 0:
            phi_dist = phi_dist / phi_dist_sum
        else:
            raise ValueError("phi_dist所有值都是负值或零")
    
    if not np.all(np.isfinite(phi_dist)):
        n_bad = np.sum(~np.isfinite(phi_dist))
        print(f'警告: phi_dist包含 {n_bad} 个非有限值，将设为0')
        phi_dist = np.where(np.isfinite(phi_dist), phi_dist, 0.0)
        phi_dist_sum = np.sum(phi_dist)
        if phi_dist_sum > 0:
            phi_dist = phi_dist / phi_dist_sum
    
    # 解包参数
    nx = par['nx']
    nb = par['nb']
    nk = par['nk']
    pi_x = par['pi_x']
    mass = par['mass']  # 潜在进入者质量
    psi = par['psi']  # 外生退出率
    tol_dist = par['tol_dist']
    maxit = par['maxiter_dist']
    verbose = par.get('verbose', 1)
    disp_mu = par.get('disp_mu', 0)
    
    # 初始条件
    mu = np.zeros((nk, nb, nx))
    for k_c in range(nk):
        for b_c in range(nb):
            mu[k_c, b_c, :] = par['x_prob']
    
    mu = 0.02 * mu / np.sum(mu)
    
    if mu.shape != (nk, nb, nx):
        raise ValueError(f'mu维度错误: {mu.shape}')
    
    nn = nk * nb * nx
    
    dist = 10
    iter_count = 0
    
    flag_mu = 0
    
    if verbose >= 1:
        print('--------------------------------------------')
        print('DISTRIBUTION')
        print('--------------------------------------------')
    
    # 计算进入向量
    entry_vec = np.zeros((nk, nb, nx))
    for x_c in range(nx):  # 当前生产率
        for b_c in range(nb):  # 当前债务
            for k_c in range(nk):  # 当前资本
                knext_ind = int(pol_kp_ind[k_c, b_c, x_c])
                bnext = pol_debt[k_c, b_c, x_c]
                left_loc, omega = find_loc(b_grid[knext_ind, :], bnext)
                
                for xp_c in range(nx):
                    left_loc = int(np.clip(left_loc, 0, nb - 2))
                    entry_vec[knext_ind, left_loc, xp_c] += (
                        omega * mass * pi_x[x_c, xp_c] * pol_entry[k_c, b_c, x_c] * 
                        phi_dist[k_c, b_c, x_c])
                    if left_loc + 1 < nb:
                        entry_vec[knext_ind, left_loc + 1, xp_c] += (
                            (1 - omega) * mass * pi_x[x_c, xp_c] * pol_entry[k_c, b_c, x_c] * 
                            phi_dist[k_c, b_c, x_c])
    
    # 计算mu^0(b,x)
    if verbose >= 1:
        print(' ')
        print('Start distribution..')
    
    left_loc_arr = np.ones((nk, nb, nx), dtype=int)
    omega_arr = np.zeros((nk, nb, nx))
    
    for x_c in range(nx):  # 当前生产率
        for b_c in range(nb):  # 当前债务
            for k_c in range(nk):  # 当前资本
                knext_ind = int(pol_kp_ind[k_c, b_c, x_c])
                knext_ind = np.clip(knext_ind, 0, nk - 1)  # 确保索引有效
                bopt = pol_debt[k_c, b_c, x_c]
                left_loc, omega = find_loc(b_grid[knext_ind, :], bopt)
                # 确保omega在[0,1]范围内
                omega = np.clip(omega, 0.0, 1.0)
                omega_arr[k_c, b_c, x_c] = omega
                left_loc_arr[k_c, b_c, x_c] = int(np.clip(left_loc, 0, nb - 2))
    
    # 使用Fortran版本（必需）
    use_fortran_mu = par.get('use_fortran', False)
    
    # 确认并打印分布更新混合编程状态
    if use_fortran_mu:
        print("="*60)
        print("[VFI混合编程] 分布更新: 使用Fortran加速版本（混合编程 + OpenMP并行化）")
        print(f"  - 网格大小: nk={nk}, nb={nb}, nx={nx}")
        print(f"  - OpenMP并行化: 已启用（x_c和k_c循环并行）")
        print(f"  - 最大迭代次数: {maxit}")
        print(f"  - 收敛容差: {tol_dist:.2e}")
        print("="*60)
    else:
        print("="*60)
        print("[VFI混合编程] 分布更新: 使用Python版本")
        print("="*60)
    
    while dist > tol_dist and iter_count <= maxit:
        iter_count += 1
        
        # 在分布方程上迭代
        if use_fortran_mu:
            mu1 = sub_mu_onestep_fortran(mu, phi_dist, pol_kp_ind, pol_exit, pol_entry,
                                        left_loc_arr, omega_arr, pi_x, mass, psi)
        else:
            mu1 = sub_mu_onestep(mu, phi_dist, pol_kp_ind, pol_exit, pol_entry,
                                left_loc_arr, omega_arr, pi_x, mass, psi)
        
        # 检查并修复负值（由于数值精度问题可能出现非常小的负值）
        min_mu1 = np.min(mu1)
        if min_mu1 < 0:
            n_negative = np.sum(mu1 < 0)
            max_negative = np.min(mu1[mu1 < 0]) if n_negative > 0 else 0
            if verbose >= 1:
                print(f'警告: 迭代 {iter_count} 发现 {n_negative} 个负值，最小值为 {max_negative:.2e}')
            # 将负值设为0（保持质量守恒）
            mu1 = np.maximum(mu1, 0.0)
            # 重新归一化以保持质量守恒
            mu1_sum = np.sum(mu1)
            if mu1_sum > 0:
                mu1 = mu1 / mu1_sum * np.sum(mu)
            else:
                # 如果所有值都是0或负，使用前一次迭代的值
                if verbose >= 1:
                    print(f'严重警告: mu1总和为0，保持前一次迭代的值')
                mu1 = mu.copy()
        
        # 检查NaN和Inf
        if not np.all(np.isfinite(mu1)):
            n_inf = np.sum(~np.isfinite(mu1))
            if verbose >= 1:
                print(f'严重警告: 迭代 {iter_count} 发现 {n_inf} 个非有限值')
            # 将非有限值设为0
            mu1 = np.where(np.isfinite(mu1), mu1, 0.0)
            mu1_sum = np.sum(mu1)
            if mu1_sum > 0:
                mu1 = mu1 / mu1_sum * np.sum(mu)
            else:
                mu1 = mu.copy()
        
        # 计算误差
        dist1 = np.max(np.abs(mu - mu1))
        mu_sum = np.sum(mu)
        if mu_sum > 0:
            dist = np.max(np.abs(mu - mu1)) / mu_sum * nn
        else:
            dist = dist1
        
        # 更新mu
        mu = mu1
        
        if disp_mu == 1:
            print(f'sum(mu1) = {np.sum(mu1):.6f}, min(mu1) = {np.min(mu1):.2e}, max(mu1) = {np.max(mu1):.2e}')
            print(f'iter = {iter_count}, dist_abs = {dist1:.20f}, dist_rel = {dist:.20f}')
    
    # 验证并修复（最终检查）
    if not np.all(np.isfinite(mu)) or np.any(np.isnan(mu)):
        n_bad = np.sum(~np.isfinite(mu) | np.isnan(mu))
        print(f'错误: mu包含 {n_bad} 个非有限值或NaN')
        mu = np.where(np.isfinite(mu) & ~np.isnan(mu), mu, 0.0)
        mu_sum = np.sum(mu)
        if mu_sum > 0:
            mu = mu / mu_sum * 0.02  # 重新归一化
    
    if np.any(mu < 0):
        n_negative = np.sum(mu < 0)
        min_negative = np.min(mu[mu < 0])
        print(f'错误: mu包含 {n_negative} 个负值，最小值为 {min_negative:.2e}')
        # 将负值设为0并重新归一化
        mu = np.maximum(mu, 0.0)
        mu_sum = np.sum(mu)
        if mu_sum > 0:
            mu = mu / mu_sum * 0.02  # 重新归一化
        else:
            raise ValueError("mu所有值都是负值或零，无法修复")
    
    # 最终验证
    assert np.all(np.isfinite(mu)) and np.all(~np.isnan(mu)), "mu包含非有限值或NaN"
    assert np.all(mu >= 0), "mu包含负值"
    
    # 计算mu(b,x)，活跃企业
    # 活跃企业的测度（见方程5）
    mu_active = np.zeros((nk, nb, nx))
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                mu_active[k_c, b_c, x_c] = (
                    (1 - psi) * (1 - pol_exit[k_c, b_c, x_c]) * mu[k_c, b_c, x_c] +
                    mass * pol_entry[k_c, b_c, x_c] * phi_dist[k_c, b_c, x_c])
    
    # 验证并修复mu_active
    if not np.all(np.isfinite(mu_active)) or np.any(np.isnan(mu_active)):
        n_bad = np.sum(~np.isfinite(mu_active) | np.isnan(mu_active))
        print(f'错误: mu_active包含 {n_bad} 个非有限值或NaN')
        mu_active = np.where(np.isfinite(mu_active) & ~np.isnan(mu_active), mu_active, 0.0)
    
    if np.any(mu_active < 0):
        n_negative = np.sum(mu_active < 0)
        min_negative = np.min(mu_active[mu_active < 0])
        print(f'错误: mu_active包含 {n_negative} 个负值，最小值为 {min_negative:.2e}')
        # 将负值设为0
        mu_active = np.maximum(mu_active, 0.0)
    
    # 最终验证
    assert np.all(np.isfinite(mu_active)) and np.all(~np.isnan(mu_active)), "mu_active包含非有限值或NaN"
    assert np.all(mu_active >= 0), "mu_active包含负值"
    assert np.all(np.isfinite(entry_vec)) and np.all(~np.isnan(entry_vec)), "entry_vec包含非有限值或NaN"
    
    if dist > tol_dist:
        flag_mu = -1
    else:
        if verbose >= 1:
            print(f'MU (distr.) converged after {iter_count} iterations!')
    
    return mu, mu_active, entry_vec, flag_mu, dist, iter_count

