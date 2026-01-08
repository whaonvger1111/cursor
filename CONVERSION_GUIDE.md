# MATLAB到Python转换指南

## 已转换的文件

### 核心文件
1. **fun.py** - 核心函数类（从fun.m转换）
   - 包含所有模型相关的函数（生产函数、利润函数、效用函数等）
   - 使用静态方法类实现

2. **set_parameters.py** - 参数设置（从set_parameters.m转换）
   - 设置数值和经济参数
   - 生成网格（生产率、资本）
   - 读取参数文件

3. **fun_transition.py** - 转移动态计算框架（从fun_transition.m转换）
   - 转移动态的主循环
   - 需要其他函数支持（fun_vfi1_transition, fun_distrib1_tran等）

4. **main.py** - 主程序框架（从main.m转换）
   - 程序入口点
   - 设置标志和参数

### 工具函数
- **tools/struct2vec.py** - 从字典提取向量
- **tools/markovapprox.py** - 马尔可夫链近似AR1过程
- **tools/paretojo.py** - Pareto分布计算
- **tools/bddparetocdf.py** - 有界Pareto CDF

## 主要转换模式

### 1. MATLAB结构体 → Python字典
```matlab
% MATLAB
par.T = 180;
par.nx = 60;
```
```python
# Python
par = {'T': 180, 'nx': 60}
# 或使用字典访问
par['T'] = 180
par['nx'] = 60
```

### 2. MATLAB类 → Python类
```matlab
% MATLAB
classdef fun
    methods (Static)
        function F = prod_small(x,kappa,labor,c,par)
            ...
        end
    end
end
```
```python
# Python
class Fun:
    @staticmethod
    def prod_small(x, kappa, labor, c, par):
        ...
```

### 3. MATLAB矩阵运算 → NumPy
```matlab
% MATLAB
A = zeros(10, 20);
B = A * 2;
C = sum(A, 2);
```
```python
# Python
import numpy as np
A = np.zeros((10, 20))
B = A * 2
C = np.sum(A, axis=1)
```

### 4. MATLAB文件读取 → Python文件读取
```matlab
% MATLAB
FID = fopen('file.txt');
C = textscan(FID, '%s %f');
fclose(FID);
```
```python
# Python
with open('file.txt', 'r') as f:
    lines = f.readlines()
    # 解析行
```

### 5. MATLAB优化函数 → SciPy
```matlab
% MATLAB
result = fzero(@(x) fun(x), x0);
```
```python
# Python
from scipy.optimize import fsolve
result = fsolve(lambda x: fun(x), x0)
```

## 需要继续转换的文件

### 高优先级
1. **fun_vfi1_transition.py** - 转移动态价值函数迭代
   - 这是转移动态计算的核心部分
   - 包含向后迭代算法

2. **fun_distrib1_tran.py** - 转移动态分布计算
   - 前向迭代计算企业分布
   - 需要处理多维数组

3. **fun_aggregates_tran.py** - 转移动态加总计算
   - 计算总产出、资本、劳动等

4. **fun_steady_state.py** - 稳态计算
   - 计算模型稳态
   - 包含价值函数迭代和分布计算

5. **fun_obj.py** - 目标函数
   - 用于校准和优化

### 中优先级
- set_targets_ss.py - 设置稳态目标
- set_shocks.py - 设置冲击
- set_grant.py - 设置补助参数
- fun_entry_exit.py - 进入和退出政策
- fun_pol_update.py - 政策函数更新

### 低优先级
- 绘图函数（plot_*.py）
- 表格生成函数（make_table_*.py）
- 模拟函数（fun_simulate.py）

## 转换注意事项

### 1. 数组索引
- MATLAB: 1-based indexing (数组从1开始)
- Python: 0-based indexing (数组从0开始)
- 需要仔细调整所有索引

### 2. 数组形状
- MATLAB: 列向量默认
- Python: NumPy数组需要明确指定形状
- 使用`.reshape(-1, 1)`创建列向量

### 3. 精度
- MATLAB: 使用`vpa`进行高精度计算
- Python: 可以使用`mpmath`或`decimal`模块

### 4. MEX文件
- MATLAB: 使用MEX文件加速计算
- Python: 可以使用Cython、Numba或C扩展

### 5. 文件I/O
- MATLAB: `.mat`文件使用`scipy.io.loadmat`和`scipy.io.savemat`
- Python: 使用`scipy.io`模块

## 测试建议

1. 单元测试：为每个转换的函数编写测试
2. 数值验证：与MATLAB输出比较
3. 性能测试：检查Python版本的性能

## 依赖包

所有依赖都在`requirements.txt`中：
- numpy >= 1.21.0
- scipy >= 1.7.0
- matplotlib >= 3.4.0
- pandas >= 1.3.0
- mpmath >= 1.2.0

## 下一步

1. 实现fun_vfi1_transition.py
2. 实现fun_distrib1_tran.py
3. 实现fun_aggregates_tran.py
4. 实现fun_steady_state.py
5. 测试完整流程

