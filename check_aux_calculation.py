"""
检查aux的计算方式，对比Python和MATLAB
"""
import numpy as np

# Python参数
A = 0.25
alpha = 0.3
delta_k = 0.015

# Python的KL_ratio（从之前的输出）
KL_ratio_python = 4.511862

# MATLAB的KL_ratio（从文档）
KL_ratio_matlab = 4.511990

print('='*80)
print('aux计算方式检查')
print('='*80)
print('')

print('Python计算方式:')
print('  aux = Fun.prod_corp(KL_ratio, 1 / KL_ratio, par) - delta_k')
print('  其中: Fun.prod_corp(KL_ratio, L, par) = A * (KL_ratio^alpha) * L')
print('  所以: aux = A * (KL_ratio^alpha) * (1/KL_ratio) - delta_k')
print('       aux = A * (KL_ratio^(alpha-1)) - delta_k')
print('')

# Python计算
aux_python = A * (KL_ratio_python ** (alpha - 1)) - delta_k
print(f'Python计算:')
print(f'  KL_ratio = {KL_ratio_python:.6f}')
print(f'  aux = {A:.6f} * ({KL_ratio_python:.6f}^({alpha:.1f}-1)) - {delta_k:.6f}')
print(f'  aux = {A:.6f} * ({KL_ratio_python:.6f}^{-1+alpha:.1f}) - {delta_k:.6f}')
print(f'  aux = {A:.6f} * {KL_ratio_python**(alpha-1):.6f} - {delta_k:.6f}')
print(f'  aux = {A * KL_ratio_python**(alpha-1):.6f} - {delta_k:.6f}')
print(f'  aux = {aux_python:.6f}')
print('')

# MATLAB结果（从文档）
aux_matlab = 0.377871
print(f'MATLAB结果:')
print(f'  KL_ratio = {KL_ratio_matlab:.6f}')
print(f'  aux = {aux_matlab:.6f}')
print('')

print('差异分析:')
print(f'  Python aux = {aux_python:.6f}')
print(f'  MATLAB aux = {aux_matlab:.6f}')
print(f'  差异 = {aux_python - aux_matlab:.6f}')
print(f'  差异倍数 = {aux_matlab / aux_python:.2f}倍')
print('')

# 尝试反推MATLAB的计算方式
print('尝试反推MATLAB的计算方式:')
print('  如果MATLAB使用不同的公式，可能是:')
print('  1. aux = A * (KL_ratio^alpha) - delta_k  (不使用1/KL_ratio)')
aux_alt1 = A * (KL_ratio_matlab ** alpha) - delta_k
print(f'     aux = {A:.6f} * ({KL_ratio_matlab:.6f}^{alpha:.1f}) - {delta_k:.6f}')
print(f'     aux = {aux_alt1:.6f}')
print(f'     与MATLAB的差异: {abs(aux_alt1 - aux_matlab):.6f}')
print('')

print('  2. aux = marg_prod_capital(KL_ratio) - delta_k')
marg_prod = A * alpha * (KL_ratio_matlab ** (alpha - 1))
aux_alt2 = marg_prod - delta_k
print(f'     marg_prod_capital = {A:.6f} * {alpha:.1f} * ({KL_ratio_matlab:.6f}^({alpha:.1f}-1))')
print(f'     marg_prod_capital = {marg_prod:.6f}')
print(f'     aux = {aux_alt2:.6f}')
print(f'     与MATLAB的差异: {abs(aux_alt2 - aux_matlab):.6f}')
print('')

print('  3. 检查是否KL_ratio的计算方式不同')
print(f'     Python KL_ratio = {KL_ratio_python:.6f}')
print(f'     MATLAB KL_ratio = {KL_ratio_matlab:.6f}')
print(f'     差异很小: {abs(KL_ratio_python - KL_ratio_matlab):.6f}')
print('')

print('='*80)
print('结论')
print('='*80)
print('')
print('Python的aux计算:')
print('  aux = A * (KL_ratio^(alpha-1)) - delta_k')
print(f'  aux = {aux_python:.6f}')
print('')
print('MATLAB的aux结果:')
print(f'  aux = {aux_matlab:.6f}')
print('')
print('可能的原因:')
print('  1. MATLAB可能使用不同的公式计算aux')
print('  2. 或者prod_corp函数的实现不同')
print('  3. 需要对比MATLAB代码中的aux计算方式')












