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
    
    # Howard加速（如果需要）- 向量化版本，大幅提升性能
    if do_howard == 1:
        from fun import Fun
        n_howard = 50
        kprime_vec = k_grid.flatten()
        
        # 预计算一些常量
        theta_delta_kprime = theta * (1 - delta) * kprime_vec  # (nk,)
        q_psi_theta_delta_kprime = q * psi * theta * (1 - delta) * kprime_vec  # (nk,)
        
        # 创建索引网格用于高级索引
        k_indices = np.arange(nk)[:, np.newaxis]  # (nk, 1)
        x_indices = np.arange(nx)[np.newaxis, :]  # (1, nx)
        
        for h_c in range(n_howard):
            # 向量化计算EV
            V1_max = np.maximum(theta_delta_kprime[:, np.newaxis], V2)  # (nk, nx)
            EVh = V1_max @ pi_x.T  # (nk, nx)
            
            # 使用高级索引获取最优k'对应的值
            kopt_kprime = k_grid[kpol_ind]  # (nk, nx) - 最优k'值
            kopt_theta_delta = theta_delta_kprime[kpol_ind]  # (nk, nx)
            kopt_q_psi = q_psi_theta_delta_kprime[kpol_ind]  # (nk, nx)
            EVh_opt = EVh[kpol_ind, x_indices]  # (nk, nx) - 使用最优k'的EV
            
            # 向量化计算调整成本
            k_today_2d = k_grid[:, np.newaxis]  # (nk, 1)
            adj_val = kopt_kprime - (1 - delta) * k_today_2d  # (nk, nx)
            adj_val = np.where(kopt_kprime < (1 - delta) * k_today_2d, 
                              theta * adj_val, adj_val)  # (nk, nx)
            
            # 向量化更新V2
            V2 = (profit_mat - adj_val + 
                  kopt_q_psi + 
                  q * (1 - psi) * EVh_opt)  # (nk, nx)
    
    return V2

