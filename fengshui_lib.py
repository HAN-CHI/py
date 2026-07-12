from fengshui_db import CALENDAR_RULES,PENGZU_STEMS,PENGZU_BRANCHES,HUANGDAO_GODS,HUANGDAO_START_RULES


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
