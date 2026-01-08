"""
计算校准目标
"""
import numpy as np
from fun import Fun


def fun_targets(sol, mustruct, par, prices, agg, b_grid):
    """
    计算校准目标
    
    参数:
    sol: 来自vfi的解策略字典
    mustruct: 分布字典
    par: 模型参数字典
    prices: 价格字典
    agg: 加总矩字典
    b_grid: 债务网格，维度(nk,nb)
    
    返回:
    mom: 模型矩字典
    """
    # 输入检查
    if not isinstance(sol, dict):
        raise TypeError("输入sol必须是字典")
    if not isinstance(mustruct, dict):
        raise TypeError("输入mustruct必须是字典")
    if not isinstance(par, dict):
        raise TypeError("输入par必须是字典")
    if not isinstance(prices, dict):
        raise TypeError("输入prices必须是字典")
    if not isinstance(agg, dict):
        raise TypeError("输入agg必须是字典")
    
    mom = {}
    
    # 解包相关变量
    pol_debt = sol['pol_debt']  # 维度: (nk,nb,nx)
    pol_exit = sol['pol_exit']
    pol_kp_ind = sol['pol_kp_ind']
    pol_exit_forced = sol['pol_exit_forced']
    pol_exit_vol = sol['pol_exit_vol']
    pol_entry = sol['pol_entry']
    phi_dist = sol['phi_dist']
    mu = mustruct['mu']
    mu_active = mustruct['mu_active']
    wage = prices['wage']
    
    # 解包一些参数
    pi_x = par['pi_x']
    nx = par['nx']
    nb = par['nb']
    nk = par['nk']
    x_grid = par['x_grid']
    k_grid = par['k_grid']
    mass = par['mass']
    psi = par['psi']
    fixcost = par['fixcost']
    N_sim = par.get('N_sim', 80000)
    T_sim = par.get('T_sim', 68)
    
    if b_grid.shape != (nk, nb):
        raise ValueError('b_grid的维度错误')
    
    # 定义总退出率和有用的排列
    exit_all = psi + (1 - psi) * pol_exit
    
    # 注意：后缀"p"表示"permuted"
    # exit_all(k,b,x) ==> exit_allp(b,x,k)
    exit_allp = np.transpose(exit_all, (1, 2, 0))
    # b_grid(k,b) ==> b_gridp(b,k)
    b_gridp = np.transpose(b_grid, (1, 0))
    
    # 小企业的产出或收入份额
    revshare_small = agg['output_small'] / (agg['output_small'] + agg['Y_corp']) if (agg['output_small'] + agg['Y_corp']) > 0 else 0
    
    # 小企业的就业份额
    empshare_small = (agg['L_agg'] - agg['L_corp']) / agg['L_agg'] if agg['L_agg'] > 0 else 0
    
    # 有正债务的企业份额
    b_mat = np.tile(b_grid[:, :, np.newaxis], (1, 1, par['nx']))
    hasNetDebt = np.sum(mu_active[b_mat > 0]) / np.sum(mu_active) if np.sum(mu_active) > 0 else 0
    
    # 在x网格上预计算劳动需求
    labor_vec = np.zeros((nk, nx))
    revenue_vec = np.zeros((nk, nx))
    for x_c in range(nx):
        x_val = x_grid[x_c]
        for k_c in range(nk):
            kappa = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
            c = fixcost[k_c]
            labor_vec[k_c, x_c] = Fun.fun_l(x_val, wage, kappa, par)
            revenue_vec[k_c, x_c] = Fun.prod_small(x_val, kappa, labor_vec[k_c, x_c], c, par)
    
    # 活跃企业的就业
    empl_active = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                empl_active += labor_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
    
    # labor_vec(k,b) ==> labor_vecp(b,k)
    labor_vecp = np.transpose(labor_vec, (1, 0))
    
    # 平均企业规模（小企业）
    avefirmsize = empl_active / np.sum(mu_active) if np.sum(mu_active) > 0 else 0
    
    # 按企业年龄的平均企业规模
    # 年龄0
    empl_age0 = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                empl_age0 += mass * labor_vec[k_c, x_c] * pol_entry[k_c, b_c, x_c] * phi_dist[k_c, b_c, x_c]
    
    # 我们已经在fun_obj.m中将其计算为Mentr
    mass_entrants = mass * np.sum(pol_entry * phi_dist)
    avefirmsize_age0 = empl_age0 / mass_entrants if mass_entrants > 0 else 0
    
    # 继续企业的就业创造和就业破坏，就业的自相关
    # b_gridp维度为(nb,nk)
    # labor_vecp维度为(nx,nk)
    
    K = pol_kp_ind
    bminK = b_gridp[0, K]
    bmaxK = b_gridp[nb - 1, K]
    Y = 1 + (nb - 1) * (pol_debt - bminK) / (bmaxK - bminK + 1e-20)
    Yt = np.clip(Y, 1, nb - 1)
    I = np.floor(Yt).astype(int)  # nk x nb x nx
    W = Yt - I
    
    # 创建ndgrid等价物
    I_expanded = np.zeros((nk, nb, nx, nx), dtype=int)
    J_expanded = np.zeros((nk, nb, nx, nx), dtype=int)
    K_expanded = np.zeros((nk, nb, nx, nx), dtype=int)
    
    for xp_c in range(nx):
        I_expanded[:, :, :, xp_c] = I
        J_expanded[:, :, :, xp_c] = xp_c
        K_expanded[:, :, :, xp_c] = K  # K已经是(nk, nb, nx)形状，不需要添加维度
    
    # 计算线性索引
    # sub2ind等价物
    rhsilin = I_expanded * (nx * nk) + J_expanded * nk + K_expanded
    rhsilin = np.clip(rhsilin, 0, nb * nx * nk - 1)
    
    # 重塑并提取值
    exit_allp_flat = exit_allp.flatten()
    dexit_inter = (1 - W[:, :, :, np.newaxis]) * exit_allp_flat[rhsilin] + \
                  W[:, :, :, np.newaxis] * exit_allp_flat[np.clip(rhsilin + 1, 0, len(exit_allp_flat) - 1)]
    dexit_inter = np.transpose(dexit_inter, (3, 0, 1, 2))  # [nx,nk,nb,nx]
    dexit = np.clip(dexit_inter, 0, 1)
    stay_arr = 1 - dexit
    
    jc_num = 0  # JC率定义中的分子
    jd_num = 0  # JD率定义中的分子
    mean_l = 0  # 存活企业就业的平均值
    contin_firms = 0  # 继续企业的质量
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                knext_ind = int(pol_kp_ind[k_c, b_c, x_c])
                stay = stay_arr[:, k_c, b_c, x_c]  # 维度是(nx',)
                
                # 就业创造
                new_jobs = np.maximum(0, labor_vecp[:, knext_ind] - labor_vec[k_c, x_c])  # (nx',)
                temp = pi_x[x_c, :] * new_jobs * stay
                jc_num += np.sum(temp) * mu_active[k_c, b_c, x_c]
                
                # 就业破坏
                firing = np.maximum(0, labor_vec[k_c, x_c] - labor_vecp[:, knext_ind])  # (nx',)
                temp = pi_x[x_c, :] * firing * stay
                jd_num += np.sum(temp) * mu_active[k_c, b_c, x_c]
                
                # 存活企业就业的平均值
                temp = labor_vecp[:, knext_ind] * stay * pi_x[x_c, :]
                mean_l += np.sum(temp) * mu_active[k_c, b_c, x_c]
                temp2 = stay * pi_x[x_c, :]
                contin_firms += np.sum(temp2) * mu_active[k_c, b_c, x_c]
    
    jc_rate = jc_num / empl_active if empl_active > 0 else 0
    jd_rate = jd_num / empl_active if empl_active > 0 else 0
    # 注意：mean_l应该通过继续企业的质量归一化
    mean_l = mean_l / contin_firms if contin_firms > 0 else 0
    
    var_l = 0  # 存活企业就业的方差
    cov_l = 0  # 存活企业中l,l'的协方差
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                knext_ind = int(pol_kp_ind[k_c, b_c, x_c])
                stay = stay_arr[:, k_c, b_c, x_c]  # 维度是(nx',)
                
                # 存活企业就业的方差，存活企业中l,l'的协方差
                var_l += np.sum((labor_vecp[:, knext_ind] - mean_l) ** 2 * stay * pi_x[x_c, :]) * mu_active[k_c, b_c, x_c]
                temp = (labor_vecp[:, knext_ind] - mean_l) * stay * pi_x[x_c, :]
                cov_l += (labor_vec[k_c, x_c] - mean_l) * np.sum(temp) * mu_active[k_c, b_c, x_c]
    
    # 存活企业中l,l'的相关性
    corr_l = cov_l / var_l if var_l > 0 else 0
    
    # 计算企业规模（就业）分布
    bin_lids = np.array([10, 20, 100])
    
    firms = np.zeros(len(bin_lids) + 1)
    workers = np.zeros(len(bin_lids) + 1)
    revenues = np.zeros(len(bin_lids) + 1)
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                lval = labor_vec[k_c, x_c]
                
                if lval < bin_lids[0]:
                    # 少于10名工人
                    firms[0] += mu_active[k_c, b_c, x_c]
                    workers[0] += labor_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
                    revenues[0] += revenue_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
                elif bin_lids[0] <= lval < bin_lids[1]:
                    # [10,20)
                    firms[1] += mu_active[k_c, b_c, x_c]
                    workers[1] += labor_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
                    revenues[1] += revenue_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
                elif bin_lids[1] <= lval < bin_lids[2]:
                    # [20,100)
                    firms[2] += mu_active[k_c, b_c, x_c]
                    workers[2] += labor_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
                    revenues[2] += revenue_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
                elif lval >= bin_lids[2]:
                    # >= 100
                    firms[3] += mu_active[k_c, b_c, x_c]
                    workers[3] += labor_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
                    revenues[3] += revenue_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
    
    share_firms = firms / np.sum(firms) if np.sum(firms) > 0 else firms
    share_empl = workers / np.sum(workers) if np.sum(workers) > 0 else workers
    share_rev = revenues / np.sum(revenues) if np.sum(revenues) > 0 else revenues
    
    # 退出和进入率
    # 强制退出占总退出的比例
    exit_forced = 0
    exit_vol = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                # 强制退出
                dexit_forced = pol_exit_forced[k_c, b_c, x_c]
                exit_forced += dexit_forced * mu[k_c, b_c, x_c]
                # 自愿退出
                dexit_vol = pol_exit_vol[k_c, b_c, x_c]
                exit_vol += dexit_vol * mu[k_c, b_c, x_c]
    
    exit_forced = exit_forced / np.sum(mu) if np.sum(mu) > 0 else 0
    exit_vol = exit_vol / np.sum(mu) if np.sum(mu) > 0 else 0
    frac_exit_forced = exit_forced / agg['exit_rate'] if agg['exit_rate'] > 0 else 0
    frac_exit_vol = exit_vol / agg['exit_rate'] if agg['exit_rate'] > 0 else 0
    
    entry_rate = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                entry = mass * pol_entry[k_c, b_c, x_c]
                entry_rate += entry * phi_dist[k_c, b_c, x_c]
    
    entry_rate = entry_rate / np.sum(mu) if np.sum(mu) > 0 else 0
    
    # 按企业规模的退出率
    bin_lids = np.array([10, 20, 100])
    min_size = par.get('emp_min', 0)
    exit_rate_size = np.zeros(len(bin_lids) + 1)
    mass_size = np.zeros(len(bin_lids) + 1)
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                lval = labor_vec[k_c, x_c]
                dexit = exit_all[k_c, b_c, x_c]
                
                if lval > min_size and lval < bin_lids[0]:
                    # 少于10名工人（但多于min_size）
                    exit_rate_size[0] += dexit * mu[k_c, b_c, x_c]
                    mass_size[0] += mu[k_c, b_c, x_c]
                elif bin_lids[0] <= lval < bin_lids[1]:
                    # [10,20)
                    exit_rate_size[1] += dexit * mu[k_c, b_c, x_c]
                    mass_size[1] += mu[k_c, b_c, x_c]
                elif bin_lids[1] <= lval < bin_lids[2]:
                    # [20,100)
                    exit_rate_size[2] += dexit * mu[k_c, b_c, x_c]
                    mass_size[2] += mu[k_c, b_c, x_c]
                elif lval >= bin_lids[2]:
                    # 100+
                    exit_rate_size[3] += dexit * mu[k_c, b_c, x_c]
                    mass_size[3] += mu[k_c, b_c, x_c]
    
    exit_rate_size = exit_rate_size / (mass_size + 1e-20)
    
    # 小企业的杠杆率（定义为债务/资产）
    # 如果企业有债务，即b>0，杠杆率是b/拥有的资本
    # 如果企业有金融资产，即b<0，杠杆率为零
    
    leverage = 0
    assets = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                kappa = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
                leverage += max(b_grid[k_c, b_c], 0) * mu_active[k_c, b_c, x_c]
                assets += kappa * mu_active[k_c, b_c, x_c]
    
    leverage = leverage / assets if assets > 0 else 0
    
    # 进入者的杠杆率
    leverage_entrants = 0
    assets_entrants = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                kappa = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
                leverage_entrants += max(b_grid[k_c, b_c], 0) * mass * pol_entry[k_c, b_c, x_c] * phi_dist[k_c, b_c, x_c]
                assets_entrants += kappa * mass * pol_entry[k_c, b_c, x_c] * phi_dist[k_c, b_c, x_c]
    
    leverage_entrants = leverage_entrants / assets_entrants if assets_entrants > 0 else 0
    
    # 小企业的劳动份额
    payroll = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                payroll += wage * labor_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
    
    laborshare_small = payroll / agg['output_small'] if agg['output_small'] > 0 else 0
    
    # 债务与工资比率，给定正债务
    tot_debt_pos = 0
    payroll_debt = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                b_val = b_grid[k_c, b_c]
                if b_val > 0:
                    tot_debt_pos += b_val * mu_active[k_c, b_c, x_c]
                    payroll_debt += wage * labor_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
    
    debt_payroll_cond = tot_debt_pos / payroll_debt if payroll_debt > 0 else 0
    
    # 现金与工资比率，条件是有现金
    tot_debt_neg = 0
    payroll_cash = 0
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                b_val = b_grid[k_c, b_c]
                if b_val <= 0:
                    tot_debt_neg += abs(b_val) * mu_active[k_c, b_c, x_c]
                    payroll_cash += wage * labor_vec[k_c, x_c] * mu_active[k_c, b_c, x_c]
    
    cash_payroll_cond = tot_debt_neg / payroll_cash if payroll_cash > 0 else 0
    
    # 小企业的资本收入比
    capital = 0
    for k_c in range(nk):
        kappa = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
        capital += kappa * np.sum(mu_active[k_c, :, :])
    
    tot_fixcost = 0
    # 计算总固定成本
    for x_c in range(nx):
        for k_c in range(nk):
            tot_fixcost += fixcost[k_c] * np.sum(mu_active[:, :, x_c])
    
    # 小企业收入 = 生产产出
    temp = tot_fixcost + agg['output_small']
    caprev = capital / temp if temp > 0 else 0
    
    # 小企业的资本工资比
    k_payroll_ratio = capital / payroll if payroll > 0 else 0
    
    # 固定成本与工资的比率
    fixedcost_to_payroll = tot_fixcost / payroll if payroll > 0 else 0
    
    # 固定成本与收入的比率
    # 注意收入 = 生产产出（需要将固定成本加回到output_small，因为固定成本被减去了）
    fixedcost_to_rev = tot_fixcost / (tot_fixcost + agg['output_small']) if (tot_fixcost + agg['output_small']) > 0 else 0
    
    # 无约束企业的投资率
    # 无约束企业的指标：
    # 无约束企业是那些b <= B_hat(k,x)的企业
    B_hat_mat = np.tile(sol['B_hat'][:, :, np.newaxis], (1, 1, nb))
    B_hat_mat = np.transpose(B_hat_mat, (0, 2, 1))
    is_uc = (b_mat < B_hat_mat)  # (nk,nb,nx)
    
    # 模拟（需要fun_simulate）
    try:
        from fun_simulate import fun_simulate
        sim = fun_simulate(sol, par, mustruct, is_uc, b_grid, N_sim, T_sim)
        
        # k_sim是一个索引，k_sim_val=k_grid(k_sim)
        k_sim = sim['k_sim_val']
        surv_sim = sim['surv_sim']
        
        # 只保留存活的企业
        k_sim = k_sim[surv_sim == 1, 3::4]  # 每4个季度取一次，从第4个季度开始
        
        # 存活企业数量
        N_surv = k_sim.shape[0]
        # 模拟年数
        Y_sim = k_sim.shape[1]
        
        if Y_sim > 1:
            # 投资率(k'-(1-delta)k)/k
            invrate = (k_sim[:, 1:Y_sim] - (1 - par['delta_k']) * k_sim[:, 0:Y_sim - 1]) / (k_sim[:, 0:Y_sim - 1] + 1e-20)
            
            # invrate的均值和标准差
            mean_invrate = np.mean(invrate)
            stdev_invrate = np.mean(np.std(invrate, axis=1))
            
            # 投资率的序列相关
            scor_invrate_vec = np.zeros(N_surv)
            for i_c in range(N_surv):
                if invrate.shape[1] > 1:
                    cov_matrix = np.cov(invrate[i_c, 1:], invrate[i_c, :-1])
                    if cov_matrix.size > 1 and cov_matrix[0, 0] > 0:
                        scor_invrate_vec[i_c] = cov_matrix[1, 0] / (cov_matrix[0, 0] + 1e-20)
            
            scor_invrate = np.mean(scor_invrate_vec)
            
            # 块状投资或正投资峰值的频率（投资率>=20%）
            lumpy_inv = invrate > 0.2
            freq_lumpinv = np.sum(lumpy_inv) / lumpy_inv.size
        else:
            mean_invrate = 0
            stdev_invrate = 0
            scor_invrate = 0
            freq_lumpinv = 0
    except ImportError:
        # fun_simulate未实现，使用占位符
        mean_invrate = 0
        stdev_invrate = 0
        scor_invrate = 0
        freq_lumpinv = 0
    
    # 将矩打包到字典中
    mom['avefirmsize'] = avefirmsize
    mom['empshare_small'] = empshare_small
    mom['revshare_small'] = revshare_small
    mom['payroll_VA_ratio'] = laborshare_small
    mom['exitrate'] = agg.get('exit_rate_emp', agg.get('exit_rate', 0))  # 排除微型企业的退出率
    mom['frac_exit_forced'] = frac_exit_forced
    mom['frac_exit_vol'] = frac_exit_vol
    
    mom['exitrate_0_9'] = exit_rate_size[0]
    mom['exitrate_10_19'] = exit_rate_size[1]
    mom['exitrate_20_99'] = exit_rate_size[2]
    mom['exitrate_100_499'] = exit_rate_size[3]
    
    mom['entryrate'] = entry_rate
    mom['avefirmsize_age0'] = avefirmsize_age0
    
    mom['jcr'] = jc_rate
    mom['jdr'] = jd_rate
    mom['fixedcost_to_rev'] = fixedcost_to_rev
    mom['fixedcost_to_payroll'] = fixedcost_to_payroll
    mom['autocorr_emp'] = corr_l
    mom['debt_asset_all'] = leverage
    mom['debt_asset_entrants'] = leverage_entrants
    mom['debt_asset_all_entrants'] = leverage / leverage_entrants if leverage_entrants > 0 else 0
    
    mom['k_VA_ratio'] = caprev
    mom['k_payroll_ratio'] = k_payroll_ratio
    mom['ave_work'] = agg['L_agg']
    
    mom['hasNetDebt'] = hasNetDebt
    mom['debt_payroll_cond'] = debt_payroll_cond
    mom['cash_payroll_cond'] = cash_payroll_cond
    
    mom['firmshare_0_9'] = share_firms[0]
    mom['firmshare_10_19'] = share_firms[1]
    mom['firmshare_20_99'] = share_firms[2]
    mom['firmshare_100_499'] = share_firms[3]
    
    mom['empshare_0_9'] = share_empl[0]
    mom['empshare_10_19'] = share_empl[1]
    mom['empshare_20_99'] = share_empl[2]
    mom['empshare_100_499'] = share_empl[3]
    
    mom['revshare_0_9'] = share_rev[0]
    mom['revshare_10_19'] = share_rev[1]
    mom['revshare_20_99'] = share_rev[2]
    mom['revshare_100_499'] = share_rev[3]
    
    # 这些是4*1
    mom['share_firms'] = share_firms
    mom['share_empl'] = share_empl
    mom['share_rev'] = share_rev
    
    # 投资率矩
    mom['stdev_invrate'] = stdev_invrate
    mom['scor_invrate'] = scor_invrate
    mom['freq_lumpinv'] = freq_lumpinv
    mom['mean_invrate'] = mean_invrate
    
    return mom

