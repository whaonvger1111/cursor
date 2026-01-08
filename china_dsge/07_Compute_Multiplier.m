% 07_Compute_Multiplier.m
% 计算政府支出乘数
% 参考: C:\Users\Administrator\Desktop\government multiplier_dynare\ReplicationPackage\Models\Het_China\ComputeMultiplier.m

clear all; clc;

fprintf('=== 步骤7: 计算政府支出乘数 ===\n\n');

%% 检查必要文件
fprintf('检查必要文件...\n');
if ~exist('Final_Steady_State.mat', 'file')
    error('找不到Final_Steady_State.mat，请先运行04_Compute_Steady_State.m');
end
if ~exist('RESULTS.mat', 'file')
    error('找不到RESULTS.mat，请先运行06_Run_Dynare.m');
end
fprintf('  ✓ 所有必要文件存在\n\n');

%% 加载数据
fprintf('加载数据...\n');
load('Final_Steady_State.mat');
load('RESULTS.mat');
fprintf('  ✓ 数据已加载\n\n');

%% 计算政府支出冲击响应
fprintf('计算政府支出冲击响应...\n');

% 政府支出响应
response_g = t_ss .* RESULTS.lnt_eps_g;

% 增加值响应
response_va = va_ss .* RESULTS.lnva_eps_g;

% 投资响应
response_inv = (qinv_ss * inv_ss) .* RESULTS.lninvvalue_eps_g;

% 消费响应
response_c = (qc_ss * c_ss) .* RESULTS.lncvalue_eps_g;

fprintf('  响应序列长度: %d\n', length(response_g));
fprintf('  政府支出初始冲击: %.6f\n', response_g(1));
fprintf('  增加值初始响应: %.6f\n', response_va(1));
fprintf('\n');

%% 计算乘数（使用折现因子）
fprintf('计算乘数（使用折现因子）...\n');

beta_df = [1 beta.^[1:1999]];

nhoriz = 2000;
if length(response_g) < nhoriz
    nhoriz = length(response_g);
    warning('响应序列长度不足2000期，使用实际长度: %d', nhoriz);
end

% 增加值乘数
Mult_VA = sum(beta_df(1:nhoriz) .* response_va(1:nhoriz)) ./ ...
          sum(beta_df(1:nhoriz) .* response_g(1:nhoriz));

% 消费乘数
Mult_C = sum(beta_df(1:nhoriz) .* response_c(1:nhoriz)) ./ ...
         sum(beta_df(1:nhoriz) .* response_g(1:nhoriz));

% 投资乘数
Mult_INV = sum(beta_df(1:nhoriz) .* response_inv(1:nhoriz)) ./ ...
           sum(beta_df(1:nhoriz) .* response_g(1:nhoriz));

fprintf('  增加值乘数 (Mult_VA): %.4f\n', Mult_VA);
fprintf('  消费乘数 (Mult_C): %.4f\n', Mult_C);
fprintf('  投资乘数 (Mult_INV): %.4f\n', Mult_INV);
fprintf('\n');

%% 计算投资最低点
trough_inv = find(response_inv == min(response_inv)) - 1;
if isempty(trough_inv)
    trough_inv = NaN;
end

fprintf('  投资最低点 (trough_inv): %d\n', trough_inv);
fprintf('\n');

%% 保存结果
fprintf('保存乘数结果...\n');

clearvars -except Mult_VA Mult_C Mult_INV trough_inv;

save('Multipliers.mat', 'Mult_VA', 'Mult_C', 'Mult_INV', 'trough_inv');

fprintf('  ✓ 乘数结果已保存到 Multipliers.mat\n');
fprintf('\n');

%% 显示结果摘要
fprintf('========================================\n');
fprintf('  政府支出乘数计算结果\n');
fprintf('========================================\n');
fprintf('  增加值乘数: %.4f\n', Mult_VA);
fprintf('  消费乘数:   %.4f\n', Mult_C);
fprintf('  投资乘数:   %.4f\n', Mult_INV);
fprintf('  投资最低点: %d期\n', trough_inv);
fprintf('========================================\n\n');

fprintf('=== 步骤7完成 ===\n\n');





















