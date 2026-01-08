"""
目标函数
该函数接受参数值向量"guess"作为输入，求解模型并生成模型矩和数据矩之间的距离
"""
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from tools.vec2struct import vec2struct
from tools.bounds2vec import bounds2vec
from fun_steady_state import fun_steady_state
from fun_estimation import fun_estimation

# 全局变量
obj_smm_best = np.inf


def fun_obj(guess, par, bounds, calibNames, data_mom, targetNames, calibWeights,
           description, dispNames, targetNames_long):
    """
    目标函数
    
    参数:
    guess: 要校准的参数向量
    par: 参数字典
    bounds: 校准参数边界的字典。每个字段是1*2向量
    calibNames: 要校准/估计的参数名称字符串列表
    data_mom: 数据矩字典
    targetNames: 字符串列表
    calibWeights: 数值字典
    description: 字符串列表
    dispNames: 字符串列表（参数的latex名称）
    targetNames_long: 字符串列表
    
    返回:
    obj_smm: 模型目标和数据目标之间的距离
    sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par: 其他模型变量
    """
    global obj_smm_best
    
    # 输入检查
    if not isinstance(par, dict):
        raise TypeError("输入par在<fun_obj>中必须是字典！")
    if not isinstance(bounds, dict):
        raise TypeError("输入bounds在<fun_obj>中必须是字典！")
    
    guess = np.asarray(guess).flatten()
    if guess.ndim > 1:
        raise ValueError("guess必须是列向量！")
    if len(guess) != len(calibNames):
        raise ValueError("guess和calibNames必须有相同数量的元素！")
    if len(bounds) != len(guess):
        raise ValueError("guess和bounds不匹配！")
    
    # 将要估计的参数添加到字典PAR
    par = vec2struct(guess, calibNames, par)
    
    # 将边界从字典转换为向量
    bounds_vec = bounds2vec(bounds, calibNames)
    
    lbounds_vec = bounds_vec[:, 0]  # 下界
    ubounds_vec = bounds_vec[:, 1]  # 上界
    
    # 检查参数是否在下界内
    if np.any(guess < lbounds_vec):
        print('警告：参数违反下界！')
        obj_smm = 10000
        return obj_smm, None, None, None, None, None, None, None, None
    
    # 检查参数是否在上界内
    if np.any(guess > ubounds_vec):
        print('警告：参数违反上界！')
        obj_smm = 10000
        return obj_smm, None, None, None, None, None, None, None, None
    
    # 求解稳态
    if par.get('verbose', 0) >= 2:
        print('Start model solution...')
        print(' ')
        print(' ')
    
    # fun_steady_state求解模型的稳态并产生解对象和model_mom
    sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par = fun_steady_state(par)
    
    if flag_ss < 0:
        # VF或分布未收敛
        print('警告：fun_steady_state中发生了一些错误')
        obj_smm = 10000
        return obj_smm, None, None, None, None, None, None, None, None
    
    # 检查市场出清条件并添加惩罚项
    market_clearing_penalty = 0
    if agg is not None:
        K_corp = agg.get('K_corp', 0)
        LHS = agg.get('LHS', 0)
        aux = agg.get('aux', 0)
        
        if K_corp < 0:
            print(f"警告：企业部门资本为负！K_corp = {K_corp:.6f}")
            # 添加大惩罚项
            market_clearing_penalty += 10000 * abs(K_corp)
        
        if LHS < 0:
            print(f"警告：市场出清方程左端为负！LHS = {LHS:.6f}")
            # 添加大惩罚项
            market_clearing_penalty += 10000 * abs(LHS)
        
        if aux <= 0:
            print(f"警告：企业部门净收益率 <= 0！aux = {aux:.6f}")
            # 添加大惩罚项
            market_clearing_penalty += 10000
    
    # 估计参数的表
    if par.get('do_table', 0) == 1:
        try:
            from mystruct2table import mystruct2table
            mystruct2table(par, calibNames, description, dispNames, 
                         ['Parameter', 'Value'], par.get('do_tex', 0), 
                         par.get('TabDir', 'tables'), 'parameters.tex')
        except ImportError:
            pass  # 表格生成函数未实现
    
    # 目标矩的表：模型 vs 数据
    if par.get('do_table', 0) == 1:
        try:
            from mystruct2table_mom import mystruct2table_mom
            mystruct2table_mom(data_mom, model_mom, targetNames, calibWeights,
                             targetNames_long, par.get('do_tex', 0),
                             par.get('TabDir', 'tables'), 'moments.tex')
        except ImportError:
            pass  # 表格生成函数未实现
    
    # 分配距离用于输出
    obj_smm = fun_estimation(model_mom, data_mom, targetNames, calibWeights)
    
    # 添加市场出清惩罚项
    obj_smm += market_clearing_penalty
    
    if np.isnan(obj_smm):
        obj_smm = 10000
    
    print('\n')
    print(f"obj_smm:      {obj_smm:.6f}")
    print('=============================================================')
    
    if obj_smm < obj_smm_best:
        obj_smm_best = obj_smm
        # 将结果追加到txt文件
        try:
            from append_results_txt import append_results_txt
            append_results_txt(obj_smm, par, calibNames, data_mom, model_mom,
                             calibWeights, targetNames, par.get('InpDir', 'inputs'))
        except ImportError:
            pass  # 追加结果函数未实现
    
    return obj_smm, sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par

