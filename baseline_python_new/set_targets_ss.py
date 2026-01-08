"""
设置稳态的数据矩和校准权重
"""
import os
from read_data_targets import read_data_targets


def set_targets_ss():
    """
    设置稳态的数据矩和校准权重
    
    返回:
    targetNames: 目标名称列表
    targetNames_long: 目标名称长描述列表
    calibWeights: 校准权重字典
    data_mom: 数据矩字典
    """
    # 加载稳态的数据矩
    # 来源: 'data_moments\data_moments.txt'
    targetNames = [
        'avefirmsize',
        'avefirmsize_age0',
        'empshare_small',
        'exitrate',
        'fixedcost_to_rev',
        'autocorr_emp',
        'ave_work',
        'exitrate_0_9',
        'scor_invrate',
        'hasNetDebt',
        'freq_lumpinv',
        'frac_exit_forced',
        'frac_exit_vol',
        'firmshare_0_9',
        'firmshare_10_19',
        'firmshare_20_99',
        'firmshare_100_499',
        'empshare_0_9',
        'empshare_10_19',
        'empshare_20_99',
        'empshare_100_499'
    ]
    
    targetNames_long = [
        'Average employment in small firms',
        'Average employment, age 0',
        'Small firm share of employment',
        'Small firm exit rate',
        'Fixed expense to revenue ratio',
        'Autocorr. employment',
        'Time spent in market work',
        'Exit rate, emp. size 0 to 9',
        'serial corr. investment rate',
        'Share of firms with debt',
        'Freq. positive lumpy investment',
        'Share forced exit',
        'Share voluntary exit',
        'firmshare0to9',
        'firmshare10to19',
        'firmshare20to99',
        'firmshare100to499',
        'empshare0to9',
        'empshare10to19',
        'empshare20to99',
        'empshare100to499'
    ]
    
    if len(targetNames) != len(targetNames_long):
        raise ValueError("字符数组<targetNames>和<targetNames_long>必须有相同数量的元素")
    
    # 设置校准权重
    calibWeights = {
        'avefirmsize': 300,
        'empshare_small': 5,
        'exitrate': 150,
        'frac_exit_forced': 0,
        'frac_exit_vol': 0,
        'avefirmsize_age0': 300,
        'fixedcost_to_rev': 5,
        'autocorr_emp': 1000,
        'ave_work': 100,
        'hasNetDebt': 0,
        'firmshare_0_9': 1,
        'firmshare_10_19': 1,
        'firmshare_20_99': 1,
        'firmshare_100_499': 1,
        'empshare_0_9': 2,
        'empshare_10_19': 2,
        'empshare_20_99': 1,
        'empshare_100_499': 1,
        'exitrate_0_9': 30,
        'scor_invrate': 50,
        'freq_lumpinv': 5
    }
    
    filename = os.path.join('..', 'data_moments', 'data_moments.txt')
    data_mom = read_data_targets(filename)  # data_mom是字典
    
    return targetNames, targetNames_long, calibWeights, data_mom

