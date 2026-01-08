"""
从结构体生成表格，只考虑pnames（如果存在）
"""
import os
import numpy as np


def mystruct2table(pstruct, pnames, description, dispNames, header, tex, tabDir, filename):
    """
    从结构体生成表格
    
    参数:
    pstruct: 包含标量字段的字典
    pnames: 要显示的字段名称列表
    description: 包含更多信息的字符串列表
    dispNames: 显示名称列表
    header: 列标题
    tex: 0/1标志；如果为1，创建tex文件
    tabDir: 保存tex表格的文件夹（如果tex=1）
    filename: tex文件名
    """
    if not isinstance(pnames, list):
        raise TypeError('输入pnames在mystruct2table中必须是列表')
    if not isinstance(description, list):
        raise TypeError('输入description在mystruct2table中必须是列表')
    if not isinstance(dispNames, list):
        raise TypeError('输入dispNames在mystruct2table中必须是列表')
    
    if not isinstance(tabDir, str):
        raise TypeError('输入tabDir在mystruct2table中必须是字符串')
    if not isinstance(filename, str):
        raise TypeError('输入filename在mystruct2table中必须是字符串')
    
    # 如果只有一个输入，使用pstruct的所有字段名
    if not pnames:
        fnames = list(pstruct.keys())
    else:
        fnames = pnames
    
    # 检查pnames和description（如果存在）是否有相同数量的元素
    if description:
        if len(fnames) != len(description):
            raise ValueError("pnames和description必须有相同数量的元素")
    
    # 检查pstruct的所有字段是否都是标量
    for i in range(len(fnames)):
        value = pstruct.get(fnames[i])
        if value is not None:
            if isinstance(value, (list, tuple, dict)):
                raise ValueError("结构体有非标量字段，不允许")
            try:
                if hasattr(value, '__len__') and len(value) > 1:
                    raise ValueError("结构体有非标量字段，不允许")
            except TypeError:
                pass  # 标量值
    
    # 将结构体转换为向量
    pvec = []
    for i in range(len(fnames)):
        value = pstruct.get(fnames[i], 0)
        if isinstance(value, (list, tuple)):
            pvec.append(value[0])
        elif isinstance(value, np.ndarray):
            pvec.append(float(value.flatten()[0]))
        else:
            pvec.append(float(value))
    
    width = max(len(name) for name in fnames) if fnames else 20
    if header:
        width = max(width, len(header[0]))
        print('------------------------------')
        print(f'{header[0]:<{width}}   {header[1]}')
        print('------------------------------')
    
    # 显示表格，参数i的名称在fnames[i]中，数值在pvec[i]中
    for i in range(len(fnames)):
        print(f'{fnames[i]:<{width}}   {pvec[i]:<8.16f}')
    
    if tex == 1:
        # 创建目录
        if not os.path.exists(tabDir):
            os.makedirs(tabDir)
        
        filepath = os.path.join(tabDir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            if not description:
                # 没有描述列的额外列
                f.write(' \\begin{tabular}{lc} \\hline \\hline \n')
                f.write(' Parameter & Description & Value \\\\ \n')
                f.write(' \\hline \n')
                for i in range(len(fnames)):
                    name = dispNames[i] if i < len(dispNames) else fnames[i]
                    f.write(f'{name}  &  {pvec[i]:8.3f} \\\\ \n')
                f.write(' \\hline \\hline \n \\end{tabular} \n')
            else:
                # 有描述列的额外列
                f.write(' \\begin{tabular}{llc} \\hline \\hline \n')
                f.write(' Parameter & Description & Value \\\\ \n')
                f.write(' \\hline \n')
                for i in range(len(fnames)):
                    name = dispNames[i] if i < len(dispNames) else fnames[i]
                    desc = description[i] if i < len(description) else ''
                    f.write(f'{name}  & {desc} & {pvec[i]:8.3f} \\\\ \n')
                f.write(' \\hline \\hline \n \\end{tabular} \n')
        
        print(f'LaTeX table saved to {filepath}')

