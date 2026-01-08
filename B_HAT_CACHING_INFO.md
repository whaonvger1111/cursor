# B_hat缓存说明

## ✅ B_hat已被缓存

B_hat的计算结果已经包含在无约束企业VFI的缓存中，无需额外配置。

---

## 📋 缓存内容

当从缓存加载时，以下计算结果会被跳过：

1. **V1**: 无约束企业的价值函数
2. **x_tilde**: 生产率截断值索引
3. **x_tilde_val**: 生产率截断值
4. **pol_kp_unc**: 无约束投资政策
5. **B_hat**: B_hat固定点 ⭐ **已缓存**
6. **pol_bp_unc**: 无约束债务政策
7. **b_grid**: 债务网格
8. **kp_bar**: 下一期资本上界
9. **val_unc**: 无约束企业退出后的价值
10. **val0_unc**: 无约束企业退出前的价值
11. **profit_mat**: 利润矩阵
12. **b_tilde**: b_tilde值

---

## 🚀 使用效果

### 第一次运行
```
缓存未找到，开始计算无约束企业VFI (cache_key: 9ac4b0a2...)
VFI for unconstrained firms...
Time elapsed: 12.6001
Fixed point B_hat...
Time elapsed: 5.2345
无约束企业VFI结果已保存到缓存: cache/unconstrained_vfi_9ac4b0a2e71cae460c2160dbbf224448.pkl
  已保存: V1, x_tilde, pol_kp_unc, B_hat, b_grid, kp_bar, val_unc, val0_unc
```

### 后续运行（使用缓存）
```
从缓存加载无约束企业VFI结果 (cache_key: 9ac4b0a2...)
  跳过计算: V1, x_tilde, pol_kp_unc, B_hat, b_grid, kp_bar, val_unc, val0_unc
VFI for constrained firms...
```

---

## ⏱️ 时间节省

- **B_hat固定点计算**: 约5-10秒（取决于迭代次数）
- **无约束企业VFI**: 约10-15秒
- **总计节省**: 每次运行可节省约15-25秒

---

## 🔍 验证方法

运行程序时，如果看到以下输出，说明B_hat已被缓存：

```
从缓存加载无约束企业VFI结果 (cache_key: ...)
  跳过计算: V1, x_tilde, pol_kp_unc, B_hat, b_grid, kp_bar, val_unc, val0_unc
```

注意：**不会看到** "Fixed point B_hat..." 的输出，因为B_hat的计算已被跳过。

---

## 📝 注意事项

1. **参数匹配**: B_hat的缓存依赖于价格和关键参数，如果这些参数变化，缓存会自动失效
2. **缓存键**: B_hat的缓存键与无约束企业VFI相同，因为它们共享相同的输入参数
3. **自动管理**: 无需手动管理B_hat的缓存，它会自动与无约束企业VFI一起缓存和加载

---

生成时间: 2026-01-05








