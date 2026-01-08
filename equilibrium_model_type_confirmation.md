# 模型类型确认：局部均衡 vs 一般均衡

## 明确结论

**是的，MATLAB代码也是局部均衡模型（Partial Equilibrium Model），不是一般均衡模型（General Equilibrium Model）**

## 关键证据

### 1. 价格外生给定（不依赖于市场出清）

**MATLAB代码 (`fun_prices.m`)**:
```matlab
q        = par.beta;                          % 金融贴现因子 
FK       = 1/q + par.delta_k -1;              % MPK企业部门
rental   = FK;                                % 租金率
KL_ratio = fun.optimal_KL(rental,par);        % 企业部门资本劳动比
wage     = fun.marg_prod_labor(KL_ratio,par); % 实际工资
```

**关键点**：
- 价格**只依赖于参数**（`beta`, `delta_k`, `A`, `alpha`）
- 价格**不依赖于**分布（`mu`, `mu_active`）或加总变量（`K_corp`, `L_corp`等）
- 价格在**开始时计算一次**，之后不再更新

### 2. 稳态计算流程（没有价格迭代）

**MATLAB (`fun_steady_state.m`)**:
```matlab
%% Step 1: prices
[prices] = fun_prices(par);  % 价格外生给定，只计算一次

%% Step 2: Value function iter
[sol,b_grid,phi_dist,flag_vf] = fun_vfi1(prices,par);  % 给定价格求解VFI

%% Distribution
[mu,mu_active,entry_vec,flag_mu,dist,iter_mu] = fun_distrib1(...);  % 计算分布

%% Aggregate variables
[agg] = fun_aggregates(par,sol,distribS,phi_dist,prices);  % 计算加总变量
```

**关键点**：
- 价格在Step 1计算一次
- **没有回到Step 1的迭代循环**
- **没有价格更新机制**
- **没有一般均衡求解**

### 3. 市场出清方程的作用（用于计算，不用于确定价格）

**MATLAB (`fun_aggregates.m`)**:
```matlab
% Left-hand side of market clearing eq. on page 49:
LHS = C_agg-output_small+cost_adj+entry_cost-liq;
aux = fun.prod_corp(KL_ratio,1/KL_ratio,par)-delta_k;

% Capital in corporate sector:
K_corp = LHS/aux;
```

**关键点**：
- 市场出清方程用于**计算**`K_corp`
- **不是**用于确定价格（`wage`, `KL_ratio`, `q`）
- 如果`LHS < 0`，`K_corp`就会为负值
- **没有检查或修正机制**

### 4. 参数校准的作用

**MATLAB (`fun_obj.m`)**:
```matlab
% fun_steady_state solves the steady-state of the model
[sol,agg,b_grid,distribS,prices,model_mom,flag_ss,par] = fun_steady_state(par);

if agg.K_corp<0
    warning("Capital in corporate sector is negative!")
    % 继续执行，不返回错误
end
```

**关键点**：
- 参数校准通过`fun_obj`进行
- 校准目标是使模型矩匹配数据矩
- **不是**使市场出清条件满足（虽然这可能是一个间接结果）
- 即使`K_corp < 0`，代码也继续执行

## 局部均衡 vs 一般均衡的区别

### 局部均衡模型（本模型）：
1. ✅ **价格外生给定**：价格由参数决定，不依赖于市场出清
2. ✅ **市场出清用于计算**：市场出清条件用于计算加总变量
3. ✅ **没有价格迭代**：价格在开始时确定，之后不再更新
4. ✅ **参数校准**：需要通过参数校准来（间接）满足市场出清条件

### 一般均衡模型（本模型不是）：
1. ❌ **价格由市场出清确定**：价格必须满足市场出清条件
2. ❌ **价格迭代**：价格迭代直到市场出清
3. ❌ **价格依赖于分布**：价格依赖于分布和加总变量
4. ❌ **市场出清用于确定价格**：市场出清条件用于确定价格，而不是计算加总变量

## 为什么会出现负值？

### 在局部均衡模型中：
- 价格是外生给定的（基于`beta`和`delta_k`）
- 如果参数校准不当，市场出清条件可能不满足
- 导致`LHS < 0`，`K_corp < 0`
- **这是参数校准问题，不是代码错误**

### 在一般均衡模型中：
- 价格由市场出清条件确定
- 如果市场出清条件不满足，价格会调整
- 不会出现`K_corp < 0`的情况（除非模型本身有问题）

## 总结

**MATLAB和Python代码都是局部均衡模型**：
- ✅ 价格外生给定（基于参数）
- ✅ 市场出清用于计算加总变量
- ✅ 需要通过参数校准来（间接）满足市场出清条件
- ✅ Python代码实现与MATLAB完全一致

**当前问题**：
- 参数校准不当导致市场出清条件不满足
- `LHS < 0`，`K_corp < 0`
- 这是参数校准问题，不是代码错误或模型设计问题

**这不是一般均衡模型**，因为：
- 价格不由市场出清条件确定
- 没有价格迭代机制
- 价格不依赖于分布或加总变量


















