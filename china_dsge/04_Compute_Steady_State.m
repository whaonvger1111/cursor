% 04_Compute_Steady_State.m
% 计算稳态值
% 参考: C:\Users\Administrator\Desktop\government multiplier_dynare\ReplicationPackage\Models\Het_China\Compute_Steady_State.m

clear all; clc;

fprintf('=== 步骤4: 计算稳态值 ===\n\n');

%% 步骤1: 检查必要的文件
fprintf('检查必要的文件...\n');
if ~exist('Model_Parameters.mat', 'file')
    error('找不到文件: Model_Parameters.mat，请先运行01_Read_IO_Data.m');
end
if ~exist('solution_io.mat', 'file')
    error('找不到文件: solution_io.mat，请先运行02_Compute_Steady_State_Initial.m');
end
fprintf('  ✓ 所有必要文件存在\n\n');

%% 步骤2: 重新生成SS_Model.m
fprintf('重新生成SS_Model.m...\n');
try
    Make_SS_Model;
    fprintf('  ✓ SS_Model.m已生成\n\n');
catch ME
    error('生成SS_Model.m失败: %s', ME.message);
end

%% 步骤3: 计算稳态
fprintf('计算稳态值...\n');
try
    SS_Model;
    fprintf('  ✓ 稳态计算完成\n\n');
catch ME
    error('稳态计算失败: %s', ME.message);
end

%% 步骤4: 加载并验证稳态值
fprintf('验证稳态值...\n');
load('Final_Steady_State.mat');

checks_passed = true;
warnings_list = {};

% 检查基本参数
if ~exist('nu_c', 'var') || isnan(nu_c) || isinf(nu_c)
    warnings_list{end+1} = 'nu_c无效';
    checks_passed = false;
end
if ~exist('nu_inv', 'var') || isnan(nu_inv) || isinf(nu_inv)
    warnings_list{end+1} = 'nu_inv无效';
    checks_passed = false;
end
if ~exist('nu_h', 'var') || isnan(nu_h) || isinf(nu_h)
    warnings_list{end+1} = 'nu_h无效';
    checks_passed = false;
end

% 检查关键稳态变量
if ~exist('c_ss', 'var') || isnan(c_ss) || isinf(c_ss) || c_ss <= 0
    warnings_list{end+1} = sprintf('c_ss无效: %.4f', c_ss);
    checks_passed = false;
end
if ~exist('w_ss', 'var') || isnan(w_ss) || isinf(w_ss) || w_ss <= 0
    warnings_list{end+1} = sprintf('w_ss无效: %.4f', w_ss);
    checks_passed = false;
end
if ~exist('lambda_ss', 'var') || isnan(lambda_ss) || isinf(lambda_ss) || lambda_ss < 0
    warnings_list{end+1} = sprintf('lambda_ss无效: %.6e', lambda_ss);
    checks_passed = false;
elseif lambda_ss < 1e-12
    warnings_list{end+1} = sprintf('lambda_ss非常小: %.6e（可能正常）', lambda_ss);
end
if ~exist('theta', 'var') || isnan(theta) || isinf(theta) || theta < 0
    warnings_list{end+1} = sprintf('theta无效: %.6e', theta);
    checks_passed = false;
elseif theta < 1e-12
    warnings_list{end+1} = sprintf('theta非常小: %.6e（可能正常）', theta);
end

% 检查部门变量
nsectors = 42;
for s = 1:min(5, nsectors)
    var_name = sprintf('c_%d_ss', s);
    if ~exist(var_name, 'var') || eval(sprintf('isnan(%s) || isinf(%s) || %s <= 0', var_name, var_name, var_name))
        warnings_list{end+1} = sprintf('%s无效', var_name);
        checks_passed = false;
    end
    
    var_name = sprintf('q_%d_ss', s);
    if ~exist(var_name, 'var') || eval(sprintf('isnan(%s) || isinf(%s) || %s <= 0', var_name, var_name, var_name))
        warnings_list{end+1} = sprintf('%s无效', var_name);
        checks_passed = false;
    end
    
    var_name = sprintf('Omega_c_%d', s);
    if ~exist(var_name, 'var') || eval(sprintf('isnan(%s) || isinf(%s)', var_name, var_name))
        warnings_list{end+1} = sprintf('%s无效', var_name);
        checks_passed = false;
    end
end

if checks_passed
    fprintf('  ✓ 所有关键稳态值有效\n\n');
else
    fprintf('  ⚠ 发现以下问题:\n');
    for i = 1:length(warnings_list)
        fprintf('    - %s\n', warnings_list{i});
    end
    fprintf('\n');
end

%% 步骤5: 显示关键稳态值
fprintf('关键稳态值摘要:\n');
fprintf('  参数:\n');
fprintf('    nu_c = %.4f\n', nu_c);
fprintf('    nu_inv = %.4f\n', nu_inv);
fprintf('    nu_h = %.4f\n', nu_h);
fprintf('    theta = %.4f\n', theta);
fprintf('  总量:\n');
fprintf('    c_ss = %.4f\n', c_ss);
fprintf('    w_ss = %.4f\n', w_ss);
fprintf('    lambda_ss = %.6e\n', lambda_ss);
fprintf('    rk_ss = %.4f\n', rk_ss);
fprintf('    va_ss = %.4f\n', va_ss);
fprintf('  前3个部门:\n');
for s = 1:min(3, nsectors)
    fprintf('    部门%d: c=%.4f, q=%.4f, Omega_c=%.6f\n', ...
        s, eval(sprintf('c_%d_ss', s)), eval(sprintf('q_%d_ss', s)), eval(sprintf('Omega_c_%d', s)));
end
fprintf('\n');

%% 步骤6: 确保所有omega参数都存在
fprintf('检查omega参数...\n');
omega_missing = false;
for s = 1:nsectors
    var_name = sprintf('Omega_c_%d', s);
    if ~exist(var_name, 'var')
        fprintf('  警告: %s不存在\n', var_name);
        omega_missing = true;
    end
end
if ~omega_missing
    fprintf('  ✓ 所有Omega_c_*参数存在\n');
end
fprintf('\n');

%% 步骤7: 重新保存稳态文件
fprintf('保存稳态值到Final_Steady_State.mat...\n');
save('Final_Steady_State.mat', '-v7.3');
fprintf('  ✓ 稳态值已保存\n\n');

%% 完成
fprintf('========================================\n');
fprintf('  稳态计算完成！\n');
fprintf('========================================\n\n');
fprintf('下一步: 生成Dynare模型文件\n');
fprintf('  运行: 05_Write_Dynare_Script.m\n\n');

if ~checks_passed
    fprintf('警告: 部分稳态值可能有问题，请检查上述警告信息。\n');
    fprintf('Dynare可能无法正常收敛。\n\n');
end

fprintf('=== 步骤4完成 ===\n\n');





















