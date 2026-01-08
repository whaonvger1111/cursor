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
        print("\n尝试使用f2py编译...")
        # 尝试使用OpenMP，如果失败则回退到不使用OpenMP
        cmd = [
            sys.executable, '-m', 'numpy.f2py',
            '--f90flags=-O3',
            '--opt=-O3',
            '-c', fortran_file,
            '-m', 'vfi_core',
            '--quiet'
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=current_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[成功] Fortran模块编译成功！")
            print(f"输出文件应在: {current_dir}")
            return True
        else:
            print("f2py编译失败！")
            print(f"错误信息: {result.stderr}")
            print(f"标准输出: {result.stdout}")
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
