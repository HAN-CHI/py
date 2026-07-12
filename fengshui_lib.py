from fengshui_db.py import PENGZU_STEMS, PENGZU_BRANCHES


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

class PengZuEngine:
    @staticmethod
    def get_taboo(gan, zhi):
        """輸入日干與日支，返回彭祖百忌說明"""
        stem_taboo = PENGZU_STEMS.get(gan, "")
        branch_taboo = PENGZU_BRANCHES.get(zhi, "")
        return [stem_taboo, branch_taboo]
