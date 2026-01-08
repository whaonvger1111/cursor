"""
转移动态校准的目标函数
"""
import numpy as np
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from fun_steady_state import fun_steady_state
from fun_transition import fun_transition
from fun_targets_tran import fun_targets_tran
from append_tran_txt import append_tran_txt

# 全局变量
obj_tran_best = np.inf


def fun_calib_transition(x_in, par, data_mom_trans, calibWeightsTran, bounds_shocks):
    """
    转移动态校准的目标函数
    
    参数:
    x_in: 要校准的参数向量
    par: 参数字典
    data_mom_trans: 转移动态数据矩
    calibWeightsTran: 校准权重
    bounds_shocks: 冲击边界
    
    返回:
    distance: 模型矩和数据矩之间的距离
    """
    global obj_tran_best
    
    # 检查参数是否在下界内
    if np.any(x_in < bounds_shocks[:, 0]):
        print('警告：参数违反下界！')
        distance = np.finfo(float).max
        return distance
    
    # 检查参数是否在上界内
    if np.any(x_in > bounds_shocks[:, 1]):
        print('警告：参数违反上界！')
        distance = np.finfo(float).max
        return distance
    
    par['eta_i'] = x_in[0]
    v_corp = x_in[1]
    util_shift = x_in[2]
    lsupply_shift = x_in[3]
    rho_shock = x_in[4]
    
    # 将冲击存储到"par"字典中，传递给fun_transition
    par['A_small'] = np.ones((par['T'] + 1, par['ni']))
    par['A_corp'] = np.ones(par['T'] + 1)
    par['margutil'] = np.ones(par['T'] + 1)
    par['lsupply'] = np.ones(par['T'] + 1)
    
    # 初始化第一期
    par['A_small'][0, 0] = 1 + par['v_small']  # 受冲击
    par['A_corp'][0] = 1 + v_corp
    par['margutil'][0] = 1 + util_shift
    par['lsupply'][0] = 1 + lsupply_shift
    
    for t in range(1, par['T'] + 1):
        par['A_small'][t, 0] = 1 + rho_shock ** t * par['v_small']  # 受冲击
        par['A_corp'][t] = 1 + rho_shock ** t * v_corp
        par['margutil'][t] = 1 + rho_shock ** t * util_shift
        par['lsupply'][t] = 1 + rho_shock ** t * lsupply_shift
    
    # 补助是否定向到受冲击企业
    par['weights'] = np.zeros((par['nk'], par['nx'], par['nn']))
    if par.get('grant_target', 0) == 1:
        if np.max(par['eta']) < par['eta_i']:
            print("受冲击企业太多，补助不足以定向！")
            # 可以考虑抛出异常或返回大值
        # 定向到受冲击企业
        # 即受冲击企业以prob=1获得补助
        # 未受冲击企业以prob = (eta-eta_i)/(1-eta_i)获得补助
        eta_unimp = (par['eta'] - par['eta_i']) / (1 - par['eta_i'] + 1e-20)
        par['weights'][:, :, 0] = par['eta_i']  # 受冲击，补助
        par['weights'][:, :, 1] = (1 - par['eta_i']) * eta_unimp  # 未受冲击，补助
        par['weights'][:, :, 2] = 0  # 受冲击，无补助
        par['weights'][:, :, 3] = (1 - par['eta_i']) * (1 - eta_unimp)  # 未受冲击，无补助
    else:  # 非定向
        par['weights'][:, :, 0] = par['eta_i'] * par['eta']
        par['weights'][:, :, 1] = (1 - par['eta_i']) * par['eta']
        par['weights'][:, :, 2] = par['eta_i'] * (1 - par['eta'])
        par['weights'][:, :, 3] = (1 - par['eta_i']) * (1 - par['eta'])
    
    if par.get('grant_flag', 0) == 0:
        raise ValueError('必须在补助开启的情况下进行校准')
    
    if par.get('grant_target', 0) == 1:
        raise ValueError('必须在非定向补助的情况下进行校准')
    
    print('=============================================================')
    print('Start steady-state computation...')
    print(' ')
    start_time = time.time()
    # 稳态中的退出率：agg.exit_rate
    sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par = fun_steady_state(par)
    if flag_ss < 0:
        print("警告：未找到稳态！")
    else:
        print('Steady-state computed!')
    elapsed = time.time() - start_time
    print(f'Time elapsed: {elapsed:.4f}')
    
    print(' ')
    print('Start transition...')
    print(f'Transition periods T = {par["T"]}')
    print(f'grant_flag           = {par.get("grant_flag", 0)}')
    
    start_time = time.time()
    # 转移动态中的退出率：agg_tran.exit_rate_vec
    agg_tran, path, conv_flag, pol_tran, distrib_tran = fun_transition(par, sol, agg, distribS, prices, b_grid)
    print('Time to compute transition:')
    elapsed = time.time() - start_time
    print(f'{elapsed:.4f}')
    
    if conv_flag < 0:
        print("警告：请小心！")
        print('Transition did not converge')
    
    # 显示冲击
    print("  ")
    print("--------------------------------------------")
    print("TRANSITION SHOCKS")
    print("--------------------------------------------")
    print(f"eta_i:       {par['eta_i']:8.6f}")
    print(f"v_small:       {par['v_small']:8.6f}")
    print(f"v_corp:        {v_corp:8.6f}")
    print(f"util_shift:    {util_shift:8.6f}")
    print(f"lsupply_shift: {lsupply_shift:8.6f}")
    print(f"rho_shock      {rho_shock:8.6f}")
    print("  ")
    
    # 计算转移动态矩
    model_mom_trans, irf = fun_targets_tran(data_mom_trans, agg_tran, path, agg, prices, calibWeightsTran)
    
    if data_mom_trans.size != model_mom_trans.size:
        raise ValueError('data_mom_trans和model_mom_trans不匹配')
    
    if data_mom_trans.size != calibWeightsTran.size:
        raise ValueError('data_mom_trans和calibWeightsTran不匹配')
    
    n_data = data_mom_trans.shape[0]
    dev = np.zeros(n_data)
    for i in range(n_data):
        dev[i] = np.sum(calibWeightsTran[i, :] * ((model_mom_trans[i, :] - data_mom_trans[i, :]) /
                                                  (np.abs(data_mom_trans[i, :]) + 1e-20)) ** 2)
    distance = np.sum(dev)
    
    if np.isnan(distance):
        distance = np.finfo(float).max
    
    print('\n')
    print(f"Sqr. dist GDP:           {dev[0]:.6f}")
    print(f"Sqr. dist C:             {dev[1]:.6f}")
    print(f"Sqr. dist Inv:           {dev[2]:.6f}")
    print(f"Sqr. dist Y small firms: {dev[3]:.6f}")
    print(f"Sqr. dist Emp:           {dev[4]:.6f}")
    print(f"Sqr. dist Emp small:     {dev[5]:.6f}")
    print(f"Sqr. dist Emp corp:      {dev[6]:.6f}")
    print(f"Sqr. dist Exit rate:     {dev[7]:.6f}")
    print(f"Sqr. dist Exit rate (annual):     {dev[8]:.6f}")
    print(f"Sqr. dist Entry rate:     {dev[9]:.6f}")
    
    print(f"Total distance:          {distance:.6f}")
    print('=============================================================')
    
    if distance < obj_tran_best:
        obj_tran_best = distance
        # 将结果追加到txt文件
        append_tran_txt(distance, x_in, data_mom_trans, model_mom_trans, calibWeightsTran, par.get('InpDir', 'inputs'))
    
    return distance

