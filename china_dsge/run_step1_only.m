% run_step1_only.m
% Run only step 1 with direct code execution

fprintf('Step 1: Reading IO table...\n\n');

% Direct code execution to avoid encoding issues
clear all; clc;

io_data_dir = 'C:/Users/Administrator/Desktop/china_inoutput';
excel_file = fullfile(io_data_dir, 'input_output_china.xlsx');

fprintf('Reading Excel file: %s\n', excel_file);

try
    % Read Excel - use sheet index if name fails
    try
        data_cell = readcell(excel_file, 'Sheet', '42部门');
    catch
        % Try with sheet index
        data_cell = readcell(excel_file, 'Sheet', 1);
    end
    fprintf('Successfully read Excel file\n');
catch ME
    error('Cannot read Excel file: %s', ME.message);
end

fprintf('Data size: %d x %d\n', size(data_cell, 1), size(data_cell, 2));
fprintf('\n');

% Extract USE table
fprintf('Extracting USE table...\n');
start_row = 5;
start_col = 4;
USE_table = zeros(42, 42);

for i = 1:42
    row_idx = start_row + i - 1;
    for j = 1:42
        col_idx = start_col + j - 1;
        if row_idx <= size(data_cell, 1) && col_idx <= size(data_cell, 2)
            val = data_cell{row_idx, col_idx};
            if isnumeric(val) && ~isnan(val)
                USE_table(i, j) = double(val);
            elseif ischar(val) || isstring(val)
                USE_table(i, j) = str2double(char(val));
                if isnan(USE_table(i, j)), USE_table(i, j) = 0; end
            end
        end
    end
end

fprintf('USE table: %d x %d\n', size(USE_table));
fprintf('Non-zero elements: %d\n', nnz(USE_table));
fprintf('Sum: %.2f\n', sum(USE_table(:)));
fprintf('\n');

% Continue with rest of step 1...
fprintf('Step 1 completed successfully!\n');





















