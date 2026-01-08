"""
检查稳态结果中的所有负值变量
"""
import numpy as np
import pickle
import os

def check_negative_values():
    """检查稳态结果中的所有负值变量"""
    print("\n" + "="*80)
    print("稳态结果负值检查")
    print("="*80)
    
    # 加载稳态结果
    if not os.path.exists('steady_state_results.pkl'):
        print("\n错误：找不到steady_state_results.pkl文件")
        print("请先运行稳态计算")
        return
    
    with open('steady_state_results.pkl', 'rb') as f:
        ss_results = pickle.load(f)
    
    agg = ss_results['agg']
    prices = ss_results['prices']
    distribS = ss_results['distribS']
    sol = ss_results.get('sol', {})
    par = ss_results.get('par', {})
    
    negative_vars = []
    
    print("\n1. 加总变量 (agg):")
    print("-" * 80)
    for key, value in sorted(agg.items()):
        if isinstance(value, (int, float, np.number)):
            if value < 0:
                negative_vars.append(('agg', key, value, 'scalar'))
                print(f"  {key:<25} = {value:15.6f} [负值]")
        elif isinstance(value, np.ndarray):
            if np.any(value < 0):
                min_val = np.min(value)
                max_val = np.max(value)
                num_negative = np.sum(value < 0)
                negative_vars.append(('agg', key, min_val, f'array (min={min_val:.6e}, {num_negative}个负值)'))
                print(f"  {key:<25} = 数组, 最小值: {min_val:15.6e}, 最大值: {max_val:15.6e}, 负值数量: {num_negative}")
    
    print("\n2. 价格变量 (prices):")
    print("-" * 80)
    for key, value in sorted(prices.items()):
        if isinstance(value, (int, float, np.number)):
            if value < 0:
                negative_vars.append(('prices', key, value, 'scalar'))
                print(f"  {key:<25} = {value:15.6f} [负值]")
        elif isinstance(value, np.ndarray):
            if np.any(value < 0):
                min_val = np.min(value)
                max_val = np.max(value)
                num_negative = np.sum(value < 0)
                negative_vars.append(('prices', key, min_val, f'array (min={min_val:.6e}, {num_negative}个负值)'))
                print(f"  {key:<25} = 数组, 最小值: {min_val:15.6e}, 最大值: {max_val:15.6e}, 负值数量: {num_negative}")
    
    print("\n3. 分布变量 (distribS):")
    print("-" * 80)
    for key, value in sorted(distribS.items()):
        if isinstance(value, np.ndarray):
            if np.any(value < 0):
                min_val = np.min(value)
                max_val = np.max(value)
                num_negative = np.sum(value < 0)
                total_elements = value.size
                negative_vars.append(('distribS', key, min_val, f'array (min={min_val:.6e}, {num_negative}/{total_elements}个负值)'))
                print(f"  {key:<25} = 数组, 最小值: {min_val:15.6e}, 最大值: {max_val:15.6e}")
                print(f"  {'':<25}   负值数量: {num_negative}/{total_elements} ({100*num_negative/total_elements:.2f}%)")
    
    print("\n4. 解变量 (sol):")
    print("-" * 80)
    if sol:
        for key, value in sorted(sol.items()):
            if isinstance(value, np.ndarray):
                if np.any(value < 0):
                    min_val = np.min(value)
                    max_val = np.max(value)
                    num_negative = np.sum(value < 0)
                    total_elements = value.size
                    negative_vars.append(('sol', key, min_val, f'array (min={min_val:.6e}, {num_negative}/{total_elements}个负值)'))
                    print(f"  {key:<25} = 数组, 最小值: {min_val:15.6e}, 最大值: {max_val:15.6e}")
                    print(f"  {'':<25}   负值数量: {num_negative}/{total_elements} ({100*num_negative/total_elements:.2f}%)")
    
    print("\n5. 关键变量详细检查:")
    print("-" * 80)
    
    # 检查关键变量
    key_vars = {
        'C_agg': agg.get('C_agg', None),
        'K_agg': agg.get('K_agg', None),
        'K_corp': agg.get('K_corp', None),
        'K_small': agg.get('K_small', None),
        'L_agg': agg.get('L_agg', None),
        'L_corp': agg.get('L_corp', None),
        'L_small': agg.get('L_small', None),
        'Y_agg': agg.get('Y_agg', None),
        'Y_corp': agg.get('Y_corp', None),
        'Y_small': agg.get('Y_small', None),
        'output_small': agg.get('output_small', None),
        'cost_adj': agg.get('cost_adj', None),
        'entry_cost': agg.get('entry_cost', None),
        'liq': agg.get('liq', None),
        'InvK': agg.get('InvK', None),
        'InvK_corp': agg.get('InvK_corp', None),
        'wage': prices.get('wage', None),
        'q': prices.get('q', None),
        'rental': prices.get('rental', None),
        'KL_ratio': prices.get('KL_ratio', None),
    }
    
    for key, value in sorted(key_vars.items()):
        if value is not None:
            if isinstance(value, (int, float, np.number)):
                status = "[负值]" if value < 0 else "[正常]"
                print(f"  {key:<25} = {value:15.6f} {status}")
            elif isinstance(value, np.ndarray):
                min_val = np.min(value)
                max_val = np.max(value)
                num_negative = np.sum(value < 0)
                status = f"[{num_negative}个负值]" if num_negative > 0 else "[正常]"
                print(f"  {key:<25} = 数组, 最小值: {min_val:15.6e}, 最大值: {max_val:15.6e} {status}")
    
    # 检查entry_vec的详细情况
    if 'entry_vec' in distribS:
        entry_vec = distribS['entry_vec']
        print("\n6. entry_vec详细分析:")
        print("-" * 80)
        print(f"  形状: {entry_vec.shape}")
        print(f"  总和: {np.sum(entry_vec):.6e}")
        print(f"  最小值: {np.min(entry_vec):.6e}")
        print(f"  最大值: {np.max(entry_vec):.6e}")
        print(f"  平均值: {np.mean(entry_vec):.6e}")
        print(f"  负值数量: {np.sum(entry_vec < 0)}")
        print(f"  负值比例: {100*np.sum(entry_vec < 0)/entry_vec.size:.2f}%")
        if np.any(entry_vec < 0):
            negative_indices = np.where(entry_vec < 0)[0]
            print(f"  负值索引（前10个）: {negative_indices[:10]}")
            print(f"  负值（前10个）: {entry_vec[negative_indices[:10]]}")
    
    # 检查mu的详细情况
    if 'mu' in distribS:
        mu = distribS['mu']
        print("\n7. mu详细分析:")
        print("-" * 80)
        print(f"  形状: {mu.shape}")
        print(f"  总和: {np.sum(mu):.6e}")
        print(f"  最小值: {np.min(mu):.6e}")
        print(f"  最大值: {np.max(mu):.6e}")
        print(f"  平均值: {np.mean(mu):.6e}")
        print(f"  负值数量: {np.sum(mu < 0)}")
        print(f"  负值比例: {100*np.sum(mu < 0)/mu.size:.2f}%")
    
    # 检查mu_active的详细情况
    if 'mu_active' in distribS:
        mu_active = distribS['mu_active']
        print("\n8. mu_active详细分析:")
        print("-" * 80)
        print(f"  形状: {mu_active.shape}")
        print(f"  总和: {np.sum(mu_active):.6e}")
        print(f"  最小值: {np.min(mu_active):.6e}")
        print(f"  最大值: {np.max(mu_active):.6e}")
        print(f"  平均值: {np.mean(mu_active):.6e}")
        print(f"  负值数量: {np.sum(mu_active < 0)}")
        print(f"  负值比例: {100*np.sum(mu_active < 0)/mu_active.size:.2f}%")
    
    # 总结
    print("\n" + "="*80)
    print("负值变量总结")
    print("="*80)
    if negative_vars:
        print(f"\n共发现 {len(negative_vars)} 个负值变量/数组:")
        for category, key, value, desc in negative_vars:
            print(f"  {category}.{key:<25} {desc}")
    else:
        print("\n未发现负值变量 ✓")
    
    # 记录到日志
    def log_message(msg):
        try:
            with open('steady_state_iterations.log', 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except:
            pass
    
    log_message("\n" + "="*80)
    log_message("稳态结果负值检查")
    log_message("="*80)
    if negative_vars:
        log_message(f"\n共发现 {len(negative_vars)} 个负值变量/数组:")
        for category, key, value, desc in negative_vars:
            log_message(f"  {category}.{key:<25} {desc}")
    else:
        log_message("\n未发现负值变量 ✓")

if __name__ == '__main__':
    check_negative_values()



















