"""
生成稳态图形
"""
import numpy as np

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("警告：matplotlib未安装，绘图功能将不可用")


def make_plots_ss(sol, distribS, b_grid, par):
    """
    生成稳态图形
    
    参数:
    sol: 解字典
    distribS: 分布字典
    b_grid: 债务网格
    par: 参数字典
    """
    if not HAS_MATPLOTLIB:
        print("错误：matplotlib未安装，无法生成图形")
        return
    
    mu_x = np.sum(distribS['mu'], axis=(0, 1))
    mu_active_x = np.sum(distribS['mu_active'], axis=(0, 1))
    
    mu_k = np.sum(distribS['mu'], axis=(1, 2))
    mu_active_k = np.sum(distribS['mu_active'], axis=(1, 2))
    
    mu_b = np.sum(distribS['mu'], axis=2)
    mu_active_b = np.sum(distribS['mu_active'], axis=2)
    
    # x在k条件下的边际分布
    mu_x_k = np.sum(distribS['mu'], axis=1)
    mu_active_x_k = np.sum(distribS['mu_active'], axis=1)
    
    # 图形1：x的边际分布
    plt.figure()
    plt.plot(par['x_grid'], mu_x, label='mu')
    plt.plot(par['x_grid'], mu_active_x, label='mu_active')
    plt.legend()
    plt.xlabel('Productivity, x')
    plt.title('Marginal distribution of x')
    plt.show()
    
    # 图形2：x在k条件下的边际分布
    k_c = 1  # 选择某个k
    plt.figure()
    plt.plot(par['x_grid'], mu_x_k[k_c, :], label='mu')
    plt.plot(par['x_grid'], mu_active_x_k[k_c, :], label='mu_active')
    plt.legend()
    plt.xlabel('Productivity, x')
    plt.title('Marginal distribution of x, conditional on k')
    plt.show()
    
    # 图形3：k的边际分布
    plt.figure()
    k_grid_flat = par['k_grid'].flatten() if par['k_grid'].ndim > 1 else par['k_grid']
    plt.plot(k_grid_flat, mu_k)
    plt.title('Marginal distribution of k')
    plt.show()
    
    # 图形4：b在k条件下的边际分布
    plt.figure()
    k1 = 0  # round(nk/2)
    k2 = 19
    k3 = 39
    k4 = par['nk'] - 1
    
    mu_b_k1 = mu_b[k1, :] / np.sum(mu_b[k1, :]) if np.sum(mu_b[k1, :]) > 0 else mu_b[k1, :]
    mu_b_k2 = mu_b[k2, :] / np.sum(mu_b[k2, :]) if np.sum(mu_b[k2, :]) > 0 else mu_b[k2, :]
    mu_b_k3 = mu_b[k3, :] / np.sum(mu_b[k3, :]) if np.sum(mu_b[k3, :]) > 0 else mu_b[k3, :]
    mu_b_k4 = mu_b[k4, :] / np.sum(mu_b[k4, :]) if np.sum(mu_b[k4, :]) > 0 else mu_b[k4, :]
    
    plt.plot(b_grid[k1, :], mu_b_k1, label='k low')
    plt.plot(b_grid[k2, :], mu_b_k2, label='k medium low')
    plt.plot(b_grid[k3, :], mu_b_k3, label='k medium high')
    plt.plot(b_grid[k4, :], mu_b_k4, label='k high')
    plt.legend()
    plt.xlabel('Debt, b')
    plt.title('Marginal distribution of b, conditional on k')
    plt.show()

