"""
从结构体中提取向量
"""
import numpy as np


def struct2vec(pstruct, pnames):
    """
    从结构体中提取向量，结构体的字段为标量值
    
    参数:
    pstruct: 字典，字段为标量值
    pnames: 字符串列表，指定要提取的字段名
    
    返回:
    pvec: k维向量
    """
    if not isinstance(pstruct, dict):
        raise TypeError('第一个输入必须是字典')
    
    if not isinstance(pnames, (list, tuple)):
        raise TypeError('第二个输入必须是字符串列表')
    
    k = len(pnames)
    pvec = []
    
    for i in range(k):
        field_name = pnames[i]
        if field_name not in pstruct:
            raise KeyError(f'字段 "{field_name}" 不存在于结构体中')
        
        value = pstruct[field_name]
        value_array = np.asarray(value)
        
        # 展平数组并添加到向量中
        pvec.extend(value_array.flatten().tolist())
    
    return np.array(pvec).reshape(-1, 1)

