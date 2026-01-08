"""
读取数据目标（名称和值）从文本文件
"""
import os


def read_data_targets(filename):
    """
    从文本文件读取数据目标（名称和值）
    
    参数:
    filename: 文件路径
    
    返回:
    data_mom: 字典，键为目标名称，值为数据矩的值
    """
    data_mom = {}
    
    # 检查文件是否存在
    if not os.path.exists(filename):
        raise FileNotFoundError(f"文件不存在: {filename}")
    
    # 读取文件
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0]
                try:
                    value = float(parts[1])
                    data_mom[name] = value
                except ValueError:
                    # 如果无法转换为浮点数，跳过这一行
                    pass
    
    # 手动处理（与MATLAB版本一致）
    # 合并企业份额
    if 'firmshare_0_4' in data_mom and 'firmshare_5_9' in data_mom:
        data_mom['firmshare_0_9'] = data_mom['firmshare_0_4'] + data_mom['firmshare_5_9']
    
    # 合并就业份额
    if 'empshare_0_4' in data_mom and 'empshare_5_9' in data_mom:
        data_mom['empshare_0_9'] = data_mom['empshare_0_4'] + data_mom['empshare_5_9']
    
    # 合并小企业就业份额
    if 'empshare_small_imp' in data_mom and 'empshare_small_unimp' in data_mom:
        data_mom['empshare_small'] = data_mom['empshare_small_imp'] + data_mom['empshare_small_unimp']
    
    # 合并小企业收入份额
    if 'revshare_small_imp' in data_mom and 'revshare_small_unimp' in data_mom:
        data_mom['revshare_small'] = data_mom['revshare_small_imp'] + data_mom['revshare_small_unimp']
    
    # 设置固定值
    data_mom['ave_work'] = 0.33
    data_mom['frac_exit_forced'] = 1.0
    data_mom['frac_exit_vol'] = 1.0
    
    # 计算债务资产比率
    if 'debt_asset_all' in data_mom and 'debt_asset_entrants' in data_mom:
        if data_mom['debt_asset_entrants'] != 0:
            data_mom['debt_asset_all_entrants'] = data_mom['debt_asset_all'] / data_mom['debt_asset_entrants']
    
    # 将年度率转换为季度率
    # 转移动态的数据矩基于年度数据：
    # - 退出率、就业创造和破坏率来自BDS
    # - 就业的自相关来自KFS
    
    if 'exitrate' in data_mom:
        data_mom['exitrate'] = 1 - (1 - data_mom['exitrate']) ** (1/4)
    
    if 'exitrate_0_9' in data_mom:
        data_mom['exitrate_0_9'] = 1 - (1 - data_mom['exitrate_0_9']) ** (1/4)
    
    if 'exitrate_10_19' in data_mom:
        data_mom['exitrate_10_19'] = 1 - (1 - data_mom['exitrate_10_19']) ** (1/4)
    
    if 'exitrate_20_99' in data_mom:
        data_mom['exitrate_20_99'] = 1 - (1 - data_mom['exitrate_20_99']) ** (1/4)
    
    if 'exitrate_100_499' in data_mom:
        data_mom['exitrate_100_499'] = 1 - (1 - data_mom['exitrate_100_499']) ** (1/4)
    
    if 'jcr' in data_mom:
        data_mom['jcr'] = data_mom['jcr'] / 4
    
    if 'jdr' in data_mom:
        data_mom['jdr'] = data_mom['jdr'] / 4
    
    if 'autocorr_emp' in data_mom:
        data_mom['autocorr_emp'] = data_mom['autocorr_emp'] ** (1/4)
    
    return data_mom

