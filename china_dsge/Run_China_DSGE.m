% Run_China_DSGE.m
% 主运行脚本 - 中国42部门DSGE模型政府支出乘数研究
% 整合所有步骤的主脚本

clear all; clc;

fprintf('========================================\n');
fprintf('  中国42部门DSGE模型\n');
fprintf('  政府支出乘数研究\n');
fprintf('========================================\n\n');

%% 步骤1: 读取数据并提取参数
fprintf('步骤1: 读取投入产出表并提取参数...\n');
try
    01_Read_IO_Data;
    fprintf('  ✓ 步骤1完成\n\n');
catch ME
    fprintf('  ✗ 步骤1失败: %s\n', ME.message);
    error('步骤1失败，程序终止');
end

%% 步骤2: 计算稳态初始值
fprintf('步骤2: 计算稳态初始值...\n');
try
    02_Compute_Steady_State_Initial;
    fprintf('  ✓ 步骤2完成\n\n');
catch ME
    fprintf('  ✗ 步骤2失败: %s\n', ME.message);
    error('步骤2失败，程序终止');
end

%% 步骤3: 生成稳态计算脚本
fprintf('步骤3: 生成稳态计算脚本...\n');
try
    03_Make_SS_Model;
    fprintf('  ✓ 步骤3完成\n\n');
catch ME
    fprintf('  ✗ 步骤3失败: %s\n', ME.message);
    error('步骤3失败，程序终止');
end

%% 步骤4: 计算稳态
fprintf('步骤4: 计算稳态值...\n');
try
    04_Compute_Steady_State;
    fprintf('  ✓ 步骤4完成\n\n');
catch ME
    fprintf('  ✗ 步骤4失败: %s\n', ME.message);
    error('步骤4失败，程序终止');
end

%% 步骤5: 生成Dynare模型文件
fprintf('步骤5: 生成Dynare模型文件...\n');
try
    05_Write_Dynare_Script;
    fprintf('  ✓ 步骤5完成\n\n');
catch ME
    fprintf('  ✗ 步骤5失败: %s\n', ME.message);
    error('步骤5失败，程序终止');
end

%% 步骤6: 运行Dynare
fprintf('步骤6: 运行Dynare求解模型...\n');
fprintf('  注意：这可能需要较长时间（几分钟到几十分钟）\n\n');
try
    06_Run_Dynare;
    fprintf('  ✓ 步骤6完成\n\n');
catch ME
    fprintf('  ✗ 步骤6失败: %s\n', ME.message);
    fprintf('  提示：请检查Dynare是否正确安装\n');
    fprintf('  或检查模型文件是否有错误\n\n');
    error('步骤6失败，程序终止');
end

%% 步骤7: 计算乘数
fprintf('步骤7: 计算政府支出乘数...\n');
try
    07_Compute_Multiplier;
    fprintf('  ✓ 步骤7完成\n\n');
catch ME
    fprintf('  ✗ 步骤7失败: %s\n', ME.message);
    error('步骤7失败，程序终止');
end

%% 完成
fprintf('========================================\n');
fprintf('  所有步骤完成！\n');
fprintf('========================================\n\n');

% 显示最终结果
if exist('Multipliers.mat', 'file')
    load('Multipliers.mat');
    fprintf('最终结果:\n');
    fprintf('  增加值乘数: %.4f\n', Mult_VA);
    fprintf('  消费乘数:   %.4f\n', Mult_C);
    fprintf('  投资乘数:   %.4f\n', Mult_INV);
    fprintf('\n');
    fprintf('结果文件:\n');
    fprintf('  - Multipliers.mat: 乘数结果\n');
    fprintf('  - RESULTS.mat: Dynare求解结果\n');
    fprintf('  - Final_Steady_State.mat: 稳态值\n');
    fprintf('  - dynare_script.mod: Dynare模型文件\n');
    fprintf('\n');
end

fprintf('程序执行完成！\n\n');





















