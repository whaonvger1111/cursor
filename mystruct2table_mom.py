"""
从两个结构体生成表格，只考虑pnames
"""
import os
import numpy as np


def mystruct2table_mom(pstruct1, pstruct2, pnames, calibWeights, targetNames_long, tex, tabDir, filename):
    """
    从两个结构体生成表格
    
    参数:
    pstruct1: 包含标量字段的字典（data_mom）
    pstruct2: 包含标量字段的字典（model_mom）
    pnames: 字符串列表
    calibWeights: 校准权重字典
    targetNames_long: 字符串列表
    tex: 0/1标志；如果为1，创建tex文件
    tabDir: 保存latex文件的文件夹
    filename: latex文件名，必须有.tex后缀
    """
    if not isinstance(pstruct1, dict):
        raise TypeError('输入pstruct1在mystruct2table_mom中必须是字典')
    if not isinstance(pstruct2, dict):
        raise TypeError('输入pstruct2在mystruct2table_mom中必须是字典')
    if not isinstance(pnames, list):
        raise TypeError('输入pnames在mystruct2table_mom中必须是列表')
    if not isinstance(targetNames_long, list):
        raise TypeError('输入targetNames_long在mystruct2table_mom中必须是列表')
    
    if not isinstance(tabDir, str):
        raise TypeError('输入tabDir在mystruct2table_mom中必须是字符串')
    if not isinstance(filename, str):
        raise TypeError('输入filename在mystruct2table_mom中必须是字符串')
    
    fnames = pnames
    
    # 检查pstruct的所有字段是否都是标量
    for i in range(len(fnames)):
        value1 = pstruct1.get(fnames[i])
        if value1 is not None:
            if isinstance(value1, (list, tuple, dict)):
                raise ValueError("结构体有非标量字段，不允许")
            try:
                if hasattr(value1, '__len__') and len(value1) > 1:
                    raise ValueError("结构体有非标量字段，不允许")
            except TypeError:
                pass
    
    for i in range(len(fnames)):
        value2 = pstruct2.get(fnames[i])
        if value2 is not None:
            if isinstance(value2, (list, tuple, dict)):
                raise ValueError("结构体有非标量字段，不允许")
            try:
                if hasattr(value2, '__len__') and len(value2) > 1:
                    raise ValueError("结构体有非标量字段，不允许")
            except TypeError:
                pass
    
    # 将结构体转换为向量
    pvec1 = []  # 数据矩
    for i in range(len(fnames)):
        value = pstruct1.get(fnames[i], 0)
        if isinstance(value, (list, tuple)):
            pvec1.append(float(value[0]))
        elif isinstance(value, np.ndarray):
            pvec1.append(float(value.flatten()[0]))
        else:
            pvec1.append(float(value))
    
    pvec2 = []  # 模型矩
    for i in range(len(fnames)):
        value = pstruct2.get(fnames[i], 0)
        if isinstance(value, (list, tuple)):
            pvec2.append(float(value[0]))
        elif isinstance(value, np.ndarray):
            pvec2.append(float(value.flatten()[0]))
        else:
            pvec2.append(float(value))
    
    calibWeights_vec = []  # 校准权重
    for i in range(len(fnames)):
        value = calibWeights.get(fnames[i], 0)
        if isinstance(value, (list, tuple)):
            calibWeights_vec.append(float(value[0]))
        elif isinstance(value, np.ndarray):
            calibWeights_vec.append(float(value.flatten()[0]))
        else:
            calibWeights_vec.append(float(value))
    
    dev = []  # 绝对偏差
    for i in range(len(fnames)):
        if pvec1[i] != 0:
            dev.append(calibWeights_vec[i] * ((pvec1[i] - pvec2[i]) / pvec1[i]) ** 2)
        else:
            dev.append(0)
    
    width = max(len(name) for name in fnames) if fnames else 20
    width = max([width, len('Moment'), len('Data')])
    
    print('--------------------------------------------------------------')
    print(f' {"Moment":<{width}}  {"Data":<8}    {"Model":<8}    {"Sqr Dist":<8}')
    print('--------------------------------------------------------------')
    print(' ')
    for i in range(len(fnames)):
        name = fnames[i]
        print(f'{name:<{width}}   {pvec1[i]:<8.4f} {pvec2[i]:<8.4f} {dev[i]:<8.4f}')
    
    if tex == 1:
        # 创建目录
        if not os.path.exists(tabDir):
            os.makedirs(tabDir)
        
        filepath = os.path.join(tabDir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(' \\begin{tabular}{lcc} \\hline \\hline \n')
            f.write(' Moment & Data & Model \\\\ \n')
            f.write('\\hline \n')
            for i in range(len(fnames)):
                name = targetNames_long[i] if i < len(targetNames_long) else fnames[i]
                f.write(f'{name}  &  {pvec1[i]:8.4f} & {pvec2[i]:8.4f} \\\\ \n')
            f.write(' \\hline \\hline \n \\end{tabular} \n')
        
        print(f'LaTeX table saved to {filepath}')

