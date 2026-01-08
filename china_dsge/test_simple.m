% test_simple.m
% Simple test script

fprintf('Testing 01_Read_IO_Data.m...\n\n');

try
    % Test file path
    io_data_dir = 'C:/Users/Administrator/Desktop/china_inoutput';
    excel_file = fullfile(io_data_dir, 'input_output_china.xlsx');
    
    fprintf('Excel file: %s\n', excel_file);
    
    if exist(excel_file, 'file')
        fprintf('Excel file exists\n');
        
        % Try to read
        fprintf('Attempting to read Excel file...\n');
        data_cell = readcell(excel_file, 'Sheet', '42部门');
        fprintf('Successfully read Excel file\n');
        fprintf('Data size: %d x %d\n', size(data_cell, 1), size(data_cell, 2));
        
        fprintf('\nTest PASSED!\n');
    else
        fprintf('Excel file does not exist\n');
        fprintf('Test FAILED!\n');
    end
    
catch ME
    fprintf('\nError occurred:\n');
    fprintf('  Message: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  File: %s\n', ME.stack(1).file);
        fprintf('  Line: %d\n', ME.stack(1).line);
    end
    fprintf('\nTest FAILED!\n');
end





















