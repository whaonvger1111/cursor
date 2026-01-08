% run_test.m
% Run test for 01_Read_IO_Data.m

fprintf('========================================\n');
fprintf('  Testing 01_Read_IO_Data.m\n');
fprintf('========================================\n\n');

try
    01_Read_IO_Data;
    fprintf('\n========================================\n');
    fprintf('  Test PASSED!\n');
    fprintf('========================================\n');
catch ME
    fprintf('\n========================================\n');
    fprintf('  Test FAILED!\n');
    fprintf('========================================\n');
    fprintf('Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('File: %s\n', ME.stack(1).file);
        fprintf('Line: %d\n', ME.stack(1).line);
        fprintf('Function: %s\n', ME.stack(1).name);
    end
    rethrow(ME);
end





















