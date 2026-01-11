"""
Bellman算子的单步：val_new = T(val)
这个函数在无限期界或转移动态的向后迭代中被调用

插值：
在早期版本中，我们在k'和b'上使用v^0的双线性插值。
现在我们强制k'在k_grid上，只对b'进行插值。
"""
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
from myinterp1 import myinterp1
from fun import Fun


def myfind_loc(x_grid, xi):
    """
    找到jl使得x_grid(jl)<=xi<x_grid(jl+1)
    
    参数:
    x_grid: 严格递增的列向量
    xi: 标量
    
    返回:
    jl: 左点（标量）
    omega: 左点的权重（标量）
    注意：omega不限制在[0,1]
    """
    from tools.find_loc import locate
    
    nx = len(x_grid)
    jl = max(min(locate(x_grid, xi), nx - 2), 0)
    
    # x_grid(j)上的权重
    omega = (x_grid[jl + 1] - xi) / (x_grid[jl + 1] - x_grid[jl])
    
    return jl, omega


def fun_howard(val_c, pol_kp_ind, val0_u, kp_bar, B_hat, profit_mat, k_grid, b_grid,
               pi_x, theta, q, delta, psi, n_howard):
    """
    Howard策略改进算法的一步
    被sub_vfi_onestep调用n_howard次
    
    注意：
    输入参数"kp_bar"未使用，但我们保留它用于调试。
    """
    nk, nb, nx = val_c.shape
    
    if nk != len(k_grid):
        raise ValueError('nk不正确')
    if nb != b_grid.shape[1]:
        raise ValueError('nb不正确')
    
    # 初始化输出
    val_c_new = np.zeros((nk, nb, nx))
    
    # 预计算以加速howard
    left_arr = np.ones((nk, nb, nx), dtype=int)
    omega_arr = np.zeros((nk, nb, nx))
    bprime_arr = np.zeros((nk, nb, nx))
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                k_val = k_grid[k_c]
                b_val = b_grid[k_c, b_c]
                profit_val = profit_mat[k_c, x_c]
                kp_c = int(pol_kp_ind[k_c, b_c, x_c])
                kp_val = k_grid[kp_c]
                b_grid_kp = b_grid[kp_c, :]
                bprime = max(b_grid_kp[0], (1 / q) * (b_val - profit_val + 
                                                      Fun.adjcost_scal(kp_val, k_val, theta, delta)))
                bprime_arr[k_c, b_c, x_c] = bprime
                jstar, omega = myfind_loc(b_grid_kp, bprime)
                left_arr[k_c, b_c, x_c] = jstar
                omega_arr[k_c, b_c, x_c] = omega
    
    for h_c in range(n_howard):
        # STEP 2 - 施加清算，方程(24)
        # 约束企业退出前的价值
        val0_c = np.zeros((nk, nb, nx))
        for x_c in range(nx):
            for b_c in range(nb):
                for k_c in range(nk):
                    k_val = k_grid[k_c]
                    b_val = b_grid[k_c, b_c]
                    profit_val = profit_mat[k_c, x_c]
                    liq1 = profit_val - b_val + theta * (1 - delta) * k_val < 0
                    liq2 = val_c[k_c, b_c, x_c] < theta * (1 - delta) * k_val - b_val
                    if liq1 or liq2:
                        val0_c[k_c, b_c, x_c] = theta * (1 - delta) * k_val - b_val
                    else:
                        val0_c[k_c, b_c, x_c] = val_c[k_c, b_c, x_c]
        
        # STEP 3 - 执行方程(23)
        val0 = np.zeros((nk, nb, nx))
        is_c = np.ones((nk, nb, nx))  # 约束企业的指标
        
        for x_c in range(nx):
            for b_c in range(nb):
                for k_c in range(nk):
                    b_val = b_grid[k_c, b_c]
                    if b_val <= B_hat[k_c, x_c]:
                        val0[k_c, b_c, x_c] = val0_u[k_c, b_c, x_c]
                        is_c[k_c, b_c, x_c] = 0
                    else:
                        val0[k_c, b_c, x_c] = val0_c[k_c, b_c, x_c]
        
        # STEP 4 - 求解方程(25)
        for x_c in range(nx):
            # 计算方程(25)中的期望值
            EVx = np.zeros((nk, nb))  # (k',b')
            for xp_c in range(nx):
                EVx = EVx + pi_x[x_c, xp_c] * val0[:, :, xp_c]
            
            for b_c in range(nb):
                for k_c in range(nk):
                    k_val = k_grid[k_c]
                    b_val = b_grid[k_c, b_c]
                    profit_val = profit_mat[k_c, x_c]
                    
                    if is_c[k_c, b_c, x_c] == 1 and profit_val - b_val + theta * (1 - delta) * k_val >= 0:
                        jstar = left_arr[k_c, b_c, x_c]
                        omega = omega_arr[k_c, b_c, x_c]
                        kp_c = int(pol_kp_ind[k_c, b_c, x_c])
                        kp_val = k_grid[kp_c]
                        bprime = bprime_arr[k_c, b_c, x_c]
                        v0_int = omega * EVx[kp_c, jstar] + (1 - omega) * EVx[kp_c, min(jstar + 1, nb - 1)]
                        val_c_new[k_c, b_c, x_c] = q * (psi * (theta * (1 - delta) * kp_val - bprime) + 
                                                       (1 - psi) * v0_int)
                    else:
                        # 无约束或强制清算：val_c无关
                        val_c_new[k_c, b_c, x_c] = theta * (1 - delta) * k_val - b_val
        
        # 更新
        val_c = val_c_new.copy()
    
    return val_c_new


def sub_vfi_onestep(val_c, val0_u, kp_bar, B_hat, profit_mat, k_grid, b_grid,
                   pi_x, theta, q, delta, psi, do_howard, n_howard):
    """
    Bellman算子的单步
    
    参数:
    val_c(k,b,x): 约束企业退出后的价值
    val0_u(k,b,x): 无约束企业退出前的价值
    kp_bar(k,b,x): 下一期k'的上界，见方程(25)
    profit_mat(k,x): 静态利润, 维度: (nk,nx)
    B_hat(k,x): 维度(nk,nx)
    k_grid: 维度(nk,), 资本的固定网格
    b_grid: 维度(nk,nb), 债务的灵活网格
    pi_x: 维度(nx,nx), x的转移矩阵
    theta,q,delta,psi: 参数
    do_howard,n_howard: 整数参数
    
    返回:
    val_c_new: 维度(nk,nb,nx)
    pol_kp_ind: 维度(nk,nb,nx), 整数
    """
    nk, nb, nx = val_c.shape
    
    # 确保k_grid是一维数组（处理可能的(nk,1)形状）
    k_grid = k_grid.flatten() if k_grid.ndim > 1 else k_grid
    
    if nk != len(k_grid):
        raise ValueError('nk不正确')
    if nb != b_grid.shape[1]:
        raise ValueError('nb不正确')
    
    # 初始化输出
    val_c_new = np.zeros((nk, nb, nx))
    pol_kp_ind = np.ones((nk, nb, nx), dtype=int)
    
    # STEP 2 - 施加清算，方程(24)
    # 约束企业退出前的价值
    val0_c = np.zeros((nk, nb, nx))
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                k_val = k_grid[k_c]
                b_val = b_grid[k_c, b_c]
                profit_val = profit_mat[k_c, x_c]
                liq1 = profit_val - b_val + theta * (1 - delta) * k_val < 0
                liq2 = val_c[k_c, b_c, x_c] < theta * (1 - delta) * k_val - b_val
                if liq1 or liq2:
                    val0_c[k_c, b_c, x_c] = theta * (1 - delta) * k_val - b_val
                else:
                    val0_c[k_c, b_c, x_c] = val_c[k_c, b_c, x_c]
    
    # STEP 3 - 执行方程(23)
    val0 = np.zeros((nk, nb, nx))
    is_c = np.ones((nk, nb, nx))  # 约束企业的指标
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                b_val = b_grid[k_c, b_c]
                if b_val <= B_hat[k_c, x_c]:
                    val0[k_c, b_c, x_c] = val0_u[k_c, b_c, x_c]
                    is_c[k_c, b_c, x_c] = 0
                else:
                    val0[k_c, b_c, x_c] = val0_c[k_c, b_c, x_c]
    
    # STEP 4 - 求解方程(25)
    # 在网格上最大化k'
    
    for x_c in range(nx):
        # 计算方程(25)中的期望值
        EVx = np.zeros((nk, nb))  # (k',b')
        for xp_c in range(nx):
            EVx = EVx + val0[:, :, xp_c] * pi_x[x_c, xp_c]
        
        for b_c in range(nb):
            for k_c in range(nk):
                k_val = k_grid[k_c]
                b_val = b_grid[k_c, b_c]
                profit_val = profit_mat[k_c, x_c]
                kp_ub = kp_bar[k_c, b_c, x_c]
                # MATLAB: kp_ub_ind = find(k_grid<=kp_ub, 1, 'last')
                # 找到最后一个满足k_grid<=kp_ub的索引（0-based）
                kp_ub_indices = np.where(k_grid <= kp_ub)[0]
                if len(kp_ub_indices) > 0:
                    kp_ub_ind = kp_ub_indices[-1]  # 最后一个满足条件的索引
                else:
                    kp_ub_ind = -1  # 没有满足条件的，但这种情况不应该发生
                
                if is_c[k_c, b_c, x_c] == 1 and profit_val - b_val + theta * (1 - delta) * k_val >= 0:
                    # 为每个k' \in k_grid创建Bellman方程25的RHS
                    rhs_vec = np.full(nk, -100000.0)
                    
                    # MATLAB: for kp_c = 1:kp_ub_ind (1-based, 包含kp_ub_ind)
                    # Python: for kp_c in range(kp_ub_ind + 1) (0-based, 包含kp_ub_ind)
                    # 但MATLAB的kp_ub_ind是1-based的最后一个索引，Python需要转换为0-based
                    # 如果MATLAB的kp_ub_ind = 10，循环1到10（10次）
                    # Python应该循环0到9（10次），所以kp_ub_ind应该是9
                    # 但我们已经用0-based索引找到了kp_ub_ind，所以直接使用
                    if kp_ub_ind >= 0:
                        for kp_c in range(kp_ub_ind + 1):
                            kp_val = k_grid[kp_c]
                            b_grid_kp = b_grid[kp_c, :]
                            bprime = max(b_grid_kp[0], (1 / q) * (b_val - profit_val + 
                                                                  Fun.adjcost_scal(kp_val, k_val, theta, delta)))
                            v0_int = myinterp1(b_grid_kp, EVx[kp_c, :], bprime, 1)
                            rhs_vec[kp_c] = q * (psi * (theta * (1 - delta) * kp_val - bprime) + 
                                                (1 - psi) * v0_int)
                    
                    max_ind = np.argmax(rhs_vec)
                    pol_kp_ind[k_c, b_c, x_c] = max_ind
                    val_c_new[k_c, b_c, x_c] = rhs_vec[max_ind]
                else:
                    # 企业无约束或强制清算：val_c无关
                    val_c_new[k_c, b_c, x_c] = theta * (1 - delta) * k_val - b_val
    
    # 现在执行Howard
    # Howard加速
    if do_howard == 1:
        val_c_new = fun_howard(val_c_new, pol_kp_ind, val0_u, kp_bar, B_hat,
                              profit_mat, k_grid, b_grid, pi_x, theta, q, delta, psi, n_howard)
    
    return val_c_new, pol_kp_ind

