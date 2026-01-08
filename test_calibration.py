"""
测试校准：验证目标函数是否正确添加市场出清惩罚项
"""
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from set_parameters import set_parameters
from set_targets_ss import set_targets_ss
from fun_obj import fun_obj

print('='*80)
print('测试校准：验证目标函数')
print('='*80)
print('')

# 设置参数
par = {}
par['do_calib'] = 2
par['InpDir'] = os.path.join('inputs')
par['TabDir'] = 'tables'
par['do_table'] = 0
par['do_tex'] = 0
par['verbose'] = 1
par['disp_mu'] = 0
par['disp_tran'] = 0

file_params = 'estim_params.txt'

# 设置参数
par, guess, bounds, calibNames, dispNames, description, ExoNames = set_parameters(par, file_params)

# 加载数据矩
targetNames, targetNames_long, calibWeights, data_mom = set_targets_ss()

# 测试当前参数值
print('测试当前参数值...')
print('')
guess_flat = np.asarray(guess).flatten()

obj_smm, sol, agg, b_grid, distribS, prices, model_mom, flag_ss, par_updated = \
    fun_obj(guess_flat, par.copy(), bounds, calibNames, data_mom, targetNames,
           calibWeights, description, dispNames, targetNames_long)

print('')
print('='*80)
print('测试结果')
print('='*80)
print(f'目标函数值: {obj_smm:.6f}')
print('')

if agg is not None:
    K_corp = agg.get('K_corp', 0)
    LHS = agg.get('LHS', 0)
    aux = agg.get('aux', 0)
    
    print('市场出清检查:')
    print(f'  K_corp = {K_corp:15.6f}')
    print(f'  LHS    = {LHS:15.6f}')
    print(f'  aux    = {aux:15.6f}')
    print('')
    
    if K_corp < 0 or LHS < 0 or aux <= 0:
        print('✗ 市场出清条件不满足，目标函数应该包含惩罚项')
        print(f'  如果惩罚项正确添加，obj_smm应该很大（>10000）')
    else:
        print('✓ 市场出清条件满足')
    
    print('')
    print('当前参数值:')
    for i, name in enumerate(calibNames):
        print(f'  {name:12s} = {guess_flat[i]:15.10f}')

