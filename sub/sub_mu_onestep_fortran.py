"""
分布更新的Fortran包装器
"""
import numpy as np
import sys
import os

# 导入Fortran模块（必需）
fortran_dir = os.path.join(os.path.dirname(__file__), '..', 'fortran')
if fortran_dir not in sys.path:
    sys.path.insert(0, fortran_dir)

try:
    import vfi_core
except ImportError as e:
    raise ImportError(
        f"错误: Fortran模块vfi_core未找到！\n"
        f"请先编译Fortran模块: python fortran/setup_fortran.py\n"
        f"原始错误: {e}"
    )


def sub_mu_onestep_fortran(mu, phi_dist, pol_kp_ind, pol_exit, pol_entry,
                           left_loc_arr, omega_arr, pi_x, mass, psi):
    """
    对分布mu^0进行一步算子操作（Fortran版本）
    
    参数:
    mu: 初始分布mu^0(k,b,x)
    phi_dist: 进入者分布Phi(k,b,x)
    pol_kp_ind: 政策k'(k,b,x)，索引
    pol_exit: 退出政策d^l(k,b,x)
    pol_entry: 进入政策d^e(k,b,x)
    left_loc_arr: b'(k,b,x)插值的索引
    omega_arr: b'(k,b,x)插值的权重
    pi_x: 生产率转移矩阵
    mass: 潜在进入者质量
    psi: 外生退出率
    
    返回:
    mu1: 更新的分布mu^0(k,b,x)
    """
    nk, nb, nx = mu.shape
    
    # 确保数组是连续的（Fortran需要列优先顺序）
    if not mu.flags.f_contiguous:
        mu = np.asfortranarray(mu, dtype=np.float64)
    else:
        mu = np.ascontiguousarray(mu, dtype=np.float64)
    
    if not phi_dist.flags.f_contiguous:
        phi_dist = np.asfortranarray(phi_dist, dtype=np.float64)
    else:
        phi_dist = np.ascontiguousarray(phi_dist, dtype=np.float64)
    
    if not pol_kp_ind.flags.f_contiguous:
        pol_kp_ind = np.asfortranarray(pol_kp_ind, dtype=np.int32)
    else:
        pol_kp_ind = np.ascontiguousarray(pol_kp_ind, dtype=np.int32)
    
    if not pol_exit.flags.f_contiguous:
        pol_exit = np.asfortranarray(pol_exit, dtype=np.float64)
    else:
        pol_exit = np.ascontiguousarray(pol_exit, dtype=np.float64)
    
    if not pol_entry.flags.f_contiguous:
        pol_entry = np.asfortranarray(pol_entry, dtype=np.float64)
    else:
        pol_entry = np.ascontiguousarray(pol_entry, dtype=np.float64)
    
    if not left_loc_arr.flags.f_contiguous:
        left_loc_arr = np.asfortranarray(left_loc_arr, dtype=np.int32)
    else:
        left_loc_arr = np.ascontiguousarray(left_loc_arr, dtype=np.int32)
    
    if not omega_arr.flags.f_contiguous:
        omega_arr = np.asfortranarray(omega_arr, dtype=np.float64)
    else:
        omega_arr = np.ascontiguousarray(omega_arr, dtype=np.float64)
    
    if not pi_x.flags.f_contiguous:
        pi_x = np.asfortranarray(pi_x, dtype=np.float64)
    else:
        pi_x = np.ascontiguousarray(pi_x, dtype=np.float64)
    
    # 调用Fortran函数（f2py会自动从数组维度推断nk, nb和nx）
    mu1 = vfi_core.vfi_core.sub_mu_onestep_fortran(
        mu, phi_dist, pol_kp_ind, pol_exit, pol_entry,
        left_loc_arr, omega_arr, pi_x, mass, psi)
    
    return mu1

