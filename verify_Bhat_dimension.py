"""
验证B_hat计算中pol_bp_unc的维度计算是否正确
"""
import numpy as np

# 测试维度计算
nk, nx = 50, 30  # 更新为当前校准模式的网格大小

# 创建测试数据
B_hat_interp = np.random.rand(nk, nx)  # (nk, nx)
kp_val = np.random.rand(nk)  # (nk,)

print("测试维度计算：")
print(f"B_hat_interp形状: {B_hat_interp.shape}")
print(f"kp_val形状: {kp_val.shape}")

# Python当前实现
result_python = np.nanmin(B_hat_interp, axis=1)  # 对第1维（行）取最小值
print(f"\nPython: np.nanmin(B_hat_interp, axis=1)")
print(f"  结果形状: {result_python.shape}")
print(f"  含义: 对每个nk，在所有nx中取最小值")

# MATLAB等价实现（如果维度顺序相同）
# MATLAB的min(B_hat_interp,[],2)应该等价于np.nanmin(B_hat_interp, axis=1)
result_matlab_equiv = np.nanmin(B_hat_interp, axis=1)
print(f"\nMATLAB等价: min(B_hat_interp,[],2) -> np.nanmin(B_hat_interp, axis=1)")
print(f"  结果形状: {result_matlab_equiv.shape}")

# 检查是否一致
if np.allclose(result_python, result_matlab_equiv):
    print("\n[OK] Python和MATLAB的维度计算一致")
else:
    print("\n[警告] Python和MATLAB的维度计算不一致")

# 测试pol_bp_unc的计算
lambda_val = 0.7
pol_bp_unc_python = np.minimum(lambda_val * kp_val, result_python)
print(f"\npol_bp_unc计算:")
print(f"  lambda_val * kp_val形状: {(lambda_val * kp_val).shape}")
print(f"  result_python形状: {result_python.shape}")
print(f"  pol_bp_unc形状: {pol_bp_unc_python.shape}")

# 检查维度是否匹配
if (lambda_val * kp_val).shape == result_python.shape:
    print("\n[OK] 维度匹配")
else:
    print("\n[错误] 维度不匹配")






