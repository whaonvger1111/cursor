"""
B_hat计算的Fortran包装器
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


def sub_Bhat_onestep_fortran(B_hat, pol_kp_unc, profit_mat, x_tilde_val, k_grid, x_grid,
                              q, theta, delta, lambda_val):
    """
    找到B_hat(k,x)，与非负股息一致的最高债务水平（Fortran版本）
    
    参数:
    B_hat: 初始最大债务, 维度: (nk,nx)
    pol_kp_unc: 无约束企业的k'(k,x)政策, 维度: (nk,nx)
    profit_mat: 静态利润, 维度: (nk,nx)
    x_tilde_val: 退出截断值, 维度: (nk,)
    k_grid: 资本的固定网格, 维度: (nk,)
    x_grid: 生产率的网格, 维度: (nx,)
    q,theta,delta,lambda_val: 标量参数
    
    返回:
    B_hat_new: 更新的B_hat, 维度: (nk,nx)
    pol_bp_unc: 无约束企业的b'(k,x)政策, 维度: (nk,nx)
    """
    nk, nx = B_hat.shape
    
    # 快速检查并转换数组为Fortran顺序（减少条件检查开销）
    # 假设数组已经是Fortran顺序（由fun_vfi1保证），只在需要时转换
    if not B_hat.flags.f_contiguous or B_hat.dtype != np.float64:
        B_hat = np.asfortranarray(B_hat, dtype=np.float64)
    if not pol_kp_unc.flags.f_contiguous or pol_kp_unc.dtype != np.float64:
        pol_kp_unc = np.asfortranarray(pol_kp_unc, dtype=np.float64)
    if not profit_mat.flags.f_contiguous or profit_mat.dtype != np.float64:
        profit_mat = np.asfortranarray(profit_mat, dtype=np.float64)
    
    x_tilde_val = np.ascontiguousarray(x_tilde_val.flatten(), dtype=np.float64)
    k_grid = np.ascontiguousarray(k_grid.flatten(), dtype=np.float64)
    x_grid = np.ascontiguousarray(x_grid.flatten(), dtype=np.float64)
    
    # 调用Fortran函数（f2py会自动从数组维度推断nk和nx）
    B_hat_new, pol_bp_unc = vfi_core.vfi_core.sub_bhat_onestep_fortran(
        B_hat, pol_kp_unc, profit_mat, x_tilde_val, k_grid, x_grid,
        q, theta, delta, lambda_val)
    
    return B_hat_new, pol_bp_unc

