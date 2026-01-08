"""
对分布mu^0进行一步算子操作
为了速度原因，我们在left_loc_arr和omega_arr中预计算了插值的索引和权重
"""
import numpy as np


def sub_mu_onestep(mu, phi_dist, pol_kp_ind, pol_exit, pol_entry,
                   left_loc_arr, omega_arr, pi_x, mass, psi):
    """
    对分布mu^0进行一步算子操作
    
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
    
    mu1 = np.zeros((nk, nb, nx))
    
    for x_c in range(nx):  # 当前生产率
        for b_c in range(nb):  # 当前债务
            for k_c in range(nk):  # 当前资本
                dexit = psi + (1 - psi) * pol_exit[k_c, b_c, x_c]  # 1=退出,0=继续
                entry = pol_entry[k_c, b_c, x_c]
                knext_ind = int(pol_kp_ind[k_c, b_c, x_c])
                left_loc = int(left_loc_arr[k_c, b_c, x_c])
                # left_loc上的权重
                omega = omega_arr[k_c, b_c, x_c]
                
                # 确保索引在有效范围内
                knext_ind = np.clip(knext_ind, 0, nk - 1)
                left_loc = np.clip(left_loc, 0, nb - 2)
                
                # 更新分布
                mu1[knext_ind, left_loc, x_c] += (omega * (1 - dexit) * mu[k_c, b_c, x_c] +
                                                   omega * mass * entry * phi_dist[k_c, b_c, x_c])
                
                if left_loc + 1 < nb:
                    mu1[knext_ind, left_loc + 1, x_c] += ((1 - omega) * (1 - dexit) * mu[k_c, b_c, x_c] +
                                                           (1 - omega) * mass * entry * phi_dist[k_c, b_c, x_c])
    
    # 矩阵乘法: mu1(k',b',x)*pi(x,x')==> mu1(k',b',x')
    for k_c in range(nk):
        temp = mu1[k_c, :, :]  # (nb, nx)
        mu1[k_c, :, :] = temp @ pi_x.T  # (nb, nx) @ (nx, nx) = (nb, nx)
    
    return mu1

