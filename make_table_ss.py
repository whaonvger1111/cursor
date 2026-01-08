"""
在屏幕上写入稳态结果，如果do_tex=1则写入latex文件
"""
import os


def make_table_ss(prices, agg, b_grid, do_tex, tabDir, filename):
    """
    生成稳态结果表格
    
    参数:
    prices, agg, b_grid: 要写入的对象
    do_tex: 写入latex文件的标志0/1
    tabDir: 保存latex文件的文件夹
    filename: latex文件名，必须有.tex后缀
    """
    if not isinstance(tabDir, str):
        raise TypeError('输入tabDir在make_table_ss中必须是字符串')
    if not isinstance(filename, str):
        raise TypeError('输入filename在make_table_ss中必须是字符串')
    
    if do_tex not in [0, 1]:
        raise ValueError('do_tex超出范围：必须是0或1')
    
    nk = b_grid.shape[0]
    
    print("  ")
    print("--------------------------------------------")
    print("STEADY-STATE RESULTS")
    print("--------------------------------------------")
    
    print(f"Firms Discount factor q:   {prices['q']:10.16f}")
    print(f"Wage rate:                 {prices['wage']:10.16f}")
    print(f"Capital-labor ratio corp:  {prices['KL_ratio']:10.16f}")
    
    print(f"Measure of active firms:   {agg['Mactive']:10.16f}")
    print(f"Measure of entrants:       {agg['Mentr']:10.16f}")
    print(f"Aggregate consumption:     {agg['C_agg']:10.16f}")
    print(f"Capital (corporate):       {agg['K_corp']:10.16f}")
    print(f"Employment (corporate):    {agg['L_corp']:10.16f}")
    print(f"Employment (small firms):  {agg['L_small']:10.16f}")
    print(f"Aggregate Capital:         {agg['K_agg']:10.16f}")
    print(f"Employment (total):        {agg['L_agg']:10.16f}")
    print(f"Output (corporate):        {agg['Y_corp']:10.16f}")
    print(f"Output (small firms):      {agg['output_small']:10.16f}")
    print(f"Total output:              {agg['Y_agg']:10.16f}")
    print(f"liq:                       {agg['liq']:10.16f}")
    print(f"entry:                     {agg['entry']:10.16f}")
    print(f"Aggregate Investment:      {agg['InvK']:10.16f}")
    print(f"btilde(1):                 {b_grid[0, 0]:10.16f}")  # b_tilde维度为(nk,1)
    print(f"btilde(nk):                {b_grid[nk - 1, 0]:10.16f}")  # b_tilde维度为(nk,1)
    
    print("  ")
    
    # 如果希望，将相同结果写入latex文件
    if do_tex == 1:
        # 创建目录
        if not os.path.exists(tabDir):
            os.makedirs(tabDir)
        
        filepath = os.path.join(tabDir, filename)
        with open(filepath, 'w', encoding='utf-8') as FID:
            FID.write(' \\begin{tabular}{lc} \\hline \\hline \n')
            FID.write(' \\hline \n')
            
            FID.write(f"Measure of active firms:   &  {agg['Mactive']:8.4f}  \\\\ \n")
            FID.write(f"Measure of entrants:       &  {agg['Mentr']:8.4f}  \\\\ \n")
            FID.write(f"Aggregate consumption:     &  {agg['C_agg']:8.4f}  \\\\ \n")
            FID.write(f"Capital (corporate):       &  {agg['K_corp']:8.4f}  \\\\ \n")
            FID.write(f"Employment (corporate):    &  {agg['L_corp']:8.4f}  \\\\ \n")
            FID.write(f"Aggregate Capital:         &  {agg['K_agg']:8.4f}  \\\\ \n")
            FID.write(f"Employment (total):        &  {agg['L_agg']:8.4f}  \\\\ \n")
            FID.write(f"Output (corporate):        &  {agg['Y_corp']:8.4f}  \\\\ \n")
            FID.write(f"Output (small firms):      &  {agg['output_small']:8.4f}  \\\\ \n")
            FID.write(f"Total output:              &  {agg['Y_agg']:8.4f}  \\\\ \n")
            FID.write(f"liq:                       &  {agg['liq']:8.4f}  \\\\ \n")
            FID.write(f"entry:                     &  {agg['entry']:8.4f}  \\\\ \n")
            FID.write(f"Aggregate Investment:      &  {agg['InvK']:8.4f}  \\\\ \n")
            FID.write(f"btilde(1):                 &  {b_grid[0, 0]:8.4f}  \\\\ \n")  # b_tilde维度为(nk,1)
            FID.write(f"btilde(nk):                &  {b_grid[nk - 1, 0]:8.4f}  \\\\ \n")  # b_tilde维度为(nk,1)
            
            FID.write(' \\hline \\hline \n \\end{tabular} \n')
        
        print(f'LaTeX table saved to {filepath}')

