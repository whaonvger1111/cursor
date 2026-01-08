"""
使用setup.py方式编译Fortran模块（支持OpenMP）
"""
import numpy
from numpy.distutils.core import setup, Extension
import os

# 设置OpenMP链接标志
os.environ['LDFLAGS'] = '-fopenmp'

ext_modules = [
    Extension(
        name='vfi_core',
        sources=['vfi_core.f90'],
        extra_f90_compile_args=['-O3', '-fopenmp'],
        extra_link_args=['-fopenmp'],
        language='f90'
    )
]

setup(
    name='vfi_core',
    ext_modules=ext_modules,
    include_dirs=[numpy.get_include()],
)

