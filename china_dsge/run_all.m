% run_all.m
% Run all steps without Chinese characters in output

fprintf('========================================\n');
fprintf('  China 42-Sector DSGE Model\n');
fprintf('  Government Spending Multiplier Study\n');
fprintf('========================================\n\n');

%% Step 1
fprintf('Step 1: Reading IO table and extracting parameters...\n');
try
    run('01_Read_IO_Data.m');
    fprintf('  Step 1: PASSED\n\n');
catch ME
    fprintf('  Step 1: FAILED\n');
    fprintf('  Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  File: %s, Line: %d\n', ME.stack(1).file, ME.stack(1).line);
    end
    error('Step 1 failed');
end

%% Step 2
fprintf('Step 2: Computing initial steady state values...\n');
try
    run('02_Compute_Steady_State_Initial.m');
    fprintf('  Step 2: PASSED\n\n');
catch ME
    fprintf('  Step 2: FAILED\n');
    fprintf('  Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  File: %s, Line: %d\n', ME.stack(1).file, ME.stack(1).line);
    end
    error('Step 2 failed');
end

%% Step 3
fprintf('Step 3: Generating steady state model script...\n');
try
    run('03_Make_SS_Model.m');
    fprintf('  Step 3: PASSED\n\n');
catch ME
    fprintf('  Step 3: FAILED\n');
    fprintf('  Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  File: %s, Line: %d\n', ME.stack(1).file, ME.stack(1).line);
    end
    error('Step 3 failed');
end

%% Step 4
fprintf('Step 4: Computing steady state...\n');
try
    run('04_Compute_Steady_State.m');
    fprintf('  Step 4: PASSED\n\n');
catch ME
    fprintf('  Step 4: FAILED\n');
    fprintf('  Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  File: %s, Line: %d\n', ME.stack(1).file, ME.stack(1).line);
    end
    error('Step 4 failed');
end

%% Step 5
fprintf('Step 5: Writing Dynare script...\n');
try
    run('05_Write_Dynare_Script.m');
    fprintf('  Step 5: PASSED\n\n');
catch ME
    fprintf('  Step 5: FAILED\n');
    fprintf('  Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  File: %s, Line: %d\n', ME.stack(1).file, ME.stack(1).line);
    end
    error('Step 5 failed');
end

%% Step 6
fprintf('Step 6: Running Dynare (this may take several minutes)...\n');
try
    run('06_Run_Dynare.m');
    fprintf('  Step 6: PASSED\n\n');
catch ME
    fprintf('  Step 6: FAILED\n');
    fprintf('  Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  File: %s, Line: %d\n', ME.stack(1).file, ME.stack(1).line);
    end
    error('Step 6 failed');
end

%% Step 7
fprintf('Step 7: Computing multipliers...\n');
try
    run('07_Compute_Multiplier.m');
    fprintf('  Step 7: PASSED\n\n');
catch ME
    fprintf('  Step 7: FAILED\n');
    fprintf('  Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('  File: %s, Line: %d\n', ME.stack(1).file, ME.stack(1).line);
    end
    error('Step 7 failed');
end

%% Summary
fprintf('========================================\n');
fprintf('  All steps completed successfully!\n');
fprintf('========================================\n\n');

if exist('Multipliers.mat', 'file')
    load('Multipliers.mat');
    fprintf('Results:\n');
    fprintf('  Value-Added Multiplier: %.4f\n', Mult_VA);
    fprintf('  Consumption Multiplier: %.4f\n', Mult_C);
    fprintf('  Investment Multiplier: %.4f\n', Mult_INV);
    fprintf('\n');
end





















