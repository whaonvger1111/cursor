"""
无约束企业VFI结果缓存模块
用于存储和加载无约束企业VFI的计算结果，避免重复计算
"""
import numpy as np
import pickle
import os
import hashlib
import json


def generate_cache_key(prices, par):
    """
    生成缓存键，基于价格和关键参数
    
    参数:
    prices: 价格字典
    par: 参数字典
    
    返回:
    cache_key: 字符串，用于标识缓存
    """
    # 提取关键参数用于生成缓存键
    key_params = {
        'q': prices.get('q', 0),
        'wage': prices.get('wage', 0),
        'nx': par.get('nx', 0),
        'nb': par.get('nb', 0),
        'nk': par.get('nk', 0),
        'theta': par.get('theta', 0),
        'delta': par.get('delta_k', 0),
        'psi': par.get('psi', 0),
        'lambda': par.get('lambda', 0),
    }
    
    # 将参数字典转换为JSON字符串，然后生成哈希
    key_str = json.dumps(key_params, sort_keys=True)
    cache_key = hashlib.md5(key_str.encode()).hexdigest()
    
    return cache_key


def save_unconstrained_vfi_cache(cache_dir, cache_key, results):
    """
    保存无约束企业VFI结果到缓存文件
    
    参数:
    cache_dir: 缓存目录
    cache_key: 缓存键
    results: 结果字典，包含：
        - V1: 无约束企业的价值函数
        - x_tilde: 生产率截断值索引
        - x_tilde_val: 生产率截断值
        - pol_kp_unc: 无约束投资政策
        - B_hat: B_hat固定点
        - pol_bp_unc: 无约束债务政策
        - b_grid: 债务网格
        - kp_bar: 下一期资本上界
        - val_unc: 无约束企业退出后的价值
        - val0_unc: 无约束企业退出前的价值
        - profit_mat: 利润矩阵
        - b_tilde: b_tilde值
    """
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_file = os.path.join(cache_dir, f'unconstrained_vfi_{cache_key}.pkl')
    
    with open(cache_file, 'wb') as f:
        pickle.dump(results, f)
    
    return cache_file


def load_unconstrained_vfi_cache(cache_dir, cache_key):
    """
    从缓存文件加载无约束企业VFI结果
    
    参数:
    cache_dir: 缓存目录
    cache_key: 缓存键
    
    返回:
    results: 结果字典，如果缓存不存在则返回None
    """
    cache_file = os.path.join(cache_dir, f'unconstrained_vfi_{cache_key}.pkl')
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'rb') as f:
            results = pickle.load(f)
        return results
    except Exception as e:
        print(f'警告：加载缓存失败: {e}')
        return None


def clear_unconstrained_vfi_cache(cache_dir=None):
    """
    清除无约束企业VFI缓存
    
    参数:
    cache_dir: 缓存目录，如果为None则使用默认目录
    """
    if cache_dir is None:
        cache_dir = 'cache'
    
    if os.path.exists(cache_dir):
        cache_files = [f for f in os.listdir(cache_dir) if f.startswith('unconstrained_vfi_')]
        for f in cache_files:
            try:
                os.remove(os.path.join(cache_dir, f))
                print(f'已删除缓存文件: {f}')
            except Exception as e:
                print(f'删除缓存文件失败 {f}: {e}')








