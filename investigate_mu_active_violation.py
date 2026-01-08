"""
深入调查mu_active违反约束问题
"""
import numpy as np
import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))


def analyze_mu_active_violation():
    """分析mu_active违反约束的详细情况"""
    
    print('='*80)
    print('mu_active违反约束问题深入分析')
    print('='*80)
    print('')
    
    try:
        with open('steady_state_results.pkl', 'rb') as f:
            ss_results = pickle.load(f)
        
        if 'distribS' in ss_results and 'par' in ss_results and 'sol' in ss_results:
            mu_active = ss_results['distribS']['mu_active']
            mu = ss_results['distribS']['mu']
            par = ss_results['par']
            sol = ss_results['sol']
            
            psi = par.get('psi', 0)
            mass = par.get('mass', 0)
            pol_exit = sol['pol_exit']
            pol_entry = sol['pol_entry']
            phi_dist = sol.get('phi_dist', None)
            
            if phi_dist is None:
                print('警告: phi_dist未找到，尝试从par中获取')
                phi_dist = par.get('phi_dist', None)
            
            nx = par['nx']
            nb = par['nb']
            nk = par['nk']
            
            print('1. 基本统计')
            print('-'*80)
            print(f'mu_active总和: {np.sum(mu_active):.6f}')
            print(f'mu总和: {np.sum(mu):.6f}')
            print(f'mu_active / mu = {np.sum(mu_active) / np.sum(mu):.6f}')
            print(f'psi (外生退出率): {psi:.6f}')
            print(f'mass (潜在进入者质量): {mass:.6f}')
            print('')
            
            # 找出所有违反约束的点
            violations = mu_active > mu + 1e-10
            num_violations = np.sum(violations)
            
            print('2. 违反约束统计')
            print('-'*80)
            print(f'违反mu_active <= mu的点数: {num_violations}')
            print(f'总点数: {nk * nb * nx}')
            print(f'违反比例: {num_violations / (nk * nb * nx) * 100:.2f}%')
            print('')
            
            # 分析违反约束的点
            violation_indices = np.where(violations)
            violation_values = mu_active[violations] - mu[violations]
            
            print('3. 违反约束的详细分析')
            print('-'*80)
            print(f'最大违反值: {np.max(violation_values):.6e}')
            print(f'平均违反值: {np.mean(violation_values):.6e}')
            print(f'违反值总和: {np.sum(violation_values):.6e}')
            print('')
            
            # 找出最大违反点
            max_violation_idx = np.unravel_index(np.argmax(violation_values), mu_active.shape)
            print('4. 最大违反点详情')
            print('-'*80)
            print(f'位置: (k={max_violation_idx[0]}, b={max_violation_idx[1]}, x={max_violation_idx[2]})')
            print(f'mu_active: {mu_active[max_violation_idx]:.6e}')
            print(f'mu: {mu[max_violation_idx]:.6e}')
            print(f'差异: {mu_active[max_violation_idx] - mu[max_violation_idx]:.6e}')
            print(f'pol_exit: {pol_exit[max_violation_idx]:.6f}')
            print(f'pol_entry: {pol_entry[max_violation_idx]:.6f}')
            if phi_dist is not None:
                print(f'phi_dist: {phi_dist[max_violation_idx]:.6e}')
            print('')
            
            # 手动计算mu_active
            print('5. 手动计算mu_active')
            print('-'*80)
            k_idx, b_idx, x_idx = max_violation_idx
            mu_val = mu[k_idx, b_idx, x_idx]
            pol_exit_val = pol_exit[k_idx, b_idx, x_idx]
            pol_entry_val = pol_entry[k_idx, b_idx, x_idx]
            phi_dist_val = phi_dist[k_idx, b_idx, x_idx] if phi_dist is not None else 0
            
            mu_active_manual = (
                (1 - psi) * (1 - pol_exit_val) * mu_val +
                mass * pol_entry_val * phi_dist_val
            )
            
            print(f'公式: mu_active = (1 - psi) * (1 - pol_exit) * mu + mass * pol_entry * phi_dist')
            print(f'计算: mu_active = (1 - {psi:.6f}) * (1 - {pol_exit_val:.6f}) * {mu_val:.6e} + {mass:.6f} * {pol_entry_val:.6f} * {phi_dist_val:.6e}')
            print(f'     = {(1 - psi) * (1 - pol_exit_val) * mu_val:.6e} + {mass * pol_entry_val * phi_dist_val:.6e}')
            print(f'     = {mu_active_manual:.6e}')
            print(f'实际mu_active: {mu_active[max_violation_idx]:.6e}')
            print(f'差异: {abs(mu_active_manual - mu_active[max_violation_idx]):.6e}')
            print('')
            
            # 分析违反约束的原因
            print('6. 违反约束原因分析')
            print('-'*80)
            
            # 检查是否是因为进入者贡献过大
            entry_contribution = mass * pol_entry * phi_dist if phi_dist is not None else np.zeros_like(mu_active)
            entry_contribution_sum = np.sum(entry_contribution)
            print(f'进入者贡献总和: {entry_contribution_sum:.6e}')
            print(f'mu总和: {np.sum(mu):.6e}')
            print(f'进入者贡献 / mu总和: {entry_contribution_sum / np.sum(mu):.6f}')
            
            # 检查违反约束点的特征
            violation_k_indices = violation_indices[0]
            violation_b_indices = violation_indices[1]
            violation_x_indices = violation_indices[2]
            
            print(f'\n违反约束点的k分布:')
            unique_k, counts_k = np.unique(violation_k_indices, return_counts=True)
            top5_k = np.argsort(counts_k)[-5:][::-1]
            for idx in top5_k:
                k_val = unique_k[idx]
                count = counts_k[idx]
                print(f'  k={k_val}: {count}个点')
            
            print(f'\n违反约束点的x分布:')
            unique_x, counts_x = np.unique(violation_x_indices, return_counts=True)
            top5_x = np.argsort(counts_x)[-5:][::-1]
            for idx in top5_x:
                x_val = unique_x[idx]
                count = counts_x[idx]
                print(f'  x={x_val}: {count}个点')
            
            # 检查phi_dist是否合理
            if phi_dist is not None:
                print(f'\n7. phi_dist检查')
                print('-'*80)
                print(f'phi_dist总和: {np.sum(phi_dist):.6f}')
                print(f'phi_dist最大值: {np.max(phi_dist):.6e}')
                print(f'phi_dist最小值: {np.min(phi_dist):.6e}')
                print(f'phi_dist非零元素数量: {np.sum(phi_dist > 0)}')
                
                # 检查phi_dist是否归一化
                phi_dist_sum_by_k = np.sum(phi_dist, axis=(1, 2))  # 按k维度求和
                print(f'\nphi_dist按k维度求和:')
                print(f'  最大值: {np.max(phi_dist_sum_by_k):.6f}')
                print(f'  最小值: {np.min(phi_dist_sum_by_k):.6f}')
                print(f'  平均值: {np.mean(phi_dist_sum_by_k):.6f}')
                
                # 检查违反约束点的phi_dist
                violation_phi_dist = phi_dist[violations]
                print(f'\n违反约束点的phi_dist统计:')
                print(f'  平均值: {np.mean(violation_phi_dist):.6e}')
                print(f'  最大值: {np.max(violation_phi_dist):.6e}')
                print(f'  总和: {np.sum(violation_phi_dist):.6e}')
            
            # 检查pol_entry
            print(f'\n8. pol_entry检查')
            print('-'*80)
            print(f'pol_entry总和: {np.sum(pol_entry):.6f}')
            print(f'pol_entry非零元素数量: {np.sum(pol_entry > 0)}')
            print(f'违反约束点的pol_entry平均值: {np.mean(pol_entry[violations]):.6f}')
            
    except FileNotFoundError:
        print('未找到steady_state_results.pkl文件')
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()


def check_mu_active_formula():
    """检查mu_active计算公式的正确性"""
    
    print('\n' + '='*80)
    print('mu_active计算公式检查')
    print('='*80)
    print('')
    
    print('Python公式 (fun_distrib1.py 第176-178行):')
    print('  mu_active[k,b,x] = (1 - psi) * (1 - pol_exit[k,b,x]) * mu[k,b,x] +')
    print('                      mass * pol_entry[k,b,x] * phi_dist[k,b,x]')
    print('')
    print('公式解释:')
    print('  1. (1 - psi) * (1 - pol_exit) * mu: 在位企业中不退出且不因外生退出而退出的部分')
    print('  2. mass * pol_entry * phi_dist: 新进入的企业')
    print('')
    print('理论分析:')
    print('  - mu_active应该 <= mu + 进入者贡献')
    print('  - 但在同一个(k,b,x)点上，mu_active不应该大于mu')
    print('  - 因为mu已经包括了所有在位企业（包括可能退出的）')
    print('  - 而mu_active只包括不退出且不因外生退出而退出的在位企业')
    print('  - 加上新进入的企业')
    print('')
    print('可能的问题:')
    print('  1. phi_dist计算错误，导致进入者分布不合理')
    print('  2. mu计算错误，导致mu值过小')
    print('  3. 公式理解错误，需要对比MATLAB实现')
    print('  4. 数值误差累积')


if __name__ == '__main__':
    analyze_mu_active_violation()
    check_mu_active_formula()
    
    print('\n' + '='*80)
    print('总结')
    print('='*80)
    print('\n主要发现:')
    print('  1. 需要检查phi_dist的计算是否正确')
    print('  2. 需要检查mu的计算是否正确')
    print('  3. 需要对比MATLAB的mu_active计算公式')
    print('  4. 需要检查是否有数值误差累积')












