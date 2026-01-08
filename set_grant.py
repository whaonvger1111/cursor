"""
设置救援政策参数Xp和eta用于转移动态
"""
import numpy as np


def set_grant(par):
    """
    设置救援政策参数
    
    参数:
    par: 参数字典
    
    返回:
    par: 更新的参数字典
    
    描述:
    我们向字典"par"添加新变量。
    设置救援政策参数Xp和eta用于转移动态
    par.weights有维度: (nk,nx,nn)。对于每个(k,x)，weights的值
    表示处于某个{impact*grant}状态的概率。
    nn是一个虚拟变量，取4个值：
    1 = 有补助且受冲击
    2 = 有补助且未受冲击
    3 = 无补助且受冲击
    4 = 无补助且未受冲击
    
    例如，无定向补助（即基准补助）
    eta_i = 受冲击的概率，维度: 标量
    eta = 接收补助的概率，维度: (nk,nx)
    在这种情况下，weights对于所有(k,x)都相同，由于两个事件
    （补助和冲击）是独立的，我们有：
    weights(:,:,n=1)是eta*eta_i
    weights(:,:,n=2)是eta*(1-eta_i)
    等等。
    注意：论文中的定向补助在这里称为"targslim"。
    """
    if not isinstance(par, dict):
        raise TypeError('输入参数"par"必须是字典')
    
    par['T_grant'] = 1  # 补助分散的期数
    
    # 基准补助金额：2.5倍月工资，取决于没有冲击时的x
    grant_flag = par.get('grant_flag', 0)
    
    if grant_flag == 0:  # 无补助
        par['Xp'] = 0
        par['eta'] = 0.76 * np.ones((par['nk'], par['nx']))  # 有补助的小企业比例
    
    elif grant_flag == 1:  # 基准补助
        par['Xp'] = 2.5 / 3
        par['eta'] = 0.76 * np.ones((par['nk'], par['nx']))  # 有补助的小企业比例
    
    elif grant_flag == 2:  # 基于x的补助
        par['Xp'] = 2.5 / 3
        par['eta'] = np.zeros((par['nk'], par['nx']))
        for k_c in range(par['nk']):
            for x_c in range(par['nx']):
                if par['x_grid'][x_c] >= 1.0 and par['x_grid'][x_c] <= 2.0:
                    par['eta'][k_c, x_c] = 0.76
    
    elif grant_flag == 3:  # 均匀补助大
        par['Xp'] = 20
        par['eta'] = 0.76 * np.ones((par['nk'], par['nx']))  # 有补助的小企业比例
    
    elif grant_flag == 4:  # 均匀补助小
        par['Xp'] = 0.5 * 2.5 / 3
        par['eta'] = 0.76 * np.ones((par['nk'], par['nx']))
    
    elif grant_flag == 5:  # 只有受冲击企业获得补助
        par['Xp'] = 2.5 / 3
        par['eta'] = par['eta_i'] * np.ones((par['nk'], par['nx']))  # eta==eta_i
    
    elif grant_flag == 6:  # 只有受冲击企业获得补助，大补助
        par['Xp'] = 2.5 / 3 * 6.32  # 增加Xp
        par['eta'] = par['eta_i'] * np.ones((par['nk'], par['nx']))  # eta==eta_i
    
    elif grant_flag == 7:  # 只有受冲击企业获得补助，小补助
        par['Xp'] = 2.5 / 3 * 0.5  # 减少Xp
        par['eta'] = par['eta_i'] * np.ones((par['nk'], par['nx']))  # eta==eta_i
    
    # 补助是否定向到受冲击企业
    par['weights'] = np.zeros((par['nk'], par['nx'], par['nn']))
    grant_target = par.get('grant_target', 0)
    
    if grant_target == 1:  # 定向补助
        if np.max(par['eta']) < par['eta_i']:
            print("受冲击企业太多，没有足够的补助来定向！")
            # 在MATLAB中这里会keyboard，在Python中我们继续
        # 定向到受冲击企业
        # 即受冲击企业以prob=1接收补助
        #   未受冲击企业以prob = (eta-eta_i)/(1-eta_i)接收补助
        eta_unimp = (par['eta'] - par['eta_i']) / (1 - par['eta_i'])
        par['weights'][:, :, 0] = par['eta_i']  # 受冲击，有补助
        par['weights'][:, :, 1] = (1 - par['eta_i']) * eta_unimp  # 未受冲击，有补助
        par['weights'][:, :, 2] = 0  # 受冲击，无补助
        par['weights'][:, :, 3] = (1 - par['eta_i']) * (1 - eta_unimp)  # 未受冲击，无补助
    
    elif grant_target == 2:  # 精简定向
        if np.max(par['eta']) < par['eta_i']:
            print("受冲击企业太多，没有足够的补助来定向！")
        # 只定向到受冲击企业
        # 即受冲击企业以prob = 1接收补助
        #   未受冲击企业以prob = 0接收补助
        par['weights'][:, :, 0] = par['eta_i']  # 受冲击，有补助
        par['weights'][:, :, 1] = 0  # 未受冲击，有补助
        par['weights'][:, :, 2] = 0  # 受冲击，无补助
        par['weights'][:, :, 3] = (1 - par['eta_i'])  # 未受冲击，无补助
    
    else:  # 无定向（即基准补助）
        par['weights'][:, :, 0] = par['eta_i'] * par['eta']
        par['weights'][:, :, 1] = (1 - par['eta_i']) * par['eta']
        par['weights'][:, :, 2] = par['eta_i'] * (1 - par['eta'])
        par['weights'][:, :, 3] = (1 - par['eta_i']) * (1 - par['eta'])
    
    # 检查：
    # 对于每个x, k，weights在n_c上的和应该等于1
    weights_sum = np.sum(par['weights'], axis=2)
    if (np.abs(np.max(weights_sum) - 1) > 1e-10 or 
        np.abs(np.min(weights_sum) - 1) > 1e-10):
        print("警告：weights和不等于1")
    
    return par

