"""
求解企业的动态规划问题，给定价格{q,w,R}
"""
import numpy as np
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'sub'))

from fun import Fun
from sub.sub_V1_onestep import sub_V1_onestep
from sub.sub_investment_onestep import sub_investment_onestep
from sub.sub_Bhat_onestep import sub_Bhat_onestep
from sub.sub_Bhat_onestep_fortran import sub_Bhat_onestep_fortran
from sub.sub_kp_onestep import sub_kp_onestep
from sub.sub_vfi_onestep import sub_vfi_onestep
try:
    from sub.sub_vfi_onestep_fortran import sub_vfi_onestep_fortran
    SUB_VFI_FORTRAN_AVAILABLE = True
except ImportError:
    SUB_VFI_FORTRAN_AVAILABLE = False
from fun_pol_update import fun_pol_update
from fun_entry_exit import fun_entry_exit
from interp_entry_exit import interp_entry_exit
from gen_phi_dist import gen_phi_dist
from tools.v2struct import pack_to_struct


def fun_vfi1(prices, par):
    """
    求解企业的动态规划问题
    
    参数:
    prices: 价格字典
    par: 参数字典
    
    返回:
    sol: 解字典
    b_grid: 债务网格
    phi_dist: 进入者分布
    conv_flag: 收敛标志
    """
    # 输入检查
    if not isinstance(prices, dict):
        raise TypeError('输入<prices>在fun_vfi1中必须是字典！')
    if not isinstance(par, dict):
        raise TypeError('输入<par>在fun_vfi1中必须是字典！')
    
    # 解包一些标志
    verbose = par.get('verbose', 1)
    max_iter = par['max_iter']
    tolerance = par['tol_vfi']
    tol_vfi_u = par['tol_vfi_u']
    do_howard = par.get('do_howard', 1)
    n_howard = par.get('n_howard', 50)
    tol_bhat = par['tol_bhat']
    
    # 解包一些参数
    theta = par['theta']
    delta = par['delta_k']
    lambda_val = par['lambda']
    cost_e = par['cost_e']
    x_grid = par['x_grid']
    pi_x = par['pi_x']
    nx = par['nx']
    nb = par['nb']
    nk = par['nk']
    x0_prob = par['x0_prob']
    k_grid = par['k_grid']
    fixcost = par['fixcost']  # 向量(nk,)
    prob_k = par['prob_k']
    psi = par['psi']
    
    bk0_vec = par['bk0_vec']
    bk0_prob = par['bk0_prob']
    
    # 解包价格
    q = prices['q']
    wage = prices['wage']
    
    if verbose >= 1:
        print('--------------------------------------------')
        print('VFI')
        print('--------------------------------------------')
    
    # 初始化收敛标志
    conv_flag = 0
    
    # 计算无约束企业扣除债务后的价值，即V(x)
    # 在网格(x,k)上预计算静态利润
    profit_mat = np.zeros((nk, nx), dtype=np.float64, order='F')  # 预先使用Fortran顺序
    for x_c in range(nx):
        for k_c in range(nk):
            k_val = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
            profit_mat[k_c, x_c] = Fun.fun_profit(x_grid[x_c], k_val, fixcost[k_c], wage, par)
    
    # 强制使用Fortran版本，如果不可用则报错
    use_fortran_v1 = par.get('use_fortran', False)
    if not use_fortran_v1:
        raise RuntimeError("错误: use_fortran必须为True！Fortran版本是必需的。")
    
    # 检查Fortran模块是否可用
    try:
        import sys
        fortran_dir = os.path.join(os.path.dirname(__file__), '..', 'fortran')
        if fortran_dir not in sys.path:
            sys.path.insert(0, fortran_dir)
        import vfi_core
        if not hasattr(vfi_core.vfi_core, 'sub_v1_onestep_fortran'):
            raise RuntimeError("错误: Fortran函数sub_v1_onestep_fortran不可用！")
    except ImportError as e:
        raise ImportError(
            f"错误: Fortran模块vfi_core未找到！\n"
            f"请先编译Fortran模块: python fortran/setup_fortran.py\n"
            f"原始错误: {e}"
        )
    
    # 预先转换数组为Fortran顺序（只转换一次）
    if not pi_x.flags.f_contiguous:
        pi_x = np.asfortranarray(pi_x, dtype=np.float64)
    elif pi_x.dtype != np.float64:
        pi_x = pi_x.astype(np.float64, order='F', copy=False)
    
    V1 = np.zeros((nk, nx), dtype=np.float64, order='F')  # 使用Fortran顺序
    profit_mat = np.asfortranarray(profit_mat, dtype=np.float64)
    
    ind = 0
    errter = 10000
    
    if verbose >= 1:
        print('VFI for unconstrained firms...')
    
    start_time = time.time()
    
    # 导入Fortran函数（只导入一次，避免循环内导入开销）
    from sub.sub_V1_onestep_fortran import sub_V1_onestep_fortran
    
    # 确认并打印VFI混合编程状态
    print("="*60)
    print("[VFI混合编程] 无约束企业VFI: 使用Fortran快速版本")
    print(f"  - 网格大小: nk={nk}, nx={nx}")
    print(f"  - Howard加速: {'启用' if do_howard == 1 else '禁用'}")
    print(f"  - 最大迭代次数: {max_iter}")
    print(f"  - 收敛容差: {tol_vfi_u:.2e}")
    print(f"  - 优化: Python BLAS计算EV + Fortran RHS计算 + 向量化Howard")
    print("="*60)
    
    while ind < max_iter and errter > tol_vfi_u:
        V2 = sub_V1_onestep_fortran(V1, pi_x, profit_mat, k_grid, q, theta, delta, psi, do_howard)
        
        errter = np.max(np.abs(V1 - V2))
        ind += 1
        # 更新（V2已经是Fortran顺序）
        V1 = V2
        
        if verbose >= 2:
            print(f'iter = {ind}, err = {errter:.6f}')
    
    if verbose >= 1:
        elapsed = time.time() - start_time
        print(f'Time elapsed: {elapsed:.4f}')
    
    # 找到生产率截断值x_tilde
    x_tilde = np.zeros(nk, dtype=int)
    x_tilde_val = np.zeros(nk)
    
    for k_c in range(nk):
        k_val = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
        viable_x = np.where(V1[k_c, :] >= theta * (1 - delta) * k_val)[0]
        if len(viable_x) > 0:
            x_tilde[k_c] = np.min(viable_x)
            x_tilde_val[k_c] = x_grid[x_tilde[k_c]]
        else:
            print(f'没有可行的x for k_c={k_c}, k_val={k_val:.6f}')
            conv_flag = -1
            return None, None, None, conv_flag
    
    if not np.all(np.isfinite(x_tilde_val)):
        print('警告：x_tilde_val不是有限的')
        conv_flag = -1
        return None, None, None, conv_flag
    
    # 计算无约束稳态投资政策
    pol_kp_unc = sub_investment_onestep(V1, k_grid, pi_x, theta, delta, q, psi)
    
    # 计算B_hat(k,x)作为(21)和(22)的固定点
    B_hat = np.ones((nk, nx), dtype=np.float64, order='F')  # 预先使用Fortran顺序
    ind = 0
    errter = 100
    
    if verbose >= 1:
        print('Fixed point B_hat...')
    
    start_time = time.time()
    # 使用Fortran版本（必需）
    use_fortran_bhat = par.get('use_fortran', False)
    
    # 确认并打印B_hat混合编程状态
    if use_fortran_bhat:
        print("="*60)
        print("[VFI混合编程] B_hat计算: 使用Fortran加速版本")
        print(f"  - 网格大小: nk={nk}, nx={nx}")
        print(f"  - 最大迭代次数: {max_iter}")
        print(f"  - 收敛容差: {tol_bhat:.2e}")
        print(f"  - 优化: 快速数组转换 + Fortran插值")
        print("="*60)
    else:
        print("="*60)
        print("[VFI混合编程] B_hat计算: 使用Python版本（优化：np.interp）")
        print(f"  - 网格大小: nk={nk}, nx={nx}")
        print("="*60)
    
    while ind < max_iter and errter > tol_bhat:
        if use_fortran_bhat:
            B_hat_new, pol_bp_unc = sub_Bhat_onestep_fortran(B_hat, pol_kp_unc, profit_mat,
                                                             x_tilde_val, k_grid, x_grid, q, 
                                                             theta, delta, lambda_val)
        else:
            B_hat_new, pol_bp_unc = sub_Bhat_onestep(B_hat, pol_kp_unc, profit_mat,
                                                     x_tilde_val, k_grid, x_grid, q, 
                                                     theta, delta, lambda_val)
        
        errter = np.max(np.abs(B_hat - B_hat_new))
        ind += 1
        # 更新（保持Fortran顺序以减少下次迭代的转换开销）
        if not B_hat_new.flags.f_contiguous:
            B_hat = np.asfortranarray(B_hat_new, dtype=np.float64)
        else:
            B_hat = B_hat_new
        
        if verbose >= 2:
            print(f'iter = {ind}, err = {errter:.6f}')
    
    if verbose >= 1:
        elapsed = time.time() - start_time
        print(f'Time elapsed: {elapsed:.4f}')
    
    if errter > tol_bhat:
        conv_flag = -1
        return None, None, None, conv_flag
    
    # 定义依赖于k的灵活b网格
    b_tilde = np.zeros(nk)
    b_grid = np.zeros((nk, nb))
    
    for k_c in range(nk):
        k_val = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
        viable_x = x_grid >= x_tilde_val[k_c]
        if np.sum(viable_x) == 0:
            print(f'k_c = {k_c}, k_val = {k_val:.6f}')
            print('警告：没有可行的x')
            conv_flag = -1
            return None, None, None, conv_flag
        
        b_tilde[k_c] = np.min(B_hat[k_c, viable_x])
        b_grid[k_c, :] = np.linspace(min(b_tilde[k_c], lambda_val * k_val), 
                                     lambda_val * k_val, nb)
    
    # 预计算下一期资本k'的上界
    # 上界取决于资本调整是向上还是向下（见草稿方程25）
    kp_bar = sub_kp_onestep(profit_mat, b_grid, k_grid, q, theta, delta, lambda_val)
    
    # 验证
    assert np.all(np.isfinite(kp_bar)) and np.all(~np.isnan(kp_bar)), "kp_bar包含非有限值或NaN"
    assert kp_bar.shape == (nk, nb, nx), f"kp_bar维度错误: {kp_bar.shape}"
    
    # 无约束企业的价值函数v(b,x)=V(x)-b
    # 无约束企业的价值函数: v(b,x,k) = V(x,k)-b
    val_unc = np.zeros((nk, nb, nx))  # 退出后（即继续经营的企业）
    val0_unc = np.zeros((nk, nb, nx))  # 退出前
    
    for x_c in range(nx):
        for b_c in range(nb):
            for k_c in range(nk):
                k_val = k_grid[k_c] if isinstance(k_grid[k_c], (int, float, np.number)) else k_grid[k_c, 0]
                b_val = b_grid[k_c, b_c]
                val_unc[k_c, b_c, x_c] = V1[k_c, x_c] - b_val
                val0_unc[k_c, b_c, x_c] = max(theta * (1 - delta) * k_val - b_val,
                                             val_unc[k_c, b_c, x_c])
    
    # 使用方程(23)-(25)求解约束企业的问题
    # 这里"val"是v_c(x,b,k)，约束企业退出后价值的初始猜测
    val = val_unc.copy()
    iter_count = 0
    dist = 100
    
    if verbose >= 1:
        print('VFI for constrained firms...')
    
    # 确认并打印约束企业VFI混合编程状态
    use_fortran_vfi = par.get('use_fortran', False)
    # 强制使用Fortran版本（如果可用），忽略Howard加速设置
    use_fortran_constrained = use_fortran_vfi and SUB_VFI_FORTRAN_AVAILABLE
    
    if use_fortran_constrained:
        print("="*60)
        print("[VFI混合编程] 约束企业VFI: 使用Fortran版本（混合编程 + OpenMP并行化）")
        print(f"  - 网格大小: nk={nk}, nb={nb}, nx={nx}")
        print(f"  - Howard加速: 禁用（Fortran版本暂不支持，但性能更优）")
        print(f"  - OpenMP并行化: 已启用（x_c循环并行，理论加速30-50倍）")
        print(f"  - 最大迭代次数: {max_iter}")
        print(f"  - 收敛容差: {tolerance:.2e}")
        print("="*60)
    elif use_fortran_vfi:
        print("="*60)
        print("[VFI混合编程] 约束企业VFI: 使用Python版本（已优化：myinterp1手动插值）")
        print(f"  - 网格大小: nk={nk}, nb={nb}, nx={nx}")
        print(f"  - Howard加速: {'启用' if do_howard == 1 else '禁用'}")
        print(f"  - 最大迭代次数: {max_iter}")
        print(f"  - 收敛容差: {tolerance:.2e}")
        if not SUB_VFI_FORTRAN_AVAILABLE:
            print(f"  - 注意: Fortran模块不可用，使用Python版本")
        print(f"  - 优化: myinterp1手动插值（比interp1d快4.2倍，与MATLAB一致）")
        print("="*60)
    else:
        print("="*60)
        print("[VFI混合编程] 约束企业VFI: 使用Python版本")
        print("="*60)
    
    start_time_constrained = time.time()
    
    # 预转换数组为Fortran顺序（只转换一次，减少循环内开销）
    if use_fortran_constrained:
        val = np.asfortranarray(val, dtype=np.float64)
        val0_unc = np.asfortranarray(val0_unc, dtype=np.float64)
        kp_bar = np.asfortranarray(kp_bar, dtype=np.float64)
        B_hat = np.asfortranarray(B_hat, dtype=np.float64)
        profit_mat = np.asfortranarray(profit_mat, dtype=np.float64)
        k_grid = np.ascontiguousarray(k_grid.flatten(), dtype=np.float64)
        b_grid = np.asfortranarray(b_grid, dtype=np.float64)
        pi_x = np.asfortranarray(pi_x, dtype=np.float64)
    
    # 固定点val --> val_new
    while iter_count < max_iter and dist > tolerance:
        if use_fortran_constrained:
            # 使用Fortran版本（不支持Howard加速，但性能更优，已并行化）
            val_new, pol_kp_ind_con = sub_vfi_onestep_fortran(
                val, val0_unc, kp_bar, B_hat,
                profit_mat, k_grid, b_grid, pi_x,
                theta, q, delta, psi
            )
        else:
            # 使用Python版本（支持Howard加速）
            val_new, pol_kp_ind_con = sub_vfi_onestep(val, val0_unc, kp_bar, B_hat,
                                                      profit_mat, k_grid, b_grid, pi_x,
                                                      theta, q, delta, psi, do_howard, n_howard)
        
        dist = np.max(np.abs(val_new - val))
        iter_count += 1
        # 更新
        val = val_new
        
        if verbose >= 2:
            print(f'iter = {iter_count}, err = {dist:.18f}')
    
    if verbose >= 1:
        elapsed_constrained = time.time() - start_time_constrained
        print(f'Time elapsed for constrained VFI: {elapsed_constrained:.4f}')
    
    if dist > tolerance:
        conv_flag = -1
        return None, None, None, conv_flag
    
    # 计算由方程(25)隐含的最优债务政策
    pol_debt, pol_kp, pol_kp_ind, val = fun_pol_update(val, val_unc, pol_bp_unc,
                                                       pol_kp_unc, pol_kp_ind_con,
                                                       profit_mat, B_hat, k_grid, b_grid,
                                                       q, theta, delta)
    
    # 计算进入和退出政策
    pol_entry, pol_exit, pol_exit_forced, pol_exit_vol = \
        fun_entry_exit(val, profit_mat, b_grid, k_grid, theta, delta, cost_e)
    
    # 插值进入/退出
    pol_entry, pol_exit = interp_entry_exit(pol_entry, pol_exit, b_grid, val,
                                           profit_mat, par)
    
    # 验证
    if not np.all(np.isfinite(b_grid)):
        print('警告：b_grid不是有限的')
        conv_flag = -1
        return None, None, None, conv_flag
    
    if not np.all(np.isfinite(val)):
        print('警告：val不是有限的')
        conv_flag = -1
        return None, None, None, conv_flag
    
    if not np.all(np.isfinite(pol_debt)):
        print('警告：pol_debt不是有限的')
        conv_flag = -1
        return None, None, None, conv_flag
    
    if not np.all(np.isfinite(pol_exit)):
        print('警告：pol_exit不是有限的')
        conv_flag = -1
        return None, None, None, conv_flag
    
    if not np.all(np.isfinite(pol_entry)):
        print('警告：pol_entry不是有限的')
        conv_flag = -1
        return None, None, None, conv_flag
    
    # 进入者的(k,b,x)初始分布（草稿中的\Phi）
    # 注意：k,b,x的分布彼此独立。
    # 进入者从两个非退化分布中抽取(k,x)：prob_k（Pareto）和x0_prob（对数正态）。
    # b0基于初始债务资本比par.bk0计算
    phi_dist = gen_phi_dist(bk0_vec, bk0_prob, k_grid, b_grid, x0_prob, prob_k)
    
    # 将解打包到字典中
    sol = pack_to_struct(
        V1=V1, val=val, pol_kp_ind=pol_kp_ind, pol_kp=pol_kp, pol_kp_unc=pol_kp_unc,
        pol_debt=pol_debt, pol_exit=pol_exit, pol_exit_forced=pol_exit_forced,
        pol_exit_vol=pol_exit_vol, pol_entry=pol_entry, val_unc=val_unc,
        val0_unc=val0_unc, profit_mat=profit_mat, x_tilde_val=x_tilde_val,
        b_tilde=b_tilde, wage=wage, kp_bar=kp_bar, B_hat=B_hat
    )
    
    # 输出检查
    if not isinstance(sol, dict):
        raise TypeError('输出<sol>必须是字典')
    
    return sol, b_grid, phi_dist, conv_flag

