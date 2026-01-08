% run_step1.m
% Wrapper to run 01_Read_IO_Data.m

fprintf('Running step 1: Read IO Data...\n\n');

try
    % Change to script directory
    script_dir = fileparts(mfilename('fullpath'));
    cd(script_dir);
    
    % Run the script
    eval('01_Read_IO_Data');
    
    fprintf('\nStep 1 completed successfully!\n');
    
catch ME
    fprintf('\nStep 1 failed!\n');
    fprintf('Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        for i = 1:min(3, length(ME.stack))
            fprintf('  File: %s\n', ME.stack(i).file);
            fprintf('  Line: %d\n', ME.stack(i).line);
            fprintf('  Function: %s\n', ME.stack(i).name);
        end
    end
    rethrow(ME);
end





















