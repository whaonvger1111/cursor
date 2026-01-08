"""
快速测试校准脚本
运行少量迭代来估算实际校准时间
"""
import numpy as np
import sys
import os
import time
import signal
from scipy.optimize import minimize

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from set_parameters import set_parameters
from set_targets_ss import set_targets_ss
from fun_obj import fun_obj

# 记录函数评估次数和时间（全局变量）
eval_count = 0
eval_times = []

# 全局中断标志
_interrupt_requested = False

def _signal_handler(signum, frame):
    """信号处理器，用于捕获 Ctrl+C"""
    global _interrupt_requested
    _interrupt_requested = True
    print("\n\n收到中断信号 (Ctrl+C)，正在安全退出...")
    print("请稍候，正在清理资源...")

def objective_wrapper(x, par_local, bounds_local, calibNames_local, data_mom_local, 
                     targetNames_local, calibWeights_local, description_local, 
                     dispNames_local, targetNames_long_local):
    """目标函数包装器，记录时间和次数"""
    global eval_count, eval_times, _interrupt_requested
    
    # 初始化变量，避免作用域问题
    elapsed = 0.0
    start_time = time.time()
    obj_smm = 1e10  # 默认返回值
    
    # 检查是否请求中断
    if _interrupt_requested:
        raise KeyboardInterrupt("用户请求中断")
    
    eval_count += 1
    
    try:
        obj_smm, sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par_updated = \
            fun_obj(x, par_local.copy(), bounds_local, calibNames_local, data_mom_local, 
                   targetNames_local, calibWeights_local, description_local, 
                   dispNames_local, targetNames_long_local)
        
        # 打印当前评估信息
        print(f'\n评估 #{eval_count}:')
        print(f'  目标函数值: {obj_smm:.6f}')
        
        if agg is not None:
            K_corp = agg.get('K_corp', 0)
            LHS = agg.get('LHS', 0)
            aux = agg.get('aux', 0)
            print(f'  K_corp = {K_corp:15.6f}')
            print(f'  LHS    = {LHS:15.6f}')
            print(f'  aux    = {aux:15.6f}')
            
            if K_corp > 0 and LHS > 0 and aux > 0:
                print(f'  [OK] 市场出清条件满足')
            else:
                print(f'  [警告] 市场出清条件不满足')
        
    except Exception as e:
        print(f'\n评估 #{eval_count}: 错误 - {e}')
        import traceback
        traceback.print_exc()
    finally:
        # 无论成功还是失败，都记录时间
        elapsed = time.time() - start_time
        eval_times.append(elapsed)
        if elapsed > 0:
            print(f'  时间: {elapsed:.2f}秒')
    
    return obj_smm

if __name__ == '__main__':
    # 设置信号处理器以捕获 Ctrl+C
    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except (AttributeError, ValueError):
        # Windows 上可能不支持某些信号，忽略错误
        pass
    
    print('='*80)
    print('快速测试校准：估算实际校准时间')
    print('='*80)
    print('提示: 按 Ctrl+C 可以中断程序')
    print('')
    
    # 设置参数
    par = {}
    par['do_calib'] = 2  # 校准模式（会自动使用更小的网格和更宽松的容差）
    par['InpDir'] = os.path.join('inputs')
    par['TabDir'] = 'tables'
    par['do_table'] = 0
    par['do_tex'] = 0
    par['verbose'] = 0  # 减少输出以加快速度
    par['disp_mu'] = 0
    par['disp_tran'] = 0
    
    file_params = 'estim_params.txt'
    
    # 设置参数、估计的初始猜测、边界
    par, guess, bounds, calibNames, dispNames, description, ExoNames = set_parameters(par, file_params)
    
    # 加载稳态的数据矩，设置校准权重
    targetNames, targetNames_long, calibWeights, data_mom = set_targets_ss()
    
    print(f'校准参数数量: {len(calibNames)}')
    print(f'参数名称: {calibNames}')
    print('')
    print(f'网格大小（校准模式）:')
    print(f'  nx = {par["nx"]}')
    print(f'  nb = {par["nb"]}')
    print(f'  nk = {par["nk"]}')
    print('')
    print(f'容差设置（校准模式）:')
    print(f'  tol_bhat = {par["tol_bhat"]}')
    print(f'  tol_vfi = {par["tol_vfi"]}')
    print(f'  tol_vfi_u = {par["tol_vfi_u"]}')
    print(f'  tol_dist = {par["tol_dist"]}')
    print(f'  n_howard = {par["n_howard"]}')
    print('')
    
    # 将边界从字典转换为向量
    from tools.bounds2vec import bounds2vec
    bounds_vec = bounds2vec(bounds, calibNames)
    lbounds_vec = bounds_vec[:, 0]
    ubounds_vec = bounds_vec[:, 1]
    
    # 确保guess是一维数组
    guess_flat = np.asarray(guess).flatten()
    
    print('='*80)
    print('开始快速测试（运行5次迭代）...')
    print('='*80)
    print('')
    
    # 使用scipy.optimize.minimize进行优化
    # 方法：L-BFGS-B（支持边界约束）
    options = {
        'maxiter': 5,  # 只运行5次迭代进行测试
        'disp': True,
        'ftol': 1e-3,  # 放宽收敛条件
        'gtol': 1e-3,
        'maxfun': 50,  # 最大函数评估次数
    }
    
    start_total = time.time()
    
    try:
        result = minimize(
            objective_wrapper,
            guess_flat,
            method='L-BFGS-B',
            bounds=list(zip(lbounds_vec, ubounds_vec)),
            options=options,
            args=(par, bounds, calibNames, data_mom, targetNames, calibWeights, 
                  description, dispNames, targetNames_long)
        )
    except KeyboardInterrupt:
        print('\n\n程序被用户中断')
        print('='*80)
        sys.exit(0)
    
    total_time = time.time() - start_total
    
    print('')
    print('='*80)
    print('快速测试完成！')
    print('='*80)
    print('')
    
    # 统计信息
    if eval_times:
        avg_time = np.mean(eval_times)
        min_time = np.min(eval_times)
        max_time = np.max(eval_times)
        
        print('统计信息:')
        print(f'  总评估次数: {eval_count}')
        print(f'  总耗时: {total_time:.2f}秒 ({total_time/60:.2f}分钟)')
        print(f'  平均每次评估时间: {avg_time:.2f}秒')
        print(f'  最短评估时间: {min_time:.2f}秒')
        print(f'  最长评估时间: {max_time:.2f}秒')
        print('')
        
        # 估算完整校准时间
        print('时间估算（基于当前设置）:')
        print('')
        
        # 假设需要50次迭代，每次迭代平均5次函数评估
        estimated_iterations = 50
        estimated_evals_per_iter = 5
        estimated_total_evals = estimated_iterations * estimated_evals_per_iter
        
        estimated_time_minutes = estimated_total_evals * avg_time / 60
        estimated_time_hours = estimated_time_minutes / 60
        
        print(f'  假设需要 {estimated_iterations} 次迭代')
        print(f'  每次迭代平均 {estimated_evals_per_iter} 次函数评估')
        print(f'  预计总评估次数: {estimated_total_evals}')
        print(f'  预计总时间: {estimated_time_minutes:.1f}分钟 ({estimated_time_hours:.2f}小时)')
        print('')
        
        # 不同场景的估算
        print('不同场景的时间估算:')
        scenarios = [
            (20, 3, "乐观"),
            (50, 5, "正常"),
            (100, 10, "困难")
        ]
        
        for iterations, evals_per_iter, name in scenarios:
            total_evals = iterations * evals_per_iter
            time_minutes = total_evals * avg_time / 60
            time_hours = time_minutes / 60
            print(f'  {name:6s}: {iterations:3d}次迭代 × {evals_per_iter}次评估 = {total_evals:4d}次评估 → {time_minutes:6.1f}分钟 ({time_hours:5.2f}小时)')
    
    print('')
    print('当前参数值:')
    for i, name in enumerate(calibNames):
        print(f'  {name:12s} = {result.x[i]:15.10f}')
    
    print('')
    print('='*80)
    print('提示: 如果时间可接受，可以运行完整校准: python run_calibration.py')
    print('='*80)


