"""
将转移动态的中间结果写入txt文件
"""
import os
import numpy as np


def append_tran_txt(distance, x_in, data_mom_trans, model_mom_trans, calibWeightsTran, InpDir):
    """
    将转移动态结果追加到txt文件
    
    参数:
    distance: 距离
    x_in: 参数向量
    data_mom_trans: 转移动态数据矩
    model_mom_trans: 转移动态模型矩
    calibWeightsTran: 校准权重
    InpDir: 输入目录
    """
    # 打开文件
    filepath = os.path.join(InpDir, 'results_tran_sofar.txt')
    with open(filepath, 'a+', encoding='utf-8') as FID:
        # 追加参数到txt文件
        FID.write("==================================== \n")
        FID.write(f"eta_i:       {x_in[0]:8.6f}  \n")
        FID.write(f"v_corp:        {x_in[1]:8.6f}  \n")
        FID.write(f"util_shift:    {x_in[2]:8.6f}  \n")
        FID.write(f"lsupply_shift: {x_in[3]:8.6f}  \n")
        FID.write(f"rho_shock:     {x_in[4]:8.6f}  \n")
        FID.write(" \n")
        
        # 追加转移动态拟合到txt文件
        width = len('Drop in small firms exit rate:') + 3
        FID.write("  \n")
        FID.write(f"{'Description':<{width}}  {'Data':<8}     {'Model':<8}     {'Weight':<8}     \n")
        FID.write(f"{'Drop in GDP q1:':<{width}}  {data_mom_trans[0,0]:<8.4f}  {model_mom_trans[0,0]:<8.4f}  {calibWeightsTran[0,0]:<8.4f}  \n")
        FID.write(f"{'Drop in GDP q2:':<{width}}  {data_mom_trans[0,1]:<8.4f}  {model_mom_trans[0,1]:<8.4f}  {calibWeightsTran[0,1]:<8.4f}  \n")
        FID.write(f"{'Drop in consumption:':<{width}}  {data_mom_trans[1,0]:<8.4f}  {model_mom_trans[1,0]:<8.4f}  {calibWeightsTran[1,0]:<8.4f}\n")
        FID.write(f"{'Drop in investment:':<{width}}  {data_mom_trans[2,0]:<8.4f}  {model_mom_trans[2,0]:<8.4f}  {calibWeightsTran[2,0]:<8.4f}  \n")
        FID.write(f"{'Drop in small firms output:':<{width}}  {data_mom_trans[3,0]:<8.4f}  {model_mom_trans[3,0]:<8.4f}  {calibWeightsTran[3,0]:<8.4f}  \n")
        FID.write(f"{'Drop in Employment q1:':<{width}}  {data_mom_trans[4,0]:<8.4f}  {model_mom_trans[4,0]:<8.4f}  {calibWeightsTran[4,0]:<8.4f}  \n")
        FID.write(f"{'Drop in Employment q2:':<{width}}  {data_mom_trans[4,1]:<8.4f}  {model_mom_trans[4,1]:<8.4f}  {calibWeightsTran[4,1]:<8.4f}  \n")
        FID.write(f"{'Drop in Employment small q1:':<{width}}  {data_mom_trans[5,0]:<8.4f}  {model_mom_trans[5,0]:<8.4f}  {calibWeightsTran[5,0]:<8.4f}  \n")
        FID.write(f"{'Drop in Employment small q2:':<{width}}  {data_mom_trans[5,1]:<8.4f}  {model_mom_trans[5,1]:<8.4f}  {calibWeightsTran[5,1]:<8.4f}  \n")
        FID.write(f"{'Drop in Employment corp q1:':<{width}}  {data_mom_trans[6,0]:<8.4f}  {model_mom_trans[6,0]:<8.4f}  {calibWeightsTran[6,0]:<8.4f}  \n")
        FID.write(f"{'Drop in Employment corp q2:':<{width}}  {data_mom_trans[6,1]:<8.4f}  {model_mom_trans[6,1]:<8.4f}  {calibWeightsTran[6,1]:<8.4f}  \n")
        FID.write(f"{'Drop in small firms exit rate:':<{width}}  {data_mom_trans[7,0]:<8.4f}  {model_mom_trans[7,0]:<8.4f}  {calibWeightsTran[7,0]:<8.4f}  \n")
        FID.write(f"{'Change in annual exit rate:':<{width}}  {data_mom_trans[8,0]:<8.4f}  {model_mom_trans[8,0]:<8.4f}  {calibWeightsTran[8,0]:<8.4f}  \n")
        
        FID.write(f"{'Distance:':<{width}} {distance:<8.6f}          \n")
        FID.write("  \n")

