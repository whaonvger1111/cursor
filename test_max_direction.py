"""
测试max操作的方向
MATLAB: max(RHS,[],1) 沿着第1维（列）取最大值
Python: np.argmax(RHS, axis=?) 应该对应哪个axis？
"""
import numpy as np

# 创建一个测试矩阵
RHS = np.array([[1, 4, 7],
                [2, 5, 8],
                [3, 6, 9]])

print('测试矩阵RHS:')
print(RHS)
print('形状:', RHS.shape)
print('')

print('MATLAB: max(RHS,[],1) 沿着第1维（列）取最大值')
print('  对每一列，找该列的最大值')
print('  第1列最大值: 3 (第3行)')
print('  第2列最大值: 6 (第3行)')
print('  第3列最大值: 9 (第3行)')
print('  返回: [3, 6, 9] 和索引 [3, 3, 3] (1-based)')
print('')

print('Python测试:')
print('-'*80)

# axis=0: 沿着行（第0维）取最大值，即对每一列找最大值
max_indices_axis0 = np.argmax(RHS, axis=0)
max_values_axis0 = np.max(RHS, axis=0)
print('np.argmax(RHS, axis=0):')
print(f'  索引: {max_indices_axis0} (0-based)')
print(f'  值: {max_values_axis0}')
print('  说明: 沿着axis=0（行）取最大值，即对每一列找最大值')
print('  第1列最大值索引: 2 (第3行，0-based)')
print('  第2列最大值索引: 2 (第3行，0-based)')
print('  第3列最大值索引: 2 (第3行，0-based)')
print('')

# axis=1: 沿着列（第1维）取最大值，即对每一行找最大值
max_indices_axis1 = np.argmax(RHS, axis=1)
max_values_axis1 = np.max(RHS, axis=1)
print('np.argmax(RHS, axis=1):')
print(f'  索引: {max_indices_axis1} (0-based)')
print(f'  值: {max_values_axis1}')
print('  说明: 沿着axis=1（列）取最大值，即对每一行找最大值')
print('  第1行最大值索引: 2 (第3列，0-based)')
print('  第2行最大值索引: 2 (第3列，0-based)')
print('  第3行最大值索引: 2 (第3列，0-based)')
print('')

print('结论:')
print('-'*80)
print('MATLAB的max(RHS,[],1)对应Python的np.argmax(RHS, axis=0)')
print('两者都是对每一列找最大值')
print('')

# 验证sub_V1_onestep中的使用
print('在sub_V1_onestep中的使用:')
print('-'*80)
print('MATLAB: [V2(:,x_c),kpol_ind(:,x_c)] = max(RHS,[],1)')
print('  RHS是(nk,nk)')
print('  max沿着第1维（列）取最大值')
print('  返回: V2(:,x_c)是(nk,1)，kpol_ind(:,x_c)是(nk,1)')
print('  含义: 对每个k（行），找最优的k\'（列）')
print('')
print('Python: max_indices = np.argmax(RHS, axis=0)')
print('  RHS是(nk,nk)')
print('  argmax沿着axis=0（行）取最大值')
print('  返回: max_indices是(nk,)')
print('  含义: 对每个k（行），找最优的k\'（列）')
print('')
print('结论: axis=0是正确的！')



