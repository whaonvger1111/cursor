"""快速测试容差设置"""
import sys
import os
sys.path.insert(0, '.')

from set_parameters import set_parameters

# 设置参数
par = {}
par, _, _, _, _, _, _ = set_parameters(par, 'estim_params.txt')

print("原始容差设置:")
print(f"  tol_vfi: {par['tol_vfi']}")
print(f"  tol_bhat: {par['tol_bhat']}")
print(f"  tol_vfi_u: {par['tol_vfi_u']}")
print(f"  tol_dist: {par['tol_dist']}")

# 修改容差
par['tol_vfi'] = 0.01
par['tol_bhat'] = 0.01
par['tol_vfi_u'] = 0.01
par['tol_dist'] = 0.01

print("\n修改后容差设置:")
print(f"  tol_vfi: {par['tol_vfi']}")
print(f"  tol_bhat: {par['tol_bhat']}")
print(f"  tol_vfi_u: {par['tol_vfi_u']}")
print(f"  tol_dist: {par['tol_dist']}")

print("\n容差设置成功！")








