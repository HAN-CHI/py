from fengshui_db import CALENDAR_RULES,PENGZU_STEMS,PENGZU_BRANCHES,HUANGDAO_GODS,HUANGDAO_START_RULES
from datetime import datetime

class PreciseCalendar:
    STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    @staticmethod
    def get_four_pillars(year, month, day, hour):
        """
        利用數學公式精準計算干支 (無需 sxtwl)
        """
        # 1. 計算年柱 (以 1984 甲子年為基準)
        year_idx = (year - 1984) % 60
        year_gz = PreciseCalendar.STEMS[year_idx % 10] + PreciseCalendar.BRANCHES[year_idx % 12]

        # 2. 計算日柱 (以 1900/1/1 為基準，那天是甲戌日，索引 10)
        base_date = datetime(1900, 1, 1)
        target_date = datetime(year, month, day)
        delta_days = (target_date - base_date).days
        day_idx = (10 + delta_days) % 60
        day_gz = PreciseCalendar.STEMS[day_idx % 10] + PreciseCalendar.BRANCHES[day_idx % 12]

        # 3. 計算時柱 (五鼠遁)
        # 找出該日日干索引
        day_gan_idx = day_idx % 10
        # 五鼠遁對應表：甲己子時為甲子...
        # 簡易公式：(日干索引 % 5) * 2
        start_hour_gan_idx = (day_gan_idx % 5) * 2
        hour_idx = (start_hour_gan_idx + (hour // 2)) % 10
        hour_gz = PreciseCalendar.STEMS[hour_idx] + PreciseCalendar.BRANCHES[(hour // 2) % 12]

        return {
            "年柱": year_gz,
            "日柱": day_gz,
            "時柱": hour_gz,
            "月柱": "註：需配合節氣計算", # 若需要精準月柱，建議改用查詢表
            "農曆": "請參考 zhdate 顯示"
        }

class CalendarEngine:
    @staticmethod
    def get_jianchu(lunar_date_idx):
        """根據農曆日期索引計算建除十二神"""
        # 需配合節氣，這裡僅為結構範例
        return CALENDAR_RULES["JianChu"]["sequence"][lunar_date_idx % 12]

    @staticmethod
    def get_constellation(date_delta):
        """根據與基點日期的天數差，推算二十八宿"""
        return CALENDAR_RULES["Constellations"]["sequence"][date_delta % 28]

def get_today_pengzu(gan, zhi):
    """
    根據當日干支，返回對應的百忌說明。
    gan: 天干字串 (如 '甲')
    zhi: 地支字串 (如 '子')
    """
    return {
        "天干百忌": PENGZU_STEMS.get(gan, "今日天干無特殊禁忌。"),
        "地支百忌": PENGZU_BRANCHES.get(zhi, "今日地支無特殊禁忌。")
    }


class HuangDaoEngine:
    @staticmethod
    def get_hour_god(day_branch, hour_idx):
        """
        day_branch: 當日地支 (如 '子')
        hour_idx: 時辰索引 (0:子, 1:丑, ..., 11:亥)
        """
        # 1. 找出子時起算的吉神
        start_god = HUANGDAO_START_RULES.get(day_branch)
        
        # 2. 獲取完整順序 (圖片中的 12 神順序)
        sequence = ["青龍", "明堂", "天刑", "朱雀", "金匱", "天德", "白虎", "玉堂", "天牢", "玄武", "司命", "勾陳"]
        
        # 3. 計算該時辰的神煞
        start_idx = sequence.index(start_god)
        target_idx = (start_idx + hour_idx) % 12
        god_name = sequence[target_idx]
        
        return god_name, HUANGDAO_GODS[god_name]


#五不遇時
class TimeSafetyEngine:
    """處理時辰禁忌邏輯"""
    
    # 五不遇時對照表 (日干: 禁忌時干)
    # 規律：陽日干剋陽時干，陰日干剋陰時干，相隔七位
    W_U_BUYU = {
        "甲": "庚", "乙": "辛", "丙": "壬", "丁": "癸", "戊": "甲",
        "己": "乙", "庚": "丙", "辛": "丁", "壬": "戊", "癸": "己"
    }

    @staticmethod
    def is_wubuyu(day_gan, hour_gan):
        """
        判斷是否為五不遇時
        day_gan: 當日天干
        hour_gan: 當日時干
        """
        forbidden_hour_gan = TimeSafetyEngine.W_U_BUYU.get(day_gan)
        return hour_gan == forbidden_hour_gan
