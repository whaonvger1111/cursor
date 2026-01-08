"""
缓存约束企业VFI之前的结果（包括无约束企业VFI结果）
"""
import os
import pickle
import hashlib
import numpy as np


def generate_pre_constrained_cache_key(prices, par):
    """
    生成约束企业VFI之前的缓存键
    
    参数:
    prices: 价格字典
    par: 参数字典
    
    返回:
    cache_key: 缓存键字符串
    """
    # 提取关键参数
    key_params = {
        'q': prices.get('q'),
        'wage': prices.get('wage'),
        'theta': par.get('theta'),
        'delta_k': par.get('delta_k'),
        'psi': par.get('psi'),
        'lambda': par.get('lambda'),
        'nx': par.get('nx'),
        'nb': par.get('nb'),
        'nk': par.get('nk'),
        'tol_vfi_u': par.get('tol_vfi_u'),
        'tol_bhat': par.get('tol_bhat'),
    }
    
    # 将参数转换为字符串并生成哈希
    key_str = str(sorted(key_params.items()))
    cache_key = hashlib.md5(key_str.encode()).hexdigest()
    return cache_key


def save_pre_constrained_vfi_cache(cache_dir, cache_key, results):
    """
    保存约束企业VFI之前的结果到缓存
    
    参数:
    cache_dir: 缓存目录
    cache_key: 缓存键
    results: 结果字典，包含：
        - V1: 无约束企业价值函数
        - x_tilde: 生产率截断值索引
        - x_tilde_val: 生产率截断值
        - pol_kp_unc: 无约束企业投资政策
        - B_hat: 债务上界
        - pol_bp_unc: 无约束企业债务政策
        - b_grid: 债务网格
        - kp_bar: 资本上界
        - val_unc: 无约束企业退出后价值
        - val0_unc: 无约束企业退出前价值
        - profit_mat: 利润矩阵
        - b_tilde: 债务下界
        - kp_ub_ind_mat: 预计算的kp上界索引
        - threshold_mat: 预计算的清算阈值
    
    返回:
    cache_file: 缓存文件路径
    """
    # 创建缓存目录
    os.makedirs(cache_dir, exist_ok=True)
    
    # 缓存文件名
    cache_file = os.path.join(cache_dir, f'pre_constrained_vfi_{cache_key}.pkl')
    
    # 保存到文件
    with open(cache_file, 'wb') as f:
        pickle.dump(results, f)
    
    return cache_file


def load_pre_constrained_vfi_cache(cache_dir, cache_key):
    """
    从缓存加载约束企业VFI之前的结果
    
    参数:
    cache_dir: 缓存目录
    cache_key: 缓存键
    
    返回:
    results: 结果字典，如果缓存不存在则返回None
    """
    cache_file = os.path.join(cache_dir, f'pre_constrained_vfi_{cache_key}.pkl')
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'rb') as f:
            results = pickle.load(f)
        return results
    except Exception as e:
        print(f'警告：加载缓存失败: {e}')
        return None







