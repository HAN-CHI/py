import math
from fengshui_db import CALENDAR_RULES,PENGZU_STEMS,PENGZU_BRANCHES,HUANGDAO_GODS,HUANGDAO_START_RULES,HUANGDAO_DAILY_SEQUENCE,MONTH_START_BRANCH_IDX
from zhdate import ZhDate
from datetime import datetime, timedelta

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
        
        # 新增：轉換為農曆
        lunar = ZhDate.from_datetime(datetime(year, month, day))

        return {
            "年柱": year_gz,
            "月柱": "（需配合節氣）",
            "日柱": day_gz,
            "時柱": hour_gz,
            "農曆": f"農曆 {lunar.lunar_month}月{lunar.lunar_day}日",
            "農曆字串": f"{lunar.chinese()}" # 例如：二〇二六年六月十九
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
    SEQUENCE = ["青龍", "明堂", "天刑", "朱雀", "金匱", "天德", "白虎", "玉堂", "天牢", "玄武", "司命", "勾陳"]
    
    @staticmethod
    def get_hour_god_info(day_branch, hour_idx):
        """
        回傳該時辰神煞的完整資訊
        """
        start_god = HUANGDAO_START_RULES.get(day_branch)
        start_idx = HuangDaoEngine.SEQUENCE.index(start_god)
        target_idx = (start_idx + hour_idx) % 12
        
        god_name = HuangDaoEngine.SEQUENCE[target_idx]
        god_info = HUANGDAO_GODS.get(god_name) # 包含屬性與適用範疇
        
        return god_name, god_info
        # fengshui_lib.py

class DailyHuangDaoEngine:
    BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    @staticmethod
    def get_daily_god(month, day_branch):
        """
        month: 農曆月份 (1-12)
        day_branch: 當日地支 (如 '子')
        """
        # 1. 取得該月份青龍起始的地支索引
        start_branch_idx = MONTH_START_BRANCH_IDX.get(month)
        
        # 2. 取得當日地支的索引
        current_idx = DailyHuangDaoEngine.BRANCHES.index(day_branch)
        
        # 3. 計算位移 (處理負數與循環：(目標 - 起始) % 12)
        # 這是擇日學的核心邏輯：從青龍起始點開始推演
        offset = (current_day_branch_idx - start_branch_idx) % 12
        
        # 4. 根據位移回傳對應的神煞
        god_name = HUANGDAO_DAILY_SEQUENCE[offset]
        
        return god_name


#五不遇時
class TimeEngine:
    # 五鼠遁對照表
    WU_SHU_DUN = {
        "甲": "甲", "己": "甲", "乙": "丙", "庚": "丙", "丙": "戊", 
        "辛": "戊", "丁": "庚", "壬": "庚", "戊": "壬", "癸": "壬"
    }
    STEMS = "甲乙丙丁戊己庚辛壬癸"

    @staticmethod
    def get_hour_gan(day_gan, hour_idx):
        start_gan = TimeEngine.WU_SHU_DUN.get(day_gan)
        start_idx = TimeEngine.STEMS.index(start_gan)
        return TimeEngine.STEMS[(start_idx + hour_idx) % 10]

class TimeSafetyEngine:
    """處理時辰禁忌邏輯"""
    W_U_BUYU = {
        "甲": "庚", "乙": "辛", "丙": "壬", "丁": "癸", "戊": "甲",
        "己": "乙", "庚": "丙", "辛": "丁", "壬": "戊", "癸": "己"
    }

    @staticmethod
    def is_wubuyu(day_gan, hour_gan):
        forbidden_hour_gan = TimeSafetyEngine.W_U_BUYU.get(day_gan)
        return hour_gan == forbidden_hour_gan

    @staticmethod
    def check_hour_safety(day_gan, hour_idx):
        """整合邏輯：計算時干並檢查是否為五不遇時"""
        hour_gan = TimeEngine.get_hour_gan(day_gan, hour_idx)
        is_unsafe = TimeSafetyEngine.is_wubuyu(day_gan, hour_gan)
        return hour_gan, is_unsafe

#天文觀測資料計算
class AstronomyEngine:
    # 節氣定義對照表 (黃經角度)
    TERMS_MAP = {
        "立春": 315, "雨水": 330, "驚蟄": 345, "春分": 0, "清明": 15, "穀雨": 30,
        "立夏": 45, "小滿": 60, "芒種": 75, "夏至": 90, "小暑": 105, "大暑": 120,
        "立秋": 135, "處暑": 150, "白露": 165, "秋分": 180, "寒露": 195, "霜降": 210,
        "立冬": 225, "小雪": 240, "大雪": 255, "冬至": 270, "小寒": 285, "大寒": 300
    }

    @staticmethod
    def get_ecliptic_longitude(jd):
        n = jd - 2451545.0
        L = (280.460 + 0.9856474 * n) % 360
        g = (357.528 + 0.9856003 * n) % 360
        g_rad = math.radians(g)
        return (L + 1.915 * math.sin(g_rad) + 0.020 * math.sin(2 * g_rad)) % 360

    @staticmethod
    def find_term_time(target_date, target_term_name):
        """ 使用二分搜尋法查找節氣交節精確時間 """
        target_lon = AstronomyEngine.TERMS_MAP.get(target_term_name, 0)
        low = datetime.combine(target_date, datetime.min.time()) - timedelta(days=2)
        high = datetime.combine(target_date, datetime.min.time()) + timedelta(days=2)
        
        for _ in range(20): # 20次迭代可達分鐘級精度
            mid = low + (high - low) / 2
            # 轉換為儒略日計算
            y, m, d = mid.year, mid.month, mid.day
            if m <= 2: y -= 1; m += 12
            A = int(y / 100); B = 2 - A + int(A / 4)
            jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5 + (mid.hour + mid.minute/60.0)/24.0
            
            if AstronomyEngine.get_ecliptic_longitude(jd) < target_lon:
                low = mid
            else:
                high = mid
        return mid.strftime("%m-%d %H:%M")

    @staticmethod
    def get_solar_details(local_date, local_hour, year_gz, day_gz, lat=24.16, lon=120.64):
        # 基礎時間運算
        local_dt = datetime.combine(local_date, datetime.min.time()) + timedelta(hours=local_hour)
        utc_dt = local_dt - timedelta(hours=8)
        y, m, d = utc_dt.year, utc_dt.month, utc_dt.day
        jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d - 1524.5 + (utc_dt.hour + utc_dt.minute/60.0)/24.0
        
        # 黃經與節氣
        lon_deg = AstronomyEngine.get_ecliptic_longitude(jd)
        terms = sorted(AstronomyEngine.TERMS_MAP.items(), key=lambda x: x[1])
        solar_term = "未知"
        for i in range(len(terms)):
            start, end = terms[i][1], terms[(i+1)%24][1]
            if start <= lon_deg < (end if end > start else end + 360):
                solar_term = terms[i][0]
                break
        
        # 月柱計算
        term_to_month_zhi = {
            "立春":"寅", "雨水":"寅", "驚蟄":"卯", "春分":"卯", "清明":"辰", "穀雨":"辰",
            "立夏":"巳", "小滿":"巳", "芒種":"午", "夏至":"午", "小暑":"未", "大暑":"未",
            "立秋":"申", "處暑":"申", "白露":"酉", "秋分":"酉", "寒露":"戌", "霜降":"戌",
            "立冬":"亥", "小雪":"亥", "大雪":"子", "冬至":"子", "小寒":"丑", "大寒":"丑"
        }
        month_zhi = term_to_month_zhi.get(solar_term, "巳")
        stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        year_gan_idx = stems.index(year_gz[0])
        first_month_gan_idx = ((year_gan_idx % 5) * 2 + 2) % 10
        month_gan_idx = (first_month_gan_idx + branches.index(month_zhi) - 2) % 10
        month_gz = stems[month_gan_idx] + month_zhi

        # 輸出 JSON 規格
        return {
            "solar_term": solar_term,
            "solar_term_time": AstronomyEngine.find_term_time(local_date, solar_term),
            "julian_day": round(jd, 5),
            "ecliptic_longitude": round(lon_deg, 1),
            "utc_datetime": utc_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "local_timezone": "UTC+8",
            "gan_zhi": f"{year_gz}年 {month_gz}月 {day_gz}日",
            "term_start": "2026-05-21 08:36:28", 
            "term_end": "2026-06-05 23:48:04"
        }
