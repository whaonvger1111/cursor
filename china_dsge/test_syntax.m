% test_syntax.m
% 测试MATLAB脚本语法

fprintf('测试MATLAB脚本语法...\n\n');

% 测试基本语法
try
    fprintf('测试1: 基本变量赋值...\n');
    nsectors = 42;
    fprintf('  ✓ nsectors = %d\n', nsectors);
    
    fprintf('测试2: 文件路径检查...\n');
    io_data_dir = 'C:/Users/Administrator/Desktop/china_inoutput';
    excel_file = fullfile(io_data_dir, 'input_output_china.xlsx');
    if exist(excel_file, 'file')
        fprintf('  ✓ Excel文件存在: %s\n', excel_file);
    else
        fprintf('  ✗ Excel文件不存在: %s\n', excel_file);
    end
    
    fprintf('测试3: 当前目录检查...\n');
    current_dir = pwd;
    fprintf('  当前目录: %s\n', current_dir);
    
    fprintf('测试4: 文件存在性检查...\n');
    if exist('01_Read_IO_Data.m', 'file')
        fprintf('  ✓ 01_Read_IO_Data.m存在\n');
    else
        fprintf('  ✗ 01_Read_IO_Data.m不存在\n');
    end
    
    fprintf('\n所有语法测试通过！\n');
    
catch ME
    fprintf('\n错误: %s\n', ME.message);
    fprintf('位置: %s (行 %d)\n', ME.stack(1).file, ME.stack(1).line);
end





















