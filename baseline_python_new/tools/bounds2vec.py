"""
将包含K个参数边界的结构体转换为(K,2)数组
"""
import numpy as np


def bounds2vec(bounds, names=None):
    """
    将包含K个参数边界的结构体转换为(K,2)数组
    
    参数:
    bounds: 字典，每个字段必须是1*ncol数组，通常ncol=2
    names: 字符串列表（可选），要提取的参数名
    
    返回:
    bounds_vec: (K,ncol)数组，通常(K,2)
    """
    if not isinstance(bounds, dict):
        raise TypeError('第一个参数必须是字典')
    
    if names is None:
        names = list(bounds.keys())
    
    if len(names) == 0:
        return np.array([])
    
    # 获取第一个字段的列数
    first_value = bounds[names[0]]
    ncol = len(first_value) if isinstance(first_value, (list, tuple, np.ndarray)) else 1
    
    bounds_vec = np.full((len(names), ncol), np.nan)
    
    for ii, name in enumerate(names):
        if name in bounds:
            value = bounds[name]
            if isinstance(value, (list, tuple)):
                bounds_vec[ii, :] = value
            elif isinstance(value, np.ndarray):
                bounds_vec[ii, :] = value.flatten()
            else:
                bounds_vec[ii, 0] = value
    
    return bounds_vec

