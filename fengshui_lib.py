def get_month_gan(year_gan, month_index):
    """
    五虎遁月：根據年干推算月份天干
    year_gan: 年份天干 (如 '甲', '乙'...)
    month_index: 農曆月份 (1-12)
    """
    # 年干對應寅月的天干
    start_gan = {
        '甲': '丙', '己': '丙',
        '乙': '戊', '庚': '戊',
        '丙': '庚', '辛': '庚',
        '丁': '壬', '壬': '壬',
        '戊': '甲', '癸': '甲'
    }
    
    gans = "甲乙丙丁戊己庚辛壬癸"
    start_char = start_gan[year_gan]
    start_idx = gans.index(start_char)
    
    # 計算該月份天干 (月干 = (寅月干索引 + 月份 - 1) % 10)
    month_gan_idx = (start_idx + month_index - 1) % 10
    return gans[month_gan_idx]
  
def get_hour_gan(day_gan, hour_index):
    """
    五鼠遁日：根據日干推算時辰天干
    day_gan: 日期天干 (如 '甲', '乙'...)
    hour_index: 子時為0, 丑時為1, ... 亥時為11
    """
    # 日干對應子時的天干
    start_gan = {
        '甲': '甲', '己': '甲',
        '乙': '丙', '庚': '丙',
        '丙': '戊', '辛': '戊',
        '丁': '庚', '壬': '庚',
        '戊': '壬', '癸': '壬'
    }
    
    gans = "甲乙丙丁戊己庚辛壬癸"
    start_char = start_gan[day_gan]
    start_idx = gans.index(start_char)
    
    # 計算該時辰天干
    hour_gan_idx = (start_idx + hour_index) % 10
    return gans[hour_gan_idx]
