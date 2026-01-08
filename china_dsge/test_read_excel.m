% test_read_excel.m
% Test reading Excel file

fprintf('Testing Excel file reading...\n\n');

io_data_dir = 'C:/Users/Administrator/Desktop/china_inoutput';
excel_file = fullfile(io_data_dir, 'input_output_china.xlsx');

fprintf('Excel file: %s\n', excel_file);

try
    % Try reading with sheet name
    sheet_name = '42部门';
    fprintf('Reading sheet: %s\n', sheet_name);
    data_cell = readcell(excel_file, 'Sheet', sheet_name);
    fprintf('Success! Data size: %d x %d\n', size(data_cell, 1), size(data_cell, 2));
    
    % Test extracting USE table
    fprintf('\nTesting USE table extraction...\n');
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
    
    fprintf('USE table extracted: %d x %d\n', size(USE_table));
    fprintf('Non-zero elements: %d\n', nnz(USE_table));
    fprintf('Sum: %.2f\n', sum(USE_table(:)));
    
    fprintf('\nTest PASSED!\n');
    
catch ME
    fprintf('\nTest FAILED!\n');
    fprintf('Error: %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('File: %s\n', ME.stack(1).file);
        fprintf('Line: %d\n', ME.stack(1).line);
    end
    rethrow(ME);
end





















