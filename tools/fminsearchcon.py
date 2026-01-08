"""
带约束的fminsearch
这是MATLAB fminsearch的约束版本
支持边界约束、线性不等式约束和非线性约束
"""
import numpy as np
from scipy.optimize import minimize


def fminsearchcon(fun, x0, LB=None, UB=None, A=None, b=None, nonlcon=None, options=None, *args):
    """
    带约束的fminsearch
    
    参数:
    fun: 目标函数
    x0: 初始猜测
    LB: 下界向量或数组，必须与x0相同大小
    UB: 上界向量或数组，必须与x0相同大小
    A, b: (可选)线性不等式约束 A*x <= b
    nonlcon: (可选)非线性不等式约束函数，返回nonlcon(x) <= 0
    options: 选项字典
    *args: 传递给fun的额外参数
    
    返回:
    x: 最优解
    fval: 最优值
    exitflag: 退出标志
    output: 输出字典
    """
    x0 = np.asarray(x0).flatten()
    n = len(x0)
    
    # 设置边界
    bounds = None
    if LB is not None or UB is not None:
        if LB is None:
            LB = np.full(n, -np.inf)
        if UB is None:
            UB = np.full(n, np.inf)
        LB = np.asarray(LB).flatten()
        UB = np.asarray(UB).flatten()
        bounds = list(zip(LB, UB))
        
        # 确保x0在边界内
        x0 = np.clip(x0, LB, UB)
    
    # 设置约束
    constraints = []
    
    # 线性不等式约束 A*x <= b
    if A is not None and b is not None:
        A = np.asarray(A)
        b = np.asarray(b).flatten()
        constraints.append({
            'type': 'ineq',
            'fun': lambda x: b - A @ x
        })
    
    # 非线性约束
    if nonlcon is not None:
        constraints.append({
            'type': 'ineq',
            'fun': nonlcon
        })
    
    # 如果没有约束，使用L-BFGS-B
    # 如果有约束，使用SLSQP或trust-constr
    if len(constraints) == 0:
        method = 'L-BFGS-B'
    else:
        method = 'SLSQP'
    
    # 使用scipy.optimize.minimize
    result = minimize(
        fun,
        x0,
        method=method,
        bounds=bounds,
        constraints=constraints if len(constraints) > 0 else None,
        options=options,
        args=args if len(args) > 0 else ()
    )
    
    output = {
        'iterations': result.nit,
        'funcCount': result.nfev,
        'algorithm': method,
        'message': result.message
    }
    
    exitflag = 1 if result.success else 0
    
    return result.x, result.fun, exitflag, output

