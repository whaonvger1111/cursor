"""
详细检查MATLAB中aux的计算方式
"""
import numpy as np

# 参数值
A = 0.25
alpha = 0.3
delta_k = 0.015
KL_ratio = 4.511862  # Python的KL_ratio

print('='*80)
print('MATLAB aux计算详细分析')
print('='*80)
print('')

print('1. MATLAB代码分析')
print('-'*80)
print('fun_aggregates.m 第100行:')
print('  aux = fun.prod_corp(KL_ratio,1/KL_ratio,par)-delta_k;')
print('')
print('fun.m 第59-64行 (prod_corp函数):')
print('  function F = prod_corp(KL_ratio,L,par)')
print('      F = par.A*KL_ratio^par.alpha*L;')
print('  end')
print('')

print('2. 逐步计算')
print('-'*80)
print('步骤1: 调用prod_corp')
print(f'  prod_corp(KL_ratio={KL_ratio:.6f}, L=1/KL_ratio={1/KL_ratio:.6f}, par)')
print('')
print('步骤2: prod_corp函数内部计算')
print(f'  F = A * KL_ratio^alpha * L')
print(f'  F = {A:.6f} * {KL_ratio:.6f}^{alpha:.1f} * {1/KL_ratio:.6f}')
print(f'  F = {A:.6f} * {KL_ratio**alpha:.6f} * {1/KL_ratio:.6f}')
prod_corp_result = A * (KL_ratio ** alpha) * (1 / KL_ratio)
print(f'  F = {prod_corp_result:.6f}')
print('')
print('步骤3: 简化公式')
print(f'  F = A * KL_ratio^alpha * (1/KL_ratio)')
print(f'  F = A * KL_ratio^alpha / KL_ratio')
print(f'  F = A * KL_ratio^(alpha-1)')
simplified = A * (KL_ratio ** (alpha - 1))
print(f'  F = {A:.6f} * {KL_ratio:.6f}^({alpha:.1f}-1)')
print(f'  F = {A:.6f} * {KL_ratio:.6f}^{-1+alpha:.1f}')
print(f'  F = {A:.6f} * {KL_ratio**(alpha-1):.6f}')
print(f'  F = {simplified:.6f}')
print('')
print('步骤4: 计算aux')
print(f'  aux = F - delta_k')
print(f'  aux = {prod_corp_result:.6f} - {delta_k:.6f}')
aux_method1 = prod_corp_result - delta_k
print(f'  aux = {aux_method1:.6f}')
print('')
print('或者使用简化公式:')
print(f'  aux = A * KL_ratio^(alpha-1) - delta_k')
print(f'  aux = {simplified:.6f} - {delta_k:.6f}')
aux_method2 = simplified - delta_k
print(f'  aux = {aux_method2:.6f}')
print('')

print('3. 验证两种方法是否一致')
print('-'*80)
print(f'方法1 (prod_corp结果 - delta_k): {aux_method1:.6f}')
print(f'方法2 (简化公式): {aux_method2:.6f}')
print(f'差异: {abs(aux_method1 - aux_method2):.2e}')
if abs(aux_method1 - aux_method2) < 1e-10:
    print('[OK] 两种方法结果一致')
else:
    print('[ERROR] 两种方法结果不一致！')
print('')

print('4. 对比Python当前实现')
print('-'*80)
print('Python当前实现 (fun_aggregates.py 第122行):')
print('  aux = A * (KL_ratio^alpha) - delta_k')
aux_python_current = A * (KL_ratio ** alpha) - delta_k
print(f'  aux = {A:.6f} * ({KL_ratio:.6f}^{alpha:.1f}) - {delta_k:.6f}')
print(f'  aux = {A:.6f} * {KL_ratio**alpha:.6f} - {delta_k:.6f}')
print(f'  aux = {aux_python_current:.6f}')
print('')
print('MATLAB方式 (根据代码):')
print('  aux = A * KL_ratio^(alpha-1) - delta_k')
print(f'  aux = {aux_method2:.6f}')
print('')
print('MATLAB实际结果 (从文档):')
aux_matlab_actual = 0.377871
print(f'  aux = {aux_matlab_actual:.6f}')
print('')

print('5. 对比分析')
print('-'*80)
print(f'Python当前实现: {aux_python_current:.6f}')
print(f'MATLAB代码方式: {aux_method2:.6f}')
print(f'MATLAB实际结果: {aux_matlab_actual:.6f}')
print('')
print('差异:')
print(f'  Python当前 vs MATLAB代码方式: {abs(aux_python_current - aux_method2):.6f}')
print(f'  Python当前 vs MATLAB实际结果: {abs(aux_python_current - aux_matlab_actual):.6f}')
print(f'  MATLAB代码方式 vs MATLAB实际结果: {abs(aux_method2 - aux_matlab_actual):.6f}')
print('')

if abs(aux_python_current - aux_matlab_actual) < abs(aux_method2 - aux_matlab_actual):
    print('[结论] Python当前实现更接近MATLAB实际结果！')
    print('        MATLAB代码可能有错误，或者prod_corp函数的调用方式不同')
else:
    print('[结论] MATLAB代码方式更接近MATLAB实际结果')
    print('        Python需要修复为使用KL_ratio^(alpha-1)')

print('')
print('6. 检查fun_aggregates_tran.m中的注释')
print('-'*80)
print('fun_aggregates_tran.m 第257行有注释:')
print('  %aux = KL_ratio(t)^(alpha-1)-delta_k;')
print('')
print('这可能是之前版本的代码，但被注释掉了')
print('实际使用的是: aux = fun.prod_corp(KL_ratio,1/KL_ratio,par)-delta_k;')












