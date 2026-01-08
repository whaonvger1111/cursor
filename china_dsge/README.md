# 中国42部门DSGE模型 - 政府支出乘数研究

## 项目概述

本项目基于中国42部门投入产出表构建DSGE模型，研究政府支出乘数。采用"先计算稳态，再赋值给Dynare"的工作流程。

## 文件结构

```
china_dsge/
├── Run_China_DSGE.m           # 主运行脚本（一键运行所有步骤）
├── 01_Read_IO_Data.m          # 步骤1: 读取投入产出表并提取参数
├── 02_Compute_Steady_State_Initial.m  # 步骤2: 计算稳态初始值
├── 03_Make_SS_Model.m         # 步骤3: 生成稳态计算脚本
├── 04_Compute_Steady_State.m   # 步骤4: 计算稳态值
├── 05_Write_Dynare_Script.m   # 步骤5: 生成Dynare模型文件
├── 06_Run_Dynare.m            # 步骤6: 运行Dynare求解
├── 07_Compute_Multiplier.m    # 步骤7: 计算政府支出乘数
├── README.md                   # 本文件
│
├── Model_Parameters.mat        # 生成的参数文件
├── solution_io.mat             # 初始稳态值
├── SS_Model.m                 # 生成的稳态计算脚本
├── Final_Steady_State.mat      # 稳态值
├── dynare_script.mod           # Dynare模型文件
├── RESULTS.mat                 # Dynare结果
└── Multipliers.mat             # 乘数结果
```

## 数据要求

- **投入产出表**: `C:\Users\Administrator\Desktop\china_inoutput\input_output_china.xlsx`
  - 需要包含名为"42部门"的工作表
  - 数据格式需符合标准投入产出表结构

## 使用方法

### 方法1: 一键运行（推荐）

在MATLAB中运行：

```matlab
cd china_dsge
Run_China_DSGE
```

这将自动执行所有步骤。

### 方法2: 分步运行

如果需要分步执行或调试：

```matlab
cd china_dsge

% 步骤1: 读取数据并提取参数
01_Read_IO_Data

% 步骤2: 计算稳态初始值
02_Compute_Steady_State_Initial

% 步骤3: 生成稳态计算脚本
03_Make_SS_Model

% 步骤4: 计算稳态
04_Compute_Steady_State

% 步骤5: 生成Dynare模型文件
05_Write_Dynare_Script

% 步骤6: 运行Dynare（需要Dynare已安装）
06_Run_Dynare

% 步骤7: 计算乘数
07_Compute_Multiplier
```

## 输出结果

### 主要输出文件

1. **Model_Parameters.mat**: 包含所有模型参数
   - `nu_h_s_x`: 投入产出矩阵 (42×42)
   - `nu_c_s`: 消费份额 (42×1)
   - `nu_inv_s`: 投资份额 (42×1)
   - `nu_g_s`: 政府支出份额 (42×1)
   - `alpha_n_s`: 劳动份额 (42×1)
   - `alpha_k_s`: 资本份额 (42×1)
   - `phi_s`: 价格粘性参数 (42×1)

2. **Final_Steady_State.mat**: 包含所有稳态值
   - 各部门价格、数量、权重等
   - 总量变量（消费、投资、增加值等）

3. **Multipliers.mat**: 包含乘数结果
   - `Mult_VA`: 增加值乘数
   - `Mult_C`: 消费乘数
   - `Mult_INV`: 投资乘数
   - `trough_inv`: 投资最低点

### 结果解读

- **Mult_VA**: 政府支出增加1单位，增加值增加Mult_VA单位
- **Mult_C**: 政府支出增加1单位，消费增加Mult_C单位
- **Mult_INV**: 政府支出增加1单位，投资增加Mult_INV单位

## 系统要求

- MATLAB R2018b或更高版本
- Dynare 4.5或更高版本（用于步骤6）
- Excel文件读取支持（用于步骤1）

## 注意事项

1. **数据路径**: 确保投入产出表文件路径正确
   - 默认路径: `C:\Users\Administrator\Desktop\china_inoutput\input_output_china.xlsx`
   - 如需修改，请编辑 `01_Read_IO_Data.m` 中的路径

2. **Dynare安装**: 步骤6需要Dynare已正确安装并配置
   - 确保Dynare在MATLAB路径中
   - 运行 `dynare` 命令测试是否安装成功

3. **计算时间**: 
   - 步骤1-5: 通常几秒到几分钟
   - 步骤6（Dynare求解）: 可能需要几分钟到几十分钟，取决于计算机性能

4. **内存要求**: 42部门模型较大，建议至少8GB内存

## 故障排除

### 问题1: Excel文件读取失败
- 检查文件路径是否正确
- 确保Excel文件格式正确
- 确保工作表名称是"42部门"

### 问题2: 稳态计算失败
- 检查 `solution_io.mat` 中的初始值是否合理
- 检查 `Model_Parameters.mat` 中的参数是否有效
- 查看 `04_Compute_Steady_State.m` 输出的警告信息

### 问题3: Dynare运行失败
- 检查Dynare是否正确安装
- 检查 `dynare_script.mod` 文件是否正确生成
- 检查稳态值是否有效（无NaN、Inf、负值）

### 问题4: 乘数结果异常
- 检查 `RESULTS.mat` 中的IRF结果是否合理
- 检查稳态值是否正确
- 检查折现因子beta是否合理（通常接近1）

## 参考文件

- 参考代码: `C:\Users\Administrator\Desktop\government multiplier_dynare\ReplicationPackage\Models\Het_China\`
- 数据目录: `C:\Users\Administrator\Desktop\china_inoutput\`

## 联系信息

如有问题，请检查：
1. 各步骤的输出信息
2. MATLAB命令窗口的错误信息
3. 生成的中间文件内容





















