"""
分解小企业产出相对于稳态的变化
deltaY(x) = deltaTFP(x)+deltaL(x)+deltaExit(x)
"""
import numpy as np
from fun import Fun


def ind2sub(shape, index):
    """
    将线性索引转换为下标
    """
    indices = np.unravel_index(index, shape)
    return indices[0], indices[1]


def fun_decomposition(T_last, distribS, prices, distrib_tran, path, weights, par):
    """
    分解小企业产出相对于稳态的变化
    
    参数:
    T_last: 我们考虑的期数
    distribS: 稳态分布字典，mu和mu_active(k,b,x)
    prices: 稳态价格字典，wage
    distrib_tran: 转移动态分布字典，mu和mu_active(k,b,x,t,n)
    path: 转移动态价格字典
    weights: 权重
    par: 参数字典
    
    返回:
    Delta: 包含deltaY,deltaTFP,deltaL,deltaExit字段的字典
    """
    nb = par['nb']  # 债务"b"的网格点数
    nx = par['nx']  # x的网格点数
    nk = par['nk']  # kappa的网格点数
    ni = par['ni']  # 受冲击/未受冲击
    ns = par['ns']  # 补助/无补助
    nn = par['nn']
    x_grid = par['x_grid']  # 生产率"x"的网格
    k_grid = par['k_grid']  # 小企业资本"kappa"的网格
    fixcost = par['fixcost']  # 固定成本向量，每个kappa一个
    
    # SS维度: (k,b,x)
    # Tran维度: (k,b,x,t,impact x grant)
    deltaY = np.zeros((nk, nx))
    deltaTFP = np.zeros((nk, nx))
    deltaL = np.zeros((nk, nx))
    deltaExit = np.zeros((nk, nx))  # 由于mu变化（即进入和退出）导致的Y变化
    
    for n_c in range(nn):
        i_c = n_c % ni  # 受冲击指标
        # s_c = n_c // ni  # 补助指标
        
        for t_c in range(T_last):
            for x_c in range(nx):
                for b_c in range(nb):  # 当前债务
                    for k_c in range(nk):
                        kappa = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
                        fixval = fixcost[k_c]
                        x1 = par['A_small'][t_c, i_c] * x_grid[x_c]
                        xss = x_grid[x_c]  # 稳态
                        # fun_l(x,wage,kappa,par)
                        l1 = Fun.fun_l(x1, path['w'][t_c], kappa, par)
                        lss = Fun.fun_l(xss, prices['wage'], kappa, par)
                        # prod_small(x,kappa,l_small,c,par)
                        y1 = weights[k_c, x_c, n_c] * distrib_tran['mu_active'][k_c, b_c, x_c, t_c, n_c] * \
                            Fun.prod_small(x1, kappa, l1, fixval, par)
                        yss = weights[k_c, x_c, n_c] * distribS['mu_active'][k_c, b_c, x_c] * \
                            Fun.prod_small(xss, kappa, lss, fixval, par)
                        deltaY[k_c, x_c] = deltaY[k_c, x_c] + (y1 - yss)
                        deltaTFP[k_c, x_c] = deltaTFP[k_c, x_c] + weights[k_c, x_c, n_c] * \
                            distribS['mu_active'][k_c, b_c, x_c] * \
                            (Fun.prod_small(x1, kappa, lss, fixval, par) - Fun.prod_small(xss, kappa, lss, fixval, par))
                        deltaL[k_c, x_c] = deltaL[k_c, x_c] + weights[k_c, x_c, n_c] * \
                            distribS['mu_active'][k_c, b_c, x_c] * \
                            (Fun.prod_small(x1, kappa, l1, fixval, par) - Fun.prod_small(x1, kappa, lss, fixval, par))
                        deltaMU = weights[k_c, x_c, n_c] * distrib_tran['mu_active'][k_c, b_c, x_c, t_c, n_c] - \
                            weights[k_c, x_c, n_c] * distribS['mu_active'][k_c, b_c, x_c]
                        deltaExit[k_c, x_c] = deltaExit[k_c, x_c] + deltaMU * Fun.prod_small(x1, kappa, l1, fixval, par)
    
    check = deltaY - (deltaTFP + deltaL + deltaExit)
    if np.max(np.abs(check)) > 1e-12:
        print(check)
        print("警告：分解不匹配！")
    
    Delta = {
        'deltaY': deltaY,
        'deltaTFP': deltaTFP,
        'deltaL': deltaL,
        'deltaExit': deltaExit
    }
    
    return Delta

