"""
主程序 - Rescue Policies for Small Businesses During the Covid-19 Recession
使用 Fortran 混合编程加速版本

论文标题: "Rescue Policies for Small Businesses During the Covid-19 Recession"
作者: Alessandro Di Nola, Leo Kaas, Haomin Wang
期刊: Review of Economic Dynamics

这个主脚本调用<fun_steady_state>来计算大流行前的稳态模型。
然后调用<fun_transition>来计算在t=1时发生一期疫情冲击后经济的转移动态。
注意：代码中的t=1对应草稿中的t=0。

本版本强制使用 Fortran 加速，如果 Fortran 模块不可用将报错。
"""
import numpy as np
import sys
import os
import pickle
import time
from datetime import datetime

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

# ============================================================
# Fortran 模块检查和验证
# ============================================================
print("="*60)
print("Fortran 混合编程版本")
print("="*60)

# 检查 Fortran 模块
FORTran_AVAILABLE = False
try:
    # 添加 fortran 目录到路径
    fortran_dir = os.path.join(os.path.dirname(__file__), 'fortran')
    if fortran_dir not in sys.path:
        sys.path.insert(0, fortran_dir)
    
    import vfi_core
    FORTRAN_AVAILABLE = True
    print("[成功] Fortran 模块已加载")
    print(f"      模块位置: {vfi_core.__file__}")
except ImportError as e:
    print("[错误] Fortran 模块未找到！")
    print(f"      错误信息: {e}")
    print("\n请先编译 Fortran 模块:")
    print("  python fortran/setup_fortran.py")
    print("\n或检查:")
    print("  1. gfortran 是否在 PATH 中")
    print("  2. fortran/vfi_core.pyd 文件是否存在")
    sys.exit(1)

# 检查 Fortran 包装器（必需）
try:
    from sub.sub_V1_onestep_fortran import sub_V1_onestep_fortran
    from sub.sub_Bhat_onestep_fortran import sub_Bhat_onestep_fortran
    from sub.sub_mu_onestep_fortran import sub_mu_onestep_fortran
    print("[成功] Fortran 包装器已加载")
    
    # 验证Fortran函数是否可用
    required_funcs = ['sub_v1_onestep_fortran', 'sub_bhat_onestep_fortran', 'sub_mu_onestep_fortran']
    available_funcs = [f for f in dir(vfi_core.vfi_core) if not f.startswith('_')]
    missing_funcs = [f for f in required_funcs if f not in available_funcs]
    
    if missing_funcs:
        print(f"[错误] 缺少必需的Fortran函数: {missing_funcs}")
        print(f"       可用函数: {available_funcs}")
        sys.exit(1)
    else:
        print(f"[成功] 所有必需的Fortran函数可用")
        
except ImportError as e:
    print(f"[错误] Fortran 包装器导入失败: {e}")
    print("\n请确保:")
    print("  1. Fortran模块已编译: python fortran/setup_fortran.py")
    print("  2. 所有包装器文件存在")
    sys.exit(1)

# 检查 Numba（作为参考，但不使用）
try:
    import numba
    NUMBA_AVAILABLE = True
    print("[信息] Numba 已安装（本版本不使用）")
except ImportError:
    NUMBA_AVAILABLE = False
    print("[信息] Numba 未安装（本版本不需要）")

print("="*60)
print()

# 初始化日志文件
log_file = 'steady_state_iterations_fortran.log'
with open(log_file, 'w', encoding='utf-8') as f:
    f.write('='*80 + '\n')
    f.write('稳态计算迭代日志 (Fortran 版本)\n')
    f.write('='*80 + '\n')
    f.write(f'开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    f.write(f'Fortran 模块: {vfi_core.__file__}\n')
    f.write('='*80 + '\n\n')

from set_parameters import set_parameters
from fun import Fun

print('Replication of Di Nola, Kaas and Wang (2023)')
print('Using Fortran Acceleration')
print(' ')

# 全局变量
obj_smm_best = None
obj_tran_best = None

# 设置标志
par = {}
par['do_calib'] = 0  # 0 = 稳态
# 1 = 稳态+转移动态,
# 2 = 校准稳态,
# 3 = 校准转移动态冲击
# 4 = 通过改变补助水平最大化转移动态福利
# 5 = 仅转移动态（从文件加载稳态结果）

# 使用baseline目录中的参数文件（但不使用MATLAB稳态结果，重新计算）
baseline_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'baseline')

par['load_steady_state'] = False  # False = 重新计算稳态，不使用已保存的结果
par['save_steady_state'] = True  # True = 保存稳态结果到文件
par['steady_state_file'] = 'steady_state_results_fortran.pkl'  # 稳态结果文件名（Fortran版本）

par['grant_flag'] = 1  # 0 = 无补助; 1 = 基准补助（均匀）; 2 = 按规模定向补助
# 3 = 均匀补助大; 4 = 均匀补助小
# 5 = eta_g==eta_i（只有受冲击企业获得补助）
# 6 = eta_g==eta_i（只有受冲击企业获得补助），大补助
# 7 = eta_g==eta_i（只有受冲击企业获得补助），小补助

par['grant_target'] = 0  # 0 = 补助无定向（基准）;
#                       1 = 补助定向到受冲击企业，一些未受冲击企业也获得补助;
#                       2 = 精简定向：只有受冲击企业获得补助。

# 使用baseline目录中的参数文件
baseline_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'baseline')
par['InpDir'] = os.path.join(baseline_dir, 'inputs')  # 从baseline目录读取参数
par['TabDir'] = 'tables'
do_save = 1  # 标志 0/1 保存图为png和mat文件
par['do_table'] = 1  # 标志 0/1 在屏幕上写入表
par['do_tex'] = 0  # 标志 0/1 写入tex表（仅当do_table=1时）

print(f"[配置] 使用baseline目录的参数文件")
print(f"  参数目录: {par['InpDir']}")
# ============================================================
# 快速模式设置（先定义）
# ============================================================
FAST_MODE = True  # 设置为 True 启用快速模式

par['verbose'] = 1  # 标志 0/1/2: 0 完全不显示, 1=中等, 2=显示所有
par['disp_mu'] = 0  # 标志 0/1 显示mu的迭代
par['disp_tran'] = 1  # 标志 0/1

# ============================================================
# 性能优化设置：强制使用 Fortran
# ============================================================
par['use_fortran'] = True   # 强制启用 Fortran
par['use_numba'] = False    # 禁用 Numba（强制使用 Fortran）

print("[配置] 强制使用 Fortran 加速")
print(f"[配置] USE_FORTRAN = {par['use_fortran']}")
print(f"[配置] USE_NUMBA = {par['use_numba']}")
print()

# VFI缓存设置：永久禁用缓存，强制重新计算
par['use_vfi_cache'] = False  # False = 禁用缓存，强制重新计算（永久禁用）
par['cache_dir'] = 'cache'  # 缓存目录（已禁用，不会使用）
est_algo = 'fminsearch'  # 可用选项: 'simulan','simulannealbnd','fminsearch'
file_params = 'estim_params.txt'  # 保存估计参数名的txt文件名
file_shocks = 'estim_shocks.txt'  # 保存估计冲击名的txt文件名
makeCompleteLatexDocument = 0  # 标志 0/1 生成独立的tex文档

# 设置参数、估计的初始猜测、边界和外生网格
par, guess, bounds, calibNames, dispNames, description, ExoNames = set_parameters(par, file_params)

# ============================================================
# 确保参数与MATLAB完全一致（从MATLAB日志文件中的最终取值）
# ============================================================
# 从MATLAB baseline/steady_state_iterations.log中的校准参数值
par['mass'] = 0.0450000000  # MATLAB最终值
par['fixcost1'] = 0.1652544033  # MATLAB最终值
par['fixcost2'] = 0.0047081982  # MATLAB最终值
par['theta'] = 0.9094588315  # MATLAB最终值
par['psi'] = 0.0039413875  # MATLAB最终值
par['k_alpha'] = 0.4458454251  # MATLAB最终值
par['x0'] = 1.0743375933  # MATLAB最终值
par['epsx'] = 0.0983399600  # MATLAB最终值（如果存在）
par['rhox'] = 0.9572858171  # MATLAB最终值
par['zeta'] = 23.4199308730  # MATLAB最终值

if par.get('verbose', 0) >= 1:
    print("\n" + "="*60)
    print("参数已设置为与MATLAB完全一致")
    print("="*60)
    print(f"  mass = {par['mass']}")
    print(f"  theta = {par['theta']}")
    print(f"  psi = {par['psi']}")
    print(f"  fixcost1 = {par['fixcost1']}")
    print(f"  fixcost2 = {par['fixcost2']}")
    print(f"  k_alpha = {par['k_alpha']}")
    print(f"  x0 = {par['x0']}")
    print(f"  rhox = {par['rhox']}")
    print(f"  zeta = {par['zeta']}")
    print("="*60 + "\n")

# ============================================================
# 参数设置：与MATLAB保持一致
# ============================================================
FAST_MODE = False  # False = 使用与MATLAB一致的容差和格点（默认）
                   # True = 快速模式（放宽容差以加速计算）

# 默认设置：不收敛时退出并报错
par['test_mode'] = False  # False = 不收敛时退出并报错（推荐）
                          # True = 不收敛时继续运行（仅用于测试，不推荐）

if FAST_MODE:
    print("\n" + "="*60)
    print("[快速模式] 放宽收敛容差以加速计算")
    print("="*60)
    print("  警告：精度会略微降低，但速度显著提升（目标：5分钟内完成）")
    print()
    
    # 放宽VFI容差（从1e-9放宽到1e-4，减少迭代次数）
    par['tol_vfi'] = 1e-4      # MATLAB: 1e-9
    par['tol_vfi_u'] = 1e-4    # MATLAB: 1e-9
    par['tol_bhat'] = 1e-5     # MATLAB: 1e-9
    
    # 减少Howard迭代次数（从50减少到10，每次迭代快5倍）
    par['n_howard'] = 10       # MATLAB: 50
    
    # 放宽分布容差（从1e-6放宽到1e-3）
    par['tol_dist'] = 1e-3     # MATLAB: 1e-6
    
    # 修改最大迭代次数
    par['max_iter'] = 1000     # MATLAB: 4000
    par['maxiter_dist'] = 1000 # MATLAB: 10000
    
    # 启用测试模式：不收敛时继续运行
    par['test_mode'] = False   # False = 不收敛时退出并报错（推荐）
                                # True = 不收敛时继续运行（仅用于测试，不推荐）
    
    print(f"  修改后的容差设置:")
    print(f"    tol_vfi = {par['tol_vfi']:.0e} (MATLAB: 1e-9)")
    print(f"    tol_vfi_u = {par['tol_vfi_u']:.0e} (MATLAB: 1e-9)")
    print(f"    tol_bhat = {par['tol_bhat']:.0e} (MATLAB: 1e-9)")
    print(f"    tol_dist = {par['tol_dist']:.0e} (MATLAB: 1e-6)")
    print(f"    n_howard = {par['n_howard']} (MATLAB: 50)")
    print(f"    max_iter = {par['max_iter']} (MATLAB: 4000)")
    print(f"    maxiter_dist = {par['maxiter_dist']} (MATLAB: 10000)")
    print(f"    test_mode = {par.get('test_mode', False)} (MATLAB: False)")
    print("="*60)
    print()
else:
    # 使用与MATLAB完全一致的设置
    print("\n" + "="*60)
    print("[MATLAB一致模式] 使用与MATLAB相同的格点和容差")
    print("="*60)
    print("  格点设置:")
    print(f"    nx = {par['nx']} (生产率网格)")
    print(f"    nb = {par['nb']} (债务网格)")
    print(f"    nk = {par['nk']} (资本网格)")
    print()
    print("  容差设置:")
    print(f"    tol_vfi = {par['tol_vfi']:.0e}")
    print(f"    tol_vfi_u = {par['tol_vfi_u']:.0e}")
    print(f"    tol_bhat = {par['tol_bhat']:.0e}")
    print(f"    tol_dist = {par['tol_dist']:.0e}")
    print(f"    n_howard = {par['n_howard']}")
    print(f"    max_iter = {par['max_iter']}")
    print(f"    maxiter_dist = {par['maxiter_dist']}")
    print("="*60)
    print()

# 导入设置函数
from set_targets_ss import set_targets_ss
from set_shocks import set_shocks
from set_grant import set_grant

# 加载稳态的数据矩，设置校准权重
targetNames, targetNames_long, calibWeights, data_mom = set_targets_ss()

# 设置冲击
par, bounds_shocks, data_mom_trans, calibWeightsTran = set_shocks(par, file_shocks)

# 设置补助和救援政策参数Xp和eta用于转移动态
par = set_grant(par)

if __name__ == '__main__':
    
    # 记录开始时间（用于性能监控）
    start_time = time.time()
    
    # 根据 do_calib 标志执行相应的计算
    do_calib = par['do_calib']
    
    if do_calib == 0:
        # 0 = 稳态
        print("\n" + "="*50)
        print("计算稳态模型 (使用 Fortran 加速)")
        print("="*50)
        print("注意：将重新计算稳态，使用baseline目录的参数文件")
        print(f"参数文件目录: {par.get('InpDir', 'N/A')}")
        print()
        try:
            from fun_steady_state import fun_steady_state
            
            ss_start_time = time.time()
            sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par = fun_steady_state(par)
            ss_elapsed_time = time.time() - ss_start_time
            
            if flag_ss < 0:
                print("\n警告：稳态计算失败！")
            else:
                print(f"\n稳态计算完成！")
                print(f"[性能] 稳态计算耗时: {ss_elapsed_time:.2f} 秒 ({ss_elapsed_time/60:.2f} 分钟)")
                if par.get('verbose', 0) >= 1:
                    print(f"\n稳态结果摘要：")
                    if agg is not None:
                        for key, value in agg.items():
                            if isinstance(value, (int, float, np.number)):
                                print(f"  {key}: {value:.6f}")
                
                # 保存稳态结果（包含分布和所有中间结果）
                if par.get('save_steady_state', True):
                    try:
                        # 加载VFI中间结果（如果存在）
                        vfi_intermediate = {}
                        vfi_intermediate_file = 'vfi_intermediate_results.pkl'
                        if os.path.exists(vfi_intermediate_file):
                            with open(vfi_intermediate_file, 'rb') as f:
                                vfi_intermediate = pickle.load(f)
                            print(f"\n已加载VFI中间结果: {vfi_intermediate_file}")
                        
                        # 收集收敛信息
                        vfi_conv_info = sol.get('convergence_info', {}) if sol else {}
                        dist_conv_info = distribS.get('convergence_info', {}) if distribS else {}
                        
                        convergence_summary = {
                            'steady_state': {
                                'converged': flag_ss >= 0,
                                'flag_ss': flag_ss,
                            },
                            'vfi': {
                                'overall_converged': vfi_conv_info.get('overall_converged', False),
                                'conv_flag': vfi_conv_info.get('conv_flag', 'N/A'),
                                'unconstrained_vfi': vfi_conv_info.get('unconstrained_vfi', {}),
                                'bhat_fixed_point': vfi_conv_info.get('bhat_fixed_point', {}),
                                'constrained_vfi': vfi_conv_info.get('constrained_vfi', {}),
                            },
                            'distribution': dist_conv_info,
                        }
                        
                        steady_state_results = {
                            'sol': sol,
                            'agg': agg,
                            'b_grid': b_grid,
                            'distribS': distribS,  # 包含mu, mu_active, entry_vec等
                            'prices': prices,
                            'model_mom': model_mom,
                            'par': par,
                            'flag_ss': flag_ss,
                            'flag_vf': vfi_intermediate.get('flag_vf', 'N/A'),
                            'flag_dist': distribS.get('flag_mu', 'N/A') if distribS else 'N/A',
                            'computation_time': ss_elapsed_time,
                            'version': 'fortran',
                            # 收敛信息汇总
                            'convergence_summary': convergence_summary,
                            # VFI中间结果
                            'vfi_intermediate': vfi_intermediate,
                            # 分布详细信息
                            'mu': distribS.get('mu') if distribS else None,
                            'mu_active': distribS.get('mu_active') if distribS else None,
                            'entry_vec': distribS.get('entry_vec') if distribS else None,
                            # 政策函数
                            'pol_exit': sol.get('pol_exit') if sol else None,
                            'pol_entry': sol.get('pol_entry') if sol else None,
                            'pol_kp_ind': sol.get('pol_kp_ind') if sol else None,
                            'pol_kp': sol.get('pol_kp') if sol else None,
                            'pol_debt': sol.get('pol_debt') if sol else None,
                            # 价值函数
                            'val': sol.get('val') if sol else None,
                            'val_unc': sol.get('val_unc') if sol else None,
                            'val0_unc': sol.get('val0_unc') if sol else None,
                            # B_hat
                            'B_hat': sol.get('B_hat') if sol else None,
                            # phi_dist
                            'phi_dist': vfi_intermediate.get('phi_dist') if vfi_intermediate else None,
                        }
                        filename = par.get('steady_state_file', 'steady_state_results_fortran.pkl')
                        with open(filename, 'wb') as f:
                            pickle.dump(steady_state_results, f)
                        print(f"\n稳态结果已保存到: {filename}")
                        print(f"  包含: sol, agg, b_grid, distribS (mu, mu_active), prices, model_mom, par")
                        print(f"  包含: VFI中间结果, 政策函数, 价值函数, B_hat, phi_dist")
                        print(f"  包含: 收敛信息汇总 (convergence_summary)")
                        
                        # 打印收敛信息摘要
                        print("\n" + "="*60)
                        print("收敛信息摘要")
                        print("="*60)
                        print(f"稳态收敛: {'✓' if flag_ss >= 0 else '✗'} (flag_ss = {flag_ss})")
                        if vfi_conv_info:
                            print(f"\nVFI收敛:")
                            print(f"  总体: {'✓' if vfi_conv_info.get('overall_converged', False) else '✗'}")
                            u_vfi = vfi_conv_info.get('unconstrained_vfi', {})
                            print(f"  无约束VFI: {'✓' if u_vfi.get('converged', False) else '✗'} "
                                  f"(iter={u_vfi.get('iterations', 'N/A')}, "
                                  f"err={u_vfi.get('final_error', 'N/A'):.6e})")
                            bhat = vfi_conv_info.get('bhat_fixed_point', {})
                            print(f"  B_hat固定点: {'✓' if bhat.get('converged', False) else '✗'} "
                                  f"(iter={bhat.get('iterations', 'N/A')}, "
                                  f"err={bhat.get('final_error', 'N/A'):.6e})")
                            c_vfi = vfi_conv_info.get('constrained_vfi', {})
                            print(f"  约束VFI: {'✓' if c_vfi.get('converged', False) else '✗'} "
                                  f"(iter={c_vfi.get('iterations', 'N/A')}, "
                                  f"err={c_vfi.get('final_error', 'N/A'):.6e})")
                        if dist_conv_info:
                            print(f"\n分布收敛: {'✓' if dist_conv_info.get('converged', False) else '✗'} "
                                  f"(iter={dist_conv_info.get('iterations', 'N/A')}, "
                                  f"err={dist_conv_info.get('final_error', 'N/A'):.6e})")
                        print("="*60)
                        
                        # 同时保存为MATLAB格式（如果scipy可用）
                        try:
                            from scipy.io import savemat
                            mat_filename = filename.replace('.pkl', '.mat')
                            # 转换数据结构为MATLAB兼容格式
                            mat_data = {
                                'sol': sol,
                                'agg': agg,
                                'b_grid': b_grid,
                                'distribS': distribS,
                                'prices': prices,
                                'model_mom': model_mom,
                                'par': par,
                                'flag_ss': flag_ss,
                                'flag_vf': vfi_intermediate.get('flag_vf', 0),
                                'flag_dist': distribS.get('flag_mu', 0) if distribS else 0,
                            }
                            savemat(mat_filename, mat_data)
                            print(f"  同时保存为MATLAB格式: {mat_filename}")
                        except ImportError:
                            print("  注意: scipy不可用，未保存MATLAB格式")
                        except Exception as e:
                            print(f"  警告: 保存MATLAB格式失败: {e}")
                        
                        # 打印主要结果摘要
                        print("\n" + "="*60)
                        print("稳态计算主要结果摘要")
                        print("="*60)
                        if prices is not None:
                            print("\n【价格】")
                            print(f"  q (贴现因子):        {prices.get('q', 'N/A'):15.10f}")
                            print(f"  wage (工资):         {prices.get('wage', 'N/A'):15.10f}")
                            print(f"  KL_ratio (资本劳动比): {prices.get('KL_ratio', 'N/A'):15.10f}")
                        
                        if agg is not None:
                            print("\n【加总变量】")
                            print(f"  Mactive (活跃企业):  {agg.get('Mactive', 'N/A'):15.10f}")
                            print(f"  Mentr (进入者):      {agg.get('Mentr', 'N/A'):15.10f}")
                            print(f"  C_agg (总消费):      {agg.get('C_agg', 'N/A'):15.10f}")
                            print(f"  K_corp (企业资本):   {agg.get('K_corp', 'N/A'):15.10f}")
                            print(f"  K_agg (总资本):      {agg.get('K_agg', 'N/A'):15.10f}")
                            print(f"  L_agg (总就业):      {agg.get('L_agg', 'N/A'):15.10f}")
                            print(f"  Y_agg (总产出):      {agg.get('Y_agg', 'N/A'):15.10f}")
                            print(f"  liq (清算率):        {agg.get('liq', 'N/A'):15.10f}")
                            print(f"  entry (进入率):      {agg.get('entry', 'N/A'):15.10f}")
                        
                        if b_grid is not None:
                            print("\n【债务网格】")
                            print(f"  b_grid形状:          {b_grid.shape}")
                            print(f"  b_grid[0,0]:         {b_grid[0, 0]:15.10f}")
                            print(f"  b_grid[-1,-1]:       {b_grid[-1, -1]:15.10f}")
                        
                        print("="*60)
                        
                        # 如果MATLAB结果存在，自动进行比较
                        baseline_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'baseline')
                        matlab_ss_file = os.path.join(baseline_dir, 'mat', 'ss.mat')
                        if os.path.exists(matlab_ss_file):
                            print("\n检测到MATLAB稳态结果文件，是否进行比较？")
                            print("运行以下命令进行比较：")
                            print(f"  python compare_matlab_python_ss.py")
                        else:
                            print(f"\n未找到MATLAB稳态结果文件: {matlab_ss_file}")
                            print("跳过自动比较")
                        
                    except Exception as e:
                        print(f"\n警告：保存稳态结果失败: {e}")
        except Exception as e:
            print(f"\n错误：稳态计算失败！")
            print(f"错误信息: {e}")
            import traceback
            traceback.print_exc()
    
    elif do_calib == 1:
        # 1 = 稳态+转移动态
        from fun_transition import fun_transition
        
        # 尝试加载稳态结果或重新计算
        load_ss = par.get('load_steady_state', True)
        filename = par.get('steady_state_file', 'steady_state_results_fortran.pkl')
        sol = None
        agg = None
        b_grid = None
        distribS = None
        prices = None
        model_mom = None
        flag_ss = -1
        
        if load_ss:
            # 尝试从文件加载稳态结果
            print("\n" + "="*50)
            print("尝试加载稳态结果")
            print("="*50)
            
            # 首先尝试从baseline目录的MATLAB文件加载
            baseline_ss_mat = par.get('baseline_ss_mat', None)
            if baseline_ss_mat and os.path.exists(baseline_ss_mat):
                try:
                    print(f"尝试从MATLAB文件加载: {baseline_ss_mat}")
                    from scipy.io import loadmat
                    mat_data = loadmat(baseline_ss_mat, squeeze_me=True, struct_as_record=False)
                    
                    # 提取MATLAB结构体中的数据
                    # MATLAB文件通常包含sol, agg, b_grid, distribS, prices, model_mom等
                    if 'sol' in mat_data:
                        print("成功从MATLAB文件加载稳态结果")
                        # 注意：MATLAB结构体需要转换为Python字典
                        # 这里需要根据实际MATLAB文件结构进行调整
                        sol = mat_data.get('sol', None)
                        agg = mat_data.get('agg', None)
                        b_grid = mat_data.get('b_grid', None)
                        distribS = mat_data.get('distribS', None)
                        prices = mat_data.get('prices', None)
                        model_mom = mat_data.get('model_mom', None)
                        
                        if sol is not None:
                            flag_ss = 0
                            print("MATLAB稳态结果加载成功！")
                        else:
                            print("警告：MATLAB文件中未找到sol数据，尝试从pickle文件加载")
                            raise ValueError("MATLAB文件格式不匹配")
                    else:
                        print("警告：MATLAB文件中未找到预期的数据结构，尝试从pickle文件加载")
                        raise ValueError("MATLAB文件格式不匹配")
                except Exception as e:
                    print(f"从MATLAB文件加载失败: {e}")
                    print("尝试从pickle文件加载...")
                    baseline_ss_mat = None  # 标记MATLAB加载失败
            
            # 如果MATLAB加载失败，尝试从pickle文件加载
            if baseline_ss_mat is None or not os.path.exists(baseline_ss_mat):
                try:
                    with open(filename, 'rb') as f:
                        ss_results = pickle.load(f)
                    
                    # 获取保存文件中的网格大小
                    ss_nx = ss_results['par'].get('nx', par['nx'])
                    ss_nb = ss_results['par'].get('nb', par['nb'])
                    ss_nk = ss_results['par'].get('nk', par['nk'])
                    
                    # 统一使用当前设置的网格大小
                    target_nx = par.get('nx', 50)
                    target_nb = par.get('nb', 60)
                    target_nk = par.get('nk', 70)
                    
                    # 检查网格大小是否匹配
                    if ss_nx == target_nx and ss_nb == target_nb and ss_nk == target_nk:
                        sol = ss_results['sol']
                        agg = ss_results['agg']
                        b_grid = ss_results['b_grid']
                        distribS = ss_results['distribS']
                        prices = ss_results['prices']
                        model_mom = ss_results['model_mom']
                        par.update(ss_results['par'])
                        flag_ss = ss_results.get('flag_ss', 0)
                        
                        par['nx'] = target_nx
                        par['nb'] = target_nb
                        par['nk'] = target_nk
                        
                        print(f"成功加载稳态结果从: {filename}")
                        print(f"网格大小匹配: nx={target_nx}, nb={target_nb}, nk={target_nk}")
                        
                        par['T'] = 50
                        print(f'[main_fortran.py] 强制设置 T = {par["T"]}')
                        
                        par, bounds_shocks, data_mom_trans, calibWeightsTran = set_shocks(par, file_shocks)
                        par = set_grant(par)
                    else:
                        print(f"注意：稳态文件的网格大小({ss_nx}, {ss_nb}, {ss_nk})与目标网格大小({target_nx}, {target_nb}, {target_nk})不匹配")
                        print(f"将使用统一网格大小({target_nx}, {target_nb}, {target_nk})重新计算稳态...")
                        par['nx'] = target_nx
                        par['nb'] = target_nb
                        par['nk'] = target_nk
                        load_ss = False
                        flag_ss = -1
                except FileNotFoundError:
                    print(f"警告：未找到稳态结果文件 {filename}，将重新计算稳态")
                    load_ss = False
                except Exception as e:
                    print(f"警告：加载稳态结果失败: {e}")
                    print("将重新计算稳态")
                    load_ss = False
        
        if not load_ss or flag_ss < 0:
            # 重新计算稳态
            print("\n" + "="*50)
            print("计算稳态模型 (使用 Fortran 加速)")
            print("="*50)
            
            import numpy as np
            par['k_grid'] = np.linspace(par['k_lb'], par['k_ub'], par['nk']).reshape(-1, 1)
            
            if par.get('x_process', 1) == 1:
                from tools.markovapprox import markovapprox
                par['mean_x'] = (1 - par['rhox']) * np.log(par['x0'])
                par['cover'] = par.get('cover', 3.5)
                Tran, log_x_grid, p, arho, asigma = markovapprox(
                    par['rhox'], par['epsx'], par['mean_x'], 
                    par['cover'], par['nx'], disp_on_screen=False)
                par['pi_x'] = Tran
                par['x_grid'] = np.exp(log_x_grid)
            
            from fun_steady_state import fun_steady_state
            
            ss_start_time = time.time()
            sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par = fun_steady_state(par)
            ss_elapsed_time = time.time() - ss_start_time
            
            if flag_ss < 0:
                print("\n警告：稳态计算失败，无法继续转移动态计算！")
            else:
                print(f"\n稳态计算完成！")
                print(f"[性能] 稳态计算耗时: {ss_elapsed_time:.2f} 秒 ({ss_elapsed_time/60:.2f} 分钟)")
                # 保存稳态结果（包含分布和所有中间结果）
                if par.get('save_steady_state', True):
                    try:
                        # 加载VFI中间结果（如果存在）
                        vfi_intermediate = {}
                        vfi_intermediate_file = 'vfi_intermediate_results.pkl'
                        if os.path.exists(vfi_intermediate_file):
                            with open(vfi_intermediate_file, 'rb') as f:
                                vfi_intermediate = pickle.load(f)
                        
                        # 收集收敛信息
                        vfi_conv_info = sol.get('convergence_info', {}) if sol else {}
                        dist_conv_info = distribS.get('convergence_info', {}) if distribS else {}
                        
                        convergence_summary = {
                            'steady_state': {
                                'converged': flag_ss >= 0,
                                'flag_ss': flag_ss,
                            },
                            'vfi': {
                                'overall_converged': vfi_conv_info.get('overall_converged', False),
                                'conv_flag': vfi_conv_info.get('conv_flag', 'N/A'),
                                'unconstrained_vfi': vfi_conv_info.get('unconstrained_vfi', {}),
                                'bhat_fixed_point': vfi_conv_info.get('bhat_fixed_point', {}),
                                'constrained_vfi': vfi_conv_info.get('constrained_vfi', {}),
                            },
                            'distribution': dist_conv_info,
                        }
                        
                        steady_state_results = {
                            'sol': sol,
                            'agg': agg,
                            'b_grid': b_grid,
                            'distribS': distribS,  # 包含mu, mu_active, entry_vec等
                            'prices': prices,
                            'model_mom': model_mom,
                            'par': par,
                            'flag_ss': flag_ss,
                            'flag_vf': vfi_intermediate.get('flag_vf', 'N/A'),
                            'flag_dist': distribS.get('flag_mu', 'N/A') if distribS else 'N/A',
                            'computation_time': ss_elapsed_time,
                            'version': 'fortran',
                            # 收敛信息汇总
                            'convergence_summary': convergence_summary,
                            # VFI中间结果
                            'vfi_intermediate': vfi_intermediate,
                            # 分布详细信息
                            'mu': distribS.get('mu') if distribS else None,
                            'mu_active': distribS.get('mu_active') if distribS else None,
                            'entry_vec': distribS.get('entry_vec') if distribS else None,
                            # 政策函数
                            'pol_exit': sol.get('pol_exit') if sol else None,
                            'pol_entry': sol.get('pol_entry') if sol else None,
                            'pol_kp_ind': sol.get('pol_kp_ind') if sol else None,
                            'pol_kp': sol.get('pol_kp') if sol else None,
                            'pol_debt': sol.get('pol_debt') if sol else None,
                            # 价值函数
                            'val': sol.get('val') if sol else None,
                            'val_unc': sol.get('val_unc') if sol else None,
                            'val0_unc': sol.get('val0_unc') if sol else None,
                            # B_hat
                            'B_hat': sol.get('B_hat') if sol else None,
                            # phi_dist
                            'phi_dist': vfi_intermediate.get('phi_dist') if vfi_intermediate else None,
                        }
                        with open(filename, 'wb') as f:
                            pickle.dump(steady_state_results, f)
                        print(f"\n稳态结果已保存到: {filename}")
                        print(f"  包含: sol, agg, b_grid, distribS (mu, mu_active), prices, model_mom, par")
                        print(f"  包含: VFI中间结果, 政策函数, 价值函数, B_hat, phi_dist")
                        print(f"  包含: 收敛信息汇总 (convergence_summary)")
                        
                        # 打印收敛信息摘要
                        print("\n" + "="*60)
                        print("收敛信息摘要")
                        print("="*60)
                        print(f"稳态收敛: {'✓' if flag_ss >= 0 else '✗'} (flag_ss = {flag_ss})")
                        if vfi_conv_info:
                            print(f"\nVFI收敛:")
                            print(f"  总体: {'✓' if vfi_conv_info.get('overall_converged', False) else '✗'}")
                            u_vfi = vfi_conv_info.get('unconstrained_vfi', {})
                            print(f"  无约束VFI: {'✓' if u_vfi.get('converged', False) else '✗'} "
                                  f"(iter={u_vfi.get('iterations', 'N/A')}, "
                                  f"err={u_vfi.get('final_error', 'N/A'):.6e})")
                            bhat = vfi_conv_info.get('bhat_fixed_point', {})
                            print(f"  B_hat固定点: {'✓' if bhat.get('converged', False) else '✗'} "
                                  f"(iter={bhat.get('iterations', 'N/A')}, "
                                  f"err={bhat.get('final_error', 'N/A'):.6e})")
                            c_vfi = vfi_conv_info.get('constrained_vfi', {})
                            print(f"  约束VFI: {'✓' if c_vfi.get('converged', False) else '✗'} "
                                  f"(iter={c_vfi.get('iterations', 'N/A')}, "
                                  f"err={c_vfi.get('final_error', 'N/A'):.6e})")
                        if dist_conv_info:
                            print(f"\n分布收敛: {'✓' if dist_conv_info.get('converged', False) else '✗'} "
                                  f"(iter={dist_conv_info.get('iterations', 'N/A')}, "
                                  f"err={dist_conv_info.get('final_error', 'N/A'):.6e})")
                        print("="*60)
                        
                        # 同时保存为MATLAB格式（如果scipy可用）
                        try:
                            from scipy.io import savemat
                            mat_filename = filename.replace('.pkl', '.mat')
                            mat_data = {
                                'sol': sol,
                                'agg': agg,
                                'b_grid': b_grid,
                                'distribS': distribS,
                                'prices': prices,
                                'model_mom': model_mom,
                                'par': par,
                                'flag_ss': flag_ss,
                                'flag_vf': vfi_intermediate.get('flag_vf', 0),
                                'flag_dist': distribS.get('flag_mu', 0) if distribS else 0,
                            }
                            savemat(mat_filename, mat_data)
                            print(f"  同时保存为MATLAB格式: {mat_filename}")
                        except ImportError:
                            print("  注意: scipy不可用，未保存MATLAB格式")
                        except Exception as e:
                            print(f"  警告: 保存MATLAB格式失败: {e}")
                    except Exception as e:
                        print(f"警告：保存稳态结果失败: {e}")
                        import traceback
                        traceback.print_exc()
        
        if flag_ss >= 0:
            # 确保冲击数组维度正确
            if 'A_small' in par and par['A_small'].shape[0] != par['T'] + 1:
                print(f'[main_fortran.py] 检测到A_small维度不匹配，重新设置冲击数组...')
                par, bounds_shocks, data_mom_trans, calibWeightsTran = set_shocks(par, file_shocks)
                par = set_grant(par)
            
            print("\n" + "="*50)
            print("计算转移动态 (使用 Fortran 加速)")
            print("="*50)
            
            tran_start_time = time.time()
            agg_tran, path, conv_flag, pol_tran, distrib_tran = fun_transition(
                par, sol, agg, distribS, prices, b_grid)
            tran_elapsed_time = time.time() - tran_start_time
            
            if conv_flag < 0:
                print("\n警告：转移动态计算未收敛！")
            else:
                print(f"\n转移动态计算完成！")
                print(f"[性能] 转移动态计算耗时: {tran_elapsed_time:.2f} 秒 ({tran_elapsed_time/60:.2f} 分钟)")
    
    elif do_calib == 2:
        # 2 = 校准稳态
        print("\n" + "="*50)
        print("校准稳态参数 (使用 Fortran 加速)")
        print("="*50)
        from fun_obj import fun_obj
        
        print(f"使用算法: {est_algo}")
        print(f"初始猜测参数数量: {len(calibNames)}")
        
        calib_start_time = time.time()
        obj_smm, sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par = fun_obj(
            guess, par, bounds, calibNames, data_mom, targetNames, calibWeights,
            description, dispNames, targetNames_long)
        calib_elapsed_time = time.time() - calib_start_time
        
        if flag_ss < 0:
            print("\n警告：校准失败！")
        else:
            print(f"\n校准完成！目标函数值: {obj_smm:.6f}")
            print(f"[性能] 校准耗时: {calib_elapsed_time:.2f} 秒 ({calib_elapsed_time/60:.2f} 分钟)")
    
    elif do_calib == 3:
        # 3 = 校准转移动态冲击
        print("\n" + "="*50)
        print("校准转移动态冲击 (使用 Fortran 加速)")
        print("="*50)
        from fun_calib_transition import fun_calib_transition
        print("警告：转移动态冲击校准需要实现优化算法")
    
    elif do_calib == 4:
        # 4 = 通过改变补助水平最大化转移动态福利
        print("\n" + "="*50)
        print("最大化转移动态福利（通过改变补助水平）(使用 Fortran 加速)")
        print("="*50)
        print("警告：此功能需要实现优化算法")
    
    elif do_calib == 5:
        # 5 = 仅转移动态（从文件加载稳态结果）
        print("\n" + "="*50)
        print("仅计算转移动态（从文件加载稳态结果）(使用 Fortran 加速)")
        print("="*50)
        from fun_transition import fun_transition
        
        filename = par.get('steady_state_file', 'steady_state_results_fortran.pkl')
        try:
            with open(filename, 'rb') as f:
                ss_results = pickle.load(f)
            
            ss_nx = ss_results['par'].get('nx', par['nx'])
            ss_nb = ss_results['par'].get('nb', par['nb'])
            ss_nk = ss_results['par'].get('nk', par['nk'])
            
            target_nx = par.get('nx', 50)
            target_nb = par.get('nb', 60)
            target_nk = par.get('nk', 70)
            
            if ss_nx == target_nx and ss_nb == target_nb and ss_nk == target_nk:
                sol = ss_results['sol']
                agg = ss_results['agg']
                b_grid = ss_results['b_grid']
                distribS = ss_results['distribS']
                prices = ss_results['prices']
                par.update(ss_results['par'])
                flag_ss = ss_results.get('flag_ss', 0)
                
                par['nx'] = target_nx
                par['nb'] = target_nb
                par['nk'] = target_nk
                par['T'] = 50
                print(f"成功加载稳态结果从: {filename}")
                print(f'使用统一网格大小: nx={target_nx}, nb={target_nb}, nk={target_nk}')
                print(f'[main_fortran.py] 强制设置 T = {par["T"]}')
            else:
                print(f"错误：稳态文件的网格大小({ss_nx}, {ss_nb}, {ss_nk})与目标网格大小({target_nx}, {target_nb}, {target_nk})不匹配")
                print("请先运行 do_calib = 0 或 do_calib = 1 来计算并保存使用统一网格大小的稳态结果")
                flag_ss = -1
            
            if flag_ss < 0:
                print("\n警告：加载的稳态结果标志为失败，无法继续转移动态计算！")
            else:
                print("\n" + "="*50)
                print("计算转移动态 (使用 Fortran 加速)")
                print("="*50)
                
                tran_start_time = time.time()
                agg_tran, path, conv_flag, pol_tran, distrib_tran = fun_transition(
                    par, sol, agg, distribS, prices, b_grid)
                tran_elapsed_time = time.time() - tran_start_time
                
                if conv_flag < 0:
                    print("\n警告：转移动态计算未收敛！")
                else:
                    print(f"\n转移动态计算完成！")
                    print(f"[性能] 转移动态计算耗时: {tran_elapsed_time:.2f} 秒 ({tran_elapsed_time/60:.2f} 分钟)")
        except FileNotFoundError:
            print(f"\n错误：未找到稳态结果文件 {filename}")
            print("请先运行 do_calib = 0 或 do_calib = 1 来计算并保存稳态结果")
        except Exception as e:
            print(f"\n错误：加载稳态结果失败: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print(f"\n警告：未知的 do_calib 值: {do_calib}")
        print("请设置 do_calib 为 0, 1, 2, 3, 4 或 5")
    
    # 总耗时
    total_elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print(f"[性能] 总计算耗时: {total_elapsed_time:.2f} 秒 ({total_elapsed_time/60:.2f} 分钟)")
    print("="*60)

