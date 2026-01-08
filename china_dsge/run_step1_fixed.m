% run_step1_fixed.m
% Wrapper to run 01_Read_IO_Data.m

fprintf('Running step 1: Read IO Data...\n\n');

try
    % Read and execute the script line by line
    script_name = '01_Read_IO_Data.m';
    
    if ~exist(script_name, 'file')
        error('Script file not found: %s', script_name);
    end
    
    % Read file content
    fid = fopen(script_name, 'r', 'n', 'UTF-8');
    if fid == -1
        fid = fopen(script_name, 'r');
    end
    
    if fid == -1
        error('Cannot open file: %s', script_name);
    end
    
    % Read and execute file
    fclose(fid);
    
    % Use run command with full path
    [filepath, name, ext] = fileparts(which(script_name));
    if isempty(filepath)
        filepath = pwd;
    end
    full_script_path = fullfile(filepath, script_name);
    
    % Execute using run
    run(full_script_path);
    
    fprintf('\nStep 1 completed successfully!\n');
    
catch ME
    fprintf('\nStep 1 failed!\n');
    fprintf('Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        for i = 1:min(3, length(ME.stack))
            fprintf('  File: %s\n', ME.stack(i).file);
            fprintf('  Line: %d\n', ME.stack(i).line);
        end
    end
    rethrow(ME);
end

