"""
设置模型的数值和经济参数
"""
import numpy as np
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from struct2vec import struct2vec
from markovapprox import markovapprox
from paretojo import paretojo


def set_parameters(par, file_params):
    """
    设置模型的数值和经济参数
    
    参数:
    par: 参数字典
    file_params: 输入参数文件名
    
    返回:
    par: 更新的参数字典
    guess: 校准的初始猜测列向量
    bounds: 字典，每个字段是1*2数值向量
    calibNames: 字符串列表
    dispNames: 字符串列表
    description: 字符串列表
    ExoNames: 字符串列表（用于外生参数表）
    """
    # 输入检查
    if not isinstance(par, dict):
        raise TypeError('输入参数"par"必须是字典')
    if not isinstance(file_params, str):
        raise TypeError('输入参数"file_params"必须是字符串')
    
    # 数值参数
    par['T'] = 180  # 转移动态长度
    par['Tmax'] = 8  # Tmax之后，所有冲击为零
    par['nx'] = 60  # 生产率网格大小
    par['nb'] = 80  # 债务网格大小
    par['nk'] = 100  # 资本网格大小
    par['ns'] = 2  # 有补助 vs 无补助
    par['ni'] = 2  # 受冲击 vs 未受冲击
    par['nn'] = par['ns'] * par['ni']
    par['x_process'] = 1  # 1 = AR1; 2 = 有界Pareto分布带持续性
    par['k_distrib'] = 2  # 1 = 均匀分布; 2 = Pareto分布
    par['k_lb'] = 0.1  # k_grid下界
    par['k_ub'] = 200  # k_grid上界
    par['k_min'] = par['k_lb']  # 进入者资本的均匀分布最小值
    par['tol_bhat'] = 1e-9  # 固定点B_hat(k,x)的容差
    par['tol_vfi'] = 1e-9  # VFI的容差
    par['max_iter'] = 4000  # VFI的最大迭代次数
    par['tol_vfi_u'] = 1e-9  # 无约束企业VFI的容差
    par['do_howard'] = 1  # 标志 0/1 Howard加速
    par['n_howard'] = 50
    par['tol_dist'] = 1e-6  # 分布的容差
    par['maxiter_dist'] = 10000  # 分布的最大迭代次数
    par['max_iter_tr'] = 100  # 转移动态的最大迭代次数
    par['tol_tran'] = 0.0005  # 转移动态的容差
    par['dampening'] = 1  # 二分法更新的阻尼
    par['seed'] = 67354  # 随机数生成器种子，用于fun_simulate
    par['write_calib_append'] = 0
    par['do_write_calib'] = 0
    par['N_sim'] = 80000
    par['T_sim'] = 68  # 17年
    par['emp_min'] = 0  # 微型企业的阈值。微型企业被排除在退出率计算之外。
    
    # 设置外生参数（不是内部校准的一部分）
    par['beta'] = 0.989  # 贴现因子
    par['sigma'] = 2.0  # CRRA参数
    par['alpha'] = 0.3  # 资本的Cobb-Douglas指数
    par['delta_k'] = 0.015  # 资本折旧率
    par['gamma1'] = 0.3182  # 小企业生产函数中资本的份额
    par['gamma2'] = 0.88  # 小企业f(l)中的控制跨度参数
    par['A'] = 0.25  # 企业部门生产函数转移因子
    par['lambda0'] = 1  # 抵押约束的紧度（即lam=lam0*theta*(1-delta)）
    par['cost_e'] = 0
    par['bk0_vec'] = np.array([-0.09375, 0.125, 0.8684])  # 初始债务资本比（进入者的p25,p50,p75，KFS）
    par['bk0_prob'] = np.array([0.25, 0.5, 0.25])  # bk0的概率
    # 生产率过程参数：AR1过程
    par['x0'] = 1  # Ln(x0) AR(1)的均值
    par['xi'] = 1  # 潜在进入者相对于在位者的生产率差距
    par['epsx'] = 0.12  # x'|x的AR(1)中创新的标准差
    par['rhox'] = 0.95  # x'|x的AR(1)中的持续性
    
    # 生产率过程参数：x的有界Pareto分布
    par['x_lb'] = 0.5
    par['x_ub'] = 4.0
    par['x_shape'] = 0.1
    par['x_rho'] = 0.9306
    
    # 初始资本分布参数：AR1过程
    par['k_max'] = 41
    # 初始资本分布参数：Pareto分布
    par['k_alpha'] = 0.3240858974
    
    # 从'estim_params.txt'读取参数
    print(f'从文件"{file_params}"读取参数')
    filepath = os.path.join(par.get('InpDir', 'inputs'), file_params)
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2:
                    name = parts[0]
                    try:
                        value = float(parts[1])
                        par[name] = value
                    except ValueError:
                        pass
    
    # 设置内部参数的边界
    # [第一个数字是下界，第二个数字是上界]
    bounds = {
        'mass': [0.0001, 10000],  # 潜在进入者的质量
        'fixcost1': [0.0001, 1],  # 额外固定运营成本
        'fixcost2': [0.000, 1],  # 额外固定运营成本
        'theta': [0.1, 1],  # 资本的转售价值
        'psi': [0, 0.01],  # 外生退出率
        'k_alpha': [0.1, 2],  # 资本的Pareto分布，形状
        'zeta': [0.0001, 10000.0],  # 闲暇的效用
        'x0': [0.1, 10.0],  # log(x)的均值，生产率冲击
        'epsx': [0.01, 1],  # log(x)的离散度
        'rhox': [0.5, 0.999],  # log(x)的持续性
    }
    
    # 设置参数名称，顺序与bounds和guess中出现的顺序相同
    # calibNames必须是字符串列列表
    calibNames = [
        'mass',
        'fixcost1',
        'fixcost2',
        'theta',
        'psi',
        'k_alpha',
        'x0',
        'epsx',
        'rhox',
        'zeta',
    ]
    
    # 用于latex表
    dispNames = [
        r'$ M $',
        r'$ fixcost1  $',
        r'$ fixcost2  $',
        r'$ \theta $',
        r'$ \psi $',
        r'$ \alpha_{\kappa}  $',
        r'$ \bar{x}    $',
        r'$ \varepsilon_x    $',
        r'$ \rho_x    $',
        r'$ \zeta    $',
    ]
    
    description = [
        '潜在进入者的质量',
        '截距固定成本',
        '斜率固定成本',
        '资本的转售价值',
        '外生退出率',
        '形状Pareto资本',
        'AR(1)的Ln(x0)均值',
        '$x$的离散度',
        '$x$的持续性',
        '闲暇的边际效用',
    ]
    
    # 用于外生参数表的N*3字符列表
    # col1: 字段名; col2: Latex名称; col3: 描述
    ExoNames = [
        ['beta', r'$\beta$', '主观贴现因子'],
        ['sigma', r'$\sigma$', 'CRRA系数'],
        ['alpha', r'$\alpha$', '企业部门资本份额'],
        ['delta_k', r'$\delta_k$', '资本折旧率'],
        ['lambda0', r'$\lambda_0$', '抵押约束参数'],
        ['gamma1', r'$\gamma_1$', '小企业资本份额'],
        ['gamma2', r'$\gamma_2$', '控制跨度'],
        ['A', r'$A$', 'TFP转移因子'],
    ]
    
    if len(calibNames) != len(description):
        raise ValueError("字符数组<calibNames>和<description>必须有相同数量的元素")
    
    if len(calibNames) != len(dispNames):
        raise ValueError("字符数组<calibNames>和<dispNames>必须有相同数量的元素")
    
    # guess必须是列向量
    guess = struct2vec(par, calibNames)
    
    # 生成异质性生产率x的初始网格
    if par['x_process'] == 1:
        # AR1，这是默认情况
        par['mean_x'] = (1 - par['rhox']) * np.log(par['x0'])
        par['cover'] = 3.5  # 标准值，参见Tauchen (1986)
        Tran, log_x_grid, p, arho, asigma = markovapprox(par['rhox'], par['epsx'], par['mean_x'], 
                                        par['cover'], par['nx'], disp_on_screen=False)
        par['pi_x'] = Tran
        par['x_grid'] = np.exp(log_x_grid)
    elif par['x_process'] == 2:
        # 有界Pareto带持续性
        par['x_grid'] = np.linspace(par['x_lb'], par['x_ub'], par['nx'])
        ergoeps, pie = paretojo(par['nx'], par['x_grid'], par['x_shape'], par['x_rho'])
        par['pi_x'] = pie
        par['x_prob'] = ergoeps
    else:
        raise ValueError("set_parameters: x_process无效！")
    
    # 生成资本网格
    par['k_grid'] = np.linspace(par['k_lb'], par['k_ub'], par['nk']).reshape(-1, 1)
    
    return par, guess, bounds, calibNames, dispNames, description, ExoNames

