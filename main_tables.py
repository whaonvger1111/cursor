"""
此脚本为论文编译结果（表格）
此脚本需要以下mat文件：
- ss.mat, nogrant.mat, grant_baseline.mat, grant_targslim.mat
此脚本创建用于文档的表格
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from mystruct2table import mystruct2table
from mystruct2table_mom import mystruct2table_mom
from make_table_ss import make_table_ss


def load_mat_file(filepath):
    """
    加载MAT文件（占位符）
    注意：在Python中需要使用scipy.io.loadmat来加载MATLAB文件
    或者将数据转换为Python格式（如pickle或numpy格式）
    """
    try:
        from scipy.io import loadmat
        return loadmat(filepath)
    except ImportError:
        print("警告：scipy.io.loadmat不可用。")
        print("请安装scipy或使用其他方法加载数据。")
        return None


def main_tables():
    """
    生成论文表格的主函数
    """
    matNames = ['ss', 'nogrant', 'grant_baseline', 'grant_targslim']
    mat_dir = 'mat'
    
    # 检查文件是否存在
    for ii in range(len(matNames)):
        filepath = os.path.join(mat_dir, f'{matNames[ii]}.mat')
        if not os.path.exists(filepath):
            print(f'警告：MAT文件 "{matNames[ii]}" 缺失')
    
    # 创建tables目录
    tabDir = 'tables'
    if not os.path.exists(tabDir):
        os.makedirs(tabDir)
    
    # 为稳态生成表格
    # 加载稳态结果
    ss_filepath = os.path.join(mat_dir, 'ss.mat')
    if os.path.exists(ss_filepath):
        # 注意：这里需要实际加载数据
        # 假设数据已经加载到变量中
        print("注意：需要加载ss.mat文件")
        print("在Python中，可以使用scipy.io.loadmat或pickle来加载数据")
        
        # 表格：计算参数
        comp_params_file = os.path.join(tabDir, 'comp_parameters.tex')
        with open(comp_params_file, 'w', encoding='utf-8') as FID:
            FID.write(' \\begin{tabular}{llc} \\hline \n')
            FID.write(' Parameter & Description & Value \\\\ \n')
            FID.write(' \\hline \n')
            # 这些值需要从par字典中获取
            FID.write('nx  & Num. of grid points for $x$       & %d \\\\ \n' % 30)  # par['nx'] (校准模式)
            FID.write('nb  & Num. of grid points for $b$       & %d \\\\ \n' % 40)  # par['nb'] (校准模式)
            FID.write('nk  & Num. of grid points for $\\kappa$  & %d \\\\ \n' % 50)  # par['nk'] (校准模式)
            FID.write('T   & Length of transition              & %d \\\\ \n' % 180)  # par['T']
            FID.write(' \\hline \n \\end{tabular} \n')
        
        print(f'计算参数表格已保存到 {comp_params_file}')
        
        # 表格：外生参数
        exo_params_file = os.path.join(tabDir, 'exo_parameters.tex')
        with open(exo_params_file, 'w', encoding='utf-8') as FID:
            FID.write(' \\begin{tabular}{llc} \\hline \n')
            FID.write(' Parameter & Description & Value \\\\ \n')
            FID.write(' \\hline \n')
            # 这些值需要从par和ExoNames中获取
            # for i in range(len(ExoNames)):
            #     FID.write('%s  & %s & %8.3f \\\\ \n' % (ExoNames[i][1], ExoNames[i][2], par[ExoNames[i][0]]))
            FID.write(' \\hline \n \\end{tabular} \n')
        
        print(f'外生参数表格已保存到 {exo_params_file}')
        
        print("注意：其他表格需要实际的数据才能生成")
        print("请确保已加载所有必要的变量：par, prices, agg, b_grid, model_mom, data_mom等")
    else:
        print(f'错误：文件 {ss_filepath} 不存在！')
    
    print("\n表格生成完成！")
    print("注意：此函数需要实际的数据文件才能完全工作。")
    print("请使用scipy.io.loadmat加载MATLAB文件，或使用pickle加载Python格式的数据。")

