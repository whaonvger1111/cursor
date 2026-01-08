# 稳态中如何保证均衡？

## 核心问题

如果稳态中没有工资利率价格循环，如何保证均衡？

## 答案：部分均衡模型 + 参数校准

### 1. 价格是外生给定的（不是通过市场出清确定的）

**价格计算（`fun_prices.py`）**：
```python
def fun_prices(par):
    q = par['beta']  # 金融贴现因子 = 消费者贴现因子
    FK = 1 / q + par['delta_k'] - 1  # 企业部门MPK
    rental = FK  # 租金率
    KL_ratio = Fun.optimal_KL(rental, par)  # 企业部门资本劳动比
    wage = Fun.marg_prod_labor(KL_ratio, par)  # 实际工资
```

**关键点**：
- 价格**完全由参数决定**，不依赖于市场出清条件
- `q = beta`：金融贴现因子等于消费者贴现因子
- `rental = 1/q + delta_k - 1`：租金率由贴现因子和折旧率决定
- `KL_ratio`：从租金率通过企业最优化得到
- `wage`：从KL_ratio通过边际生产率得到

**这不是一般均衡**：价格不是通过市场出清条件迭代得到的。

### 2. 市场出清方程用来计算数量（不是确定价格）

**市场出清方程（`fun_aggregates.py`）**：
```python
# 市场出清方程的左端（第49页）
LHS = C_agg - output_small + cost_adj + entry_cost - liq
aux = Fun.prod_corp(KL_ratio, 1 / KL_ratio, par) - delta_k

# 企业部门资本
K_corp = LHS / aux
```

**市场出清方程的含义**：
- **LHS**：消费 + 调整成本 + 进入成本 - 小企业产出 - 清算
- **aux**：企业部门净收益率 = `A * (KL_ratio^alpha) - delta_k`
- **K_corp**：企业部门资本 = `LHS / aux`

**关键点**：
- 市场出清方程**不是用来确定价格的**
- 市场出清方程**是用来计算K_corp的**
- 给定价格，市场出清条件决定了企业部门资本的数量

### 3. 如何保证均衡？

#### 方法1：参数校准（主要方法）

**参数校准过程**：
1. **给定目标矩**：模型需要匹配一些数据矩（如企业规模分布、进入率、退出率等）
2. **调整参数**：通过调整参数（如`zeta`, `mass`, `theta`, `psi`, `fixcost1`, `fixcost2`等）使得：
   - 模型矩匹配数据矩
   - **同时**，市场出清条件能够满足（`LHS > 0`, `aux > 0`, `K_corp > 0`）

**校准目标**：
- 匹配数据矩（企业规模分布、进入率、退出率等）
- **隐含地**，确保市场出清条件能够满足

**如果参数没有正确校准**：
- `LHS < 0` → `K_corp < 0` → 不是有效的均衡
- `aux <= 0` → `K_corp`无法计算或为负值 → 不是有效的均衡

#### 方法2：模型设计（部分均衡）

**部分均衡模型的特点**：
- 价格是**外生给定的**（由参数决定）
- 市场出清条件用来**计算数量**（K_corp），而不是确定价格
- 不需要价格迭代循环

**为什么这是合理的？**
- 如果模型是**小企业部门模型**，企业部门（corporate sector）的价格可以看作是外生给定的
- 小企业部门是**价格接受者**（price taker）
- 企业部门的价格由**大企业部门**或**外生因素**决定

### 4. 均衡的定义

在部分均衡模型中，**均衡**意味着：

1. **价格一致性**：
   - 价格由参数决定（`q = beta`, `rental = 1/q + delta_k - 1`等）
   - 价格满足企业最优化条件（`KL_ratio = optimal_KL(rental)`）

2. **市场出清**：
   - 给定价格，市场出清条件决定了企业部门资本`K_corp`
   - `K_corp = LHS / aux`，其中`LHS`和`aux`都是正数

3. **分布一致性**：
   - 企业分布`mu`是平稳分布（满足进入和退出平衡）
   - 分布与价格和政策函数一致

### 5. 与一般均衡模型的对比

#### 一般均衡模型

```python
# 伪代码
while not converged:
    # 给定价格，计算VFI和分布
    sol = fun_vfi1(prices, par)
    distrib = fun_distrib1(sol, par)
    
    # 计算市场出清条件
    L_demand = compute_labor_demand(distrib, sol)
    K_demand = compute_capital_demand(distrib, sol)
    
    # 更新价格（市场出清）
    if L_demand != L_supply:
        wage = update_wage(wage, L_demand, L_supply)
    if K_demand != K_supply:
        rental = update_rental(rental, K_demand, K_supply)
```

**特点**：
- 价格通过市场出清条件**迭代**得到
- 需要价格循环

#### 部分均衡模型（本模型）

```python
# 伪代码
# 1. 价格外生给定
prices = fun_prices(par)  # 从参数直接计算

# 2. 给定价格，计算VFI和分布
sol = fun_vfi1(prices, par)
distrib = fun_distrib1(sol, par)

# 3. 市场出清条件用来计算数量
LHS = C_agg - output_small + cost_adj + entry_cost - liq
aux = prod_corp(KL_ratio) - delta_k
K_corp = LHS / aux  # 计算企业部门资本
```

**特点**：
- 价格**不迭代**，从参数直接计算
- 市场出清条件用来**计算数量**，不是确定价格

### 6. 为什么当前稳态可能有负值？

**问题**：
- `LHS < 0` → `K_corp < 0`
- `cost_adj < 0`
- `entry_vec`有负值

**原因**：
- **参数没有正确校准**：当前参数集（特别是从`estim_params.txt`读取的参数）可能没有经过完整的校准过程
- **参数不匹配**：某些参数（如`zeta`, `mass`, `theta`, `psi`, `fixcost1`, `fixcost2`）可能不适合当前的价格设置

**解决方案**：
- **参数校准**：通过校准参数使得：
  1. 模型矩匹配数据矩
  2. 市场出清条件满足（`LHS > 0`, `aux > 0`, `K_corp > 0`）

### 7. 总结

**稳态中如何保证均衡？**

1. **价格外生给定**：
   - 价格从参数直接计算（`q = beta`, `rental = 1/q + delta_k - 1`等）
   - 不通过市场出清条件迭代

2. **市场出清条件计算数量**：
   - 给定价格，市场出清条件决定了企业部门资本`K_corp`
   - `K_corp = LHS / aux`

3. **参数校准保证均衡**：
   - 通过校准参数使得：
     - 模型矩匹配数据矩
     - 市场出清条件满足（`LHS > 0`, `aux > 0`, `K_corp > 0`）

4. **模型类型**：
   - 这是**部分均衡模型**，不是一般均衡模型
   - 小企业部门是价格接受者
   - 企业部门的价格由外生因素决定

**关键区别**：
- **一般均衡**：价格通过市场出清条件迭代 → 需要价格循环
- **部分均衡**：价格外生给定，市场出清条件计算数量 → **不需要价格循环**


















