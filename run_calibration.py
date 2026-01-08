"""
运行参数校准脚本
确保市场出清条件满足（K_corp > 0, LHS > 0）
"""
import numpy as np
import sys
import os
import pickle
import signal
from scipy.optimize import minimize

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from set_parameters import set_parameters
from set_targets_ss import set_targets_ss
from fun_obj import fun_obj

# 全局中断标志
_interrupt_requested = False

def _signal_handler(signum, frame):
    """信号处理器，用于捕获 Ctrl+C"""
    global _interrupt_requested
    _interrupt_requested = True
    print("\n\n收到中断信号 (Ctrl+C)，正在安全退出...")
    print("请稍候，正在清理资源...")

# 定义目标函数包装器
def objective_wrapper(x, par_local, bounds_local, calibNames_local, data_mom_local, 
                     targetNames_local, calibWeights_local, description_local, 
                     dispNames_local, targetNames_long_local):
    """目标函数包装器，用于scipy.optimize"""
    global _interrupt_requested
    
    # 检查是否请求中断
    if _interrupt_requested:
        raise KeyboardInterrupt("用户请求中断")
    
    try:
        obj_smm, sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par_updated = \
            fun_obj(x, par_local.copy(), bounds_local, calibNames_local, data_mom_local, 
                   targetNames_local, calibWeights_local, description_local, 
                   dispNames_local, targetNames_long_local)
        
        # 打印当前参数值
        print(f'\n当前参数值:')
        for i, name in enumerate(calibNames_local):
            print(f'  {name:12s} = {x[i]:15.10f}')
        
        if agg is not None:
            K_corp = agg.get('K_corp', 0)
            LHS = agg.get('LHS', 0)
            aux = agg.get('aux', 0)
            print(f'\n市场出清检查:')
            print(f'  K_corp = {K_corp:15.6f}')
            print(f'  LHS    = {LHS:15.6f}')
            print(f'  aux    = {aux:15.6f}')
            print(f'  obj_smm = {obj_smm:15.6f}')
        
        return obj_smm
    except Exception as e:
        print(f'错误: {e}')
        return 1e10

if __name__ == '__main__':
    # 设置信号处理器以捕获 Ctrl+C
    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except (AttributeError, ValueError):
        # Windows 上可能不支持某些信号，忽略错误
        pass
    
    print('='*80)
    print('参数校准：确保市场出清条件满足')
    print('='*80)
    print('提示: 按 Ctrl+C 可以中断程序')
    print('')
    
    # 设置参数
    par = {}
    par['do_calib'] = 2  # 校准模式
    par['InpDir'] = os.path.join('inputs')
    par['TabDir'] = 'tables'
    par['do_table'] = 0
    par['do_tex'] = 0
    par['verbose'] = 1
    par['disp_mu'] = 0
    par['disp_tran'] = 0
    
    file_params = 'estim_params.txt'
    
    # 设置参数、估计的初始猜测、边界
    par, guess, bounds, calibNames, dispNames, description, ExoNames = set_parameters(par, file_params)
    
    # 加载稳态的数据矩，设置校准权重
    targetNames, targetNames_long, calibWeights, data_mom = set_targets_ss()
    
    # 备份原始参数文件
    backup_file = os.path.join(par['InpDir'], 'estim_params_backup.txt')
    if os.path.exists(os.path.join(par['InpDir'], file_params)):
        import shutil
        shutil.copy(os.path.join(par['InpDir'], file_params), backup_file)
        print(f'已备份原始参数文件到: {backup_file}')
        print('')
    
    # 将边界从字典转换为向量
    from tools.bounds2vec import bounds2vec
    bounds_vec = bounds2vec(bounds, calibNames)
    lbounds_vec = bounds_vec[:, 0]
    ubounds_vec = bounds_vec[:, 1]
    
    print('='*80)
    print('开始校准...')
    print('='*80)
    print(f'校准参数数量: {len(calibNames)}')
    print(f'参数名称: {calibNames}')
    print(f'初始猜测: {guess.flatten()}')
    print('')
    
    # 确保guess是一维数组
    guess_flat = np.asarray(guess).flatten()
    
    # 使用scipy.optimize.minimize进行优化
    # 方法：L-BFGS-B（支持边界约束）
    print('使用L-BFGS-B算法进行优化...')
    print('')
    
    options = {
        'maxiter': 100,  # 最大迭代次数（完整校准）
        'disp': True,
        'ftol': 1e-4,
        'gtol': 1e-4
    }
    
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
    
    print('')
    print('='*80)
    print('校准完成！')
    print('='*80)
    print(f'优化状态: {result.status}')
    print(f'优化消息: {result.message}')
    print(f'最终目标函数值: {result.fun:.6f}')
    print('')
    
    # 打印最终参数值
    print('最终参数值:')
    for i, name in enumerate(calibNames):
        print(f'  {name:12s} = {result.x[i]:15.10f}')
    
    # 验证最终结果
    print('')
    print('验证最终结果...')
    final_obj, final_sol, final_agg, final_b_grid, final_distribS, final_prices, \
        final_model_mom, final_flag_ss, final_par = \
        fun_obj(result.x, par.copy(), bounds, calibNames, data_mom, targetNames,
               calibWeights, description, dispNames, targetNames_long)
    
    if final_agg is not None:
        K_corp = final_agg.get('K_corp', 0)
        LHS = final_agg.get('LHS', 0)
        aux = final_agg.get('aux', 0)
        print('')
        print('市场出清检查:')
        print(f'  K_corp = {K_corp:15.6f} {"✓" if K_corp > 0 else "✗"}')
        print(f'  LHS    = {LHS:15.6f} {"✓" if LHS > 0 else "✗"}')
        print(f'  aux    = {aux:15.6f} {"✓" if aux > 0 else "✗"}')
        
        if K_corp > 0 and LHS > 0 and aux > 0:
            print('')
            print('✓ 市场出清条件满足！')
        else:
            print('')
            print('✗ 市场出清条件不满足！')
    
    # 保存校准后的参数到文件
    output_file = os.path.join(par['InpDir'], file_params)
    print('')
    print(f'保存校准后的参数到: {output_file}')
    with open(output_file, 'w') as f:
        for i, name in enumerate(calibNames):
            f.write(f'{name}  {result.x[i]:.10f}\n')
    
    print('完成！')

