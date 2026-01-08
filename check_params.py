"""检查参数类型"""
import sys
import numpy as np
from set_parameters import set_parameters

par = {}
par, _, _, _, _, _, _ = set_parameters(par, 'estim_params.txt')

print(f'theta类型: {type(par["theta"])}, 值: {par["theta"]}')
print(f'delta_k类型: {type(par["delta_k"])}, 值: {par["delta_k"]}')
print(f'theta是数组: {isinstance(par["theta"], np.ndarray)}')
print(f'delta_k是数组: {isinstance(par["delta_k"], np.ndarray)}')

# 检查是否需要转换
theta = par['theta']
delta = par['delta_k']

if isinstance(theta, np.ndarray):
    if theta.size == 1:
        theta = float(theta.item())
        print(f'theta转换为标量: {theta}')
    else:
        print(f'theta是数组，形状: {theta.shape}')
else:
    print(f'theta已经是标量: {theta}')

if isinstance(delta, np.ndarray):
    if delta.size == 1:
        delta = float(delta.item())
        print(f'delta转换为标量: {delta}')
    else:
        print(f'delta是数组，形状: {delta.shape}')
else:
    print(f'delta已经是标量: {delta}')







