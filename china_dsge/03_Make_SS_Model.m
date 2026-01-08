% 03_Make_SS_Model.m
% 生成SS_Model.m脚本，用于计算所有稳态变量
% 参考: C:\Users\Administrator\Desktop\government multiplier_dynare\ReplicationPackage\Models\Het_China\Make_SS_Model.m

clear all; close all; clc;

fprintf('=== 步骤3: 生成稳态计算脚本 ===\n\n');

nsectors = 42;

% 获取当前工作目录
current_dir = pwd;
param_file = fullfile(current_dir, 'Model_Parameters.mat');
solution_file = fullfile(current_dir, 'solution_io.mat');

fprintf('生成SS_Model.m...\n');
fprintf('  参数文件: %s\n', param_file);
fprintf('  初始解文件: %s\n', solution_file);
fprintf('\n');

fid = fopen('SS_Model.m', 'w');

%% 文件头
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('%%%% NUMBER OF SECTORS\n'); fwrite(fid,nstring);
nstring = sprintf('nsectors = 42;\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('%%%% CALIBRATION\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('load(''%s'');\n', param_file); fwrite(fid,nstring);
nstring = sprintf('load(''%s'');\n', solution_file); fwrite(fid,nstring);
nstring = sprintf('solution = solution_io;\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% 参数赋值
for n = 1:nsectors
    nstring = sprintf('nu_c_%g = nu_c_s(%g);\n',n*ones(1,2)); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('delta_k = 0.025;\n'); fwrite(fid,nstring);
nstring = sprintf('delta = 0.025;\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('alpha_n_%g = alpha_n_s(%g);\n',n*ones(1,2)); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('alpha_k_%g = alpha_k_s(%g);\n',n*ones(1,2)); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('nu_g_%g = nu_g_s(%g);\n',n*ones(1,2)); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('nu_inv_%g = nu_inv_s(%g);\n',n*ones(1,2)); fwrite(fid,nstring); 
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors
    for m = 1:nsectors
    nstring = sprintf('nu_h_%g_%g =  ',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring); 
    nstring = sprintf('nu_h_s_x(%g,',m*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('%g);\n',n*ones(1,1)); fwrite(fid,nstring);
    end
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

nstring = sprintf('n_ss = 0.33;\n'); fwrite(fid,nstring);
nstring = sprintf('bbeta = 0.995;\n'); fwrite(fid,nstring);
nstring = sprintf('nu_n = 1;\n'); fwrite(fid,nstring);
nstring = sprintf('nu_k = 1;\n'); fwrite(fid,nstring);
nstring = sprintf('epsilon = 4;\n'); fwrite(fid,nstring);
nstring = sprintf('omega_g = 0.2;\n'); fwrite(fid,nstring);
nstring = sprintf('beta = bbeta;\n'); fwrite(fid,nstring);
nstring = sprintf('eta = 1/.8;\n'); fwrite(fid,nstring);
nstring = sprintf('sigma = 2;\n'); fwrite(fid,nstring);
nstring = sprintf('rho_g = .9;\n'); fwrite(fid,nstring);
nstring = sprintf('sigma_g = .1;\n'); fwrite(fid,nstring);
nstring = sprintf('Omega = 20;\n'); fwrite(fid,nstring);
nstring = sprintf('psi_w = .7;\n'); fwrite(fid,nstring);
nstring = sprintf('psi_el = .3;\n'); fwrite(fid,nstring);
nstring = sprintf('nu_c = 2;\n'); fwrite(fid,nstring);
nstring = sprintf('nu_inv = 2;\n'); fwrite(fid,nstring);
nstring = sprintf('nu_h = 2;\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('phi_%g = (phi_s(%g)-1)./phi_s(%g);\n',n*ones(1,3)); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors-1
    nstring = sprintf('omega_n_%g = solution(nsectors + %g) / n_ss;\n',n*ones(1,2)); fwrite(fid,nstring); 
end
nstring = sprintf('omega_n_42 = 1'); fwrite(fid,nstring);
for n = 1:nsectors-1
    nstring = sprintf(' - omega_n_%g',n*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf(';\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% 变量计算
nstring = sprintf('%%%% VARIABLES\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

% C_s
for n = 1:nsectors
    nstring = sprintf('c_%g_ss = solution(%g);\n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

% N_s
for n = 1:nsectors
    nstring = sprintf('n_%g_ss = solution(nsectors+%g);\n',n*ones(1,2)); fwrite(fid,nstring); 
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

% W
nstring = sprintf('w_ss = solution(2*nsectors +1);\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% Omega_{c,s}
nstring = sprintf('nu_c_avg = (nu_c_1'); fwrite(fid,nstring);
for n = 2:nsectors
    nstring = sprintf(' + nu_c_%g',n*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf(') / nsectors; \n'); fwrite(fid,nstring);
nstring = sprintf('nu_c_ref = max(nu_c_1, max(nu_c_avg, 1e-6)); \n'); fwrite(fid,nstring);
nstring = sprintf('c_ref_ss = c_1_ss; \n'); fwrite(fid,nstring);
nstring = sprintf('OmegaAux_c_1 = 1; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
for n = 2:nsectors
    nstring = sprintf('nu_c_%g_safe = max(nu_c_%g, 1e-10); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('OmegaAux_c_%g =  OmegaAux_c_1 * ((nu_c_%g_safe/nu_c_ref)^nu_c) * ((c_%g_ss/c_ref_ss)^(1-nu_c)); \n',n*ones(1,3)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf('OmegaAuxNorm = 0 '); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('+ OmegaAux_c_%g',n*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf(';\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('Omega_c_%g =  OmegaAux_c_%g/OmegaAuxNorm; \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

%% C_ss
nstring = sprintf('c_ss = (0 '); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('+ ((Omega_c_%g^(1/nu_c)) * (c_%g_ss^((nu_c-1)/nu_c)))',n*ones(1,2)); fwrite(fid,nstring);
end
nstring = sprintf(')^(nu_c/(nu_c-1));\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% q_s
nstring = sprintf('%% EQUATION 2 \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('q_%g_ss = (Omega_c_%g * c_ss / c_%g_ss)^(1/nu_c); \n',n*ones(1,3)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);                                                                                                                                                      
end

%% mc_s
for n = 1:nsectors
    nstring = sprintf('mc_%g_ss = ((epsilon-1)/epsilon) * q_%g_ss; \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

%% omega_{inv,s}
for n = 1:nsectors
    nstring = sprintf('omega_inv_tilde_%g = nu_inv_%g / q_%g_ss^(1-nu_inv); \n',n*ones(1,3)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf('norm_inv = 0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' + omega_inv_tilde_%g',n*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf('; \n'); fwrite(fid,nstring);
nstring = sprintf('\n'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('omega_inv_%g = omega_inv_tilde_%g / norm_inv; \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

%% qinv_s
nstring = sprintf('%% EQUATION 4 \n'); fwrite(fid,nstring);
nstring = sprintf('qinv_ss = ( 0 '); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' + (omega_inv_%g * (q_%g_ss^(1-nu_inv)))',n*ones(1,2)); fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1-nu_inv)); \n'); fwrite(fid,nstring);
nstring = sprintf('\n'); fwrite(fid,nstring);

%% omega_h_s_x
nstring = sprintf('%% EQUATION 5 \n'); fwrite(fid,nstring);
for n = 1:nsectors
    for m = 1:nsectors        
nstring = sprintf('omega_h_tilde_%g_%g = ',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('nu_h_%g_%g / ',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring); 
nstring = sprintf('q_%g_ss^(1-nu_h); \n',m*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('\n'); fwrite(fid,nstring);   
    end
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors
nstring = sprintf('norm_%g = 0',n*ones(1,1)); fwrite(fid,nstring);
for m = 1:nsectors    
nstring = sprintf('+ omega_h_tilde_%g_%g',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf('; \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors
    for m = 1:nsectors        
nstring = sprintf('omega_h_%g_%g = ',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('omega_h_tilde_%g_%g/ ',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring); 
nstring = sprintf('norm_%g; \n',n*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('\n'); fwrite(fid,nstring);   
    end
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% qh_s
nstring = sprintf('%% EQUATION 5 \n'); fwrite(fid,nstring);
for n = 1:nsectors
nstring = sprintf('qh_%g_ss = (0',n*ones(1,1)); fwrite(fid,nstring);
for m = 1:nsectors    
nstring = sprintf('+ (omega_h_%g_%g',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf(' * q_%g_ss^(1-nu_h))',m*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1-nu_h)); \n'); fwrite(fid,nstring);
nstring = sprintf('\n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% rk
nstring = sprintf('rk_ss = ((1-bbeta*(1-delta_k))/bbeta) * qinv_ss; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% GO_s
for n = 1:nsectors
    nstring = sprintf('go_%g_ss = (w_ss * n_%g_ss) / (alpha_n_%g * mc_%g_ss); \n',n*ones(1,4)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% K_s
for n = 1:nsectors
    nstring = sprintf('k_%g_ss = (alpha_k_%g * mc_%g_ss * go_%g_ss) / rk_ss; \n',n*ones(1,4)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% K
nstring = sprintf('k_ss  = k_1_ss'); fwrite(fid,nstring);  
for n = 2:nsectors
    nstring = sprintf(' + k_%g_ss',n*ones(1,1)); fwrite(fid,nstring);  
end
nstring = sprintf(';\n'); fwrite(fid,nstring); 
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% omega_k
for n = 1:nsectors-1
    nstring = sprintf('omega_k_%g = k_%g_ss / k_ss;\n',n*ones(1,2)); fwrite(fid,nstring); 
end
nstring = sprintf('omega_k_42 = 1'); fwrite(fid,nstring);
for n = 1:nsectors-1
    nstring = sprintf(' - omega_k_%g',n*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf(';\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% I_s
nstring = sprintf('inv_ss = k_ss * delta_k; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% H_s
for n = 1:nsectors
    nstring = sprintf('h_%g_ss = ((1-alpha_n_%g-alpha_k_%g) * mc_%g_ss * go_%g_ss) / qh_%g_ss; \n',n*ones(1,6)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% H_sx
nstring = sprintf('%% EQUATION 11 \n'); fwrite(fid,nstring);
for n = 1:nsectors
    for m = 1:nsectors        
nstring = sprintf('h_%g_%g_ss = ',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('omega_h_%g_%g * ',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring); 
nstring = sprintf(' ((q_%g_ss/ ',m*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('qh_%g_ss)^-nu_h)',n*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf(' * h_%g_ss; \n ',n*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('\n'); fwrite(fid,nstring);   
    end
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% I_sx
nstring = sprintf('%% EQUATION 12 \n'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('inv_%g_ss = omega_inv_%g * ((q_%g_ss / qinv_ss)^-nu_inv) * inv_ss; \n',n*ones(1,3)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% VA
nstring = sprintf('va_ss  = (1/ (1-omega_g)) * (c_ss + (qinv_ss * inv_ss));\n'); fwrite(fid,nstring);  
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% qg_s
nstring = sprintf('%% EQUATION 4 \n'); fwrite(fid,nstring);
nstring = sprintf('qg_ss = 1'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' * (q_%g_ss^nu_g_%g)',n*ones(1,2)); fwrite(fid,nstring);
end
nstring = sprintf('; \n'); fwrite(fid,nstring);
nstring = sprintf('\n'); fwrite(fid,nstring);

%% G
nstring = sprintf('g_ss  = omega_g * va_ss / qg_ss;\n'); fwrite(fid,nstring);  
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% G_s
for n = 1:nsectors
    nstring = sprintf('g_%g_ss = (nu_g_%g  * qg_ss * g_ss) / q_%g_ss; \n',n*ones(1,3)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% Numeraire
nstring = sprintf('Num_Num = 0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('+ (q_%g_ss * (c_%g_ss + inv_%g_ss + g_%g_ss))',n*ones(1,4)); fwrite(fid,nstring);
end
nstring = sprintf('; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('Num_Den = 0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('+ (c_%g_ss + inv_%g_ss + g_%g_ss)',n*ones(1,3)); fwrite(fid,nstring);
end
nstring = sprintf('; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('Num = Num_Num / Num_Den; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('q_%g_ss = q_%g_ss/Num; \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

nstring = sprintf('qc_ss = 1/Num;\n'); fwrite(fid,nstring);
nstring = sprintf('qg_ss = qg_ss/Num;\n'); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('qh_%g_ss = qh_%g_ss/Num; \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

nstring = sprintf('qinv_ss = qinv_ss/Num;\n'); fwrite(fid,nstring);
nstring = sprintf('rk_ss = rk_ss/Num; \n'); fwrite(fid,nstring);
nstring = sprintf('va_ss = va_ss/Num;\n'); fwrite(fid,nstring);
nstring = sprintf('w_ss = w_ss/Num;\n'); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('mc_%g_ss = mc_%g_ss/Num; \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

%% R
nstring = sprintf('r_ss = 1/beta; \n' ); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% rk_s
for n = 1:nsectors
    nstring = sprintf('rk_%g_ss = rk_ss; \n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% w_s
for n = 1:nsectors
    nstring = sprintf('w_%g_ss = w_ss; \n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% T
nstring = sprintf('t_ss  = qg_ss * g_ss; \n'); fwrite(fid,nstring);  
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% CTILDE
nstring = sprintf('ctilde_ss = (((psi_w^(1/psi_el)) * (c_ss^((psi_el-1)/psi_el))) + (((1-psi_w)^(1/psi_el)) * (g_ss^((psi_el-1)/psi_el))))^(psi_el/(psi_el-1)); \n' ); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% LAMBDA
nstring = sprintf('lambda_ss = (psi_w^(1/psi_el)) * (ctilde_ss^((1/psi_el)-sigma)) * (c_ss^(-1/psi_el)) / qc_ss; \n' ); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% m1_s
for n = 1:nsectors
    nstring = sprintf('m1_%g_ss = lambda_ss * go_%g_ss * mc_%g_ss / (1 - beta*phi_%g); \n',n*ones(1,4)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% m2_s
for n = 1:nsectors
    nstring = sprintf('m2_%g_ss = lambda_ss * go_%g_ss / (1 - beta*phi_%g); \n',n*ones(1,3)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% VAs
for n = 1:nsectors
    nstring = sprintf('va_%g_ss = q_%g_ss * go_%g_ss - qh_%g_ss * h_%g_ss; \n',n*ones(1,5)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% rho_r
nstring = sprintf('rho_r = .8; \n' ); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% phi_pi
nstring = sprintf('phi_pi = 1.5; \n' ); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% phi_y
nstring = sprintf('phi_y = .2; \n' ); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

%% Theta
nstring = sprintf('theta = w_ss * lambda_ss / (n_ss^eta); \n' ); fwrite(fid,nstring);

%% 清理和保存
nstring = sprintf('clear alpha_k_s alpha_n_s ans bbeta delta difference difference_step fid  m n nstring nsectors phi_s nu_c_s nu_inv_s nu_g_s nu_h_s_x solution_cons10 z; \n' ); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('save(''Final_Steady_State''); \n' ); fwrite(fid,nstring);

fclose(fid);

fprintf('  ✓ SS_Model.m已生成\n');
fprintf('\n');

fprintf('=== 步骤3完成 ===\n\n');





















