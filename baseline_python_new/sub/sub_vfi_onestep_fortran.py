"""
约束企业VFI的Fortran加速版本
"""
import numpy as np
import sys
import os

# 添加fortran目录到路径
fortran_dir = os.path.join(os.path.dirname(__file__), '..', 'fortran')
if fortran_dir not in sys.path:
    sys.path.insert(0, fortran_dir)

try:
    import vfi_core
    FORTRAN_AVAILABLE = True
except ImportError:
    FORTRAN_AVAILABLE = False


def sub_vfi_onestep_fortran(val_c, val0_u, kp_bar, B_hat, profit_mat, k_grid, b_grid,
                            pi_x, theta, q, delta, psi):
    """
    约束企业VFI的单步Bellman算子（Fortran版本）
    
    参数:
    val_c: 约束企业退出后的价值 (nk, nb, nx)
    val0_u: 无约束企业退出前的价值 (nk, nb, nx)
    kp_bar: 下一期k'的上界 (nk, nb, nx)
    B_hat: 维度(nk, nx)
    profit_mat: 静态利润 (nk, nx)
    k_grid: 维度(nk,)
    b_grid: 维度(nk, nb)
    pi_x: 维度(nx, nx)
    theta, q, delta, psi: 参数
    
    返回:
    val_c_new: 维度(nk, nb, nx)
    pol_kp_ind: 维度(nk, nb, nx), 整数
    """
    if not FORTRAN_AVAILABLE:
        raise ImportError("Fortran模块不可用，请先编译: python fortran/setup_fortran.py")
    
    nk, nb, nx = val_c.shape
    
    # 确保数组是Fortran连续的（如果已经是Fortran连续，则避免复制）
    if not val_c.flags.f_contiguous or val_c.dtype != np.float64:
        val_c = np.asfortranarray(val_c, dtype=np.float64)
    if not val0_u.flags.f_contiguous or val0_u.dtype != np.float64:
        val0_u = np.asfortranarray(val0_u, dtype=np.float64)
    if not kp_bar.flags.f_contiguous or kp_bar.dtype != np.float64:
        kp_bar = np.asfortranarray(kp_bar, dtype=np.float64)
    if not B_hat.flags.f_contiguous or B_hat.dtype != np.float64:
        B_hat = np.asfortranarray(B_hat, dtype=np.float64)
    if not profit_mat.flags.f_contiguous or profit_mat.dtype != np.float64:
        profit_mat = np.asfortranarray(profit_mat, dtype=np.float64)
    if not k_grid.flags.c_contiguous or k_grid.dtype != np.float64:
        k_grid = np.ascontiguousarray(k_grid.flatten(), dtype=np.float64)
    if not b_grid.flags.f_contiguous or b_grid.dtype != np.float64:
        b_grid = np.asfortranarray(b_grid, dtype=np.float64)
    if not pi_x.flags.f_contiguous or pi_x.dtype != np.float64:
        pi_x = np.asfortranarray(pi_x, dtype=np.float64)
    
    # 初始化输出
    val_c_new = np.zeros((nk, nb, nx), order='F', dtype=np.float64)
    pol_kp_ind = np.zeros((nk, nb, nx), order='F', dtype=np.int32)
    
    # 调用Fortran子程序（f2py会自动从数组维度推断nk, nb, nx，并自动处理输出参数）
    val_c_new, pol_kp_ind = vfi_core.vfi_core.sub_vfi_onestep_fortran(
        val_c, val0_u, kp_bar, B_hat, profit_mat, k_grid, b_grid,
        pi_x, theta, q, delta, psi
    )
    
    return val_c_new, pol_kp_ind
