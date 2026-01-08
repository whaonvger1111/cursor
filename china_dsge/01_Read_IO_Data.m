% 01_Read_IO_Data.m
% 读取中国42部门投入产出表并提取模型参数
% 参考: C:\Users\Administrator\Desktop\china_inoutput\Generate_China_Model_Parameters.m

clear all; clc;

fprintf('=== 步骤1: 读取投入产出表并提取参数 ===\n\n');

%% 设置路径
io_data_dir = 'C:/Users/Administrator/Desktop/china_inoutput';
excel_file = fullfile(io_data_dir, 'input_output_china.xlsx');

%% 读取Excel文件
fprintf('读取Excel文件: %s\n', excel_file);

try
    data_cell = readcell(excel_file, 'Sheet', '42部门');
    fprintf('  成功读取Excel文件\n');
catch ME
    error('无法读取Excel文件: %s', ME.message);
end

data_matrix = data_cell;
fprintf('  数据维度: %d × %d\n', size(data_matrix));
fprintf('\n');

%% 提取USE表（中间投入矩阵）
fprintf('提取USE表（中间投入矩阵）...\n');

start_row = 5;
end_row = start_row + 41;
start_col = 4;

USE_table = zeros(42, 42);
for i = 1:42
    row_idx = start_row + i - 1;
    for j = 1:42
        col_idx = start_col + j - 1;
        if row_idx <= size(data_matrix, 1) && col_idx <= size(data_matrix, 2)
            val = data_matrix{row_idx, col_idx};
            if isnumeric(val) && ~isnan(val)
                USE_table(i, j) = double(val);
            elseif ischar(val) || isstring(val)
                try
                    USE_table(i, j) = str2double(char(val));
                catch
                    USE_table(i, j) = 0;
                end
            end
        end
    end
end

fprintf('  USE表维度: %d × %d\n', size(USE_table));
fprintf('  非零元素: %d (%.2f%%)\n', nnz(USE_table), 100*nnz(USE_table)/numel(USE_table));
fprintf('  USE表总和: %.2f\n', sum(USE_table(:)));
fprintf('\n');

%% 提取总产出
fprintf('提取总产出...\n');

ti_row = 53;
Total_Output = zeros(42, 1);

for i = 1:42
    col_idx = start_col + i - 1;
    if ti_row <= size(data_matrix, 1) && col_idx <= size(data_matrix, 2)
        val = data_matrix{ti_row, col_idx};
        if isnumeric(val) && ~isnan(val)
            Total_Output(i) = double(val);
        elseif ischar(val) || isstring(val)
            try
                Total_Output(i) = str2double(char(val));
                if isnan(Total_Output(i)), Total_Output(i) = 0; end
            catch
                Total_Output(i) = 0;
            end
        end
    end
end

if sum(Total_Output) < 1e-6
    warning('总产出数据可能有问题，尝试从中间投入和增加值计算');
    tii_row = 47;
    tva_row = 52;
    for i = 1:42
        col_idx = start_col + i - 1;
        tii_val = 0;
        tva_val = 0;
        if tii_row <= size(data_matrix, 1) && col_idx <= size(data_matrix, 2)
            val = data_matrix{tii_row, col_idx};
            if isnumeric(val) && ~isnan(val), tii_val = double(val); end
        end
        if tva_row <= size(data_matrix, 1) && col_idx <= size(data_matrix, 2)
            val = data_matrix{tva_row, col_idx};
            if isnumeric(val) && ~isnan(val), tva_val = double(val); end
        end
        Total_Output(i) = tii_val + tva_val;
    end
end

fprintf('  总产出维度: %d × 1\n', length(Total_Output));
fprintf('  总产出总和: %.2f\n', sum(Total_Output));
fprintf('  总产出范围: [%.2f, %.2f]\n', min(Total_Output), max(Total_Output));
fprintf('\n');

%% 提取最终需求
fprintf('提取最终需求...\n');

Final_Demand = zeros(42, 3);
consumption_col = 48;
govt_cons_col = 49;
investment_col = 53;

for i = 1:42
    row_idx = start_row + i - 1;
    
    if row_idx <= size(data_matrix, 1) && consumption_col <= size(data_matrix, 2)
        val = data_matrix{row_idx, consumption_col};
        if isnumeric(val) && ~isnan(val)
            Final_Demand(i, 1) = double(val);
        elseif ischar(val) || isstring(val)
            try
                Final_Demand(i, 1) = str2double(char(val));
                if isnan(Final_Demand(i, 1)), Final_Demand(i, 1) = 0; end
            catch
                Final_Demand(i, 1) = 0;
            end
        end
    end
    
    if row_idx <= size(data_matrix, 1) && govt_cons_col <= size(data_matrix, 2)
        val = data_matrix{row_idx, govt_cons_col};
        if isnumeric(val) && ~isnan(val)
            govt_cons_val = double(val);
        elseif ischar(val) || isstring(val)
            try
                govt_cons_val = str2double(char(val));
                if isnan(govt_cons_val), govt_cons_val = 0; end
            catch
                govt_cons_val = 0;
            end
        else
            govt_cons_val = 0;
        end
        Final_Demand(i, 1) = Final_Demand(i, 1) + govt_cons_val;
        Final_Demand(i, 3) = govt_cons_val;
    end
    
    if row_idx <= size(data_matrix, 1) && investment_col <= size(data_matrix, 2)
        val = data_matrix{row_idx, investment_col};
        if isnumeric(val) && ~isnan(val)
            Final_Demand(i, 2) = double(val);
        elseif ischar(val) || isstring(val)
            try
                Final_Demand(i, 2) = str2double(char(val));
                if isnan(Final_Demand(i, 2)), Final_Demand(i, 2) = 0; end
            catch
                Final_Demand(i, 2) = 0;
            end
        end
    end
end

if any(Final_Demand(:) < 0)
    warning('某些最终需求值为负，尝试从总产出和中间使用计算');
    intermediate_use = sum(USE_table, 2);
    final_use = Total_Output - intermediate_use;
    final_use(final_use < 0) = 0;
    
    if sum(Final_Demand(:)) < 0 || sum(Final_Demand(:)) < sum(final_use) * 0.1
        fprintf('  使用从总产出计算的最终使用\n');
        Final_Demand(:, 1) = final_use * 0.50;
        Final_Demand(:, 2) = final_use * 0.45;
        Final_Demand(:, 3) = final_use * 0.05;
    end
end

fprintf('  最终需求维度: %d × 3\n', size(Final_Demand));
fprintf('  消费总和: %.2f\n', sum(Final_Demand(:, 1)));
fprintf('  投资总和: %.2f\n', sum(Final_Demand(:, 2)));
fprintf('  政府购买总和: %.2f\n', sum(Final_Demand(:, 3)));
fprintf('\n');

%% 计算投入产出矩阵 nu_h_s_x
fprintf('计算投入产出矩阵 nu_h_s_x...\n');

nsectors = 42;
A = zeros(nsectors, nsectors);
for j = 1:nsectors
    if Total_Output(j) > 0
        A(:, j) = USE_table(:, j) / Total_Output(j);
    else
        warning('部门 %d 的总产出为0或负数！', j);
        A(:, j) = 0;
    end
end

nu_h_s_x = A;

fprintf('  投入产出矩阵计算完成\n');
fprintf('  非零元素比例: %.2f%%\n', 100 * nnz(nu_h_s_x) / numel(nu_h_s_x));
fprintf('  列和范围: [%.4f, %.4f]\n', min(sum(nu_h_s_x, 1)), max(sum(nu_h_s_x, 1)));
fprintf('\n');

%% 计算中间品投入份额
fprintf('计算中间品投入份额...\n');

total_intermediate_inputs = sum(USE_table, 1)';
alpha_h_s = total_intermediate_inputs ./ Total_Output;
alpha_h_s(isnan(alpha_h_s)) = 0;
alpha_h_s(isinf(alpha_h_s)) = 0;
alpha_h = sum(total_intermediate_inputs) / sum(Total_Output);

fprintf('  中间品投入份额计算完成\n');
fprintf('  总体中间品投入份额 alpha_h: %.4f\n', alpha_h);
fprintf('  各部门份额范围: [%.4f, %.4f]\n', min(alpha_h_s), max(alpha_h_s));
fprintf('\n');

%% 计算最终需求份额
fprintf('计算最终需求份额...\n');

consumption = Final_Demand(:, 1);
total_consumption = sum(consumption);
if total_consumption > 0
    nu_c_s = consumption / total_consumption;
else
    warning('总消费为0，使用均匀分布');
    nu_c_s = ones(nsectors, 1) / nsectors;
end

investment = Final_Demand(:, 2);
total_investment = sum(investment);
if total_investment > 0
    nu_inv_s = investment / total_investment;
else
    warning('总投资为0，使用均匀分布');
    nu_inv_s = ones(nsectors, 1) / nsectors;
end

govt_purchases = Final_Demand(:, 3);
total_govt = sum(govt_purchases);
if total_govt > 0
    nu_g_s = govt_purchases / total_govt;
else
    warning('政府购买为0，使用均匀分布');
    nu_g_s = ones(nsectors, 1) / nsectors;
end

fprintf('  消费份额计算完成（总和=%.4f）\n', sum(nu_c_s));
fprintf('  投资份额计算完成（总和=%.4f）\n', sum(nu_inv_s));
fprintf('  政府支出份额计算完成（总和=%.4f）\n', sum(nu_g_s));
fprintf('\n');

%% 计算生产函数参数
fprintf('计算生产函数参数...\n');

va_row = 48;
tva_row = 52;

Value_Added = zeros(42, 1);
Labor_Cost = zeros(42, 1);

for i = 1:42
    col_idx = start_col + i - 1;
    
    if tva_row <= size(data_matrix, 1) && col_idx <= size(data_matrix, 2)
        val = data_matrix{tva_row, col_idx};
        if isnumeric(val) && ~isnan(val)
            Value_Added(i) = double(val);
        elseif ischar(val) || isstring(val)
            try
                Value_Added(i) = str2double(char(val));
                if isnan(Value_Added(i)), Value_Added(i) = 0; end
            catch
                Value_Added(i) = 0;
            end
        end
    end
    
    if va_row <= size(data_matrix, 1) && col_idx <= size(data_matrix, 2)
        val = data_matrix{va_row, col_idx};
        if isnumeric(val) && ~isnan(val)
            Labor_Cost(i) = double(val);
        elseif ischar(val) || isstring(val)
            try
                Labor_Cost(i) = str2double(char(val));
                if isnan(Labor_Cost(i)), Labor_Cost(i) = 0; end
            catch
                Labor_Cost(i) = 0;
            end
        end
    end
end

if sum(Value_Added) < 1e-6
    Value_Added = Total_Output - total_intermediate_inputs;
    Value_Added(Value_Added < 0) = 0;
end

if sum(Labor_Cost) > 1e-6
    alpha_n_s = Labor_Cost ./ Value_Added;
    alpha_n_s(isnan(alpha_n_s)) = 0.55;
    alpha_n_s(isinf(alpha_n_s)) = 0.55;
    alpha_n_s = max(0.1, min(0.9, alpha_n_s));
    
    Capital_Cost = Value_Added - Labor_Cost;
    Capital_Cost(Capital_Cost < 0) = 0;
    alpha_k_s = Capital_Cost ./ Value_Added;
    alpha_k_s(isnan(alpha_k_s)) = 0.30;
    alpha_k_s(isinf(alpha_k_s)) = 0.30;
    alpha_k_s = max(0.1, min(0.9, alpha_k_s));
    
    fprintf('  使用实际的劳动和资本成本数据\n');
else
    fprintf('  未找到劳动成本数据，使用校准值\n');
    alpha_n_s = 0.55 * ones(nsectors, 1);
    alpha_k_s = 0.30 * ones(nsectors, 1);
    fprintf('  使用默认校准值：alpha_n=0.55, alpha_k=0.30\n');
end

alpha_n_s = max(0.1, min(0.9, alpha_n_s));
alpha_k_s = max(0.1, min(0.9, alpha_k_s));

fprintf('  生产函数参数计算完成\n');
fprintf('  劳动份额范围: [%.4f, %.4f]\n', min(alpha_n_s), max(alpha_n_s));
fprintf('  资本份额范围: [%.4f, %.4f]\n', min(alpha_k_s), max(alpha_k_s));
fprintf('\n');

%% 计算价格粘性参数
fprintf('计算价格粘性参数...\n');

phi_s = 0.80 * ones(nsectors, 1);
phi_s = max(0.5, min(0.95, phi_s));

fprintf('  使用默认校准值：phi=0.80\n');
fprintf('  价格粘性参数计算完成\n');
fprintf('  参数范围: [%.4f, %.4f]\n', min(phi_s), max(phi_s));
fprintf('\n');

%% 数据验证
fprintf('数据验证和检查...\n');

checks_passed = true;

if any(sum(nu_h_s_x, 1) > 1.5)
    warning('某些部门的中间品投入系数之和超过1.5，可能不合理');
    checks_passed = false;
end

if abs(sum(nu_c_s) - 1) > 0.01
    warning('消费份额之和不为1: %.4f', sum(nu_c_s));
    checks_passed = false;
end

if abs(sum(nu_inv_s) - 1) > 0.01
    warning('投资份额之和不为1: %.4f', sum(nu_inv_s));
    checks_passed = false;
end

if abs(sum(nu_g_s) - 1) > 0.01
    warning('政府支出份额之和不为1: %.4f', sum(nu_g_s));
    checks_passed = false;
end

if checks_passed
    fprintf('  所有检查通过！\n');
else
    fprintf('  警告：部分检查未通过，请检查数据\n');
end
fprintf('\n');

%% 保存参数文件
fprintf('保存参数文件...\n');

save('Model_Parameters.mat', ...
    'nu_h_s_x', ...
    'nu_c_s', ...
    'nu_inv_s', ...
    'nu_g_s', ...
    'alpha_n_s', ...
    'alpha_k_s', ...
    'phi_s', ...
    'alpha_h', ...
    'alpha_h_s', ...
    'nsectors', ...
    'USE_table', ...
    'Total_Output', ...
    'Final_Demand');

fprintf('  参数已保存到 Model_Parameters.mat\n\n');

fprintf('=== 步骤1完成 ===\n\n');





















