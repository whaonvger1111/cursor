# 模型设计分析：局部均衡 vs 一般均衡

## 结论

**是的，MATLAB代码也是局部均衡模型（Partial Equilibrium Model）**

## 证据

### 1. 价格是外生给定的

**MATLAB代码 (`fun_prices.m`)**:
```matlab
q        = par.beta;                          % 金融贴现因子 
FK       = 1/q + par.delta_k -1;              % MPK企业部门
rental   = FK;                                % 租金率
KL_ratio = fun.optimal_KL(rental,par);        % 企业部门资本劳动比
wage     = fun.marg_prod_labor(KL_ratio,par); % 实际工资
```

**Python代码 (`fun_prices.py`)**:
```python
q = par['beta']  # 金融贴现因子
FK = 1 / q + par['delta_k'] - 1  # 企业部门MPK
rental = FK  # 租金率
KL_ratio = Fun.optimal_KL(rental, par)  # 企业部门资本劳动比
wage = Fun.marg_prod_labor(KL_ratio, par)  # 实际工资
```

**关键点**：
- 价格**不依赖于**分布或加总变量
- 价格**只依赖于**参数（`beta`, `delta_k`, `A`, `alpha`）
- **没有价格迭代机制**

### 2. 稳态计算流程

**MATLAB (`fun_steady_state.m`)**:
```matlab
%% Step 1: prices
[prices] = fun_prices(par);  % 价格外生给定

%% Step 2: Value function iter
[sol,b_grid,phi_dist,flag_vf] = fun_vfi1(prices,par);  % 给定价格求解VFI

%% Distribution
[mu,mu_active,entry_vec,flag_mu,dist,iter_mu] = fun_distrib1(par,sol,b_grid,phi_dist);  % 计算分布

%% Aggregate variables
[agg] = fun_aggregates(par,sol,distribS,phi_dist,prices);  % 计算加总变量
```

**流程**：
1. **价格外生给定**（Step 1）
2. 给定价格，求解VFI（Step 2）
3. 计算分布（Step 3）
4. 计算加总变量（Step 4）
5. **没有回到Step 1的迭代**

### 3. 市场出清方程的作用

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
- **不是**用于确定价格
- 如果`LHS < 0`，`K_corp`就会为负值
- **没有检查或修正机制**

### 4. 没有一般均衡迭代

**搜索结果显示**：
- ❌ 没有价格迭代循环
- ❌ 没有一般均衡求解
- ❌ 没有市场出清条件用于确定价格
- ✅ 价格完全外生给定

## 模型类型：局部均衡模型

### 局部均衡模型的特征：
1. ✅ **价格外生给定**：价格由参数决定，不依赖于市场出清
2. ✅ **市场出清用于计算**：市场出清条件用于计算加总变量，而不是确定价格
3. ✅ **没有价格迭代**：价格在开始时确定，之后不再更新
4. ✅ **参数校准**：需要通过参数校准来满足市场出清条件

### 一般均衡模型的特征（本模型不具备）：
1. ❌ 价格由市场出清条件确定
2. ❌ 价格迭代直到市场出清
3. ❌ 价格依赖于分布和加总变量

## 为什么会出现负值？

### 在局部均衡模型中：
- 价格是外生给定的（基于`beta`和`delta_k`）
- 如果参数校准不当，市场出清条件可能不满足
- 导致`LHS < 0`，`K_corp < 0`

### 解决方案：
1. **参数校准**：通过`fun_obj`调整参数，使市场出清条件满足
2. **不是代码错误**：这是模型设计的特征，不是实现错误

## 总结

**MATLAB和Python代码都是局部均衡模型**：
- ✅ 价格外生给定
- ✅ 市场出清用于计算加总变量
- ✅ 需要通过参数校准来满足市场出清条件
- ✅ Python代码实现与MATLAB完全一致

**当前问题**：
- 参数校准不当导致市场出清条件不满足
- `LHS < 0`，`K_corp < 0`
- 这是参数校准问题，不是代码错误


















