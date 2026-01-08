"""
检查实际结果文件中的参数值
"""
import pickle

try:
    with open('steady_state_results.pkl', 'rb') as f:
        ss_results = pickle.load(f)
    
    par = ss_results.get('par', {})
    sol = ss_results.get('sol', {})
    
    print('='*80)
    print('实际结果文件中的网格大小')
    print('='*80)
    print('')
    
    print('参数中的网格大小:')
    print('-'*80)
    print(f'  nx = {par.get("nx", "N/A")}')
    print(f'  nb = {par.get("nb", "N/A")}')
    print(f'  nk = {par.get("nk", "N/A")}')
    print('')
    
    print('实际数组的形状:')
    print('-'*80)
    if 'V1' in sol:
        print(f'  V1形状: {sol["V1"].shape} (应该是(nk, nx))')
    if 'pol_kp_unc' in sol:
        print(f'  pol_kp_unc形状: {sol["pol_kp_unc"].shape} (应该是(nk, nx))')
    if 'pol_kp' in sol:
        print(f'  pol_kp形状: {sol["pol_kp"].shape} (应该是(nk, nb, nx))')
    if 'k_grid' in par:
        print(f'  k_grid长度: {len(par["k_grid"]) if hasattr(par["k_grid"], "__len__") else "N/A"} (应该是nk)')
    if 'x_grid' in par:
        print(f'  x_grid长度: {len(par["x_grid"]) if hasattr(par["x_grid"], "__len__") else "N/A"} (应该是nx)')
    print('')
    
    print('结论:')
    print('-'*80)
    if 'V1' in sol:
        actual_nk, actual_nx = sol['V1'].shape
        param_nk = par.get('nk', 0)
        param_nx = par.get('nx', 0)
        
        if actual_nk != param_nk or actual_nx != param_nx:
            print(f'警告：实际网格大小({actual_nk}, {actual_nx})与参数({param_nk}, {param_nx})不匹配！')
            print('这说明结果文件是用旧的参数计算的')
        else:
            print('实际网格大小与参数一致')
    
except FileNotFoundError:
    print('未找到steady_state_results.pkl文件')



