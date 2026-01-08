# 转移动态中的价格循环分析

## 结论

转移动态中有一个**外层价格循环**（通过消费路径迭代），在这个循环内部，价格路径是**顺序计算**的（不是迭代）。

## 价格循环结构

### 1. 外层循环：消费路径迭代（二分法）

**MATLAB (`fun_transition.m`)**:
```matlab
while abs(err_tran)>tol_tran && iter<=max_iter_tr
    %% 1. 求解价格路径（给定C_init）
    path.C(1) = C_init;
    for t=1:T+1
        path.w(t) = lsupply(t)*zeta*(path.C(t))^sigma;
        path.KL_ratio(t) = ...;
        path.q(t) = ...;
        path.C(t+1) = ...;
    end
    
    %% 2. VFI和分布
    [pol_tran] = fun_vfi1_transition(...);
    [distrib_tran] = fun_distrib1_tran(...);
    
    %% 3. 加总变量
    [agg_tran] = fun_aggregates_tran(...);
    
    %% 4. 更新C_init（二分法）
    if K_agg(T+1) < agg_ss.K_agg
        C_h = damp*C_init + (1-damp)*C_h;
    else
        C_l = damp*C_init + (1-damp)*C_l;
    end
    C_init = 0.5*(C_h+C_l);
    iter = iter+1;
end
```

**Python (`fun_transition.py`)**:
```python
while abs(err_tran) > tol_tran and iter_count <= max_iter_tr:
    # 1. 求解价格路径（给定C_init）
    path['C'][0] = C_init
    for t in range(T + 1):
        path['w'][t] = lsupply[t] * zeta * (path['C'][t] ** sigma)
        path['KL_ratio'][t] = ...
        path['q'][t] = ...
        path['C'][t + 1] = ...
    
    # 2. VFI和分布
    pol_tran = fun_vfi1_transition(...)
    distrib_tran = fun_distrib1_tran(...)
    
    # 3. 加总变量
    agg_tran = fun_aggregates_tran(...)
    
    # 4. 更新C_init（二分法）
    if K_agg[T] < agg_ss['K_agg']:
        C_h = damp * C_init + (1 - damp) * C_h
    else:
        C_l = damp * C_init + (1 - damp) * C_l
    C_init = 0.5 * (C_h + C_l)
    iter_count += 1
```

## 价格计算顺序（内层，非迭代）

在每次外层迭代中，给定`C_init`，价格路径是**顺序计算**的：

### 1. 工资 (wage)

```python
for t in range(T + 1):
    path['w'][t] = lsupply[t] * zeta * (path['C'][t] ** sigma)
```

**关键点**：
- 工资依赖于消费路径`C[t]`
- 从`t=0`到`t=T`**顺序计算**
- **不是迭代**，是直接计算

### 2. 资本劳动比 (KL_ratio)

```python
for t in range(T + 1):
    if t == 0:
        path['KL_ratio'][t] = Fun.KL_tran(path['w'][t], A_corp[t], par)
    
    if t < T:
        def fun_KL_ratio(k_next):
            return Fun.dyn_eqn_capital(k_next, path['KL_ratio'][t], par, t)
        path['KL_ratio'][t + 1] = fsolve(fun_KL_ratio, path['KL_ratio'][t])
```

**关键点**：
- `KL_ratio[0]`从工资计算
- `KL_ratio[t+1]`通过求解动态方程得到（给定`KL_ratio[t]`）
- 从`t=0`到`t=T`**顺序计算**
- **不是迭代**，是顺序求解

### 3. 金融贴现因子 (q)

```python
for t in range(T + 1):
    if t < T:
        path['q'][t] = 1 / (1 - delta_k + A_corp[t + 1] * 
                            Fun.marg_prod_capital(path['KL_ratio'][t + 1], par))
    else:
        path['q'][t] = prices_ss['q']
```

**关键点**：
- `q[t]`依赖于`KL_ratio[t+1]`
- 从`t=0`到`t=T`**顺序计算**
- **不是迭代**，是直接计算

### 4. 消费路径 (C)

```python
for t in range(T + 1):
    if t < T:
        path['C'][t + 1] = path['C'][t] * ((beta * margutil[t + 1]) / 
                                           (path['q'][t] * margutil[t])) ** (1 / sigma)
```

**关键点**：
- `C[t+1]`依赖于`C[t]`和`q[t]`
- 从`t=0`到`t=T`**顺序计算**
- **不是迭代**，是顺序计算

## 价格循环总结

### 外层循环（迭代）：消费路径迭代

**目标**：找到`C[0]`使得`K_agg[T] = K_agg_ss`

**方法**：二分法
- 如果`K_agg[T] < K_agg_ss` → `C_h`减小（消费太高，资本太低）
- 如果`K_agg[T] > K_agg_ss` → `C_l`增大（消费太低，资本太高）
- `C_init = 0.5*(C_h + C_l)`

**迭代变量**：`C_init`（第1期的消费）

### 内层计算（非迭代）：价格路径顺序计算

给定`C_init`，价格路径是**顺序计算**的：
1. `C[0] = C_init`
2. `w[0] = lsupply[0] * zeta * C[0]^sigma`
3. `KL_ratio[0] = KL_tran(w[0], A_corp[0])`
4. `q[0] = 1/(1-delta_k + A_corp[1]*MPK(KL_ratio[1]))`
5. `C[1] = C[0] * ((beta*margutil[1])/(q[0]*margutil[0]))^(1/sigma)`
6. 重复步骤2-5直到`t=T`

## 价格依赖关系

```
C[0] (给定)
  ↓
w[0] = f(C[0])
  ↓
KL_ratio[0] = f(w[0])
  ↓
q[0] = f(KL_ratio[1])
  ↓
C[1] = f(C[0], q[0])
  ↓
w[1] = f(C[1])
  ↓
...
```

## 总结

**转移动态中的价格循环**：

1. **外层循环（迭代）**：
   - 变量：`C_init`（第1期消费）
   - 方法：二分法
   - 目标：使`K_agg[T] = K_agg_ss`
   - 这是**价格循环**（通过消费路径迭代）

2. **内层计算（非迭代）**：
   - 给定`C_init`，价格路径是**顺序计算**的
   - `wage`, `KL_ratio`, `q`都是顺序计算，不是迭代
   - 这是**价格路径计算**，不是价格迭代

**关键区别**：
- **稳态**：价格外生给定，没有价格循环
- **转移动态**：价格路径通过消费路径迭代求解，有一个**外层价格循环**（通过`C_init`迭代）


















