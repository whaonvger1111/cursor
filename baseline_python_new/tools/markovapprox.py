"""
使用马尔可夫链近似一阶自回归过程
"""
import numpy as np
from scipy.stats import norm


def markovapprox(rho, sigma, mu, m, N, disp_on_screen=False):
    """
    使用N状态马尔可夫链近似一阶自回归过程
    
    参数:
    rho: 持续性参数
    sigma: 创新标准差
    mu: 均值
    m: 离散化状态空间宽度（Tauchen使用m=3）
    N: 状态数
    disp_on_screen: 是否在屏幕上显示
    
    返回:
    Tran: 转移矩阵
    s: 离散化状态空间
    p: 平稳分布
    arho: 马尔可夫链的理论一阶自回归系数
    asigma: 马尔可夫链的理论标准差
    """
    # 离散化状态空间
    stvy = np.sqrt(sigma**2 / (1 - rho**2))  # y(t)的标准差
    ystar = mu / (1.0 - rho)  # y的期望值
    ymax = m * stvy  # 状态空间上界
    ymin = -ymax  # 状态空间下界
    w = (ymax - ymin) / (N - 1)  # 点之间的距离
    s = ystar + np.linspace(ymin, ymax, N)  # 离散化状态空间
    
    # 计算转移矩阵
    Tran = np.zeros((N, N))
    for j in range(N):
        for k in range(1, N - 1):
            Tran[j, k] = (norm.cdf(s[k] - rho * s[j] + w / 2, mu, sigma) -
                          norm.cdf(s[k] - rho * s[j] - w / 2, mu, sigma))
        Tran[j, 0] = norm.cdf(s[0] - rho * s[j] + w / 2, mu, sigma)
        Tran[j, N - 1] = 1 - norm.cdf(s[N - 1] - rho * s[j] - w / 2, mu, sigma)
    
    # 检查转移矩阵是否正确
    sum_rows = np.sum(Tran, axis=1)
    if np.max(np.abs(sum_rows - 1)) > 1e-6:
        raise ValueError('概率和不等于1')
    
    # 计算马尔可夫链的不变分布
    Trans = Tran.T
    p = (1 / N) * np.ones(N)  # 状态的初始分布
    test = 1
    while test > 1e-8:
        p1 = Trans @ p
        test = np.max(np.abs(p1 - p))
        p = p1
    
    meanm = s @ p  # 不变分布的均值
    varm = ((s - meanm)**2) @ p  # 不变分布的方差
    midaut1 = np.outer(s - meanm, s - meanm)  # yt和yt-1与均值偏差的交叉积
    probmat = np.outer(p, np.ones(N))  # 每列是不变分布
    midaut2 = Tran * probmat * midaut1  # 前两项的乘积是(Yt-1,Yt)的联合分布
    autcov1 = np.sum(midaut2)  # 一阶自协方差
    
    if disp_on_screen:
        # 显示链的矩
        print('原始过程的rho vs 马尔可夫链的rho')
        print('')
        arho = autcov1 / varm  # 理论rho
        print([rho, arho])
        
        print('真实过程的标准差 vs 马尔可夫链的标准差')
        print('')
        asigma = np.sqrt(varm)
        print([stvy, asigma])
    else:
        arho = autcov1 / varm
        asigma = np.sqrt(varm)
    
    return Tran, s, p, arho, asigma

