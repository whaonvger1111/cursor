% 运行稳态计算的MATLAB脚本
% 这个脚本在baseline文件夹中运行main.m来重新计算稳态

clear
clc
close all
format long g

% 切换到baseline目录
cd('C:\Users\Administrator\Desktop\Rescue-Policies-COVID-main\baseline');

% 添加路径
addpath(genpath(fullfile('tools')));

disp('========================================');
disp('重新运行MATLAB稳态计算');
disp('========================================');
disp(' ');

% 运行main.m
try
    run('main.m');
    disp(' ');
    disp('========================================');
    disp('稳态计算完成！');
    disp('结果已保存到: mat/ss.mat');
    disp('========================================');
catch ME
    disp(' ');
    disp('========================================');
    disp('错误: 稳态计算失败');
    disp('========================================');
    disp(ME.message);
    disp(ME.stack(1));
end

