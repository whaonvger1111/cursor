% 06_Run_Dynare.m
% 运行Dynare求解模型
% 参考: C:\Users\Administrator\Desktop\government multiplier_dynare\ReplicationPackage\Models\Het_China\Aux_Script.m

clear all; clc;

fprintf('=== 步骤6: 运行Dynare求解模型 ===\n\n');

%% 检查必要文件
fprintf('检查必要文件...\n');
if ~exist('Final_Steady_State.mat', 'file')
    error('找不到Final_Steady_State.mat，请先运行04_Compute_Steady_State.m');
end
if ~exist('dynare_script.mod', 'file')
    error('找不到dynare_script.mod，请先运行05_Write_Dynare_Script.m');
end
fprintf('  ✓ 所有必要文件存在\n\n');

%% 加载稳态值
fprintf('加载稳态值...\n');
load('Final_Steady_State.mat');
fprintf('  ✓ 稳态值已加载\n\n');

%% 运行Dynare
fprintf('运行Dynare求解模型...\n');
fprintf('  这可能需要几分钟时间...\n\n');

try
    dynare dynare_script.mod noclearall;
    
    fprintf('\n');
    fprintf('  ✓ Dynare求解完成\n\n');
    
    % 提取结果
    if exist('oo_', 'var') && isfield(oo_, 'irfs')
        RESULTS = oo_.irfs;
        save('RESULTS.mat', 'RESULTS');
        fprintf('  ✓ 结果已保存到 RESULTS.mat\n\n');
    else
        warning('Dynare结果结构不完整，请检查Dynare输出');
    end
    
catch ME
    fprintf('\n');
    fprintf('  ✗ Dynare运行失败: %s\n', ME.message);
    fprintf('  请检查dynare_script.mod文件是否正确\n');
    fprintf('  或检查稳态值是否合理\n\n');
    rethrow(ME);
end

fprintf('=== 步骤6完成 ===\n\n');





















