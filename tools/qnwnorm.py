"""
计算多元正态分布的节点和权重
基于CompEcon工具箱
"""
import numpy as np
from scipy.linalg import sqrtm, cholesky


def qnwnorm(n, mu=None, var=None, usesqrtm=0):
    """
    计算多元正态分布的节点和权重
    
    参数:
    n: 1 by d向量，每个变量的节点数
    mu: 1 by d均值向量
    var: d by d正定协方差矩阵
    usesqrtm: 0/1，如果为1，使用sqrtm分解var而不是chol
    
    返回:
    x: prod(n) by d矩阵，评估节点
    w: prod(n) by 1向量，概率
    
    注意：此实现是简化版本，完整版本需要ckron和gridmake函数
    """
    d = len(n) if isinstance(n, (list, np.ndarray)) else 1
    
    if var is None:
        var = np.eye(d)
    if mu is None:
        mu = np.zeros(d)
    
    mu = np.asarray(mu).flatten()
    if len(mu.shape) > 1:
        mu = mu.T
    
    # 简化实现：只处理一维情况
    if d == 1:
        x, w = qnwnorm1(n)
        if usesqrtm:
            x = x * np.sqrt(var[0, 0]) + mu[0]
        else:
            x = x * np.sqrt(var[0, 0]) + mu[0]
        return x, w
    else:
        # 多维情况需要更复杂的实现
        raise NotImplementedError('多维情况需要ckron和gridmake函数')


def qnwnorm1(n):
    """
    计算单变量标准正态分布的节点和权重
    
    参数:
    n: 节点数
    
    返回:
    x: n by 1向量，评估节点
    w: n by 1向量，概率
    
    基于W.H. Press, S.A. Teukolsky, W.T. Vetterling和B.P. Flannery的算法
    "Numerical Recipes in FORTRAN", 2nd ed. Cambridge University Press, 1992.
    """
    maxit = 100
    pim4 = 1 / np.pi ** 0.25
    m = (n + 1) // 2
    x = np.zeros(n)
    w = np.zeros(n)
    
    for i in range(m):
        # 合理的起始值
        if i == 0:
            z = np.sqrt(2 * n + 1) - 1.85575 * ((2 * n + 1) ** (-1 / 6))
        elif i == 1:
            z = z - 1.14 * (n ** 0.426) / z
        elif i == 2:
            z = 1.86 * z + 0.86 * x[0]
        elif i == 3:
            z = 1.91 * z + 0.91 * x[1]
        else:
            z = 2 * z + x[i - 2]
        
        # 求根迭代
        its = 0
        while its < maxit:
            its += 1
            p1 = pim4
            p2 = 0
            for j in range(1, n + 1):
                p3 = p2
                p2 = p1
                p1 = z * np.sqrt(2 / j) * p2 - np.sqrt((j - 1) / j) * p3
            
            pp = np.sqrt(2 * n) * p2
            z1 = z
            z = z1 - p1 / pp
            if abs(z - z1) < 1e-14:
                break
        
        if its >= maxit:
            raise RuntimeError('qnwnorm1中收敛失败')
        
        x[n - i] = z
        x[i] = -z
        w[i] = 2 / (pp * pp)
        w[n - 1 - i] = w[i]
    
    w = w / np.sqrt(np.pi)
    x = x * np.sqrt(2)
    
    return x.reshape(-1, 1), w.reshape(-1, 1)

