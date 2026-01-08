"""
比较百分比变化的图
"""
import numpy as np
import os

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("警告：matplotlib未安装，绘图功能将不可用")


def plot_ppchange_compare(data1, data2, data3, labels, SaveDir, FormatFig, do_save, FS):
    """
    比较百分比变化的图
    
    参数:
    data1, data2, data3: 要比较的数据
    labels: 标签列表
    SaveDir: 保存目录
    FormatFig: 图形格式
    do_save: 是否保存标志
    FS: 字体大小
    """
    if not HAS_MATPLOTLIB:
        print("错误：matplotlib未安装，无法生成图形")
        return
    
    # 创建保存目录
    if do_save and not os.path.exists(SaveDir):
        os.makedirs(SaveDir)
    
    print("比较百分比变化...")
    print("注意：完整的绘图功能需要根据具体需求实现")

