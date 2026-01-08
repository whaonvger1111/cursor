% start_matlab.m
% Start MATLAB and run the main script
% This file should be run from MATLAB GUI

fprintf('========================================\n');
fprintf('  China 42-Sector DSGE Model\n');
fprintf('  Government Spending Multiplier Study\n');
fprintf('========================================\n\n');

% Change to script directory
script_dir = fileparts(mfilename('fullpath'));
cd(script_dir);
fprintf('Working directory: %s\n\n', pwd);

% Run main script
fprintf('Starting main script...\n\n');
Run_China_DSGE;





















