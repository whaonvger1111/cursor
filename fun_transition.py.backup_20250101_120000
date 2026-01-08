"""
转移动态计算函数
计算意外疫情冲击后的转移动态
"""
import numpy as np
import os
import time
from scipy.optimize import fsolve
from fun import Fun


def fun_transition(par, sol_ss, agg_ss, distrib_ss, prices_ss, b_grid_ss):
    """
    计算意外疫情冲击后的转移动态（在t=0时）
    
    参数:
    par: 参数字典
    sol_ss: 稳态解结构（政策函数和值函数）
    agg_ss: 稳态加总变量结构
    distrib_ss: 稳态分布结构
    prices_ss: 稳态价格结构
    b_grid_ss: 稳态债务网格
    
    返回:
    agg_tran: 转移动态加总变量
    path: 价格路径
    conv_flag: 收敛标志
    pol_tran: 转移动态政策函数
    distrib_tran: 转移动态分布
    """
    # 解包参数
    T = par['T']  # 转移动态期数
    max_iter_tr = par['max_iter_tr']
    tol_tran = par['tol_tran']
    damp = par['dampening']
    verbose = par.get('verbose', 1)
    disp_tran = par.get('disp_tran', 1)
    
    beta = par['beta']
    A_corp = par['A_corp']
    margutil = par['margutil']
    lsupply = par['lsupply']
    delta_k = par['delta_k']
    zeta = par['zeta']
    sigma = par['sigma']
    
    # 初始化路径
    path = {
        'C': np.zeros(T + 1),
        'KL_ratio': np.zeros(T + 1),
        'w': np.zeros(T + 1),
        'q': np.zeros(T + 1)
    }
    
    # 0. 猜测第1期的消费 (C_path(1))
    # 代码中的第t=0期对应草稿中的第t=1期
    # 改善初始猜测：更接近稳态值，缩小搜索范围
    C_h = 0.88 * agg_ss['C_agg']  # 从0.85改为0.88，更接近稳态
    C_l = 0.96 * agg_ss['C_agg']  # 从0.95改为0.96，更接近稳态
    C_init = 0.92 * agg_ss['C_agg']  # 从0.9改为0.92，更接近稳态（中点）
    
    iter_count = 0
    err_tran = tol_tran + 1
    
    # 创建输出文件记录每次迭代的err trans
    log_file = 'transition_iterations.log'
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("转移动态迭代日志\n")
        f.write("="*80 + "\n")
        f.write(f"转移动态长度 T = {T}\n")
        f.write(f"最大迭代次数 = {max_iter_tr}\n")
        f.write(f"容差 tol_tran = {tol_tran}\n")
        f.write(f"稳态 K_agg = {agg_ss['K_agg']:.10f}\n")
        f.write("="*80 + "\n\n")
    
    # 开始转移动态循环
    while abs(err_tran) > tol_tran and iter_count <= max_iter_tr:
        if disp_tran == 1:
            start_time = time.time()
        
        # 1. 求解 C_path(2:T+1), wage(1:T+1), KL_ratio(1:T+1), q(1:T+1)
        path['C'][0] = C_init
        
        for t in range(T + 1):
            # wage(t)
            path['w'][t] = lsupply[t] * zeta * (path['C'][t] ** sigma)
            
            # KL_ratio(t)
            if t == 0:
                path['KL_ratio'][t] = Fun.KL_tran(path['w'][t], A_corp[t], par)
            
            # KL_ratio(t+1)
            if t < T:
                def fun_KL_ratio(k_next):
                    return Fun.dyn_eqn_capital(k_next, path['KL_ratio'][t], par, t)
                
                result = fsolve(fun_KL_ratio, path['KL_ratio'][t], xtol=1e-10)
                path['KL_ratio'][t + 1] = result[0]
            
            # q(t)
            if t < T:
                path['q'][t] = 1 / (1 - delta_k + A_corp[t + 1] * 
                                    Fun.marg_prod_capital(path['KL_ratio'][t + 1], par))
            else:
                path['q'][t] = prices_ss['q']
            
            # C(t+1)
            if t < T:
                path['C'][t + 1] = path['C'][t] * ((beta * margutil[t + 1]) / 
                                                   (path['q'][t] * margutil[t])) ** (1 / sigma)
        
        # 2. 价值函数：向后迭代
        #   2.a. 计算利润 profit_mat(1:xn,1:T+1)
        #   2.b. 通过向后归纳计算价值函数 val(1:nb,1:nx,1:T+1), val0(1:nb,1:nx,2:T+1);
        #       同时计算相关的政策函数 pol_entry, pol_exit, pol_debt for t = 1,...T+1
        if verbose >= 1:
            print('--------------------------------------------')
            print('START VFI TRANSITION..')
            vfi_start = time.time()
        
        # 调用fun_vfi1_transition
        from fun_vfi1_transition import fun_vfi1_transition
        pol_tran = fun_vfi1_transition(par, path, sol_ss, b_grid_ss)
        
        if verbose >= 1:
            vfi_time = time.time() - vfi_start
            print(f'Time to do VFI TRANSITION: {vfi_time:8.4f}')
            print(' ')
        
        # 3. 分布：前向迭代
        # 分布的输入：稳态mu和mu_active，所有t的债务、进入和清算政策函数，在VFI中计算
        # 输出：所有t的分布序列
        if verbose >= 1:
            dist_start = time.time()
        
        from fun_distrib1_tran import fun_distrib1_tran
        distrib_tran = fun_distrib1_tran(par, pol_tran, distrib_ss, sol_ss)
        
        if verbose >= 1:
            dist_time = time.time() - dist_start
            print(f'Time to do DISTRIBUTION: {dist_time:8.4f}')
            print(' ')
        
        # 转移动态的加总
        from fun_aggregates_tran import fun_aggregates_tran
        agg_tran = fun_aggregates_tran(par, pol_tran, distrib_tran, path, 
                                      agg_ss, distrib_ss, prices_ss)
        
        K_agg = agg_tran.get('K_agg', np.zeros(T + 1))
        
        # 更新 C(1) - 找到 C(1) 使得 agg_tran.K_agg(1) 接近 agg_ss.K_agg
        if np.any(K_agg < 0) or np.any(~np.isreal(K_agg)):
            # K太低，减少C(1)
            C_h = damp * C_init + (1 - damp) * C_h
        else:
            if K_agg[T] < agg_ss['K_agg']:
                C_h = damp * C_init + (1 - damp) * C_h
            else:
                C_l = damp * C_init + (1 - damp) * C_l
        
        # 更新
        err_tran_vec = K_agg[T] - agg_ss['K_agg']
        err_tran = err_tran_vec
        C_init = 0.5 * (C_h + C_l)
        iter_count += 1
        
        # 计算额外信息
        err_abs = abs(err_tran)
        if agg_ss['K_agg'] > 0:
            err_pct = (err_tran / agg_ss['K_agg']) * 100
        else:
            err_pct = 0
        K_agg_T = K_agg[T] if len(K_agg) > T else 0
        
        if disp_tran == 1:
            print(f"iter trans = {iter_count}")
            print(f"err  trans = {err_tran}")
            print(err_tran_vec)
            print(f"C_l = {C_l:.18f}")
            print(f"C_h = {C_h:.18f}")
            elapsed = time.time() - start_time
            print(f"Time elapsed: {elapsed:.4f}")
            print('--------------------------------------------')
        
        # 写入文件记录每次迭代的err trans
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"迭代 {iter_count}/{max_iter_tr}\n")
            f.write(f"  误差 (err trans):     {err_tran:15.6f}\n")
            f.write(f"  误差绝对值:          {err_abs:15.6f}\n")
            f.write(f"  容差 (tol_tran):      {tol_tran:15.6f}\n")
            if tol_tran > 0:
                f.write(f"  误差/容差:           {err_abs/tol_tran:15.6f}\n")
            f.write(f"  K_agg[T] (第{T}期):   {K_agg_T:15.6f}\n")
            f.write(f"  K_agg_ss (稳态):      {agg_ss['K_agg']:15.6f}\n")
            f.write(f"  相对误差 (%):         {err_pct:15.6f}%\n")
            f.write(f"  C_init:               {C_init:15.6f}\n")
            f.write(f"  C_l:                  {C_l:15.6f}\n")
            f.write(f"  C_h:                  {C_h:15.6f}\n")
            f.write(f"  C区间宽度:            {C_h - C_l:15.6f}\n")
            if disp_tran == 1:
                elapsed = time.time() - start_time
                f.write(f"  累计耗时:            {elapsed:15.4f}秒\n")
            f.write("-"*80 + "\n\n")
    
    # 在循环结束后，写入最终结果到文件
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        if abs(err_tran) <= tol_tran:
            f.write(f"收敛成功！迭代次数: {iter_count}, 最终误差: {err_tran:.10f}\n")
        else:
            f.write(f"未收敛！迭代次数: {iter_count}, 最终误差: {err_tran:.10f}\n")
        f.write("="*80 + "\n")
    
    if disp_tran == 1:
        print(f"\n转移动态迭代日志已保存到: {log_file}")
    
    # 在输出中包含动态b网格
    if 'b_grid' in pol_tran:
        agg_tran['b_grid'] = pol_tran['b_grid']
    
    conv_flag = 0
    if abs(err_tran) > tol_tran:
        conv_flag = -1
    
    return agg_tran, path, conv_flag, pol_tran, distrib_tran

