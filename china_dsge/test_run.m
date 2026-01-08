% test_run.m
% 测试运行第一个脚本

try
    fprintf('开始测试01_Read_IO_Data.m...\n\n');
    01_Read_IO_Data;
    fprintf('\n测试成功完成！\n');
catch ME
    fprintf('\n错误发生:\n');
    fprintf('  错误信息: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  文件: %s\n', ME.stack(1).file);
        fprintf('  行号: %d\n', ME.stack(1).line);
        fprintf('  函数: %s\n', ME.stack(1).name);
    end
    rethrow(ME);
end





















