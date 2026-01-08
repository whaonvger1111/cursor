"""
编译Fortran模块的setup脚本
使用f2py将Fortran代码编译为Python可调用的模块
"""
import numpy as np
import os
import sys
import subprocess

def compile_fortran():
    """编译Fortran模块"""
    print("="*60)
    print("编译Fortran模块")
    print("="*60)
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fortran_file = os.path.join(current_dir, 'vfi_core.f90')
    
    if not os.path.exists(fortran_file):
        print(f"错误：找不到Fortran文件: {fortran_file}")
        return False
    
    print(f"Fortran源文件: {fortran_file}")
    
    # 使用f2py编译
    try:
        # 方法1: 使用f2py命令行工具
        print("\n尝试使用f2py编译（启用OpenMP并行化）...")
        # 尝试使用OpenMP，如果失败则回退到不使用OpenMP
        import platform
        is_windows = platform.system() == 'Windows'
        
        # 首先尝试使用OpenMP
        if is_windows:
            # Windows: 尝试使用-fopenmp，并添加链接器选项
            # 方法1: 使用--link-args传递链接器选项
            cmd_with_openmp = [
                sys.executable, '-m', 'numpy.f2py',
                '--f90flags=-O3 -fopenmp',
                '--opt=-O3',
                '--link-args=-fopenmp',
                '-c', fortran_file,
                '-m', 'vfi_core',
                '--quiet'
            ]
        else:
            # Linux/Mac: 使用-fopenmp
            cmd_with_openmp = [
                sys.executable, '-m', 'numpy.f2py',
                '--f90flags=-O3 -fopenmp',
                '--opt=-O3',
                '-c', fortran_file,
                '-m', 'vfi_core',
                '--quiet'
            ]
        
        print(f"执行命令（OpenMP）: {' '.join(cmd_with_openmp)}")
        # 设置环境变量以支持OpenMP链接
        env = os.environ.copy()
        if is_windows:
            env['LDFLAGS'] = '-fopenmp'
            env['F90FLAGS'] = '-O3 -fopenmp'
        result = subprocess.run(cmd_with_openmp, cwd=current_dir, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print("[成功] Fortran模块编译成功（OpenMP已启用）！")
            print(f"输出文件应在: {current_dir}")
            
            # Windows上需要复制libgomp.dll到输出目录
            if is_windows:
                import shutil
                import glob
                # 查找libgomp.dll
                possible_paths = [
                    r'C:\msys64\mingw64\bin\libgomp*.dll',
                    r'C:\mingw64\bin\libgomp*.dll',
                ]
                dll_found = False
                for pattern in possible_paths:
                    dll_files = glob.glob(pattern)
                    if dll_files:
                        dll_file = dll_files[0]
                        dest_file = os.path.join(current_dir, os.path.basename(dll_file))
                        try:
                            shutil.copy2(dll_file, dest_file)
                            print(f"[信息] 已复制OpenMP运行时库: {os.path.basename(dll_file)}")
                            dll_found = True
                            break
                        except Exception as e:
                            print(f"[警告] 无法复制OpenMP运行时库: {e}")
                
                if not dll_found:
                    print("[警告] 未找到libgomp.dll，可能需要手动复制到fortran目录")
                    print("       或者将MinGW bin目录添加到PATH环境变量")
            
            return True
        else:
            print("OpenMP编译失败，尝试不使用OpenMP...")
            print(f"错误信息: {result.stderr[-500:] if len(result.stderr) > 500 else result.stderr}")
            
            # 回退到不使用OpenMP
            cmd_no_openmp = [
                sys.executable, '-m', 'numpy.f2py',
                '--f90flags=-O3',
                '--opt=-O3',
                '-c', fortran_file,
                '-m', 'vfi_core',
                '--quiet'
            ]
            print(f"执行命令（无OpenMP）: {' '.join(cmd_no_openmp)}")
            result2 = subprocess.run(cmd_no_openmp, cwd=current_dir, capture_output=True, text=True)
            
            if result2.returncode == 0:
                print("[成功] Fortran模块编译成功（未启用OpenMP，代码仍包含OpenMP指令但不会并行）！")
                print(f"输出文件应在: {current_dir}")
                print("注意：OpenMP指令已保留在代码中，但编译器未链接OpenMP库")
                return True
            else:
                print("f2py编译失败！")
                print(f"错误信息: {result2.stderr[-1000:] if len(result2.stderr) > 1000 else result2.stderr}")
                print(f"标准输出: {result2.stdout[-500:] if len(result2.stdout) > 500 else result2.stdout}")
                return False
            
    except Exception as e:
        print(f"编译失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = compile_fortran()
    if success:
        print("\n" + "="*60)
        print("编译完成！")
        print("="*60)
        print("\n可以导入模块测试:")
        print("  import vfi_core")
        print("  print(vfi_core.__file__)")
    else:
        print("\n" + "="*60)
        print("编译失败！")
        print("="*60)
        print("\n请检查:")
        print("1. gfortran是否在PATH中")
        print("2. numpy.f2py是否可用")
        print("3. Fortran代码语法是否正确")
        sys.exit(1)
