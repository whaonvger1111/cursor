"""
将中间结果（参数值、模型拟合和模型矩与数据矩之间的距离）写入txt文件
在全局优化例程估计参数时特别有用
"""
import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from struct2vec import struct2vec


def append_results_txt(obj_smm, param_struct, calib_names, data_mom_struct,
                      model_mom_struct, calib_weights_struct, mom_names, TxtDir):
    """
    将结果追加到txt文件
    
    参数:
    param_struct: 包含所有参数的结构体
    calib_names: 估计参数名称的字符串列表
    mom_names: 目标矩名称的字符串列表
    data_mom_struct: 数据矩字典
    model_mom_struct: 模型矩字典
    calib_weights_struct: 校准权重字典
    TxtDir: 要追加txt文件的文件夹
    """
    # 将参数字典转换为向量
    param_vec = struct2vec(param_struct, calib_names)
    
    # 将data_moments转换为向量
    data_mom_vec = struct2vec(data_mom_struct, mom_names)
    
    # 将model_moments转换为向量
    model_mom_vec = struct2vec(model_mom_struct, mom_names)
    
    # 将校准权重转换为向量
    calibWeights_vec = struct2vec(calib_weights_struct, mom_names)
    
    dev = np.zeros(len(mom_names))  # 绝对偏差
    for i in range(len(mom_names)):
        if data_mom_vec[i] != 0:
            dev[i] = calibWeights_vec[i] * ((data_mom_vec[i] - model_mom_vec[i]) / data_mom_vec[i]) ** 2
    
    # 打开文件
    filepath = os.path.join(TxtDir, 'results_sofar.txt')
    with open(filepath, 'a+', encoding='utf-8') as FID:
        # 追加参数到txt文件
        width = max(len(name) for name in calib_names) if calib_names else 20
        FID.write('--------------------------------------------------  \n')
        FID.write(' Parameter  Value  \n')
        FID.write('--------------------------------------------------  \n')
        for i in range(len(calib_names)):
            # 确保 param_vec[i] 是标量而不是数组
            param_value = param_vec[i].item() if isinstance(param_vec[i], np.ndarray) else float(param_vec[i])
            FID.write(f'{calib_names[i]:<{width}}   {param_value:<8.16f} \n')
        FID.write(' \n')
        
        # 追加模型拟合结果到txt文件
        width = max(len(name) for name in mom_names) if mom_names else 20
        FID.write('--------------------------------------------------  \n')
        FID.write(f'{"Moment":<{width}} {"Data":<12} {"Model":<12} \n')
        FID.write('--------------------------------------------------  \n')
        for i in range(len(mom_names)):
            # 确保值是标量而不是数组
            data_value = data_mom_vec[i].item() if isinstance(data_mom_vec[i], np.ndarray) else float(data_mom_vec[i])
            model_value = model_mom_vec[i].item() if isinstance(model_mom_vec[i], np.ndarray) else float(model_mom_vec[i])
            FID.write(f'{mom_names[i]:<{width}}    {data_value:<8.4f}  {model_value:<8.4f}  \n')
        FID.write('--------------------------------------------------  \n')
        FID.write(f'obj_smm = {obj_smm:<8.4f} \n')
        FID.write('=======================================================  \n')

