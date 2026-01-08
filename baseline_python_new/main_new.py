"""
主程序 - Rescue Policies for Small Businesses During the Covid-19 Recession
使用修复后的代码版本（带代码版本检查）

论文标题: "Rescue Policies for Small Businesses During the Covid-19 Recession"
作者: Alessandro Di Nola, Leo Kaas, Haomin Wang
期刊: Review of Economic Dynamics

这个主脚本调用<fun_steady_state>来计算大流行前的稳态模型。
然后调用<fun_transition>来计算在t=1时发生一期疫情冲击后经济的转移动态。
注意：代码中的t=1对应草稿中的t=0。

本版本使用修复后的代码，并在运行时检查是否使用了旧代码。
"""
import numpy as np
import sys
import os
import pickle
import time
import importlib
import inspect
from datetime import datetime

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'sub'))

# ============================================================
# 代码版本检查函数
# ============================================================
def check_sub_aggregates_code_version():
    """
    检查sub_aggregates_onestep是否使用了旧代码
    
    返回:
        dict: 包含检查结果的字典
            - has_old_code: bool, 是否包含旧代码
            - has_new_code: bool, 是否包含新代码
            - status: str, 状态描述
            - module_file: str, 模块文件路径
    """
    result = {
        'has_old_code': False,
        'has_new_code': False,
        'status': 'unknown',
        'module_file': None
    }
    
    try:
        # 清除缓存
        if 'sub_aggregates_onestep' in sys.modules:
            del sys.modules['sub_aggregates_onestep']
        
        # 重新加载模块
        import sub_aggregates_onestep
        importlib.reload(sub_aggregates_onestep)
        
        # 获取模块源代码
        module_src = inspect.getsource(sub_aggregates_onestep.sub_aggregates_onestep)
        module_file = inspect.getfile(sub_aggregates_onestep.sub_aggregates_onestep)
        
        result['module_file'] = module_file
        
        # 检查是否包含旧代码
        has_old = '(A * x_grid)' in module_src
        # 检查是否包含新代码
        has_new = 'x_val = np.tile(x_grid' in module_src and '(A * x_grid)' not in module_src
        
        result['has_old_code'] = has_old
        result['has_new_code'] = has_new
        
        if has_old:
            result['status'] = 'OLD_CODE_DETECTED'
        elif has_new:
            result['status'] = 'NEW_CODE_OK'
        else:
            result['status'] = 'UNKNOWN'
            
    except Exception as e:
        result['status'] = f'ERROR: {str(e)}'
    
    return result

# ============================================================
# 程序开始时的代码版本检查
# ============================================================
print("="*70)
print("代码版本检查")
print("="*70)

# 清除所有Python缓存
import shutil
import glob

cache_count = 0
for cache_dir in glob.glob('**/__pycache__', recursive=True):
    if os.path.isdir(cache_dir):
        shutil.rmtree(cache_dir)
        cache_count += 1

for pyc_file in glob.glob('**/*.pyc', recursive=True):
    if os.path.isfile(pyc_file):
        os.remove(pyc_file)
        cache_count += 1

if cache_count > 0:
    print(f"[缓存] 已清除 {cache_count} 个缓存项")

# 检查代码版本
check_result = check_sub_aggregates_code_version()

print("\n[代码版本检查结果]")
print("-"*70)
print(f"模块文件: {check_result['module_file']}")
print(f"包含旧代码 (A * x_grid): {check_result['has_old_code']}")
print(f"包含新代码 (x_grid only): {check_result['has_new_code']}")
print(f"状态: {check_result['status']}")

if check_result['has_old_code']:
    print("\n" + "!"*70)
    print("警告: 检测到旧代码！")
    print("sub_aggregates_onestep模块仍在使用旧代码 (A * x_grid)")
    print("这可能导致加总值计算错误（负值或异常大的值）")
    print("\n解决方案:")
    print("  1. 确认文件 sub/sub_aggregates_onestep.py 第56行应为:")
    print("     x_val = np.tile(x_grid[np.newaxis, np.newaxis, :], (nk, nb, 1))")
    print("  2. 删除所有 __pycache__ 目录")
    print("  3. 重启Python进程和IDE")
    print("!"*70)
    print("\n是否继续运行？(y/n): ", end='')
    # 注意：这里不等待用户输入，直接继续运行，但会打印警告
    print("继续运行（但结果可能不正确）")
elif check_result['has_new_code']:
    print("\n✓ 代码版本正常，使用修复后的代码")
    print("可以安全运行程序")
else:
    print("\n? 无法确定代码版本，请手动检查")

print("="*70)
print()

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
log_file = 'steady_state_iterations_new.log'
with open(log_file, 'w', encoding='utf-8') as f:
    f.write('='*80 + '\n')
    f.write('稳态计算迭代日志 (新版本 - 带代码检查)\n')
    f.write('='*80 + '\n')
    f.write(f'开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    f.write(f'Fortran 模块: {vfi_core.__file__}\n')
    f.write(f'代码版本检查: {check_result["status"]}\n')
    f.write('='*80 + '\n\n')

from set_parameters import set_parameters
from fun import Fun

print('Replication of Di Nola, Kaas and Wang (2023)')
print('Using Fixed Code Version with Code Check')
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
par['steady_state_file'] = 'steady_state_results_new.pkl'  # 稳态结果文件名（新版本）

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
FAST_MODE = False  # 设置为 False 使用与MATLAB一致的设置

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
        print("计算稳态模型 (使用修复后的代码)")
        print("="*50)
        print("注意：将重新计算稳态，使用baseline目录的参数文件")
        print(f"参数文件目录: {par.get('InpDir', 'N/A')}")
        print()
        
        # 再次检查代码版本（在计算前）
        print("\n" + "="*70)
        print("[计算前代码版本检查]")
        print("="*70)
        check_result_before = check_sub_aggregates_code_version()
        if check_result_before['has_old_code']:
            print("  [警告] 检测到旧代码！计算结果可能不正确！")
        elif check_result_before['has_new_code']:
            print("  [OK] 代码版本正常，可以安全计算")
        else:
            print("  [未知] 无法确定代码版本")
        print("="*70)
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
                
                # 计算后再次检查代码版本
                print("\n" + "="*70)
                print("[计算后代码版本检查]")
                print("="*70)
                check_result_after = check_sub_aggregates_code_version()
                if check_result_after['has_old_code']:
                    print("  [警告] 检测到旧代码！计算结果可能不正确！")
                elif check_result_after['has_new_code']:
                    print("  [OK] 代码版本正常")
                else:
                    print("  [未知] 无法确定代码版本")
                print("="*70)
                print()
                
                if par.get('verbose', 0) >= 1:
                    print(f"\n稳态结果摘要：")
                    if agg is not None:
                        for key, value in agg.items():
                            if isinstance(value, (int, float, np.number)):
                                print(f"  {key}: {value:.6f}")
                
                # 保存稳态结果
                if par.get('save_steady_state', True):
                    try:
                        steady_state_results = {
                            'sol': sol,
                            'agg': agg,
                            'b_grid': b_grid,
                            'distribS': distribS,
                            'prices': prices,
                            'model_mom': model_mom,
                            'par': par,
                            'flag_ss': flag_ss,
                            'computation_time': ss_elapsed_time,
                            'version': 'new_with_check',
                            'code_check_before': check_result_before,
                            'code_check_after': check_result_after,
                        }
                        filename = par.get('steady_state_file', 'steady_state_results_new.pkl')
                        with open(filename, 'wb') as f:
                            pickle.dump(steady_state_results, f)
                        print(f"\n稳态结果已保存到: {filename}")
                        print(f"  包含代码版本检查信息")
                        
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
                        
                    except Exception as e:
                        print(f"\n警告：保存稳态结果失败: {e}")
        except Exception as e:
            print(f"\n错误：稳态计算失败！")
            print(f"错误信息: {e}")
            import traceback
            traceback.print_exc()
    
    elif do_calib == 1:
        # 1 = 稳态+转移动态
        print("\n转移动态计算功能待实现...")
    
    else:
        print(f"\n警告：do_calib = {do_calib} 暂未实现")
    
    # 总耗时
    total_elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print(f"[性能] 总计算耗时: {total_elapsed_time:.2f} 秒 ({total_elapsed_time/60:.2f} 分钟)")
    print("="*60)

