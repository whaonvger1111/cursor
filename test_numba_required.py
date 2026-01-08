"""
测试Numba必须启用的功能
"""
import sys
import numpy as np
sys.path.insert(0, 'sub')

# 测试1: 正常情况（Numba可用）
print("=" * 60)
print("测试1: Numba可用时的行为")
print("=" * 60)
try:
    from sub_vfi_onestep import sub_vfi_onestep, USE_NUMBA
    print(f"USE_NUMBA = {USE_NUMBA}")
    if USE_NUMBA:
        print("[OK] Numba已启用，代码应该正常工作")
    else:
        print("[ERROR] Numba未启用，应该抛出RuntimeError")
except Exception as e:
    print(f"[ERROR] 导入失败: {e}")

# 测试2: 模拟Numba不可用的情况
print("\n" + "=" * 60)
print("测试2: 模拟Numba不可用的情况")
print("=" * 60)
try:
    import sub.sub_vfi_onestep as mod
    # 临时禁用Numba
    original_use_numba = mod.USE_NUMBA
    mod.USE_NUMBA = False
    
    # 尝试调用函数
    nk, nb, nx = 10, 10, 5
    val_c = np.random.rand(nk, nb, nx)
    val0_u = np.random.rand(nk, nb, nx)
    kp_bar = np.random.rand(nk, nb, nx)
    B_hat = np.random.rand(nk, nx)
    profit_mat = np.random.rand(nk, nx)
    k_grid = np.linspace(0.1, 10, nk)
    b_grid = np.random.rand(nk, nb)
    pi_x = np.random.rand(nx, nx)
    pi_x = pi_x / pi_x.sum(axis=1, keepdims=True)
    
    result = mod.sub_vfi_onestep(
        val_c, val0_u, kp_bar, B_hat, profit_mat,
        k_grid, b_grid, pi_x, 0.5, 0.99, 0.015, 0.01, 1, 5
    )
    print("[ERROR] 应该抛出RuntimeError但没有抛出")
except RuntimeError as e:
    print(f"[SUCCESS] 按预期抛出RuntimeError")
    print(f"  错误信息: {str(e)[:80]}")
except Exception as e:
    print(f"[ERROR] 意外错误: {type(e).__name__}: {e}")
finally:
    # 恢复原始状态
    mod.USE_NUMBA = original_use_numba

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)

