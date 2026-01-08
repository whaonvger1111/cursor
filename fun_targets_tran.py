"""
给定转移动态路径，计算一些矩（如消费下降等）
"""
import numpy as np


def fun_targets_tran(data_mom_trans, agg_tran, path, agg_ss, prices, calibWeightsTran):
    """
    计算转移动态矩
    
    参数:
    data_mom_trans: 转移动态数据矩数组, (9,4)
    agg_tran: 转移动态加总字典
    path: 转移动态加总字典（外部循环）
    agg_ss: 稳态加总字典
    prices: 稳态价格字典
    calibWeightsTran: 与data_mom_trans相同维度的数组
    
    返回:
    model_mom_trans: 转移动态模型矩数组，与data_mom_trans相同维度
    irf: 转移动态IRF字典（相对于稳态的百分比变化）
    """
    irf = {}
    
    # 脉冲响应函数，以百分比表示
    # 长度为T+1
    # ---------------- 外部循环 ----------------------------%
    irf['C_agg'] = (path['C'] - agg_ss['C_agg']) / agg_ss['C_agg']  # 消费
    KL_ratio_ss = agg_ss['K_corp'] / agg_ss['L_corp'] if agg_ss['L_corp'] > 0 else 0
    irf['KL_ratio'] = (path['KL_ratio'] - KL_ratio_ss) / KL_ratio_ss if KL_ratio_ss > 0 else 0  # 小企业产出
    irf['q'] = (path['q'] - prices['q']) / prices['q'] if prices['q'] != 0 else 0  # 企业贴现因子
    irf['w'] = (path['w'] - prices['wage']) / prices['wage'] if prices['wage'] != 0 else 0  # 工资
    
    # ------------------- 异质主体 --------------------------%
    irf['K_agg'] = (agg_tran['K_agg'] - agg_ss['K_agg']) / agg_ss['K_agg'] if agg_ss['K_agg'] > 0 else 0  # 家庭资本
    irf['K_small'] = (agg_tran['K_small'] - agg_ss['K_small']) / agg_ss['K_small'] if agg_ss['K_small'] > 0 else 0  # 小企业资本
    irf['K_corp'] = (agg_tran['K_corp'] - agg_ss['K_corp']) / agg_ss['K_corp'] if agg_ss['K_corp'] > 0 else 0  # 企业部门资本
    irf['mass_small'] = (agg_tran['mass_small'] - agg_ss['mass_small']) / agg_ss['mass_small'] if agg_ss['mass_small'] > 0 else 0  # 小企业质量
    irf['Y_agg'] = (agg_tran['Y_agg'] - agg_ss['Y_agg']) / agg_ss['Y_agg'] if agg_ss['Y_agg'] > 0 else 0  # 总产出
    irf['Y_corp'] = (agg_tran['Y_corp'] - agg_ss['Y_corp']) / agg_ss['Y_corp'] if agg_ss['Y_corp'] > 0 else 0  # 企业部门产出
    irf['output_small'] = (agg_tran['output_small'] - agg_ss['output_small']) / agg_ss['output_small'] if agg_ss['output_small'] > 0 else 0  # 小企业产出
    irf['L_agg'] = (agg_tran['L_agg'] - agg_ss['L_agg']) / agg_ss['L_agg'] if agg_ss['L_agg'] > 0 else 0  # 总就业
    irf['L_small'] = (agg_tran['L_small'] - agg_ss['L_small']) / agg_ss['L_small'] if agg_ss['L_small'] > 0 else 0  # 小企业就业
    irf['L_corp'] = (agg_tran['L_corp'] - agg_ss['L_corp']) / agg_ss['L_corp'] if agg_ss['L_corp'] > 0 else 0  # 企业部门就业
    irf['entry'] = (agg_tran['entry_vec'] - agg_ss['entry']) / agg_ss['entry'] if agg_ss['entry'] > 0 else 0  # 进入者测度
    irf['entry_rate'] = (agg_tran['entry_rate_vec'] - agg_ss['entry_rate']) / agg_ss['entry_rate'] if agg_ss['entry_rate'] > 0 else 0  # 进入率
    irf['entry_cost'] = (agg_tran['entry_cost_vec'] - agg_ss['entry_cost']) / agg_ss['entry_cost'] if agg_ss['entry_cost'] > 0 else 0  # 进入总成本
    irf['exit_rate'] = (agg_tran['exit_rate_vec'] - agg_ss['exit_rate']) / agg_ss['exit_rate'] if agg_ss['exit_rate'] > 0 else 0  # 退出率
    irf['exit'] = (agg_tran['exit_vec'] - agg_ss['exit']) / agg_ss['exit'] if agg_ss['exit'] > 0 else 0  # 退出企业测度
    irf['liq'] = (agg_tran['liq_vec'] - agg_ss['liq']) / agg_ss['liq'] if agg_ss['liq'] > 0 else 0  # 清算成本
    irf['InvK'] = (agg_tran['InvK'] - agg_ss['InvK']) / agg_ss['InvK'] if agg_ss['InvK'] > 0 else 0  # 家庭投资
    irf['InvK_corp'] = (agg_tran['InvK_corp'] - agg_ss['InvK_corp']) / agg_ss['InvK_corp'] if agg_ss['InvK_corp'] > 0 else 0  # 企业部门投资
    irf['exit_rate_emp'] = (agg_tran['exit_rate_emp_vec'] - agg_ss['exit_rate_emp']) / agg_ss['exit_rate_emp'] if agg_ss['exit_rate_emp'] > 0 else 0  # 退出率
    
    n_data = data_mom_trans.shape[0]
    model_mom_trans = np.ones((n_data, 4))
    
    # 确保索引不越界
    T_len = len(irf['Y_agg'])
    indices = [min(i, T_len - 1) for i in range(4)]
    
    model_mom_trans[0, :4] = 100 * irf['Y_agg'][indices]  # GDP变化
    model_mom_trans[1, :4] = 100 * irf['C_agg'][indices]  # 消费变化
    model_mom_trans[2, :4] = 100 * irf['InvK'][indices]  # 投资变化
    model_mom_trans[3, :4] = 100 * irf['output_small'][indices]  # 小企业收入变化
    model_mom_trans[4, :4] = 100 * irf['L_agg'][indices]  # 就业变化
    model_mom_trans[5, :4] = 100 * irf['L_small'][indices]  # 小企业就业变化
    model_mom_trans[6, :4] = 100 * irf['L_corp'][indices]  # 企业部门就业变化
    model_mom_trans[7, :4] = 100 * irf['exit_rate'][indices]  # 小企业退出率变化
    # 从2019年到2020年的年度退出率变化
    exitrate_2019 = 1 - (1 - agg_ss['exit_rate']) ** 4
    if T_len >= 3:
        exitrate_2020 = 1 - (1 - agg_ss['exit_rate']) * (1 - agg_tran['exit_rate_vec'][0]) * \
                        (1 - agg_tran['exit_rate_vec'][1]) * (1 - agg_tran['exit_rate_vec'][2])
    else:
        exitrate_2020 = exitrate_2019
    model_mom_trans[8, 0] = 100 * (exitrate_2020 - exitrate_2019) / exitrate_2019 if exitrate_2019 > 0 else 0  # 年度企业退出率变化
    model_mom_trans[9, :4] = 100 * irf['entry_rate'][indices]  # 小企业进入率变化
    
    width = len('Firm exit rate, annual change:') + 3
    print("  ")
    print("--------------------------------------------")
    print("TRANSITION RESULTS")
    print("--------------------------------------------")
    
    # calibWeightsTran维度为(7,4)
    print(f"{'Description':<{width}}  {'Data':<8}     {'Model':<8}     {'Weight':<8}")
    print(f"{'Drop in GDP q1:':<{width}}  {data_mom_trans[0,0]:<8.4f}  {model_mom_trans[0,0]:<8.4f}  {calibWeightsTran[0,0]:<8.4f}")
    print(f"{'Drop in GDP q2:':<{width}}  {data_mom_trans[0,1]:<8.4f}  {model_mom_trans[0,1]:<8.4f}  {calibWeightsTran[0,1]:<8.4f}")
    print(f"{'Drop in consumption:':<{width}}  {data_mom_trans[1,0]:<8.4f}  {model_mom_trans[1,0]:<8.4f}  {calibWeightsTran[1,0]:<8.4f}")
    print(f"{'Drop in investment:':<{width}}  {data_mom_trans[2,0]:<8.4f}  {model_mom_trans[2,0]:<8.4f}  {calibWeightsTran[2,0]:<8.4f}")
    print(f"{'Drop in small firms output:':<{width}}  {data_mom_trans[3,0]:<8.4f}  {model_mom_trans[3,0]:<8.4f}  {calibWeightsTran[3,0]:<8.4f}")
    print(f"{'Drop in Employment q1:':<{width}}  {data_mom_trans[4,0]:<8.4f}  {model_mom_trans[4,0]:<8.4f}  {calibWeightsTran[4,0]:<8.4f}")
    print(f"{'Drop in Employment q2:':<{width}}  {data_mom_trans[4,1]:<8.4f}  {model_mom_trans[4,1]:<8.4f}  {calibWeightsTran[4,1]:<8.4f}")
    print(f"{'Drop in Employment small q1:':<{width}}  {data_mom_trans[5,0]:<8.4f}  {model_mom_trans[5,0]:<8.4f}  {calibWeightsTran[5,0]:<8.4f}")
    print(f"{'Drop in Employment small q2:':<{width}}  {data_mom_trans[5,1]:<8.4f}  {model_mom_trans[5,1]:<8.4f}  {calibWeightsTran[5,1]:<8.4f}")
    print(f"{'Drop in Employment corp q1:':<{width}}  {data_mom_trans[6,0]:<8.4f}  {model_mom_trans[6,0]:<8.4f}  {calibWeightsTran[6,0]:<8.4f}")
    print(f"{'Drop in Employment corp q2:':<{width}}  {data_mom_trans[6,1]:<8.4f}  {model_mom_trans[6,1]:<8.4f}  {calibWeightsTran[6,1]:<8.4f}")
    print(f"{'Drop in small firm exit, q1:':<{width}}  {data_mom_trans[7,0]:<8.4f}  {model_mom_trans[7,0]:<8.4f}  {calibWeightsTran[7,0]:<8.4f}")
    print(f"{'Firm exit rate, annual change:':<{width}}  {data_mom_trans[8,0]:<8.4f}  {model_mom_trans[8,0]:<8.4f}  {calibWeightsTran[8,0]:<8.4f}")
    print(f"{'Drop in small firm entry, q1:':<{width}}  {data_mom_trans[9,0]:<8.4f}  {model_mom_trans[9,0]:<8.4f}  {calibWeightsTran[9,0]:<8.4f}")
    
    print(f"{'Total grant amount:':<{width}}  {agg_tran.get('tot_grant', 0):<8.6f}")
    print("  ")
    
    return model_mom_trans, irf

