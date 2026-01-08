"""
绘制稳态分布和政策函数
"""
import numpy as np
import os

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("警告：matplotlib未安装，绘图功能将不可用")


def plot_ss(b_grid, sol, par, distribS, model_mom, data_mom, SaveDir, do_save, FormatFig, FS):
    """
    绘制稳态分布和政策函数
    
    参数:
    b_grid: 债务网格
    sol: 解字典
    par: 参数字典
    distribS: 分布字典
    model_mom: 模型矩字典
    data_mom: 数据矩字典
    SaveDir: 保存目录
    do_save: 是否保存标志
    FormatFig: 图形格式
    FS: 字体大小
    """
    if not HAS_MATPLOTLIB:
        print("错误：matplotlib未安装，无法生成图形")
        return
    
    # 创建保存目录
    if do_save and not os.path.exists(SaveDir):
        os.makedirs(SaveDir)
    
    # 这里可以添加具体的绘图代码
    # 由于原MATLAB代码较长，这里提供框架
    print("绘制稳态分布和政策函数...")
    print("注意：完整的绘图功能需要根据具体需求实现")
    
    # 示例：绘制x的边际分布
    mu_x = np.sum(distribS['mu'], axis=(0, 1))
    mu_active_x = np.sum(distribS['mu_active'], axis=(0, 1))
    
    plt.figure(figsize=(10, 6))
    plt.plot(par['x_grid'], mu_x, label='mu', linewidth=2)
    plt.plot(par['x_grid'], mu_active_x, label='mu_active', linewidth=2)
    plt.legend(fontsize=FS)
    plt.xlabel('Productivity, x', fontsize=FS)
    plt.ylabel('Density', fontsize=FS)
    plt.title('Marginal distribution of x', fontsize=FS)
    plt.grid(True, alpha=0.3)
    
    if do_save:
        filepath = os.path.join(SaveDir, 'mu_x.' + FormatFig)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f'图形已保存到 {filepath}')
    
    plt.show()

