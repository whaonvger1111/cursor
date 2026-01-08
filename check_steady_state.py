"""
检查稳态计算结果，查找不合理的值（负值、异常值等）
"""
import numpy as np
import pickle
import os
import sys

def check_steady_state(filename='steady_state_results.pkl'):
    """
    检查稳态结果文件中的不合理值
    
    参数:
    filename: 稳态结果文件名
    """
    if not os.path.exists(filename):
        print(f"错误：未找到稳态结果文件 {filename}")
        print("请先运行 main.py 计算稳态")
        return
    
    print("="*80)
    print("检查稳态计算结果")
    print("="*80)
    print(f"加载文件: {filename}\n")
    
    try:
        with open(filename, 'rb') as f:
            ss_results = pickle.load(f)
    except Exception as e:
        print(f"错误：加载文件失败: {e}")
        return
    
    # 检查加总变量
    print("-"*80)
    print("1. 加总变量 (agg)")
    print("-"*80)
    agg = ss_results.get('agg')
    if agg is None:
        print("警告：未找到加总变量")
    else:
        negative_vars = []
        zero_vars = []
        very_large_vars = []
        
        for key, value in agg.items():
            if isinstance(value, (int, float, np.number)):
                if value < 0:
                    negative_vars.append((key, value))
                elif value == 0:
                    zero_vars.append((key, value))
                elif abs(value) > 1e10:
                    very_large_vars.append((key, value))
                else:
                    print(f"  {key:20s} = {value:15.6f}")
        
        if negative_vars:
            print("\n[警告] 负值变量:")
            for key, value in negative_vars:
                print(f"  {key:20s} = {value:15.6f} [负值]")
        
        if zero_vars:
            print("\n[警告] 零值变量（可能有问题）:")
            for key, value in zero_vars:
                print(f"  {key:20s} = {value:15.6f}")
        
        if very_large_vars:
            print("\n[警告] 异常大的值:")
            for key, value in very_large_vars:
                print(f"  {key:20s} = {value:15.6e}")
    
    # 检查价格
    print("\n" + "-"*80)
    print("2. 价格 (prices)")
    print("-"*80)
    prices = ss_results.get('prices')
    if prices is None:
        print("警告：未找到价格变量")
    else:
        for key, value in prices.items():
            if isinstance(value, (int, float, np.number)):
                status = ""
                if value < 0:
                    status = " [负值]"
                elif value == 0:
                    status = " [零值]"
                print(f"  {key:20s} = {value:15.6f}{status}")
    
    # 检查分布
    print("\n" + "-"*80)
    print("3. 分布统计 (distribS)")
    print("-"*80)
    distribS = ss_results.get('distribS')
    if distribS is None:
        print("警告：未找到分布变量")
    else:
        mu = distribS.get('mu')
        mu_active = distribS.get('mu_active')
        entry_vec = distribS.get('entry_vec')
        
        if mu is not None:
            print(f"  mu 形状: {mu.shape}")
            print(f"  mu 总和: {np.sum(mu):.6f}")
            print(f"  mu 最小值: {np.min(mu):.6e}")
            print(f"  mu 最大值: {np.max(mu):.6e}")
            if np.any(mu < 0):
                print(f"  [警告] mu包含负值! 最小值 = {np.min(mu):.6e}")
            if np.any(np.isnan(mu)) or np.any(np.isinf(mu)):
                print(f"  [警告] mu包含NaN或Inf值!")
        
        if mu_active is not None:
            print(f"\n  mu_active 形状: {mu_active.shape}")
            print(f"  mu_active 总和: {np.sum(mu_active):.6f}")
            print(f"  mu_active 最小值: {np.min(mu_active):.6e}")
            print(f"  mu_active 最大值: {np.max(mu_active):.6e}")
            if np.any(mu_active < 0):
                print(f"  [警告] mu_active包含负值! 最小值 = {np.min(mu_active):.6e}")
            if np.any(np.isnan(mu_active)) or np.any(np.isinf(mu_active)):
                print(f"  [警告] mu_active包含NaN或Inf值!")
        
        if entry_vec is not None:
            print(f"\n  entry_vec 形状: {entry_vec.shape}")
            print(f"  entry_vec 总和: {np.sum(entry_vec):.6f}")
            print(f"  entry_vec 最小值: {np.min(entry_vec):.6e}")
            print(f"  entry_vec 最大值: {np.max(entry_vec):.6e}")
            if np.any(entry_vec < 0):
                print(f"  [警告] entry_vec包含负值! 最小值 = {np.min(entry_vec):.6e}")
    
    # 检查参数
    print("\n" + "-"*80)
    print("4. 关键参数")
    print("-"*80)
    par = ss_results.get('par')
    if par is not None:
        key_params = ['nx', 'nb', 'nk', 'tol_vfi', 'tol_dist', 'mass', 'psi', 
                     'theta', 'delta_k', 'beta', 'alpha', 'gamma1', 'gamma2']
        for key in key_params:
            if key in par:
                value = par[key]
                if isinstance(value, (int, float, np.number)):
                    print(f"  {key:20s} = {value:15.6f}")
    
    # 检查收敛标志
    print("\n" + "-"*80)
    print("5. 收敛状态")
    print("-"*80)
    flag_ss = ss_results.get('flag_ss', -1)
    if flag_ss >= 0:
        print("  [成功] 稳态计算收敛成功")
    else:
        print("  [警告] 稳态计算未收敛或失败")
    
    # 总结
    print("\n" + "="*80)
    print("检查完成")
    print("="*80)
    
    # 检查是否有明显不合理的情况
    issues = []
    if agg is not None:
        if agg.get('K_corp', 0) < 0:
            issues.append("企业部门资本K_corp为负值")
        if agg.get('K_small', 0) < 0:
            issues.append("小企业资本K_small为负值")
        if agg.get('C_agg', 0) < 0:
            issues.append("总消费C_agg为负值")
        if agg.get('L_corp', 0) < 0:
            issues.append("企业部门就业L_corp为负值")
        if agg.get('L_small', 0) < 0:
            issues.append("小企业就业L_small为负值")
    
    if distribS is not None:
        mu = distribS.get('mu')
        if mu is not None and np.any(mu < 0):
            issues.append("分布mu包含负值")
        mu_active = distribS.get('mu_active')
        if mu_active is not None and np.any(mu_active < 0):
            issues.append("分布mu_active包含负值")
    
    if issues:
        print("\n[警告] 发现的问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n[成功] 未发现明显的不合理值")


if __name__ == '__main__':
    filename = 'steady_state_results.pkl'
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    check_steady_state(filename)

