"""
创建MATLAB和Python结果对比表格
"""
import numpy as np
import pickle
import scipy.io
import os
import pandas as pd


def extract_matlab_value(mat_data, struct_name, field_name):
    """从MATLAB结构数组中提取值"""
    if struct_name not in mat_data:
        return None
    
    struct = mat_data[struct_name]
    if not isinstance(struct, np.ndarray) or not struct.dtype.names:
        return None
    
    if field_name not in struct.dtype.names:
        return None
    
    val = struct[field_name][0, 0]
    if isinstance(val, np.ndarray):
        if val.size == 1:
            return float(val.item())
        else:
            return val
    else:
        return float(val) if isinstance(val, (int, float, np.number)) else val


def create_comparison_table(matlab_file=None, python_file=None, output_file='comparison_table.txt'):
    """
    创建对比表格
    
    参数:
    matlab_file: MATLAB .mat文件路径
    python_file: Python .pkl文件路径
    output_file: 输出文件路径
    """
    # 默认文件路径
    if matlab_file is None:
        possible_matlab_files = [
            '../baseline_python/steady_state_results_fortran.mat',
            '../alternative/mat/ss.mat',
            'steady_state_results.mat'
        ]
        for f in possible_matlab_files:
            if os.path.exists(f):
                matlab_file = f
                break
    
    if python_file is None:
        possible_python_files = [
            'steady_state_results_new.pkl',
            '../baseline_python/steady_state_results_fortran.pkl',
            '../baseline_python/steady_state_results.pkl'
        ]
        for f in possible_python_files:
            if os.path.exists(f):
                python_file = f
                break
    
    if matlab_file is None or not os.path.exists(matlab_file):
        print("错误: 找不到MATLAB结果文件")
        return
    
    if python_file is None or not os.path.exists(python_file):
        print("错误: 找不到Python结果文件")
        return
    
    # 加载数据
    try:
        mat_data = scipy.io.loadmat(matlab_file)
    except Exception as e:
        print(f"无法加载MATLAB文件: {e}")
        return
    
    try:
        with open(python_file, 'rb') as f:
            py_data = pickle.load(f)
    except Exception as e:
        print(f"无法加载Python文件: {e}")
        return
    
    # 准备对比数据
    comparison_data = []
    
    # 1. 价格
    print("\n正在提取价格数据...")
    price_fields = ['q', 'rental', 'wage', 'KL_ratio']
    for field in price_fields:
        mat_val = extract_matlab_value(mat_data, 'prices', field)
        py_val = py_data.get('prices', {}).get(field) if isinstance(py_data.get('prices'), dict) else None
        
        if mat_val is not None and py_val is not None:
            diff = abs(mat_val - py_val)
            rel_diff = diff / (abs(mat_val) + 1e-10) * 100
            status = "匹配" if diff < 1e-8 else "差异"
            comparison_data.append({
                '类别': '价格',
                '指标': field,
                'MATLAB值': f"{mat_val:.10f}",
                'Python值': f"{py_val:.10f}",
                '绝对差异': f"{diff:.2e}",
                '相对差异(%)': f"{rel_diff:.4f}",
                '状态': status
            })
    
    # 2. 加总变量
    print("正在提取加总变量数据...")
    agg_fields = ['C_agg', 'K_corp', 'K_agg', 'K_small', 'L_agg', 'L_corp', 'L_small', 
                  'Y_corp', 'output_small', 'exit_rate', 'entry_rate', 'Mactive', 'Mentr']
    
    for field in agg_fields:
        mat_val = extract_matlab_value(mat_data, 'agg', field)
        py_val = py_data.get('agg', {}).get(field) if isinstance(py_data.get('agg'), dict) else None
        
        if mat_val is not None and py_val is not None:
            diff = abs(mat_val - py_val)
            rel_diff = diff / (abs(mat_val) + 1e-10) * 100
            # 判断差异大小
            if diff < 1e-6:
                status = "匹配"
            elif rel_diff < 1:
                status = "很小"
            elif rel_diff < 10:
                status = "较小"
            else:
                status = "较大"
            
            comparison_data.append({
                '类别': '加总变量',
                '指标': field,
                'MATLAB值': f"{mat_val:.10f}",
                'Python值': f"{py_val:.10f}",
                '绝对差异': f"{diff:.2e}",
                '相对差异(%)': f"{rel_diff:.4f}",
                '状态': status
            })
    
    # 3. 模型矩
    print("正在提取模型矩数据...")
    mom_fields = ['avefirmsize', 'empshare_small', 'revshare_small', 'exitrate', 
                  'avefirmsize_age0', 'autocorr_emp', 'fixedcost_to_rev', 'hasNetDebt',
                  'jcr', 'jdr', 'entryrate', 'frac_exit_forced', 'frac_exit_vol']
    
    for field in mom_fields:
        mat_val = extract_matlab_value(mat_data, 'model_mom', field)
        py_val = py_data.get('model_mom', {}).get(field) if isinstance(py_data.get('model_mom'), dict) else None
        
        if mat_val is not None and py_val is not None:
            diff = abs(mat_val - py_val)
            rel_diff = diff / (abs(mat_val) + 1e-10) * 100
            # 判断差异大小
            if diff < 1e-4:
                status = "匹配"
            elif rel_diff < 1:
                status = "很小"
            elif rel_diff < 10:
                status = "较小"
            else:
                status = "较大"
            
            comparison_data.append({
                '类别': '模型矩',
                '指标': field,
                'MATLAB值': f"{mat_val:.10f}",
                'Python值': f"{py_val:.10f}",
                '绝对差异': f"{diff:.2e}",
                '相对差异(%)': f"{rel_diff:.4f}",
                '状态': status
            })
    
    # 创建DataFrame
    df = pd.DataFrame(comparison_data)
    
    # 保存为文本表格
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*120 + "\n")
        f.write("MATLAB vs Python 稳态结果对比表\n")
        f.write("="*120 + "\n")
        f.write(f"MATLAB文件: {matlab_file}\n")
        f.write(f"Python文件: {python_file}\n")
        f.write("="*120 + "\n\n")
        
        # 按类别分组输出
        for category in ['价格', '加总变量', '模型矩']:
            f.write(f"\n【{category}】\n")
            f.write("-"*120 + "\n")
            f.write(f"{'指标':<25} {'MATLAB值':<20} {'Python值':<20} {'绝对差异':<15} {'相对差异(%)':<15} {'状态':<10}\n")
            f.write("-"*120 + "\n")
            
            category_data = df[df['类别'] == category]
            for _, row in category_data.iterrows():
                f.write(f"{row['指标']:<25} {row['MATLAB值']:<20} {row['Python值']:<20} "
                       f"{row['绝对差异']:<15} {row['相对差异(%)']:<15} {row['状态']:<10}\n")
        
        # 统计摘要
        f.write("\n" + "="*120 + "\n")
        f.write("差异统计摘要\n")
        f.write("="*120 + "\n")
        
        status_counts = df['状态'].value_counts()
        for status, count in status_counts.items():
            f.write(f"{status}: {count} 个指标\n")
        
        # 找出差异最大的指标
        f.write("\n差异最大的10个指标:\n")
        f.write("-"*120 + "\n")
        df_sorted = df.copy()
        df_sorted['相对差异数值'] = df_sorted['相对差异(%)'].astype(float)
        df_sorted = df_sorted.sort_values('相对差异数值', ascending=False)
        for _, row in df_sorted.head(10).iterrows():
            f.write(f"{row['指标']:<25} 相对差异: {row['相对差异(%)']}%\n")
    
    # 也保存为CSV
    csv_file = output_file.replace('.txt', '.csv')
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    
    print(f"\n对比表格已保存:")
    print(f"  文本格式: {output_file}")
    print(f"  CSV格式: {csv_file}")
    
    # 打印摘要
    print("\n" + "="*80)
    print("差异统计摘要")
    print("="*80)
    status_counts = df['状态'].value_counts()
    for status, count in status_counts.items():
        print(f"{status}: {count} 个指标")
    
    print("\n差异最大的5个指标:")
    print("-"*80)
    df_sorted = df.copy()
    df_sorted['相对差异数值'] = df_sorted['相对差异(%)'].astype(float)
    df_sorted = df_sorted.sort_values('相对差异数值', ascending=False)
    for _, row in df_sorted.head(5).iterrows():
        print(f"  {row['指标']:<25} 相对差异: {row['相对差异(%)']}%")
    
    return df


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='创建MATLAB和Python结果对比表格')
    parser.add_argument('--matlab', type=str, help='MATLAB .mat文件路径')
    parser.add_argument('--python', type=str, help='Python .pkl文件路径')
    parser.add_argument('--output', type=str, default='comparison_table.txt', help='输出文件路径')
    
    args = parser.parse_args()
    
    create_comparison_table(args.matlab, args.python, args.output)

