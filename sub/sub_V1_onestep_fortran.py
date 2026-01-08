"""
无约束企业VFI的Fortran包装器
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


def sub_V1_onestep_fortran(V1, pi_x, profit_mat, k_grid, q, theta, delta, psi, do_howard):
    """
    无约束企业价值函数V(k,x)的单步Bellman算子（Fortran版本）
    
    参数:
    V1: 价值函数V(k,x), 维度: (nk,nx)
    pi_x: 转移概率矩阵prob(x,x'), 维度: (nx,nx)
    profit_mat: 静态利润pi(k,x), 维度: (nk,nx)
    k_grid: 资本的固定网格, 维度: (nk,)
    q,theta,delta,psi: 参数, 标量
    do_howard: 是否使用Howard加速
    
    返回:
    V2: 价值函数V(k,x), 维度: (nk,nx)
    """
    nk, nx = V1.shape
    
    # 关键优化：在Python中使用BLAS优化的矩阵乘法计算EV（比Fortran循环快得多）
    kprime = k_grid.flatten()
    V1_max = np.maximum(theta * (1 - delta) * kprime[:, np.newaxis], V1)  # 维度: (nk,nx)
    EV = V1_max @ pi_x.T  # 使用NumPy的BLAS优化矩阵乘法，非常快！
    
    # 预先转换数组为Fortran顺序（只在第一次或需要时转换，避免每次迭代都转换）
    if not V1.flags.f_contiguous:
        V1 = np.asfortranarray(V1, dtype=np.float64)
    elif V1.dtype != np.float64:
        V1 = V1.astype(np.float64, order='F', copy=False)
    
    if not EV.flags.f_contiguous:
        EV = np.asfortranarray(EV, dtype=np.float64)
    elif EV.dtype != np.float64:
        EV = EV.astype(np.float64, order='F', copy=False)
    
    if not profit_mat.flags.f_contiguous:
        profit_mat = np.asfortranarray(profit_mat, dtype=np.float64)
    elif profit_mat.dtype != np.float64:
        profit_mat = profit_mat.astype(np.float64, order='F', copy=False)
    
    k_grid = np.ascontiguousarray(k_grid.flatten(), dtype=np.float64)
    
    # 调用Fortran函数，传入已计算的EV（跳过Fortran中的矩阵乘法）
    # 优先使用快速版本，如果不可用则使用原版本（但原版本会在Fortran中重新计算EV）
    if hasattr(vfi_core.vfi_core, 'sub_v1_onestep_fortran_fast'):
        # 使用快速版本（接受EV，跳过矩阵乘法）
        V2, kpol_ind = vfi_core.vfi_core.sub_v1_onestep_fortran_fast(V1, EV, profit_mat, k_grid, q, theta, delta, psi)
    else:
        # 使用原版本（会在Fortran中重新计算EV，但至少Python部分使用了BLAS）
        V2, kpol_ind = vfi_core.vfi_core.sub_v1_onestep_fortran(V1, pi_x, profit_mat, k_grid, q, theta, delta, psi)
    
    # Howard加速（如果需要）
    if do_howard == 1:
        from fun import Fun  # 使用Python版本的adjcost_scal，避免Python-Fortran调用开销
        n_howard = 50
        for h_c in range(n_howard):
            V1_max = np.maximum(theta * (1 - delta) * k_grid[:, np.newaxis], V2)
            EVh = V1_max @ pi_x.T
            for x_c in range(nx):
                EV_x = EVh[:, x_c]
                for k_c in range(nk):
                    kopt_ind = kpol_ind[k_c, x_c]
                    V2[k_c, x_c] = (profit_mat[k_c, x_c] - 
                                   Fun.adjcost_scal(k_grid[kopt_ind], k_grid[k_c], theta, delta) + 
                                   q * (psi * theta * (1 - delta) * k_grid[kopt_ind] + 
                                        (1 - psi) * EV_x[kopt_ind]))
    
    return V2

