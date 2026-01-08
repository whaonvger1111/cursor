"""
快速测试脚本 - 验证Numba编译和基本功能
"""
import sys
import numpy as np
import time

print("=" * 60)
print("快速测试 - Numba编译和基本功能")
print("=" * 60)

# 测试1: 导入模块
print("\n1. 测试模块导入...")
try:
    sys.path.insert(0, 'sub')
    from sub_vfi_onestep import sub_vfi_onestep_numba_no_precomputed, USE_NUMBA
    print(f"   [OK] USE_NUMBA = {USE_NUMBA}")
    print(f"   [OK] 函数类型: {type(sub_vfi_onestep_numba_no_precomputed)}")
except Exception as e:
    print(f"   [ERROR] 导入失败: {e}")
    sys.exit(1)

# 测试2: Numba编译
print("\n2. 测试Numba编译...")
try:
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
    theta, q, delta, psi = 0.5, 0.99, 0.015, 0.01
    do_howard, n_howard = 1, 5
    
    start_time = time.time()
    result = sub_vfi_onestep_numba_no_precomputed(
        val_c, val0_u, kp_bar, B_hat, profit_mat,
        k_grid, b_grid, pi_x, theta, q, delta, psi,
        do_howard, n_howard
    )
    elapsed = time.time() - start_time
    
    val_new, pol_kp_ind = result
    print(f"   [OK] Numba编译成功")
    print(f"   [OK] 执行时间: {elapsed:.4f}秒")
    print(f"   [OK] 输出形状: val_new={val_new.shape}, pol_kp_ind={pol_kp_ind.shape}")
except Exception as e:
    print(f"   [ERROR] Numba编译失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3: 测试sub_vfi_onestep包装函数
print("\n3. 测试sub_vfi_onestep包装函数...")
try:
    from sub_vfi_onestep import sub_vfi_onestep
    
    start_time = time.time()
    result = sub_vfi_onestep(
        val_c, val0_u, kp_bar, B_hat, profit_mat,
        k_grid, b_grid, pi_x, theta, q, delta, psi,
        do_howard, n_howard
    )
    elapsed = time.time() - start_time
    
    val_new2, pol_kp_ind2 = result
    print(f"   [OK] 包装函数执行成功")
    print(f"   [OK] 执行时间: {elapsed:.4f}秒")
    print(f"   [OK] 输出形状: val_new={val_new2.shape}, pol_kp_ind={pol_kp_ind2.shape}")
except Exception as e:
    print(f"   [ERROR] 包装函数失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("所有测试通过！")
print("=" * 60)

