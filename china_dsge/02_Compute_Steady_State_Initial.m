% 02_Compute_Steady_State_Initial.m
% 从投入产出表数据计算初始稳态值 solution_io
% solution_io结构：前42个元素=c_s，中间42个元素=n_s，最后1个元素=w

clear all; clc;

fprintf('=== 步骤2: 计算稳态初始值 ===\n\n');

%% 加载参数
if ~exist('Model_Parameters.mat', 'file')
    error('找不到Model_Parameters.mat，请先运行01_Read_IO_Data.m');
end

load('Model_Parameters.mat');

nsectors = 42;

%% 创建初始解
% solution_io结构：
% 前nsectors个元素：c_s的初始值（消费）
% 中间nsectors个元素：n_s的初始值（劳动）
% 最后1个元素：w的初始值（工资）

solution_io = zeros(2*nsectors+1, 1);

%% 1. 消费初始值：基于消费份额和总产出
fprintf('计算消费初始值...\n');

total_output_sum = sum(Total_Output);
total_consumption = 0.5 * total_output_sum;  % 假设总消费占总产出的50%

for s = 1:nsectors
    if nu_c_s(s) > 0 && total_consumption > 0
        % 基于消费份额分配
        c_s_value = nu_c_s(s) * total_consumption;
        solution_io(s) = max(c_s_value, 1e-6);  % 确保为正数
    else
        solution_io(s) = 1e-6;
    end
end

fprintf('  消费初始值范围: [%.4f, %.4f]\n', ...
    min(solution_io(1:nsectors)), max(solution_io(1:nsectors)));
fprintf('  消费总和: %.4f\n', sum(solution_io(1:nsectors)));
fprintf('\n');

%% 2. 劳动初始值：基于劳动份额
fprintf('计算劳动初始值...\n');

n_ss = 0.33;  % 总劳动供给（标准值）

% 基于各部门产出分配劳动（产出越大，劳动越多）
if sum(Total_Output) > 0
    labor_shares = Total_Output / sum(Total_Output);
else
    labor_shares = ones(nsectors, 1) / nsectors;
end

for s = 1:nsectors
    n_s_value = n_ss * labor_shares(s);
    solution_io(nsectors + s) = max(n_s_value, 1e-6);
end

fprintf('  劳动初始值范围: [%.4f, %.4f]\n', ...
    min(solution_io(nsectors+1:2*nsectors)), max(solution_io(nsectors+1:2*nsectors)));
fprintf('  劳动总和: %.4f (目标: %.4f)\n', ...
    sum(solution_io(nsectors+1:2*nsectors)), n_ss);
fprintf('\n');

%% 3. 工资初始值：设为1（标准化）
fprintf('设置工资初始值...\n');

solution_io(2*nsectors + 1) = 1.0;

fprintf('  工资初始值: %.4f\n', solution_io(2*nsectors+1));
fprintf('\n');

%% 验证
fprintf('验证初始解...\n');

if any(solution_io <= 0)
    error('初始解中包含非正值！');
end

if any(isnan(solution_io)) || any(isinf(solution_io))
    error('初始解中包含NaN或Inf！');
end

fprintf('  ✓ 所有值都为正数\n');
fprintf('  ✓ 无NaN或Inf值\n');
fprintf('  初始解维度: %d × 1\n', length(solution_io));
fprintf('\n');

%% 保存
fprintf('保存初始解...\n');

save('solution_io.mat', 'solution_io');

fprintf('  初始解已保存到 solution_io.mat\n');
fprintf('\n');

fprintf('=== 步骤2完成 ===\n\n');





















