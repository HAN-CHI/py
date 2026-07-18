import os
import math
from fengshui_db import CALENDAR_RULES,PENGZU_STEMS,PENGZU_BRANCHES,HUANGDAO_GODS,HUANGDAO_START_RULES,HUANGDAO_DAILY_SEQUENCE,MONTH_START_BRANCH_IDX
from zhdate import ZhDate
from skyfield.api import load
from skyfield.data import spice
from skyfield.framelib import ecliptic_frame
from datetime import datetime, timedelta, timezone

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
# 初始化 Skyfield 全域物件 (NASA DE421 星曆)
try:
    ts = load.timescale()
    planets = load('de421.bsp')
    earth = planets['earth']
    sun = planets['sun']
except Exception as e:
    st.error(f"套件載入失敗，請確認已在 requirements.txt 加入 skyfield 與 numpy: {e}")

class AstronomyEngine:
    TERMS_MAP = {
        "立春": 315, "雨水": 330, "驚蟄": 345, "春分": 0, "清明": 15, "穀雨": 30,
        "立夏": 45, "小滿": 60, "芒種": 75, "夏至": 90, "小暑": 105, "大暑": 120,
        "立秋": 135, "處暑": 150, "白露": 165, "秋分": 180, "寒露": 195, "霜降": 210,
        "立冬": 225, "小雪": 240, "大雪": 255, "冬至": 270, "小寒": 285, "大寒": 300
    }

    @staticmethod
    def get_solar_longitude_skyfield(t):
        astrometric = earth.at(t).observe(sun)
        # 改用 ecliptic_frame
        _, lon, _ = astrometric.ecliptic_latlon(epoch=ecliptic_frame)
        return lon.degrees

    @staticmethod
    def get_astro_params(jd, true_lon):
        # 台中西屯座標 (24.17N, 120.63E)
        lat, lon = 24.17, 120.63
        T = (jd - 2451545.0) / 36525.0
        
        # 1. 均時差 (Equation of Time)
        M = math.radians((357.52911 + 35999.05029 * T) % 360)
        L0 = math.radians((280.46646 + 36000.76983 * T) % 360)
        e = 0.016708634
        obliquity = math.radians(23.439291 - 0.0130042 * T)
        y = math.tan(obliquity / 2)**2
        eot = y * math.sin(2*L0) - 2*e*math.sin(M) + 4*e*y*math.sin(M)*math.cos(2*L0) - 0.5*y**2*math.sin(4*L0) - 1.25*e**2*math.sin(2*M)
        eot_minutes = math.degrees(eot) * 4.0
        
        # 2. 太陽高度角
        declination = math.asin(math.sin(obliquity) * math.sin(math.radians(true_lon)))
        gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0)
        lmst = math.radians((gmst + lon) % 360)
        right_ascension = math.atan2(math.cos(obliquity) * math.sin(math.radians(true_lon)), math.cos(math.radians(true_lon)))
        hour_angle = lmst - right_ascension
        
        alt = math.asin(math.sin(math.radians(lat)) * math.sin(declination) + 
                        math.cos(math.radians(lat)) * math.cos(declination) * math.cos(hour_angle))
        
        return round(eot_minutes, 1), round(math.degrees(alt), 1)

    @staticmethod
    def find_term_time_skyfield(target_date, target_term_name):
        target_lon = AstronomyEngine.TERMS_MAP.get(target_term_name, 0)
        t0 = ts.utc(target_date.year, target_date.month, target_date.day - 15)
        t1 = ts.utc(target_date.year, target_date.month, target_date.day + 15)
        
        for _ in range(40):
            mid = ts.tt_jd((t0.tt + t1.tt) / 2)
            if AstronomyEngine.get_solar_longitude_skyfield(mid) < target_lon:
                t0 = mid
            else:
                t1 = mid
        return t0.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def get_month_pillar(year_gz, solar_term):
        term_to_branch = {
            "立春": "寅", "雨水": "寅", "驚蟄": "卯", "春分": "卯", "清明": "辰", "穀雨": "辰",
            "立夏": "巳", "小滿": "巳", "芒種": "午", "夏至": "午", "小暑": "未", "大暑": "未",
            "立秋": "申", "處暑": "申", "白露": "酉", "秋分": "酉", "寒露": "戌", "霜降": "戌",
            "立冬": "亥", "小雪": "亥", "大雪": "子", "冬至": "子", "小寒": "丑", "大寒": "丑"
        }
        month_branch = term_to_branch.get(solar_term, "寅")
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "寅卯辰巳午未申酉戌亥子丑"
        stem_starts = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚", "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
        
        start_stem = stem_starts.get(year_gz[0], "丙")
        month_stem_idx = (stems.index(start_stem) + branches.index(month_branch)) % 10
        return f"{stems[month_stem_idx]}{month_branch}月"

    @staticmethod
    def get_solar_details(local_date, local_hour, year_gz, day_gz):
        t = ts.utc(local_date.year, local_date.month, local_date.day, local_hour)
        lon_deg = AstronomyEngine.get_solar_longitude_skyfield(t)
        eot, alt = AstronomyEngine.get_astro_params(t.tt, lon_deg)
        
        terms_list = sorted(AstronomyEngine.TERMS_MAP.items(), key=lambda x: x[1])
        solar_term, current_idx = "未知", 0
        for i in range(24):
            start, end = terms_list[i][1], terms_list[(i+1)%24][1]
            if (start > end and (lon_deg >= start or lon_deg < end)) or (start <= lon_deg < end):
                solar_term, current_idx = terms_list[i][0], i; break
        
        next_term = terms_list[(current_idx + 1) % 24][0]
        
        return {
            "solar_term": solar_term,
            "solar_term_time": AstronomyEngine.find_term_time_skyfield(local_date, solar_term),
            "term_start": AstronomyEngine.find_term_time_skyfield(local_date, solar_term),
            "term_end": AstronomyEngine.find_term_time_skyfield(local_date, next_term),
            "julian_day": round(t.tt, 5),
            "ecliptic_longitude": round(lon_deg, 2),
            "equation_of_time": f"{eot}m",
            "sun_altitude": alt,
            "utc_datetime": t.utc_iso(),
            "gan_zhi": f"{year_gz} {AstronomyEngine.get_month_pillar(year_gz, solar_term)} {day_gz}"
        }
