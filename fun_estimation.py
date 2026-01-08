"""
计算模型矩和数据矩之间的距离
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from struct2vec import struct2vec


def fun_estimation(model_mom, data_mom, targetNames, calibWeights):
    """
    计算模型矩和数据矩之间的距离
    
    参数:
    model_mom: 模型矩字典
    data_mom: 数据矩字典
    targetNames: 矩名称列表
    calibWeights: 校准权重字典
    
    返回:
    obj_smm: 目标函数值（距离）
    """
    # 将model_mom字典转换为向量
    model_mom_vec = struct2vec(model_mom, targetNames).flatten()
    data_mom_vec = struct2vec(data_mom, targetNames).flatten()
    calibWeights_vec = struct2vec(calibWeights, targetNames).flatten()
    
    if len(model_mom_vec) != len(data_mom_vec):
        raise ValueError("模型和数据目标不兼容！")
    if len(calibWeights_vec) != len(data_mom_vec):
        raise ValueError("模型和数据目标不兼容！")
    
    obj_smm = 0
    for i in range(len(model_mom_vec)):
        if data_mom_vec[i] != 0:
            dist2 = ((model_mom_vec[i] - data_mom_vec[i]) / data_mom_vec[i]) ** 2
            obj_smm += dist2 * calibWeights_vec[i]
    
    # 惩罚项：如果empshare_small>1
    if 'empshare_small' in model_mom:
        check = model_mom['empshare_small'] > 1
        penalty = 1000 * max(model_mom['empshare_small'] - 1, 0) ** 2
        if check:
            obj_smm += penalty
    
    return obj_smm

