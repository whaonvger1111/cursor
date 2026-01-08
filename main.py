"""
主程序 - Rescue Policies for Small Businesses During the Covid-19 Recession
这是MATLAB main.m的Python转换版本

论文标题: "Rescue Policies for Small Businesses During the Covid-19 Recession"
作者: Alessandro Di Nola, Leo Kaas, Haomin Wang
期刊: Review of Economic Dynamics

这个主脚本调用<fun_steady_state>来计算大流行前的稳态模型。
然后调用<fun_transition>来计算在t=1时发生一期疫情冲击后经济的转移动态。
注意：代码中的t=1对应草稿中的t=0。
"""
import numpy as np
import sys
import os
import pickle
import time
from datetime import datetime

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

# 初始化日志文件
log_file = 'steady_state_iterations.log'
with open(log_file, 'w', encoding='utf-8') as f:
    f.write('='*80 + '\n')
    f.write('稳态计算迭代日志\n')
    f.write('='*80 + '\n')
    f.write(f'开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    f.write('='*80 + '\n\n')

from set_parameters import set_parameters
from fun import Fun

print('Replication of Di Nola, Kaas and Wang (2023)')
print(' ')

# 全局变量
obj_smm_best = None
obj_tran_best = None

# 设置标志
par = {}
par['do_calib'] = 0  # 0 = 稳态,image.png
# 1 = 稳态+转移动态,
# 2 = 校准稳态,
# 3 = 校准转移动态冲击
# 4 = 通过改变补助水平最大化转移动态福利
# 5 = 仅转移动态（从文件加载稳态结果）

par['load_steady_state'] = False  # True = 尝试从文件加载稳态结果，False = 重新计算（强制重新计算以应用修复）
par['save_steady_state'] = True  # True = 保存稳态结果到文件
par['steady_state_file'] = 'steady_state_results.pkl'  # 稳态结果文件名

par['grant_flag'] = 1  # 0 = 无补助; 1 = 基准补助（均匀）; 2 = 按规模定向补助
# 3 = 均匀补助大; 4 = 均匀补助小
# 5 = eta_g==eta_i（只有受冲击企业获得补助）
# 6 = eta_g==eta_i（只有受冲击企业获得补助），大补助
# 7 = eta_g==eta_i（只有受冲击企业获得补助），小补助

par['grant_target'] = 0  # 0 = 补助无定向（基准）;
#                       1 = 补助定向到受冲击企业，一些未受冲击企业也获得补助;
#                       2 = 精简定向：只有受冲击企业获得补助。

par['InpDir'] = os.path.join('inputs')  # 读取参数的文件夹
par['TabDir'] = 'tables'
do_save = 1  # 标志 0/1 保存图为png和mat文件
par['do_table'] = 1  # 标志 0/1 在屏幕上写入表
par['do_tex'] = 0  # 标志 0/1 写入tex表（仅当do_table=1时）
par['verbose'] = 1  # 标志 0/1/2: 0 完全不显示, 1=中等, 2=显示所有
par['disp_mu'] = 0  # 标志 0/1 显示mu的迭代
par['disp_tran'] = 1  # 标志 0/1

# 性能优化设置：自动选择最佳加速方案
# 优先级：Fortran > Numba > 纯Python
# 如果Fortran可用，将自动使用；否则使用Numba
par['use_numba'] = True  # 启用Numba JIT编译加速（Fortran不可用时的后备）
par['use_fortran'] = True  # 启用Fortran（如果已编译）

# VFI缓存设置：禁用缓存，强制重新计算
par['use_vfi_cache'] = False  # False = 禁用缓存，强制重新计算无约束企业VFI
par['cache_dir'] = 'cache'  # 缓存目录（即使禁用也会保存新结果）
est_algo = 'fminsearch'  # 可用选项: 'simulan','simulannealbnd','fminsearch'
file_params = 'estim_params.txt'  # 保存估计参数名的txt文件名
file_shocks = 'estim_shocks.txt'  # 保存估计冲击名的txt文件名
makeCompleteLatexDocument = 0  # 标志 0/1 生成独立的tex文档

# 设置参数、估计的初始猜测、边界和外生网格
par, guess, bounds, calibNames, dispNames, description, ExoNames = set_parameters(par, file_params)

# 快速测试：降低容差到0.01
par['tol_bhat'] = 0.01  # 固定点B_hat的容差
par['tol_vfi'] = 0.01  # VFI的容差
par['tol_vfi_u'] = 0.01  # 无约束VFI的容差
par['tol_dist'] = 0.01  # 分布的容差
print(f"快速测试模式：容差已降低到0.01")

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
    
    # 根据 do_calib 标志执行相应的计算
    do_calib = par['do_calib']
    
    if do_calib == 0:
        # 0 = 稳态
        print("\n" + "="*50)
        print("计算稳态模型")
        print("="*50)
        try:
            from fun_steady_state import fun_steady_state
            
            sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par = fun_steady_state(par)
            
            if flag_ss < 0:
                print("\n警告：稳态计算失败！")
            else:
                print("\n稳态计算完成！")
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
                            'flag_ss': flag_ss
                        }
                        filename = par.get('steady_state_file', 'steady_state_results.pkl')
                        with open(filename, 'wb') as f:
                            pickle.dump(steady_state_results, f)
                        print(f"\n稳态结果已保存到: {filename}")
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
        load_ss = par.get('load_steady_state', True)  # 从参数读取是否加载稳态
        filename = par.get('steady_state_file', 'steady_state_results.pkl')
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
            try:
                with open(filename, 'rb') as f:
                    ss_results = pickle.load(f)
                
                # 获取保存文件中的网格大小
                ss_nx = ss_results['par'].get('nx', par['nx'])
                ss_nb = ss_results['par'].get('nb', par['nb'])
                ss_nk = ss_results['par'].get('nk', par['nk'])
                
                # 统一使用当前设置的网格大小（正常模式使用较大网格）
                target_nx = par.get('nx', 50)
                target_nb = par.get('nb', 60)
                target_nk = par.get('nk', 70)
                
                # 检查网格大小是否匹配
                if ss_nx == target_nx and ss_nb == target_nb and ss_nk == target_nk:
                    # 网格大小匹配，可以使用加载的稳态结果
                    # 使用保存的稳态结果
                    sol = ss_results['sol']
                    agg = ss_results['agg']
                    b_grid = ss_results['b_grid']
                    distribS = ss_results['distribS']
                    prices = ss_results['prices']
                    model_mom = ss_results['model_mom']
                    par.update(ss_results['par'])  # 更新参数
                    flag_ss = ss_results.get('flag_ss', 0)
                    
                    # 强制使用统一网格大小（在par.update之后，确保覆盖）
                    par['nx'] = target_nx
                    par['nb'] = target_nb
                    par['nk'] = target_nk
                    
                    print(f"成功加载稳态结果从: {filename}")
                    print(f"网格大小匹配: nx={target_nx}, nb={target_nb}, nk={target_nk}")
                    
                    # 强制设置T（覆盖从文件加载的值）
                    par['T'] = 50  # 转移动态长度（降低到50期以加快计算）
                    print(f'[main.py] 强制设置 T = {par["T"]}')
                    
                    # 重新设置冲击数组（因为T改变了，需要重新创建A_small等数组）
                    print('[main.py] 重新设置冲击数组以适应新的T值...')
                    par, bounds_shocks, data_mom_trans, calibWeightsTran = set_shocks(par, file_shocks)
                    par = set_grant(par)  # 重新设置补助参数
                else:
                    # 网格大小不匹配，需要重新计算
                    print(f"注意：稳态文件的网格大小({ss_nx}, {ss_nb}, {ss_nk})与目标网格大小({target_nx}, {target_nb}, {target_nk})不匹配")
                    print(f"将使用统一网格大小({target_nx}, {target_nb}, {target_nk})重新计算稳态...")
                    # 强制使用统一网格大小
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
            print("计算稳态模型")
            print("="*50)
            
            # 如果网格大小改变了，需要重新生成网格
            # k_grid 需要重新生成
            import numpy as np
            par['k_grid'] = np.linspace(par['k_lb'], par['k_ub'], par['nk']).reshape(-1, 1)
            
            # x_grid 会在 fun_steady_state 中重新生成，但我们需要确保参数正确
            # 重新生成 x_grid 和 pi_x（如果需要）
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
            
            sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par = fun_steady_state(par)
            
            if flag_ss < 0:
                print("\n警告：稳态计算失败，无法继续转移动态计算！")
            else:
                print("\n稳态计算完成！")
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
                            'flag_ss': flag_ss
                        }
                        with open(filename, 'wb') as f:
                            pickle.dump(steady_state_results, f)
                        print(f"稳态结果已保存到: {filename}")
                    except Exception as e:
                        print(f"警告：保存稳态结果失败: {e}")
        
        if flag_ss >= 0:
            # 转移动态计算前，参数已在set_parameters.py中设置
            
            # 确保冲击数组维度正确（如果T改变了）
            if 'A_small' in par and par['A_small'].shape[0] != par['T'] + 1:
                print(f'[main.py] 检测到A_small维度不匹配 ({par["A_small"].shape[0]} != {par["T"]+1})，重新设置冲击数组...')
                par, bounds_shocks, data_mom_trans, calibWeightsTran = set_shocks(par, file_shocks)
                par = set_grant(par)  # 重新设置补助参数
            
            print("\n" + "="*50)
            print("计算转移动态")
            print("="*50)
            
            agg_tran, path, conv_flag, pol_tran, distrib_tran = fun_transition(
                par, sol, agg, distribS, prices, b_grid)
            
            if conv_flag < 0:
                print("\n警告：转移动态计算未收敛！")
            else:
                print("\n转移动态计算完成！")
    
    elif do_calib == 2:
        # 2 = 校准稳态
        print("\n" + "="*50)
        print("校准稳态参数")
        print("="*50)
        from fun_obj import fun_obj
        
        print(f"使用算法: {est_algo}")
        print(f"初始猜测参数数量: {len(calibNames)}")
        
        # 调用目标函数进行校准
        obj_smm, sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par = fun_obj(
            guess, par, bounds, calibNames, data_mom, targetNames, calibWeights,
            description, dispNames, targetNames_long)
        
        if flag_ss < 0:
            print("\n警告：校准失败！")
        else:
            print(f"\n校准完成！目标函数值: {obj_smm:.6f}")
    
    elif do_calib == 3:
        # 3 = 校准转移动态冲击
        print("\n" + "="*50)
        print("校准转移动态冲击")
        print("="*50)
        from fun_calib_transition import fun_calib_transition
        
        # 这里需要设置初始冲击猜测值
        # 暂时使用占位符
        print("警告：转移动态冲击校准需要实现优化算法")
    
    elif do_calib == 4:
        # 4 = 通过改变补助水平最大化转移动态福利
        print("\n" + "="*50)
        print("最大化转移动态福利（通过改变补助水平）")
        print("="*50)
        print("警告：此功能需要实现优化算法")
    
    elif do_calib == 5:
        # 5 = 仅转移动态（从文件加载稳态结果）
        print("\n" + "="*50)
        print("仅计算转移动态（从文件加载稳态结果）")
        print("="*50)
        from fun_transition import fun_transition
        
        filename = par.get('steady_state_file', 'steady_state_results.pkl')
        try:
            with open(filename, 'rb') as f:
                ss_results = pickle.load(f)
            
            # 获取保存文件中的网格大小
            ss_nx = ss_results['par'].get('nx', par['nx'])
            ss_nb = ss_results['par'].get('nb', par['nb'])
            ss_nk = ss_results['par'].get('nk', par['nk'])
            
            # 统一使用当前设置的网格大小（正常模式使用较大网格）
            target_nx = par.get('nx', 50)
            target_nb = par.get('nb', 60)
            target_nk = par.get('nk', 70)
            
            # 检查网格大小是否匹配
            if ss_nx == target_nx and ss_nb == target_nb and ss_nk == target_nk:
                # 网格大小匹配，可以使用加载的稳态结果
                sol = ss_results['sol']
                agg = ss_results['agg']
                b_grid = ss_results['b_grid']
                distribS = ss_results['distribS']
                prices = ss_results['prices']
                par.update(ss_results['par'])  # 更新参数
                flag_ss = ss_results.get('flag_ss', 0)
                
                # 强制设置网格大小和T（确保使用统一网格大小）
                par['nx'] = target_nx
                par['nb'] = target_nb
                par['nk'] = target_nk
                par['T'] = 50  # 转移动态长度（降低到50期以加快计算）
                print(f"成功加载稳态结果从: {filename}")
                print(f'使用统一网格大小: nx={target_nx}, nb={target_nb}, nk={target_nk}')
                print(f'[main.py] 强制设置 T = {par["T"]}')
            else:
                # 网格大小不匹配，无法使用保存的稳态结果
                print(f"错误：稳态文件的网格大小({ss_nx}, {ss_nb}, {ss_nk})与目标网格大小({target_nx}, {target_nb}, {target_nk})不匹配")
                print("请先运行 do_calib = 0 或 do_calib = 1 来计算并保存使用统一网格大小的稳态结果")
                flag_ss = -1
            
            if flag_ss < 0:
                print("\n警告：加载的稳态结果标志为失败，无法继续转移动态计算！")
            else:
                print("\n" + "="*50)
                print("计算转移动态")
                print("="*50)
                
                agg_tran, path, conv_flag, pol_tran, distrib_tran = fun_transition(
                    par, sol, agg, distribS, prices, b_grid)
                
                if conv_flag < 0:
                    print("\n警告：转移动态计算未收敛！")
                else:
                    print("\n转移动态计算完成！")
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

