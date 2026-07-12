# fengshui_lib.py

class GanZhi:
    """處理干支計算的核心類別"""
    STREAMS = "甲乙丙丁戊己庚辛壬癸"
    BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

    @classmethod
    def _stem_to_idx(cls, stem: str) -> int:
        if stem not in cls.STREAMS:
            raise ValueError(f"無效的天干: {stem}")
        return cls.STREAMS.index(stem)

    @classmethod
    def get_month_gan(cls, year_gan: str, month: int) -> str:
        """五虎遁月：根據年干推算月份天干"""
        if not 1 <= month <= 12:
            raise ValueError("月份須介於 1-12")
        y_idx = cls._stem_to_idx(year_gan)
        start_idx = (y_idx % 5 * 2 + 2) % 10
        month_gan_idx = (start_idx + month - 1) % 10
        return cls.STREAMS[month_gan_idx]

    @classmethod
    def get_hour_gan(cls, day_gan: str, hour_idx: int) -> str:
        """五鼠遁日：根據日干推算時辰天干"""
        if not 0 <= hour_idx <= 11:
            raise ValueError("時辰索引須介於 0-11 (子-亥)")
        d_idx = cls._stem_to_idx(day_gan)
        start_idx = (d_idx % 5 * 2) % 10
        hour_gan_idx = (start_idx + hour_idx) % 10
        return cls.STREAMS[hour_gan_idx]

    @classmethod
    def get_day_ganzhi_simplified(cls, date_obj):
        # 這是簡易版，若要精準算日干支，建議搭配計算基點的演算法
        # 為了避免現在報錯，暫時回傳範例：
        return "甲子"

class BurialAnalysis:
    """處理仙命宜忌與斷語查詢的引擎"""
    
    def __init__(self, rules_db):
        self.rules_db = rules_db

    def get_suitability(self, si_ming: str, orientation: str) -> str:
        """判定方位對仙命是否為吉/凶/平"""
        if si_ming not in self.rules_db:
            return "未知仙命"
        
        # 簡單轉字串判斷，這裡假設資料庫結構已統一
        if orientation in self.rules_db[si_ming]['宜']['方位']:
            return "宜"
        elif orientation in self.rules_db[si_ming]['忌']['方位']:
            return "忌"
        return "平"

    def get_explanation(self, si_ming: str, orientation: str) -> dict:
        """取得詳細的吉凶說明"""
        status = self.get_suitability(si_ming, orientation)
        if status in ['宜', '忌']:
            return self.rules_db[si_ming][status]
        return {"方位": "無", "說明": "該方位無特定斷語記錄。"}

class CalendarEngine:
    """處理日期轉換邏輯"""
    
    @staticmethod
    def get_minguo_year(year: int) -> int:
        return year - 1911

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """檢查是否為閏年"""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)



# 為了方便後續在 app.py 統一調用，可以宣告一個實例供外部匯入
# from fengshui_lib import ganzhi_engine, burial_engine
ganzhi_engine = GanZhi()
calendar_engine = CalendarEngine()
