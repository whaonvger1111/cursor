"""
计算僵尸企业（被拯救和僵尸）和非僵尸被拯救企业的统计
"""
import numpy as np
from fun import Fun


def fun_zombie(pol_tran, distrib_tran, path, par):
    """
    计算僵尸企业统计
    
    参数:
    pol_tran: 政策字典，使用的字段：pol_exit(k,b,x,t,n)和V1(k,x,t,n)
    distrib_tran: 转移动态分布字典，使用的字段：mu(k,b,x,t,n)
    path: 转移动态价格字典，使用的字段：w(t)
    par: 参数字典，使用的字段包括weights(k,x,n)
    
    返回:
    out_zombie: 包含字段的字典：ave_x_zombie, ave_x_no_zombie, ave_b_zombie, 
                ave_b_no_zombie, ave_k_zombie, ave_k_no_zombie, ave_l_zombie, 
                ave_l_no_zombie, ave_y_zombie, ave_y_no_zombie, mass_zombie,
                mass_no_zombie, mass_not_saved, mass_nogrant_exit
    """
    # 创建僵尸指标，维度：nb,nx,nk,ni
    # 0 = 企业未被拯救（要么一直在，要么一直退出）
    # 1 = 企业被拯救，且是僵尸
    # 2 = 企业被拯救，不是僵尸
    
    # 1 = 受冲击，补助, 2 = 未受冲击，补助, 3 = 受冲击，无补助, 4 = 未受冲击，无补助
    zombie = np.zeros((par['nk'], par['nb'], par['nx'], par['ni']))
    t_c = 0  # 只考虑冲击期（Python索引从0开始）
    
    for i_c in range(par['ni']):  # 受冲击 vs 未受冲击
        for k_c in range(par['nk']):
            for x_c in range(par['nx']):
                for b_c in range(par['nb']):
                    # 检查企业是否被拯救
                    # n_c = i_c 表示有补助，n_c = i_c + 2 表示无补助
                    if pol_tran['pol_exit'][k_c, b_c, x_c, t_c, i_c] < 0.5 and \
                       pol_tran['pol_exit'][k_c, b_c, x_c, t_c, i_c + 2] >= 0.5:
                        # 如果企业在有补助时不退出（n_c = i_c）但在无补助时退出（n_c = i_c+2），企业被拯救
                        zombie[k_c, b_c, x_c, i_c] = 2
                        # 检查企业是否是僵尸
                        # 注意V1维度为(nk,nx,T+1,nn)
                        if pol_tran['V1'][k_c, x_c, t_c, i_c + 2] < par['theta'] * (1 - par['delta_k']) * par['k_grid'][k_c]:
                            # 如果企业的无约束价值小于清算价值，企业是僵尸
                            zombie[k_c, b_c, x_c, i_c] = 1
    
    # 被拯救企业中僵尸的比例是多少？僵尸和非僵尸的平均x、k、b是多少？
    # 使用退出前的分布，草稿中称为mu^0
    t_c = 0  # 只考虑冲击期
    
    mass_not_saved = 0
    mass_zombie = 0
    mass_no_zombie = 0
    mass_nogrant_exit = 0  # 有补助但在无补助时会退出的企业
    mass_allfirms = 0  # 所有活跃企业的质量
    ave_x_zombie = 0
    ave_b_zombie = 0
    ave_k_zombie = 0
    ave_l_zombie = 0
    ave_y_zombie = 0
    ave_x_no_zombie = 0
    ave_b_no_zombie = 0
    ave_k_no_zombie = 0
    ave_l_no_zombie = 0
    ave_y_no_zombie = 0
    
    for i_c in range(par['ni']):  # 受冲击 vs 未受冲击，有补助
        for k_c in range(par['nk']):
            for x_c in range(par['nx']):
                for b_c in range(par['nb']):
                    # 企业质量
                    weight_val = par['weights'][k_c, x_c, i_c]
                    mu_val = distrib_tran['mu'][k_c, b_c, x_c, t_c, i_c]
                    
                    mass_zombie += weight_val * mu_val * (zombie[k_c, b_c, x_c, i_c] == 1)
                    mass_no_zombie += weight_val * mu_val * (zombie[k_c, b_c, x_c, i_c] == 2)
                    mass_not_saved += weight_val * mu_val * (zombie[k_c, b_c, x_c, i_c] == 0)
                    
                    # 检查企业是否会在无补助时退出
                    if pol_tran['pol_exit'][k_c, b_c, x_c, t_c, i_c + 2] >= 0.5:
                        mass_nogrant_exit += weight_val * mu_val
                    
                    mass_allfirms += weight_val * distrib_tran['mu_active'][k_c, b_c, x_c, t_c, i_c]
                    
                    # 僵尸企业的平均值
                    if zombie[k_c, b_c, x_c, i_c] == 1:
                        kappa = par['k_grid'][k_c] if isinstance(par['k_grid'][k_c], (int, float, np.number)) else par['k_grid'][k_c, 0]
                        b_val = pol_tran['b_grid'][k_c, b_c, t_c, i_c]
                        x_val = par['x_grid'][x_c] * par['A_small'][t_c, i_c]
                        l_val = Fun.fun_l(x_val, path['w'][t_c], kappa, par)
                        y_val = Fun.prod_small(x_val, kappa, l_val, par['fixcost'][k_c], par)
                        
                        ave_x_zombie += weight_val * mu_val * x_val
                        ave_b_zombie += weight_val * mu_val * b_val
                        ave_k_zombie += weight_val * mu_val * kappa
                        ave_l_zombie += weight_val * mu_val * l_val
                        ave_y_zombie += weight_val * mu_val * y_val
                    
                    # 非僵尸企业的平均值
                    if zombie[k_c, b_c, x_c, i_c] == 2:
                        kappa = par['k_grid'][k_c] if isinstance(par['k_grid'][k_c], (int, float, np.number)) else par['k_grid'][k_c, 0]
                        b_val = pol_tran['b_grid'][k_c, b_c, t_c, i_c]
                        x_val = par['x_grid'][x_c] * par['A_small'][t_c, i_c]
                        l_val = Fun.fun_l(x_val, path['w'][t_c], kappa, par)
                        y_val = Fun.prod_small(x_val, kappa, l_val, par['fixcost'][k_c], par)
                        
                        ave_x_no_zombie += weight_val * mu_val * x_val
                        ave_b_no_zombie += weight_val * mu_val * b_val
                        ave_k_no_zombie += weight_val * mu_val * kappa
                        ave_l_no_zombie += weight_val * mu_val * l_val
                        ave_y_no_zombie += weight_val * mu_val * y_val
    
    # 归一化平均值
    if mass_zombie > 0:
        ave_x_zombie = ave_x_zombie / mass_zombie
        ave_b_zombie = ave_b_zombie / mass_zombie
        ave_k_zombie = ave_k_zombie / mass_zombie
        ave_l_zombie = ave_l_zombie / mass_zombie
        ave_y_zombie = ave_y_zombie / mass_zombie
    
    if mass_no_zombie > 0:
        ave_x_no_zombie = ave_x_no_zombie / mass_no_zombie
        ave_b_no_zombie = ave_b_no_zombie / mass_no_zombie
        ave_k_no_zombie = ave_k_no_zombie / mass_no_zombie
        ave_l_no_zombie = ave_l_no_zombie / mass_no_zombie
        ave_y_no_zombie = ave_y_no_zombie / mass_no_zombie
    
    out_zombie = {
        'ave_x_zombie': ave_x_zombie,
        'ave_x_no_zombie': ave_x_no_zombie,
        'ave_b_zombie': ave_b_zombie,
        'ave_b_no_zombie': ave_b_no_zombie,
        'ave_k_zombie': ave_k_zombie,
        'ave_k_no_zombie': ave_k_no_zombie,
        'ave_l_zombie': ave_l_zombie,
        'ave_l_no_zombie': ave_l_no_zombie,
        'ave_y_zombie': ave_y_zombie,
        'ave_y_no_zombie': ave_y_no_zombie,
        'mass_zombie': mass_zombie,
        'mass_no_zombie': mass_no_zombie,
        'mass_not_saved': mass_not_saved,
        'mass_nogrant_exit': mass_nogrant_exit,
        'mass_allfirms': mass_allfirms
    }
    
    return out_zombie

