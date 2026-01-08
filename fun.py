"""
核心函数类 - 包含所有模型相关的函数（函数形式）
这是MATLAB fun.m类的Python转换版本
"""
import numpy as np


class Fun:
    """包含所有模型相关函数的静态类"""
    
    @staticmethod
    def adjcost_scal(kprime, k, theta, delta):
        """
        计算资本调整成本（标量版本）
        
        参数:
        kprime: 下一期资本，标量
        k: 当期资本，标量
        theta: 转售价值，在(0,1)之间
        delta: 折旧率
        """
        if kprime >= (1 - delta) * k:
            adj = kprime - (1 - delta) * k
        else:
            adj = theta * (kprime - (1 - delta) * k)
        return adj
    
    @staticmethod
    def adjcost(kprime, k, theta, delta):
        """
        计算资本调整成本（向量化版本）
        
        参数:
        kprime: 下一期资本，维度 (nk,) 或 (nk,1) 或其他形状
        k: 当期资本，标量或维度 (nk,) 或 (1,nk) 或其他可广播的形状
        theta: 转售价值，在(0,1)之间
        delta: 折旧率
        
        注意：当kprime是(nk,1)列向量且k是(1,nk)行向量时，
        会广播成(nk,nk)矩阵，与MATLAB行为一致
        """
        kprime = np.asarray(kprime)
        k = np.asarray(k)
        
        # numpy的广播会自动处理：
        # - kprime (nk,1) - k (1,nk) → (nk,nk)
        # - kprime (nk,) - k (nk,) → (nk,) 元素对应
        # - kprime (nk,1) - k (nk,) → (nk,nk) 如果k被广播
        
        adj = kprime - (1 - delta) * k
        mask = kprime < (1 - delta) * k
        adj[mask] = theta * adj[mask]
        return adj
    
    @staticmethod
    def fun_fixcost(k, fixcost1, fixcost2, par):
        """
        计算固定运营成本
        
        参数:
        k: 当期资本，标量
        fixcost1, fixcost2: 固定成本函数参数
        """
        return fixcost1 + fixcost2 * k
    
    @staticmethod
    def C_foc_labor(wage, par):
        """
        从劳动供给家庭的一阶条件得到消费作为工资的函数
        
        参数:
        wage: 工资
        par: 参数结构体
        """
        return (wage / par['zeta']) ** (1 / par['sigma'])
    
    @staticmethod
    def prod_corp(KL_ratio, L, par):
        """
        企业部门生产函数
        
        参数:
        KL_ratio: 资本劳动比
        L: 劳动
        par: 参数结构体
        """
        return par['A'] * (KL_ratio ** par['alpha']) * L
    
    @staticmethod
    def optimal_KL(rental, par):
        """
        给定租金率的最优KL比
        从一阶条件 "rental = 资本的边际产出" 得到
        
        参数:
        rental: 租金率
        par: 参数结构体
        """
        return (rental / (par['A'] * par['alpha'])) ** (1 / (par['alpha'] - 1))
    
    @staticmethod
    def KL_tran(wage, A_corp_t, par):
        """
        从企业部门劳动需求的一阶条件得到最优KL比
        
        参数:
        wage: 工资
        A_corp_t: 企业部门TFP
        par: 参数结构体
        """
        return (wage / ((1 - par['alpha']) * A_corp_t * par['A'])) ** (1 / par['alpha'])
    
    @staticmethod
    def marg_prod_labor(KL_ratio, par):
        """
        企业部门劳动的边际产出
        
        参数:
        KL_ratio: 资本劳动比
        par: 参数结构体
        """
        return par['A'] * (1 - par['alpha']) * (KL_ratio ** par['alpha'])
    
    @staticmethod
    def marg_prod_capital(KL_ratio, par):
        """
        企业部门资本的边际产出
        
        参数:
        KL_ratio: 资本劳动比
        par: 参数结构体
        """
        return par['A'] * par['alpha'] * (KL_ratio ** (par['alpha'] - 1))
    
    @staticmethod
    def prod_small(x, kappa, labor, c, par):
        """
        小企业部门生产函数，依赖于生产率"x"、资本"kappa"、劳动和固定成本c
        注意：c是依赖于kappa的固定成本
        
        参数:
        x: 生产率
        kappa: 资本
        labor: 劳动
        c: 固定成本
        par: 参数结构体
        """
        A = par['A']
        gamma1 = par['gamma1']
        gamma2 = par['gamma2']
        return A * x * ((kappa ** gamma1) * (labor ** (1 - gamma1))) ** gamma2 - c
    
    @staticmethod
    def fun_l(x, wage, k, par):
        """
        具有生产率x和资本k的小企业的劳动需求
        
        参数:
        x: 异质性生产率
        k: 资本
        wage: 工资
        par: 参数结构体
        """
        gamma1 = par['gamma1']
        gamma2 = par['gamma2']
        aux = (1 - gamma1) * gamma2
        # 避免除零：确保分母不为零
        aux_minus_one = aux - 1
        
        # 处理标量和数组情况
        x = np.asarray(x)
        k = np.asarray(k)
        wage = np.asarray(wage)
        
        # 如果 aux_minus_one 接近 0，使用极限情况
        if isinstance(aux_minus_one, np.ndarray):
            # 数组情况：向量化处理
            aux_minus_one = np.where(np.abs(aux_minus_one) < 1e-10,
                                    np.where(aux_minus_one >= 0, 1e-10, -1e-10),
                                    aux_minus_one)
        else:
            # 标量情况
            if abs(aux_minus_one) < 1e-10:
                aux_minus_one = 1e-10 if aux_minus_one >= 0 else -1e-10
        
        # 避免除零：确保分母不为零
        denominator = par['A'] * x * aux
        
        # 处理标量和数组情况
        if isinstance(denominator, np.ndarray):
            # 数组情况：向量化处理
            denominator = np.where(np.abs(denominator) < 1e-10,
                                  np.where(denominator >= 0, 1e-10, -1e-10),
                                  denominator)
        else:
            # 标量情况
            if abs(denominator) < 1e-10:
                denominator = 1e-10 if denominator >= 0 else -1e-10
        
        return (wage / denominator) ** (1 / aux_minus_one) * (k ** (-gamma1 * gamma2 / aux_minus_one))
    
    @staticmethod
    def fun_profit(x, k, c, wage, par):
        """
        具有生产率x和资本k的小企业的静态利润
        固定成本c^f已经包含在fun.prod_small中
        
        参数:
        x: 生产率
        k: 资本
        c: 固定成本
        wage: 工资
        par: 参数结构体
        """
        l_small = Fun.fun_l(x, wage, k, par)
        return Fun.prod_small(x, k, l_small, c, par) - wage * l_small
    
    @staticmethod
    def dyn_eqn_capital(k_next, k_current, par, t):
        """
        转移动态期间要解决的资本差分方程
        
        参数:
        k_next: 下一期资本
        k_current: 当期资本
        par: 参数结构体
        t: 时间索引
        """
        k_next = max(k_next, 1e-10)
        
        lhs = par['beta'] * (k_current ** par['alpha'])
        rhs1 = (par['A_corp'][t+1] * par['margutil'][t] * par['lsupply'][t] / 
                (par['A_corp'][t] * par['margutil'][t+1] * par['lsupply'][t+1]))
        rhs2 = (k_next ** par['alpha']) / (1 - par['delta_k'] + 
                                           par['alpha'] * par['A_corp'][t+1] * 
                                           par['A'] * (k_next ** (par['alpha'] - 1)))
        
        return lhs - rhs1 * rhs2
    
    @staticmethod
    def utility_consumption(C, D, par):
        """
        给定消费C和效用转移因子D的消费效用
        
        参数:
        C: 消费
        D: 效用转移因子
        par: 参数结构体
        """
        return D * (C ** (1 - par['sigma'])) / (1 - par['sigma'])
    
    @staticmethod
    def utility_leisure(L, zeta_shift, par):
        """
        给定劳动供给L和zeta转移因子的闲暇效用
        
        参数:
        L: 劳动供给
        zeta_shift: zeta转移因子
        par: 参数结构体
        """
        return par['zeta'] * zeta_shift * (1 - L)
    
    @staticmethod
    def utility(C, D, L, zeta_shifter, par):
        """
        给定消费C、效用转移因子D、劳动供给L和zeta转移因子的效用
        
        参数:
        C: 消费
        D: 效用转移因子
        L: 劳动供给
        zeta_shifter: zeta转移因子
        par: 参数结构体
        """
        return (Fun.utility_consumption(C, D, par) + 
                Fun.utility_leisure(L, zeta_shifter, par))

