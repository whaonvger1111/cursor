% check_setup.m
% 检查设置和文件是否存在

clear all; clc;

fprintf('========================================\n');
fprintf('  检查设置和文件\n');
fprintf('========================================\n\n');

all_ok = true;

%% 检查1: 数据文件
fprintf('检查1: 数据文件...\n');
io_data_dir = 'C:/Users/Administrator/Desktop/china_inoutput';
excel_file = fullfile(io_data_dir, 'input_output_china.xlsx');

if exist(excel_file, 'file')
    fprintf('  ✓ Excel文件存在: %s\n', excel_file);
else
    fprintf('  ✗ Excel文件不存在: %s\n', excel_file);
    all_ok = false;
end
fprintf('\n');

%% 检查2: MATLAB脚本文件
fprintf('检查2: MATLAB脚本文件...\n');
scripts = {'01_Read_IO_Data.m', '02_Compute_Steady_State_Initial.m', ...
           '03_Make_SS_Model.m', '04_Compute_Steady_State.m', ...
           '05_Write_Dynare_Script.m', '06_Run_Dynare.m', ...
           '07_Compute_Multiplier.m', 'Run_China_DSGE.m'};

for i = 1:length(scripts)
    if exist(scripts{i}, 'file')
        fprintf('  ✓ %s\n', scripts{i});
    else
        fprintf('  ✗ %s 不存在\n', scripts{i});
        all_ok = false;
    end
end
fprintf('\n');

%% 检查3: MATLAB函数可用性
fprintf('检查3: MATLAB函数可用性...\n');
functions_to_check = {'readcell', 'fullfile', 'fopen', 'fwrite', 'fclose', 'save', 'load'};

for i = 1:length(functions_to_check)
    if exist(functions_to_check{i}, 'builtin') || exist(functions_to_check{i}, 'file')
        fprintf('  ✓ %s 可用\n', functions_to_check{i});
    else
        fprintf('  ✗ %s 不可用\n', functions_to_check{i});
        all_ok = false;
    end
end
fprintf('\n');

%% 检查4: Dynare可用性（可选）
fprintf('检查4: Dynare可用性（步骤6需要）...\n');
if exist('dynare', 'file')
    fprintf('  ✓ Dynare可用\n');
else
    fprintf('  ⚠ Dynare不可用（步骤6将无法运行）\n');
    fprintf('    提示：请确保Dynare已安装并添加到MATLAB路径\n');
end
fprintf('\n');

%% 检查5: 当前目录
fprintf('检查5: 当前工作目录...\n');
current_dir = pwd;
fprintf('  当前目录: %s\n', current_dir);
fprintf('\n');

%% 总结
fprintf('========================================\n');
if all_ok
    fprintf('  ✓ 所有基本检查通过！\n');
    fprintf('  可以运行: Run_China_DSGE\n');
else
    fprintf('  ✗ 部分检查未通过，请修复后再运行\n');
end
fprintf('========================================\n\n');





















