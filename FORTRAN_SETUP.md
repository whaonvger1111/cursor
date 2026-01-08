# Fortran混合编程设置指南

## 概述

本项目支持使用Fortran混合编程来加速VFI（Value Function Iteration）计算，这与MATLAB版本的MEX文件方式类似。

## 优势

1. **性能**: Fortran编译后的代码性能接近C/C++，比纯Python快10-100倍
2. **并行化**: 使用OpenMP进行多线程并行计算
3. **兼容性**: 与MATLAB版本使用相同的底层实现方式

## 系统要求

### Windows
1. 安装MinGW-w64（包含gfortran）
   - 下载: https://www.mingw-w64.org/downloads/
   - 或使用MSYS2: `pacman -S mingw-w64-x86_64-gcc-fortran`
2. 确保gfortran在PATH中

### Linux
```bash
sudo apt-get update
sudo apt-get install gfortran
```

### macOS
```bash
brew install gcc
```

## 编译步骤

1. **安装依赖**
   ```bash
   pip install numpy
   ```

2. **编译Fortran模块**
   ```bash
   python fortran/setup_fortran.py
   ```

   或者手动编译：
   ```bash
   python -m numpy.f2py -c fortran/vfi_core.f90 -m vfi_core \
       --f90exec=gfortran --fcompiler=gnu95 \
       --opt=-O3 --f90flags=-fopenmp --link-flags=-fopenmp
   ```

3. **验证安装**
   ```python
   import vfi_core
   print("Fortran模块加载成功！")
   ```

## 使用方法

在`sub/sub_vfi_onestep.py`中，代码会自动检测Fortran模块是否可用：

```python
try:
    from sub.sub_vfi_onestep_fortran import sub_vfi_onestep_fortran, USE_FORTRAN
    if USE_FORTRAN:
        # 使用Fortran版本
        return sub_vfi_onestep_fortran(...)
except ImportError:
    # 回退到纯Python版本
    pass
```

## 性能对比

预期性能提升：
- **纯Python**: ~30-80分钟（稳态计算）
- **Fortran + OpenMP**: ~3-8分钟（稳态计算）
- **加速比**: 约10倍

## 故障排除

### 编译错误：找不到gfortran
- Windows: 确保MinGW-w64的bin目录在PATH中
- Linux/macOS: 使用包管理器安装gfortran

### 运行时错误：模块未找到
- 确保编译后的`.so`（Linux/macOS）或`.pyd`（Windows）文件在Python路径中
- 检查`fortran/`目录是否包含编译后的模块

### OpenMP错误
- 确保编译器支持OpenMP（gfortran 4.2+）
- 检查`--f90flags=-fopenmp`和`--link-flags=-fopenmp`参数

## 代码结构

- `fortran/vfi_core.f90`: Fortran源代码
- `fortran/setup_fortran.py`: 编译脚本
- `sub/sub_vfi_onestep_fortran.py`: Python包装器

## 注意事项

1. Fortran使用1-based索引，但f2py会自动处理转换
2. 数组需要是Fortran顺序（列优先）以获得最佳性能
3. 确保所有数组维度匹配，否则会出现运行时错误








