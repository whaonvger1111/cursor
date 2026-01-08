% 05_Write_Dynare_Script.m
% 生成Dynare模型文件 dynare_script.mod
% 参考: C:\Users\Administrator\Desktop\government multiplier_dynare\ReplicationPackage\Models\Het_China\write_dynare_script.m

clear all; clc;

fprintf('=== 步骤5: 生成Dynare模型文件 ===\n\n');

nsectors = 42;

% 确保加载最新的稳态值
if ~exist('Final_Steady_State.mat', 'file')
    error('找不到Final_Steady_State.mat，请先运行04_Compute_Steady_State.m');
end

load('Final_Steady_State.mat');

fprintf('生成dynare_script.mod...\n');

fid = fopen('dynare_script.mod', 'w');

%% ENDOGENOUS VARIABLES
nstring = sprintf('// list of endogenous variables \n'); fwrite(fid,nstring);
nstring = sprintf('var '); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('lnn_%g, lnw_%g, lnrk_%g, lnq_%g, lnqh_%g,          \n',n*ones(1,5)); fwrite(fid,nstring);
    nstring = sprintf('lnh_%g, lnmc_%g, lnpistar_%g, lnv_%g, lnm1_%g,     \n',n*ones(1,5)); fwrite(fid,nstring);
    nstring = sprintf('lnm2_%g, lnva_%g,                                  \n',n*ones(1,2)); fwrite(fid,nstring);
end 

for n = 1:nsectors
    nstring = sprintf('lnwflex_%g, lnrkflex_%g, lnqflex_%g, lnqhflex_%g, lnhflex_%g,   \n',n*ones(1,5)); fwrite(fid,nstring);
end

nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('lnc, lnn, lnt, lnw, lnr, '); fwrite(fid,nstring); 
nstring = sprintf('lnpi, lninv, lnrk, lnk, lnqinv, '); fwrite(fid,nstring); 
nstring = sprintf('lnva, lninvvalue, lnqk, lnlambda, lng,  '); fwrite(fid,nstring); 
nstring = sprintf('lnqg, lnqc, lncvalue, '); fwrite(fid,nstring); 

nstring = sprintf('lncflex, lnnflex, lntflex, lnwflex, lnrflex, '); fwrite(fid,nstring);
nstring = sprintf('lninvflex, lnrkflex, lnkflex, lnqinvflex, lnvaflex, '); fwrite(fid,nstring);
nstring = sprintf('lnqkflex, lngap, lnlambdaflex, lnqcflex, lnqgflex; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


%% EXOGENOUS VARIABLES
nstring = sprintf('// list of exogenous variables \n'); fwrite(fid,nstring);
nstring = sprintf('varexo eps_g, eps_r; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


%% PARAMETERS
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('// structural parameters and ss values \n'); fwrite(fid,nstring);
nstring = sprintf('parameters beta, sigma, theta, eta, nu_n, '); fwrite(fid,nstring);
nstring = sprintf('nu_k, epsilon, rho_g, omega_g, rho_r,  '); fwrite(fid,nstring);
nstring = sprintf('phi_pi, phi_y, delta_k, Omega, psi_w,   '); fwrite(fid,nstring);
nstring = sprintf('psi_el, nu_c, nu_inv, nu_h, \n'); fwrite(fid,nstring);


for n = 1:nsectors
    nstring = sprintf('omega_c_%g, omega_n_%g, omega_k_%g, alpha_n_%g, alpha_k_%g, \n',n*ones(1,5)); fwrite(fid,nstring);
    nstring = sprintf('phi_%g, omega_inv_%g, nu_g_%g,\n',n*ones(1,3)); fwrite(fid,nstring);

end

for n = 1:nsectors
    for m = 1:nsectors
        nstring = sprintf('omega_h_%g_%g,',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring);
    end
end
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('n_%g_ss, q_%g_ss, qh_%g_ss, h_%g_ss, mc_%g_ss, \n',n*ones(1,5)); fwrite(fid,nstring);
    nstring = sprintf('m1_%g_ss, m2_%g_ss, va_%g_ss, \n',n*ones(1,3)); fwrite(fid,nstring);
end


nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('c_ss, n_ss, t_ss, w_ss, r_ss, '); fwrite(fid,nstring);
nstring = sprintf('qg_ss, g_ss, inv_ss, va_ss, k_ss,  '); fwrite(fid,nstring);
nstring = sprintf('rk_ss, qinv_ss, lambda_ss, qc_ss; \n'); fwrite(fid,nstring);

nstring = sprintf(' \n'); fwrite(fid,nstring);

%% PARAMETERS - LOAD
nstring = sprintf('// structural parameters \n'); fwrite(fid,nstring);
out =  sprintf('load Final_Steady_State; \n'); fwrite(fid,out);

nstring = sprintf('set_param_value(''beta'',beta); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''sigma'',sigma); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''theta'',theta); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''eta'',eta); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''nu_n'',nu_n); \n'); fwrite(fid,nstring);

nstring = sprintf('set_param_value(''nu_k'',nu_k); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''epsilon'',epsilon); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''rho_g'',rho_g); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''omega_g'',omega_g); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''rho_r'',rho_r); \n'); fwrite(fid,nstring); 

nstring = sprintf('set_param_value(''phi_pi'',phi_pi); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''phi_y'',phi_y); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''delta_k'',delta_k); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''Omega'',Omega); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''psi_w'',psi_w); \n'); fwrite(fid,nstring);

nstring = sprintf('set_param_value(''psi_el'',psi_el); \n'); fwrite(fid,nstring); 
nstring = sprintf('set_param_value(''nu_c'',nu_c); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''nu_inv'',nu_inv); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''nu_h'',nu_h); \n'); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('set_param_value(''omega_c_%g'',Omega_c_%g); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''omega_n_%g'',omega_n_%g); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''omega_k_%g'',omega_k_%g); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''omega_inv_%g'',omega_inv_%g); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''nu_g_%g'',nu_g_%g); \n',n*ones(1,2)); fwrite(fid,nstring);

    nstring = sprintf('set_param_value(''alpha_n_%g'',alpha_n_%g); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''alpha_k_%g'',alpha_k_%g); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''phi_%g'',phi_%g); \n',n*ones(1,2)); fwrite(fid,nstring);
end

for n = 1:nsectors
    for m = 1:nsectors
        nstring = sprintf('set_param_value(''omega_h_%g_%g'',',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring);
        nstring = sprintf('omega_h_%g_%g); \n',n*ones(1,1),m*ones(1,1)); fwrite(fid,nstring);
    end
end

nstring = sprintf('// ss values \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''c_ss'',c_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''n_ss'',n_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''t_ss'',t_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''w_ss'',w_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''r_ss'',r_ss); \n'); fwrite(fid,nstring);

nstring = sprintf('set_param_value(''qg_ss'',qg_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''g_ss'',g_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''inv_ss'',inv_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''va_ss'',va_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''k_ss'',k_ss); \n'); fwrite(fid,nstring);

nstring = sprintf('set_param_value(''rk_ss'',rk_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''qinv_ss'',qinv_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''lambda_ss'',lambda_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('set_param_value(''qc_ss'',qc_ss); \n'); fwrite(fid,nstring);


for n = 1:nsectors
    nstring = sprintf('set_param_value(''n_%g_ss'',n_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''q_%g_ss'',q_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''qh_%g_ss'',qh_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''h_%g_ss'',h_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''mc_%g_ss'',mc_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    
    nstring = sprintf('set_param_value(''m1_%g_ss'',m1_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('set_param_value(''m2_%g_ss'',m2_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);   
    nstring = sprintf('set_param_value(''va_%g_ss'',va_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
end


nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('model; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('// Equation 1 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnlambda) = beta * exp(lnlambda(+1)) * exp(lnr) / exp(lnpi(+1));  \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('// Equation 2 \n'); fwrite(fid,nstring);
nstring = sprintf('theta * (exp(lnn)^eta) = exp(lnw) * exp(lnlambda);  \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

for n = 1:nsectors
    nstring = sprintf('// Equation 3 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnn_%g) = omega_n_%g * exp(lnn) * (exp(lnw_%g)/exp(lnw))^nu_n ; \n',n*ones(1,3)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

nstring = sprintf('// Equation 4 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnw) = ( (omega_n_1 * (exp(lnw_1)^(1+nu_n)))'); fwrite(fid,nstring);
for n = 2:nsectors
    nstring = sprintf(' + (omega_n_%g * (exp(lnw_%g)^(1+nu_n)))',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1+nu_n)); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 5 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnrk) = ( (omega_k_1 * (exp(lnrk_1)^(1+nu_k)))'); fwrite(fid,nstring);
for n = 2:nsectors
    nstring = sprintf(' + (omega_k_%g * (exp(lnrk_%g)^(1+nu_k)))',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1+nu_k)); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 6 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnk) = (1-delta_k) * exp(lnk(-1)) + exp(lninv)  * (1- ((Omega/2)* (((exp(lninv)/exp(lninv(-1)))-1)^2))); \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 7 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqk) = beta * (exp(lnlambda(+1))/exp(lnlambda)) * (exp(lnrk(+1))+exp(lnqk(+1))*(1-delta_k)) ; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 8 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqinv) = exp(lnqk) * ( 1 - ((Omega/2)*(((exp(lninv)/exp(lninv(-1)))-1)^2)) - (Omega*((exp(lninv)/exp(lninv(-1)))-1)*(exp(lninv)/exp(lninv(-1))))) + beta*(exp(lnlambda(+1))/exp(lnlambda))*exp(lnqk(+1))*Omega*((exp(lninv(+1))/exp(lninv))-1)*((exp(lninv(+1))/exp(lninv))^2); \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


for n = 1:nsectors
    nstring = sprintf('// Equation 9 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnq_%g) = exp(lnq_%g(-1)) * (((1-phi_%g) * (exp(lnpistar_%g)^(1-epsilon)) + phi_%g)^(1/(1-epsilon))) / exp(lnpi);\n',n*ones(1,5));fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);    
end

nstring = sprintf('// Equation 10 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqinv)  = (0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' + (omega_inv_%g * (exp(lnq_%g)^(1-nu_inv)))',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1-nu_inv)); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


for n = 1:nsectors
    nstring = sprintf('// Equation 11 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnw_%g) * exp(lnn_%g) = alpha_n_%g * exp(lnmc_%g) * ((exp(lnn_%g)^alpha_n_%g) * ((omega_k_%g * exp(lnk(-1)) * (exp(lnrk_%g)/exp(lnrk))^nu_k)^alpha_k_%g) * (exp(lnh_%g)^(1-alpha_n_%g-alpha_k_%g)) / exp(lnv_%g)) ; \n',n*ones(1,13)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

for n = 1:nsectors
    nstring = sprintf('// Equation 12 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnrk_%g) * (omega_k_%g * exp(lnk(-1)) * (exp(lnrk_%g)/exp(lnrk))^nu_k) = alpha_k_%g * exp(lnmc_%g) * ((exp(lnn_%g)^alpha_n_%g) * ((omega_k_%g * exp(lnk(-1)) * (exp(lnrk_%g)/exp(lnrk))^nu_k)^alpha_k_%g) * (exp(lnh_%g)^(1-alpha_n_%g-alpha_k_%g)) / exp(lnv_%g)) ; \n',n*ones(1,14)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

for n = 1:nsectors
    nstring = sprintf('// Equation 13 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnqh_%g) * exp(lnh_%g) = (1-alpha_n_%g-alpha_k_%g) * exp(lnmc_%g) * ((exp(lnn_%g)^alpha_n_%g) * ((omega_k_%g * exp(lnk(-1)) * (exp(lnrk_%g)/exp(lnrk))^nu_k)^alpha_k_%g) * (exp(lnh_%g)^(1-alpha_n_%g-alpha_k_%g)) / exp(lnv_%g)) ; \n',n*ones(1,14)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end


for n = 1:nsectors
nstring = sprintf('// Equation 14 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('exp(lnqh_%g) = (0 ',n*ones(1,1)); fwrite(fid,nstring);
    for m = 1:nsectors
    nstring = sprintf('+ (omega_h_%g_%g',n*ones(1,1),m*ones(1,1));fwrite(fid,nstring);
    nstring = sprintf(' * exp(lnq_%g)^(1-nu_h))',m*ones(1,1));fwrite(fid,nstring);
    end
    nstring = sprintf(')^(1/(1-nu_h)); \n');fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

for n = 1:nsectors
    nstring = sprintf('// Equation 15 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnm1_%g) = exp(lnlambda) * exp(lnmc_%g) * ((exp(lnn_%g)^alpha_n_%g) * ((omega_k_%g * exp(lnk(-1)) * (exp(lnrk_%g)/exp(lnrk))^nu_k)^alpha_k_%g) * (exp(lnh_%g)^(1-alpha_n_%g-alpha_k_%g)) / exp(lnv_%g)) + beta*phi_%g*exp(lnm1_%g(+1)) * ((((1-phi_%g) * (exp(lnpistar_%g(+1))^(1-epsilon)) + phi_%g)^(1/(1-epsilon)))^epsilon); \n',n*ones(1,16)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

for n = 1:nsectors    
    nstring = sprintf('// Equation 16 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnm2_%g) = exp(lnlambda) * ((exp(lnn_%g)^alpha_n_%g) * ((omega_k_%g * exp(lnk(-1)) * (exp(lnrk_%g)/exp(lnrk))^nu_k)^alpha_k_%g) * (exp(lnh_%g)^(1-alpha_n_%g-alpha_k_%g)) / exp(lnv_%g)) + beta*phi_%g*(exp(lnm2_%g(+1)) * ((((1-phi_%g) * (exp(lnpistar_%g(+1))^(1-epsilon)) + phi_%g)^(1/(1-epsilon)))^epsilon) / (exp(lnpi(+1)))) ; \n',n*ones(1,15)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end
    
for n = 1:nsectors
    nstring = sprintf('// Equation 17 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnpistar_%g) = (epsilon/(epsilon-1)) * (exp(lnm1_%g)/exp(lnm2_%g)) * exp(lnpi) / exp(lnq_%g(-1)); \n',n*ones(1,4)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end


for n = 1:nsectors    
    nstring = sprintf('// Equation 18 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnv_%g) = (1-phi_%g) * (exp(lnpistar_%g)^(-epsilon)) * ((((1-phi_%g) * (exp(lnpistar_%g)^(1-epsilon)) + phi_%g)^(1/(1-epsilon)))^(epsilon)) + phi_%g * ((((1-phi_%g) * (exp(lnpistar_%g)^(1-epsilon)) + phi_%g)^(1/(1-epsilon)))^(epsilon)) * exp(lnv_%g(-1)); \n',n*ones(1,11)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end


for n = 1:nsectors
nstring = sprintf('// Equation 19 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('((exp(lnn_%g)^alpha_n_%g) * ((omega_k_%g * exp(lnk(-1)) * (exp(lnrk_%g)/exp(lnrk))^nu_k)^alpha_k_%g) * (exp(lnh_%g)^(1-alpha_n_%g-alpha_k_%g)) / exp(lnv_%g)) = (omega_c_%g * exp(lnc) * (exp(lnq_%g) / exp(lnqc))^(-nu_c)) + (nu_g_%g * exp(lnqg) * exp(lng) / exp(lnq_%g)) + (omega_inv_%g * exp(lninv) * (exp(lnq_%g)/exp(lnqinv))^(-nu_inv)) ',n*ones(1,15)); fwrite(fid,nstring);
for m = 1:nsectors
    nstring = sprintf('+ (omega_h_%g_%g  ',m*ones(1,1),n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('* ((exp(lnq_%g) ',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('/ exp(lnqh_%g))^(-nu_h))  ',m*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('* exp(lnh_%g))',m*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf('; \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
end


nstring = sprintf('// Equation 20 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnt) = exp(lnqg) * exp(lng); \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring); 


nstring = sprintf('// Equation 21 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnr)/r_ss = ((exp(lnr(-1))/r_ss)^rho_r)*((exp(lnpi)^phi_pi)^(1-rho_r))*((exp(lngap)^phi_y)^(1-rho_r)) + eps_r;  \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 22 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqc) = (0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' + (omega_c_%g * (exp(lnq_%g)^(1-nu_c)))',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1-nu_c)); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 23 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnva) = exp(lnqc) * exp(lnc) + exp(lnt) + exp(lninv) *  exp(lnqinv);\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 24 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lninvvalue) = exp(lnqinv) * exp(lninv); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);



nstring = sprintf('// Equation 25 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnlambda) = (psi_w^(1/psi_el)) * (((((psi_w^(1/psi_el)) * (exp(lnc)^((psi_el-1)/psi_el))) + (((1-psi_w)^(1/psi_el)) * (exp(lng)^((psi_el-1)/psi_el))))^(psi_el/(psi_el-1)))^((1/psi_el)-sigma)) * (exp(lnc)^(-1/psi_el)) / exp(lnqc); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 26 \n'); fwrite(fid,nstring);
nstring = sprintf('lng = (1 - rho_g) * log(g_ss) + rho_g * lng(-1) + eps_g; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 27 \n'); fwrite(fid,nstring);
nstring = sprintf('0  = 0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' + ((exp(lnq_%g) - 1) * ((omega_c_%g * exp(lnc) * (exp(lnq_%g) / exp(lnqc))^(-nu_c)) + (omega_inv_%g * exp(lninv) * (exp(lnq_%g)/exp(lnqinv))^(-nu_inv)) + (nu_g_%g * exp(lnqg) * exp(lng) / exp(lnq_%g)))) ',n*ones(1,7));fwrite(fid,nstring);
end
nstring = sprintf('; \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('// Equation 28 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lncvalue) = exp(lnqc) * exp(lnc); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 29 \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqg)  = 1'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' * (exp(lnq_%g)^nu_g_%g)',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf('; \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


for n = 1:nsectors
    nstring = sprintf('// Equation 30 - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnva_%g) = exp(lnq_%g) * ((exp(lnn_%g)^alpha_n_%g) * ((omega_k_%g * exp(lnk(-1)) * (exp(lnrk_%g)/exp(lnrk))^nu_k)^alpha_k_%g) * (exp(lnh_%g)^(1-alpha_n_%g-alpha_k_%g)) / exp(lnv_%g)) - exp(lnqh_%g) * exp(lnh_%g); \n',n*ones(1,13)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring); 
end


nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);




nstring = sprintf('// Equation 1 - FLEX\n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnlambdaflex) = beta * exp(lnlambdaflex(+1)) * exp(lnrflex);  \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 2 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('theta * (exp(lnnflex)^eta) = exp(lnwflex) * exp(lnlambdaflex);  \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 3 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnwflex) = ( (omega_n_1 * (exp(lnwflex_1)^(1+nu_n)))'); fwrite(fid,nstring);
for n = 2:nsectors
    nstring = sprintf(' + (omega_n_%g * (exp(lnwflex_%g)^(1+nu_n)))',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1+nu_n)); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 4 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnrkflex) = ( (omega_k_1 * (exp(lnrkflex_1)^(1+nu_k)))'); fwrite(fid,nstring);
for n = 2:nsectors
    nstring = sprintf(' + (omega_k_%g * (exp(lnrkflex_%g)^(1+nu_k)))',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1+nu_k)); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 5 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnkflex) = (1-delta_k) * exp(lnkflex(-1)) + exp(lninvflex)  * (1- ((Omega/2)* (((exp(lninvflex)/exp(lninvflex(-1)))-1)^2))) ; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 6 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqkflex) = beta * (exp(lnlambdaflex(+1))/exp(lnlambdaflex)) * (exp(lnrkflex(+1))+exp(lnqkflex(+1))*(1-delta_k)) ; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('// Equation 7 - FLEX \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqinvflex) = exp(lnqkflex) * ( 1 - ((Omega/2)*(((exp(lninvflex)/exp(lninvflex(-1)))-1)^2)) - (Omega*((exp(lninvflex)/exp(lninvflex(-1)))-1)*(exp(lninvflex)/exp(lninvflex(-1))))) + beta*(exp(lnlambdaflex(+1))/exp(lnlambdaflex))*exp(lnqkflex(+1))*Omega*((exp(lninvflex(+1))/exp(lninvflex))-1)*((exp(lninvflex(+1))/exp(lninvflex))^2); \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 8 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqinvflex)  = (0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' + (omega_inv_%g * (exp(lnqflex_%g)^(1-nu_inv)))',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1-nu_inv)); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


for n = 1:nsectors
    nstring = sprintf('// Equation 9 - FLEX  - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnwflex_%g) * (omega_n_%g * exp(lnnflex) * (exp(lnwflex_%g)/exp(lnwflex))^nu_n) = alpha_n_%g * (exp(lnqflex_%g) * ((epsilon-1)/epsilon)) * (((omega_n_%g * exp(lnnflex) * (exp(lnwflex_%g)/exp(lnwflex))^nu_n)^alpha_n_%g) * ((omega_k_%g * exp(lnkflex(-1)) * (exp(lnrkflex_%g)/exp(lnrkflex))^nu_k)^alpha_k_%g) * (exp(lnhflex_%g)^(1-alpha_n_%g-alpha_k_%g))) ; \n',n*ones(1,14)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

for n = 1:nsectors
    nstring = sprintf('// Equation 10 - FLEX  - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnrkflex_%g) * (omega_k_%g * exp(lnkflex(-1)) * (exp(lnrkflex_%g)/exp(lnrkflex))^nu_k) = alpha_k_%g * (exp(lnqflex_%g) * ((epsilon-1)/epsilon)) * (((omega_n_%g * exp(lnnflex) * (exp(lnwflex_%g)/exp(lnwflex))^nu_n)^alpha_n_%g) * ((omega_k_%g * exp(lnkflex(-1)) * (exp(lnrkflex_%g)/exp(lnrkflex))^nu_k)^alpha_k_%g) * (exp(lnhflex_%g)^(1-alpha_n_%g-alpha_k_%g))) ; \n',n*ones(1,14)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end

for n = 1:nsectors
    nstring = sprintf('// Equation 11 - FLEX  - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('exp(lnqhflex_%g) * exp(lnhflex_%g) = (1-alpha_n_%g-alpha_k_%g) * (exp(lnqflex_%g) * ((epsilon-1)/epsilon)) * (((omega_n_%g * exp(lnnflex) * (exp(lnwflex_%g)/exp(lnwflex))^nu_n)^alpha_n_%g) * ((omega_k_%g * exp(lnkflex(-1)) * (exp(lnrkflex_%g)/exp(lnrkflex))^nu_k)^alpha_k_%g) * (exp(lnhflex_%g)^(1-alpha_n_%g-alpha_k_%g))) ; \n',n*ones(1,14)); fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end


for n = 1:nsectors
nstring = sprintf('// Equation 12 - FLEX  - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('exp(lnqhflex_%g) = (0 ',n*ones(1,1)); fwrite(fid,nstring);
    for m = 1:nsectors
    nstring = sprintf('+ (omega_h_%g_%g',n*ones(1,1),m*ones(1,1));fwrite(fid,nstring);
    nstring = sprintf(' * exp(lnqflex_%g)^(1-nu_h))',m*ones(1,1));fwrite(fid,nstring);
    end
    nstring = sprintf(')^(1/(1-nu_h)); \n');fwrite(fid,nstring);
    nstring = sprintf(' \n'); fwrite(fid,nstring);
end


for n = 1:nsectors
nstring = sprintf('// Equation 13 - FLEX  - Sector %g\n',n*ones(1,1)); fwrite(fid,nstring);
nstring = sprintf('(((omega_n_%g * exp(lnnflex) * (exp(lnwflex_%g)/exp(lnwflex))^nu_n)^alpha_n_%g) * ((omega_k_%g * exp(lnkflex(-1)) * (exp(lnrkflex_%g)/exp(lnrkflex))^nu_k)^alpha_k_%g) * (exp(lnhflex_%g)^(1-alpha_n_%g-alpha_k_%g))) = (omega_c_%g * exp(lncflex) * (exp(lnqflex_%g) / exp(lnqcflex))^(-nu_c)) + (nu_g_%g * exp(lnqgflex) * exp(lng) / exp(lnqflex_%g)) + (omega_inv_%g * exp(lninvflex) * (exp(lnqflex_%g)/exp(lnqinvflex))^(-nu_inv)) ',n*ones(1,15)); fwrite(fid,nstring);
for m = 1:nsectors
        nstring = sprintf('+ (omega_h_%g_%g  ',m*ones(1,1),n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('* ((exp(lnqflex_%g) ',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('/ exp(lnqhflex_%g))^(-nu_h))  ',m*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('* exp(lnhflex_%g))',m*ones(1,1)); fwrite(fid,nstring);
end
nstring = sprintf('; \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
end


nstring = sprintf('// Equation 14 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lntflex) = exp(lnqgflex) * exp(lng); \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 15 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqcflex)  = (0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' + (omega_c_%g * (exp(lnqflex_%g)^(1-nu_c)))',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf(')^(1/(1-nu_c)); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('// Equation 16 - FLEX  - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnvaflex) = exp(lnqcflex) * exp(lncflex) + exp(lntflex) + exp(lninvflex) *  exp(lnqinvflex);\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('// Equation 17 - FLEX  \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lngap) = exp(lnva) / exp(lnvaflex); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 18 - FLEX \n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnlambdaflex) = (psi_w^(1/psi_el)) * (((((psi_w^(1/psi_el)) * (exp(lncflex)^((psi_el-1)/psi_el))) + (((1-psi_w)^(1/psi_el)) * (exp(lng)^((psi_el-1)/psi_el))))^(psi_el/(psi_el-1)))^((1/psi_el)-sigma)) * (exp(lncflex)^(-1/psi_el)) / exp(lnqcflex); \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('// Equation 19 - FLEX \n'); fwrite(fid,nstring);
nstring = sprintf('0  = 0'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' + ((exp(lnqflex_%g) - 1) * ((omega_c_%g * exp(lncflex) * (exp(lnqflex_%g) / exp(lnqcflex))^(-nu_c)) + (omega_inv_%g * exp(lninvflex) * (exp(lnqflex_%g)/exp(lnqinvflex))^(-nu_inv)) + (nu_g_%g * exp(lnqgflex) * exp(lng) / exp(lnqflex_%g)))) ',n*ones(1,7));fwrite(fid,nstring);
end
nstring = sprintf('; \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('// Equation 20 - FLEX\n'); fwrite(fid,nstring);
nstring = sprintf('exp(lnqgflex)  = 1'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf(' * (exp(lnqflex_%g)^nu_g_%g)',n*ones(1,2));fwrite(fid,nstring);
end
nstring = sprintf('; \n');fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);
nstring = sprintf('end; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('write_latex_static_model; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);





nstring = sprintf('initval; \n'); fwrite(fid,nstring);
for n = 1:nsectors
    nstring = sprintf('lnn_%g = log(n_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('lnw_%g = log(w_ss); \n',n*ones(1,1)); fwrite(fid,nstring);     
    nstring = sprintf('lnrk_%g = log(rk_ss); \n',n*ones(1,1)); fwrite(fid,nstring);     
    nstring = sprintf('lnq_%g = log(q_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring); 
    nstring = sprintf('lnqh_%g = log(qh_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    
    nstring = sprintf('lnh_%g = log(h_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('lnmc_%g = log(mc_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);        
    nstring = sprintf('lnpistar_%g = 0; \n',n*ones(1,1)); fwrite(fid,nstring);    
    nstring = sprintf('lnv_%g = 0; \n',n*ones(1,1)); fwrite(fid,nstring);
    nstring = sprintf('lnm1_%g = log(m1_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    
    nstring = sprintf('lnm2_%g = log(m2_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);    
    nstring = sprintf('lnva_%g = log(va_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);


    nstring = sprintf('lnwflex_%g = log(w_ss); \n',n*ones(1,1)); fwrite(fid,nstring);    
    nstring = sprintf('lnrkflex_%g = log(rk_ss); \n',n*ones(1,1)); fwrite(fid,nstring);    
    nstring = sprintf('lnqflex_%g = log(q_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('lnqhflex_%g = log(qh_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);
    nstring = sprintf('lnhflex_%g = log(h_%g_ss); \n',n*ones(1,2)); fwrite(fid,nstring);       
end


nstring = sprintf('lnc = log(c_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnn = log(n_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnt = log(t_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnw = log(w_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnr = log(r_ss); \n'); fwrite(fid,nstring);

nstring = sprintf('lnpi = 0; \n'); fwrite(fid,nstring);
nstring = sprintf('lninv = log(inv_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnk = log(k_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnrk = log(rk_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnqinv = log(qinv_ss); \n'); fwrite(fid,nstring);

nstring = sprintf('lnqk = log(qinv_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnva = log(va_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnlambda = log(lambda_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lng = log(g_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lninvvalue = log(inv_ss * qinv_ss); \n'); fwrite(fid,nstring);

nstring = sprintf('lnqc = log(qc_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lncvalue = log(c_ss * qc_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnqg = log(qg_ss); \n'); fwrite(fid,nstring);


nstring = sprintf('lncflex = log(c_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnqkflex = log(qinv_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnnflex = log(n_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lntflex = log(t_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnwflex = log(w_ss); \n'); fwrite(fid,nstring);

nstring = sprintf('lnrflex = log(r_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lninvflex = log(inv_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnkflex = log(k_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnrkflex = log(rk_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnqinvflex = log(qinv_ss); \n'); fwrite(fid,nstring);

nstring = sprintf('lnvaflex = log(va_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lngap = 0; \n'); fwrite(fid,nstring);
nstring = sprintf('lnlambdaflex = log(lambda_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnqcflex = log(qc_ss); \n'); fwrite(fid,nstring);
nstring = sprintf('lnqgflex = log(qg_ss); \n'); fwrite(fid,nstring);



nstring = sprintf('end; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

% 不使用steady命令，直接使用外部计算的稳态值
% nstring = sprintf('steady(nocheck); \n'); fwrite(fid,nstring);
% nstring = sprintf(' \n'); fwrite(fid,nstring);

nstring = sprintf('shocks; \n'); fwrite(fid,nstring);
nstring = sprintf('var eps_g = 1; \n'); fwrite(fid,nstring);
nstring = sprintf('var eps_r = 1; \n'); fwrite(fid,nstring);
nstring = sprintf('end; \n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);


nstring = sprintf('stoch_simul(irf=2000, periods =2000, order=1, nograph, noprint) lncvalue, lnt, lnva, lninvvalue, lnpi, lnn, lnw, lnr'); fwrite(fid,nstring);
for n = 1:nsectors
nstring = sprintf(', lnva_%g, lnn_%g ',n*ones(1,2)); fwrite(fid,nstring);
end
nstring = sprintf(';\n'); fwrite(fid,nstring);
nstring = sprintf(' \n'); fwrite(fid,nstring);

fclose(fid);

fprintf('  ✓ dynare_script.mod已生成\n');
fprintf('\n');

fprintf('=== 步骤5完成 ===\n\n');

