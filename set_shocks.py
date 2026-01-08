"""
设置冲击参数、转移动态目标和校准权重
"""
import numpy as np
import os


def set_shocks(par, file_shocks):
    """
    设置冲击参数、转移动态目标和校准权重
    
    参数:
    par: 参数字典
    file_shocks: 冲击文件名
    
    返回:
    par: 更新的参数字典
    bounds_shocks: 冲击边界
    data_mom_trans: 转移动态数据矩
    calibWeightsTran: 转移动态校准权重
    """
    if not isinstance(par, dict):
        raise TypeError('输入参数"par"必须是字典')
    if not isinstance(file_shocks, str):
        raise TypeError('输入参数"file_shocks"必须是字符串')
    
    # 读取疫情冲击参数
    print(f'从文件"{file_shocks}"读取转移动态冲击')
    filepath = os.path.join(par.get('InpDir', 'inputs'), file_shocks)
    
    values = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[1])
                        values.append(value)
                    except ValueError:
                        pass
    
    # 如果文件不存在或读取失败，使用默认值
    if len(values) < 5:
        values = [0.5, -0.1, -0.15, 0.1, 0.2]  # 默认值
    
    par['eta_i'] = values[0]  # 受冲击小企业的比例
    par['v_corp'] = values[1]  # 企业部门TFP冲击
    par['util_shift'] = values[2]  # 需求冲击
    par['lsupply_shift'] = values[3]  # 劳动供给冲击
    par['rho_shock'] = values[4]  # 冲击的自相关
    
    par['v_small'] = -1.0  # 受冲击小企业的TFP冲击（关闭冲击 = -100%影响）
    par['v_small_unimp'] = -0.0  # 未受冲击小企业的TFP冲击
    
    # 信贷冲击。注意：lam=lam0*theta*(1-delta)
    par['lambda_shift'] = -0.158  # lambda0的冲击
    
    # 进入冲击
    par['mass_shift'] = 0.24
    
    # 校准冲击的边界
    bounds_shocks = np.zeros((5, 2))
    bounds_shocks[0, :] = [0, 1]  # 受冲击小企业的比例
    bounds_shocks[1, :] = [-0.2, 0]  # v_corp: 企业部门TFP
    bounds_shocks[2, :] = [-0.25, 0]  # util_shift: 需求冲击
    bounds_shocks[3, :] = [0, 0.25]  # lsupply_shift: 劳动供给冲击
    bounds_shocks[4, :] = [0.0, 0.5]  # rho_shock
    
    # A是小企业部门或企业部门的TFP
    # A_small的第二维表示受冲击程度：
    # i => (1=受冲击,2=未受冲击)
    # margutil是消费的边际效用乘数。它在第一期下降到1以下，然后逐渐回到1。
    # lsupply是闲暇的边际效用乘数。它在第一期增加到1以上，然后回到1。
    T = par['T']
    ni = par['ni']
    
    par['A_small'] = np.ones((T + 1, ni))  # 第二维: 1=受冲击, 2=未受冲击
    par['A_corp'] = np.ones(T + 1)
    par['margutil'] = np.ones(T + 1)
    par['lsupply'] = np.ones(T + 1)
    par['lambda_vec'] = np.ones(T + 1)
    par['mass_vec'] = np.ones(T + 1)
    
    # 初始化第一期
    par['A_small'][0, 0] = 1 + par['v_small']  # 受冲击
    par['A_small'][0, 1] = 1 + par['v_small_unimp']  # 未受冲击
    
    par['A_corp'][0] = 1 + par['v_corp']
    par['margutil'][0] = 1 + par['util_shift']
    par['lsupply'][0] = 1 + par['lsupply_shift']
    par['lambda_vec'][0] = 1 + par['lambda_shift']
    par['mass_vec'][0] = 1 + par['mass_shift']
    
    for t in range(1, T + 1):
        par['A_small'][t, 0] = 1 + (par['rho_shock'] ** (t - 1)) * par['v_small']  # 受冲击
        par['A_small'][t, 1] = 1 + (par['rho_shock'] ** (t - 1)) * par['v_small_unimp']  # 未受冲击
        
        par['A_corp'][t] = 1 + (par['rho_shock'] ** (t - 1)) * par['v_corp']
        par['margutil'][t] = 1 + (par['rho_shock'] ** (t - 1)) * par['util_shift']
        par['lsupply'][t] = 1 + (par['rho_shock'] ** (t - 1)) * par['lsupply_shift']
        par['lambda_vec'][t] = (1 + (par['rho_shock'] ** (t - 1)) * par['lambda_shift'])
        par['mass_vec'][t] = (1 + (par['rho_shock'] ** (t - 1)) * par['mass_shift'])
    
    par['lambda_vec'] = par['lambda_vec'] * par['lambda0'] * par['theta'] * (1 - par['delta_k'])
    par['mass_vec'] = par['mass_vec'] * par['mass']
    
    # 加载转移动态的数据矩
    # 如果一期=一季度
    # 7个变量 x 4个季度：第一季度是2020Q2
    data_mom_trans = np.full((10, 4), np.nan)
    data_mom_trans[0, :] = [-10.857, -2.246, -0.774, 1.256]  # 非农企业部门产出
    data_mom_trans[1, :] = [-9.667, -1.488, -0.665, 2.061]  # 消费
    data_mom_trans[2, :] = [-15.398, -1.723, 3.843, 3.242]  # 投资
    data_mom_trans[3, :] = [-15.650, -4.107, -1.404, 0]  # 小企业产出
    data_mom_trans[4, :] = [-12.85, -7.578, -5.437, -5.052]  # 就业
    # 按企业规模的就业下降基于Cajner等人(2020)提供的数据，基于ADP数据。只有2020Q2可用。
    data_mom_trans[5, :] = [-16.02133603, 0, 0, 0]  # 小企业就业
    data_mom_trans[6, :] = [-13.24832078, 0, 0, 0]  # 大企业就业
    # 小企业退出率变化
    data_mom_trans[7, :] = [37.84, -0.06, -10.40, -13.85]  # 0表示缺失
    # 年度小企业退出率变化
    data_mom_trans[8, :] = [3.4, 0, 0, 0]  # 0表示缺失
    # 小企业进入率变化
    data_mom_trans[9, :] = [-12.5, 6.25, 9.38, 12.5]
    
    # 设置转移动态的校准权重
    calibWeightsTran = np.zeros((10, 4))
    calibWeightsTran[0, 0] = 1.0  # delta GDP q1的权重
    calibWeightsTran[0, 1] = 1.0  # delta GDP q2的权重
    calibWeightsTran[1, 0] = 1.0  # delta消费的权重
    calibWeightsTran[2, :] = 0.0  # 投资的权重
    calibWeightsTran[3, 0] = 0.0  # 小企业产出的权重
    calibWeightsTran[4, 0] = 1.0  # 就业的权重
    calibWeightsTran[5, 0] = 1.0  # 小企业就业的权重
    calibWeightsTran[6, 0] = 0.0  # 大企业就业的权重
    calibWeightsTran[7, 0] = 0.0  # 小企业退出的权重
    calibWeightsTran[8, 0] = 0.001  # 小企业年度退出的权重
    calibWeightsTran[9, 0] = 1.0  # 小企业进入率的权重
    
    return par, bounds_shocks, data_mom_trans, calibWeightsTran

