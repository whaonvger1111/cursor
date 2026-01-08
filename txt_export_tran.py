"""
导出转移动态结果到文本文件
手动校准转移动态冲击
"""
import os
import numpy as np


def txt_export_tran(par, model_mom_trans, agg_tran, TabDir):
    """
    导出转移动态参数值和目标到txt文件
    
    参数:
    par: 参数字典
    model_mom_trans: 转移动态模型矩数组
    agg_tran: 转移动态加总字典
    TabDir: 表格目录
    """
    # 创建目录
    if not os.path.exists(TabDir):
        os.makedirs(TabDir)
    
    # 写入txt文件
    filepath = os.path.join(TabDir, 'targets_transition_manual.txt')
    with open(filepath, 'w', encoding='utf-8') as fid:
        fid.write('PARAMETER \n')
        fid.write(f'eta_i         :    {par.get("eta_i", 0):f} \n')
        fid.write(f'v_small       :    {par.get("v_small", 0):f} \n')
        fid.write(f'v_small_unimp :    {par.get("v_small_unimp", 0):f} \n')
        fid.write(f'v_corp        :    {par.get("v_corp", 0):f} \n')
        fid.write(f'util_shift    :    {par.get("util_shift", 0):f} \n')
        fid.write(f'lsupply_shift :    {par.get("lsupply_shift", 0):f} \n')
        fid.write(f'lambda_shift  :    {par.get("lambda_shift", 0):f} \n')
        fid.write(f'mass_shift  :    {par.get("mass_shift", 0):f} \n')
        fid.write(f'rho_shock     :    {par.get("rho_shock", 0):f} \n')
        
        fid.write(' \n')
        
        fid.write('MOMENT \n')
        fid.write(f'Change in GDP q1                   :    {model_mom_trans[0,0]:f} \n')
        fid.write(f'Change in GDP q2                   :    {model_mom_trans[0,1]:f} \n')
        fid.write(f'Change in consumption              :    {model_mom_trans[1,0]:f} \n')
        fid.write(f'Change in investment               :    {model_mom_trans[2,0]:f} \n')
        fid.write(f'Change in small firms output       :    {model_mom_trans[3,0]:f} \n')
        fid.write(f'Change in employment q1            :    {model_mom_trans[4,0]:f} \n')
        fid.write(f'Change in employment q2            :    {model_mom_trans[4,1]:f} \n')
        fid.write(f'Change in employment small q1      :    {model_mom_trans[5,0]:f} \n')
        fid.write(f'Change in employment small q2      :    {model_mom_trans[5,1]:f} \n')
        fid.write(f'Change in employment corp q1       :    {model_mom_trans[6,0]:f} \n')
        fid.write(f'Change in employment corp q2       :    {model_mom_trans[6,1]:f} \n')
        fid.write(f'Change in small firm exit q1       :    {model_mom_trans[7,0]:f} \n')
        fid.write(f'Change in small firm exit, annual  :    {model_mom_trans[8,0]:f} \n')
        fid.write(f'Change in small firm entry, q1  :    {model_mom_trans[9,0]:f} \n')
        fid.write(f'Total grant amount                 :    {agg_tran.get("tot_grant", 0):f} \n')
    
    print(f"Transition targets exported to {filepath}")

