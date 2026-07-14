import streamlit as st
import pandas as pd
import io
import re
import fengshui_lib 
import importlib
from datetime import datetime, date, timedelta
from zhdate import ZhDate
from config_data import BURIAL_RULES_60
from fengshui_lib import PreciseCalendar,TimeSafetyEngine,TimeEngine,HuangDaoEngine,DailyHuangDaoEngine
from fengshui_db import CALENDAR_RULES,PENGZU_STEMS,PENGZU_BRANCHES,HUANGDAO_GODS,HUANGDAO_START_RULES


# 設定網頁標題與圖示
st.set_page_config(
    page_title="萬年曆通用轉換系統", 
    page_icon="📅", 
    layout="wide"
)

# 核心同步機制：初始化全域「最新日期」記憶庫，預設為今天
if 'latest_date' not in st.session_state:
    st.session_state['latest_date'] = date.today()

st.title("🏮 跨世紀萬年曆自動轉換系統 (西元/民國/祭祀/塔位通用版)")
st.markdown(
    "本系統支援西元曆、中華民國曆自動識別轉換，"
    "內建傳統民俗頭七、百日、對年之精準祭祀時間計算，並新增生肖專屬塔位適宜方位查詢。"
)

# ==========================================
# 🔮 智慧演算法：精準計算天干地支與生肖
# ==========================================
def get_ganzhi_zodiac_details(lunar_year):
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    zodiacs = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]
    
    stem_idx = (lunar_year - 4) % 10
    branch_idx = (lunar_year - 4) % 12
    
    gz = f"{stems[stem_idx]}{branches[branch_idx]}"
    zd = zodiacs[branch_idx]
    return gz, zd

def get_ganzhi_zodiac(lunar_year):
    gz, zd = get_ganzhi_zodiac_details(lunar_year)
    return f"{gz}年 ({zd})"

# ==========================================
# 🧭 風水地理：生肖對應塔位適宜方位資料庫
# ==========================================
def get_tower_orientation(zodiac):
    # 依據傳統民俗三合、八宅派生肖坐向五行推補
    data = {
        "鼠": {"吉方": "坐正北朝正南、坐正東朝正西", "次吉": "坐正西朝正東", "煞方": "忌坐正南朝正北（相沖）"},
        "牛": {"吉方": "坐北朝南、坐西朝東", "次吉": "坐東南朝西北", "煞方": "忌坐西南朝東北（相沖）"},
        "虎": {"吉方": "坐東朝西、坐南朝北", "次吉": "坐西北朝東南", "煞方": "忌坐正西朝正東（相沖）"},
        "兔": {"吉方": "坐正東朝正西、坐正北朝正南", "次吉": "坐正南朝正北", "煞方": "忌坐正西朝正東（相沖）"},
        "龍": {"吉方": "坐東朝西、坐北朝南", "次吉": "坐西朝東", "煞方": "忌坐西北朝東南（相沖）"},
        "蛇": {"吉方": "坐南朝北、坐西朝東", "次吉": "坐東北朝西南", "煞方": "忌坐西北朝東南（相沖）"},
        "馬": {"吉方": "坐正南朝正北、坐正西朝正東", "次吉": "坐正東朝正西", "煞方": "忌坐正北朝正南（相沖）"},
        "羊": {"吉方": "坐南朝北、坐東朝西", "次吉": "坐西北朝東南", "煞方": "忌坐東北朝西南（相沖）"},
        "猴": {"吉方": "坐西朝東、坐北朝南", "次吉": "坐東南朝西北", "煞方": "忌坐正東朝正西（相沖）"},
        "雞": {"吉方": "坐正西朝正東、坐正南朝正北", "次吉": "坐東南朝西北", "煞方": "忌坐正東朝正西（相沖）"},
        "狗": {"吉方": "坐西朝東、坐南朝北", "次吉": "坐東北朝西南", "煞方": "忌坐東南朝西北（相沖）"},
        "豬": {"吉方": "坐北朝南、坐東朝西", "次吉": "坐西南朝東北", "煞方": "忌坐正北朝正南（相沖）"}
    }
    return data.get(zodiac, {"吉方": "通用方位", "次吉": "通用方位", "煞方": "無特殊禁忌"})

# ==========================================
# 🪦 風水地理：60仙命與二十四山吉凶 (土葬)
# ==========================================
def display_burial_info(si_ming):
    rules = BURIAL_RULES_60.get(si_ming)

# ==========================================
# 🧠 核心：西元/民國智慧識別過濾器
# ==========================================
def clean_and_parse_date(date_val):
    if pd.isna(date_val):
        return None
    
    if isinstance(date_val, (datetime, date, pd.Timestamp)):
        y, m, d = date_val.year, date_val.month, date_val.day
        if y < 1900:
            y += 1911
        try:
            return datetime(y, m, d)
        except:
            return None
    
    if isinstance(date_val, (int, float)):
        date_val = str(int(date_val))
        
    if isinstance(date_val, str):
        text = date_val.strip()
        text = text.replace("民國", "").replace("西元", "").replace("Minguo", "")
        text = text.replace("年", "-").replace("月", "-").replace("日", "")
        
        nums = re.findall(r'\d+', text)
        
        if len(nums) == 3:
            y, m, d = int(nums[0]), int(nums[1]), int(nums[2])
            if y < 1900:
                y += 1911
            try:
                return datetime(y, m, d)
            except:
                return None
                
        elif len(nums) == 1 and len(nums[0]) in [6, 7, 8]:
            s = nums[0]
            try:
                if len(s) == 7:    
                    return datetime(int(s[:3]) + 1911, int(s[3:5]), int(s[5:]) or 1)
                elif len(s) == 6:  
                    return datetime(int(s[:2]) + 1911, int(s[2:4]), int(s[4:]) or 1)
                elif len(s) == 8:  
                    return datetime(int(s[:4]), int(s[4:6]), int(s[6:]) or 1)
            except:
                return None
                
    return None
    

# ==========================================
# 建立網頁分頁 (新增分頁)
# ==========================================
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📌 單日萬能查詢",
    "🕯️ 頭七/百日/對年計算機",
    "🦁 生肖與塔位吉方查詢",
    "🪦 土葬二十四山查詢",
    "📅 萬年曆"
])

# ==========================================
# 📌 分頁一：單日萬能查詢
# ==========================================
with tab1:
    st.header("📌 單日萬能查詢 (國曆/農曆互轉)")
    
    # 選擇模式
    mode = st.radio("請選擇轉換方式：", ["國曆 ➔ 農曆", "農曆 ➔ 國曆"], horizontal=True)
    st.markdown("---")
    
    target_date = None
    is_triggered = False

    if mode == "國曆 ➔ 農曆":
        # (保持原樣...)
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            st.subheader("📍 方法 A (日曆選單)")
            date_picker = st.date_input("選擇日期：", st.session_state['latest_date'], min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), key="tab1_dp")
            if st.button("🚀 執行方法 A 查詢", use_container_width=True, key="tab1_btn_a"):
                target_date = clean_and_parse_date(date_picker)
                is_triggered = True
        with col_input2:
            st.subheader("📍 方法 B (文字輸入)")
            ld = st.session_state['latest_date']
            current_minguo_str = f"{ld.year - 1911}/{ld.strftime('%m/%d')}"
            date_text = st.text_input("直接輸入日期：", value=current_minguo_str, help="範例: 115/7/10 或 2026-07-10", key="tab1_ti")
            if st.button("🚀 執行方法 B 查詢", use_container_width=True, key="tab1_btn_b"):
                target_date = clean_and_parse_date(date_text)
                is_triggered = True
            
    else: # 農曆 ➔ 國曆
        st.subheader("📍 方法 C (農曆輸入)")
        
        # 預先計算當前的民國年份
        current_year = date.today().year
        current_minguo_year = current_year - 1911
        
        cal_type = st.radio("農曆對應的年份格式：", ["西元曆", "中華民國曆"], horizontal=True)
        
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            # 根據選擇動態改變預設值
            default_val = current_year if cal_type == "西元曆" else current_minguo_year
            year_label = "農曆年份 (西元)" if cal_type == "西元曆" else "農曆年份 (民國)"
            
            # 使用我們算出的 default_val
            l_year = st.number_input(year_label, 1, 2100, default_val)
            
        with c2:
            l_month = st.number_input("月份", 1, 12, 1)
        with c3:
            l_day = st.number_input("日期", 1, 30, 1)
        with c4:
            is_leap = st.checkbox("是否閏月")
            
        if st.button("🚀 執行農曆轉國曆查詢", use_container_width=True, key="tab1_btn_c"):
            try:
                # 轉換年份邏輯
                actual_year = l_year + 1911 if cal_type == "中華民國曆" else l_year
                target_date = ZhDate(actual_year, l_month, l_day, is_leap).to_datetime()
                is_triggered = True
            except Exception as e:
                st.error(f"❌ 日期輸入錯誤，請確認該農曆日期是否存在。")

    # === 統一顯示結果區塊 ===
    if is_triggered and target_date:
        st.session_state['latest_date'] = target_date.date()
        try:
            lunar = ZhDate.from_datetime(target_date)
            minguo_year = target_date.year - 1911
            leap_prefix = "閏" if lunar.leap_month else ""
            lunar_display = f"農曆 {leap_prefix}{lunar.lunar_month}月{lunar.lunar_day}日"
            ganzhi_display = get_ganzhi_zodiac(lunar.lunar_year)
            
            st.markdown("---")
            st.subheader("🔮 查詢對照結果：")
            cols = st.columns(4)
            cols[0].metric("解析後西元國曆", target_date.strftime('%Y-%m-%d'))
            cols[1].metric("對應中華民國曆", f"民國 {minguo_year} 年")
            cols[2].metric("計算後農曆", lunar_display)
            cols[3].metric("歲次干支 (生肖)", ganzhi_display)
            st.success(f"💡 完整農曆中文表示：{lunar.chinese()}")
        except Exception as e:
            st.error(f"❌ 轉換錯誤: {e}")

# ==========================================
# 🕯️ 分頁三：頭七/百日/對年計算機
# ==========================================
with tab2:
    st.header("🕯️ 傳統祭祀時間計算機")
    st.markdown("傳統習俗中，**往生當天即算作「第 1 天」**。本計算機依此基準精確推算。")
    
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        death_date_input = st.date_input("選擇日期：", st.session_state['latest_date'], min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), key="tab3_dp")
    
    # 🧠 核心演算法：智慧型「全域跨閏月動態掃描引擎」
    has_cross_leap = False
    detected_leap_name = ""
    p_dt = datetime(death_date_input.year, death_date_input.month, death_date_input.day)
    
    try:
        lunar_now = ZhDate.from_datetime(p_dt)
    except:
        lunar_now = None
        
    if lunar_now:
        for day_offset in range(1, 350):
            scan_dt = p_dt + timedelta(days=day_offset)
            try:
                scan_lunar = ZhDate.from_datetime(scan_dt)
                if scan_lunar.leap_month and (not lunar_now.leap_month or scan_lunar.lunar_month != lunar_now.lunar_month):
                    has_cross_leap = True
                    detected_leap_name = f"閏 {scan_lunar.lunar_month} 月"
                    break
            except:
                continue
            
    with col_r:
        if has_cross_leap:
            st.warning(f"⚠️ 偵測到守喪期內適逢【{detected_leap_name}】")
            st.info("💡 依「死人無閏月」傳統，系統已自動將對年月份提前一個月（對日作），確保對年相隔時間總計為 354 天（含起始日為 355 天）。")
        else:
            st.info("💡 守喪期間無跨閏月，對年依常規對齊隔年農曆同月同日辦理，相隔時間總計為 354 天（含起始日為 355 天）。")

    click_calc = st.button("🚀 執行祭祀日期推算", use_container_width=True, key="tab3_run")
    
    if click_calc:
        st.session_state['latest_date'] = death_date_input
        
    final_calc_date = st.session_state['latest_date']
    
    if final_calc_date:
        p_dt = datetime(final_calc_date.year, final_calc_date.month, final_calc_date.day)
        week_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        
        def get_lunar_str(dt_obj):
            try:
                l = ZhDate.from_datetime(dt_obj)
                lp = "閏" if l.leap_month else ""
                return f"農曆 {lp}{l.lunar_month}月{l.lunar_day}日"
            except:
                return "無法計算"
                
        p_lunar = get_lunar_str(p_dt)
        t6_dt = p_dt + timedelta(days=5)
        t6_lunar = get_lunar_str(t6_dt)
        t7_dt = p_dt + timedelta(days=6)
        t7_lunar = get_lunar_str(t7_dt)
        b100_dt = p_dt + timedelta(days=99)
        b100_lunar = get_lunar_str(b100_dt)
        
        dn_dt_display = "無法計算"
        dn_lunar_display = "無法計算"
        dn_week_display = "無法計算"
        dn_remark = ""
        
        if lunar_now:
            try:
                if has_cross_leap:
                    dn_y = lunar_now.lunar_year + 1
                    dn_m = lunar_now.lunar_month - 1
                    if dn_m == 0:
                        dn_m = 12
                        dn_y -= 1
                    dn_d = lunar_now.lunar_day
                    
                    for offset in range(5):
                        try:
                            test_lunar = ZhDate(dn_y, dn_m, dn_d - offset)
                            test_dt = test_lunar.to_datetime()
                            dn_dt_display = test_dt.strftime('%Y-%m-%d')
                            dn_lunar_display = get_lunar_str(test_dt)
                            break
                        except:
                            continue
                    dn_remark = "⚠️ 守喪期逢跨閏月，依俗自動提前一個月辦理（對日作）。符合對年相隔時間總計為 354 天（含起始日為 355 天）原則。"
                
                elif lunar_now.leap_month:
                    dn_y = lunar_now.lunar_year + 1
                    dn_m = lunar_now.lunar_month 
                    dn_d = lunar_now.lunar_day
                    for offset in range(5):
                        try:
                            test_lunar = ZhDate(dn_y, dn_m, dn_d - offset)
                            test_dt = test_lunar.to_datetime()
                            dn_dt_display = test_dt.strftime('%Y-%m-%d')
                            dn_lunar_display = get_lunar_str(test_dt)
                            break
                        except:
                            continue
                    dn_remark = "⚠️ 往生當月為閏月，依俗自動對齊隔年正月同日辦理。符合對年相隔時間總計為 354 天（含起始日為 355 天）原則。"
                
                else:
                    dn_y = lunar_now.lunar_year + 1
                    dn_m = lunar_now.lunar_month
                    dn_d = lunar_now.lunar_day
                    for offset in range(5):
                        try:
                            test_lunar = ZhDate(dn_y, dn_m, dn_d - offset)
                            test_dt = test_lunar.to_datetime()
                            dn_dt_display = test_dt.strftime('%Y-%m-%d')
                            dn_lunar_display = get_lunar_str(test_dt)
                            break
                        except:
                            continue
                    dn_remark = "依常規對齊隔年農曆同月同日辦理。符合對年相隔時間總計為 354 天（含起始日為 355 天）原則。"
                    
                if dn_dt_display != "無法計算":
                    parsed_dn_dt = datetime.strptime(dn_dt_display, '%Y-%m-%d')
                    dn_week_display = week_names[parsed_dn_dt.weekday()]
                    days_diff = (parsed_dn_dt.date() - p_dt.date()).days
                    dn_remark += f"（本案實際國曆相隔：{days_diff} 天，含起始日：{days_diff + 1} 天）"
            except:
                pass
            
        calc_data = {
            "祭祀項目": ["往生當天 (第 1 天)", "🕯️ 頭七儀式 (第 6 天深夜)", "頭七正日 (第 7 天)", "百日 (第 100 天)", "對年 (周年紀念)"],
            "國曆日期": [p_dt.strftime('%Y-%m-%d'), f"★ {t6_dt.strftime('%Y-%m-%d')}", t7_dt.strftime('%Y-%m-%d'), b100_dt.strftime('%Y-%m-%d'), dn_dt_display],
            "星期": [week_names[p_dt.weekday()], week_names[t6_dt.weekday()], week_names[t7_dt.weekday()], week_names[b100_dt.weekday()], dn_week_display],
            "對應農曆": [p_lunar, t6_lunar, t7_lunar, b100_lunar, dn_lunar_display],
            "建議時程 / 備註": ["家屬守靈安靈", "⏱️ 21:00 開始準備，23:00~01:00 (子時) 完成儀式交子", "頭七當天，民俗上亡靈會在此日返家探視", "卒後百日祭祀，各地方可能略有提早", dn_remark]
        }
        
        st.markdown("---")
        st.subheader("📋 智能化祭祀日期與儀式推算結果表")
        st.dataframe(pd.DataFrame(calc_data), use_container_width=True)
        
        st.info(
            "💡 **民俗小常識：對年固定 12 個農曆月原則**\n\n"
            "當往生日至隔年對年的週期中遭遇「閏月」時，活人的曆法會經歷 13 個農曆月（約 384 天）。但依傳統「死人無閏月」之限制，"
            "亡者的第一個年度必須扣除閏月，維持與常規年相同的 12 個農曆月。**其相隔時間總計為 354 天（若包含起始日則為 355 天）**。\n\n"
            "本系統已全面自動化此規則：若遇跨閏月，會自動將農曆月份提前一個月並採取「對日作」辦理，確保不論有無閏月，逝者的守喪週期皆精準契合此傳統定義。"
        )

# ==========================================
# 🦁 新增分頁3：生肖與塔位吉方查詢
# ==========================================
with tab3:
    st.header("🦁 生肖與晉塔適宜方位查詢")
    st.markdown("輸入逝者（或使用者）的出生（或往生）日期，系統將自動識別生肖，並推算適合的進塔、晉塔坐向方位。")
    
    col_t4_1, col_t4_2 = st.columns(2)
    search_date = None
    
    with col_t4_1:
        st.subheader("📍 方式一：用日曆選單選擇")
        dp_t4 = st.date_input("選擇日期：", st.session_state['latest_date'], min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), key="tab4_dp")
        if st.button("🚀 依選單日期查詢", use_container_width=True, key="tab4_btn_a"):
            search_date = clean_and_parse_date(dp_t4)
            
    with col_t4_2:
        st.subheader("📍 方式二：直接文字輸入")
        ld_t4 = st.session_state['latest_date']
        minguo_str_t4 = f"{ld_t4.year - 1911}/{ld_t4.strftime('%m/%d')}"
        ti_t4 = st.text_input(
            "輸入西元或中華民國曆（如 54/3/22 或 1965-03-22）：", 
            value=minguo_str_t4, 
            key="tab4_ti"
        )
        if st.button("🚀 依打字日期查詢", use_container_width=True, key="tab4_btn_b"):
            search_date = clean_and_parse_date(ti_t4)
            
    if search_date:
        try:
            # 轉換為農曆以確認精準生肖與歲次
            lunar_t4 = ZhDate.from_datetime(search_date)
            gz_name, zodiac_name = get_ganzhi_zodiac_details(lunar_t4.lunar_year)
            orientations = get_tower_orientation(zodiac_name)
            
            st.session_state['latest_date'] = search_date.date()
            
            st.markdown("---")
            st.subheader(f"🔮 【{zodiac_name}】生肖專屬命理與塔位解析")
            
            # 以美觀的 Metric 卡片顯示基本資訊
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("輸入國曆日期", search_date.strftime('%Y-%m-%d'))
            with c2:
                st.metric("對應民國紀年", f"民國 {search_date.year - 1911} 年")
            with c3:
                st.metric("對應農曆歲次", f"{gz_name} 年")
            with c4:
                st.metric("本命生肖", zodiac_name)
                
            # 顯示方位推算結果表格
            oriented_data = {
                "評等分類": ["🟢 最佳首選吉方 (大吉)", "🟡 次佳配選方位 (中吉)", "🔴 絕不可選煞方 (大凶)"],
                "建議塔位坐向 (白話地理方位)": [orientations["吉方"], orientations["次吉"], orientations["煞方"]],
                "風水堪輿說明說明": [
                    "此為本命三合、三會、或相生之本命祿位，進塔後最利於骨灰安穩、福廕子孫。",
                    "此方位雖非最優，但若與家族墓園、現成塔位環境衝突時，可作為折衷妥協之選。",
                    "此方向與本命生肖相沖（歲破、地支相沖），民俗上認為會磁場不合，務必避開。"
                ]
            }
            st.dataframe(pd.DataFrame(oriented_data), use_container_width=True)
            
            st.caption(
                "💡 **地理小知識：** 這裡所說的『坐向』是指骨灰罈入塔位後，其『刻字正面（或照片正面）』所面朝的反方向。例如：『坐北朝南』意即逝者照片背對北方，面向南方看出去。"
            )
            
            st.markdown("---")
            st.subheader("📜 民俗堪輿對照表 (固定參考)")
            
            with st.expander("點擊展開：查看生肖方位與月煞/年煞對照表"):
                st.markdown("### 1. 生肖三合吉凶方位表")
                st.table(pd.DataFrame({
                    "生肖": ["鼠、龍、猴", "牛、蛇、雞", "虎、馬、狗", "兔、羊、豬"],
                    "大吉方": ["西", "南", "東", "北"],
                    "小吉方": ["北", "西", "南", "東"],
                    "次之座": ["東", "北", "西", "南"],
                    "煞方": ["南", "東", "北", "西"]
                }))
                
                st.markdown("### 2. 農曆月份【月煞】不宜座向")
                st.table(pd.DataFrame({
                    "農曆月份": ["1、5、9", "2、6、10", "3、7、11", "4、8、12"],
                    "不宜座向": ["北方", "西方", "南方", "東方"]
                }))
                
                st.markdown("### 3. 【年煞】方位對照表")
                st.table(pd.DataFrame({
                    "年份地支": ["寅、午、戌", "申、子、辰", "亥、卯、未", "巳、酉、丑"],
                    "對應生肖": ["虎、馬、狗", "猴、鼠、龍", "豬、兔、羊", "蛇、雞、牛"],
                    "煞方": ["北方", "南方", "西方", "東方"]
                }))
        
            
        except Exception as e:
            st.error(f"❌ 處理失敗，請確認年份是否在 1900~2100 之間（錯誤原因: {e}）")
# ==========================================
# 🪦 新增分頁4：土葬二十四山查詢
# ==========================================
with tab4:
    st.header("🪦 仙命二十四山吉凶與斷語查詢")
    
    si_ming = st.selectbox("請選擇仙命：", list(BURIAL_RULES_60.keys()))
    rule = BURIAL_RULES_60[si_ming]
    
    # 建立兩欄顯示
    col_yi, col_ji = st.columns(2)
    
    with col_yi:
        st.success("✅ 宜葬六山")
        st.write(f"**方位**：{rule['宜']['方位']}")
        st.caption(f"說明：{rule['宜']['說明']}")
        
    with col_ji:
        st.error("❌ 忌葬六山")
        st.write(f"**方位**：{rule['忌']['方位']}")
        st.caption(f"說明：{rule['忌']['說明']}")

# ==========================================
# 🪦 新增分頁5：萬年曆
# ==========================================
with tab5:
    st.header("📅 擇日分析控制台")

    # 1. 介面輸入
    col_date, col_hour = st.columns(2)
    with col_date:
        selected_date = st.date_input("選擇日期", st.session_state.get('latest_date', datetime.now().date()))
    with col_hour:
        selected_hour = st.slider("選擇時辰 (小時)", 0, 23, 12)

    # 2. 核心運算
    pillars = PreciseCalendar.get_four_pillars(selected_date.year, selected_date.month, selected_date.day, selected_hour)
    
    
    # 顯示四柱
    st.subheader("🔮 當日四柱結構")
    # 這裡顯示農曆，放在最上方非常直觀
    st.info(f"📅 **農曆日期：** {pillars['農曆']} ({pillars['農曆字串']})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("年柱", pillars["年柱"])
    c2.metric("月柱", pillars["月柱"])
    c3.metric("日柱", pillars["日柱"])
    c4.metric("時柱", pillars["時柱"])

    # 判斷顏色：如果是黃道吉，用綠色；黑道凶，用紅色
    is_lucky = "吉" in god_info["屬性"]   
    # 在 metric 中顯示名稱與屬性
    col_g1.metric(label="當前值神", value=god_name)
    col_g1.caption(god_info["屬性"])
        
    # 在右側顯示建議
    col_g2.write(f"**💡 擇日建議：**")
    if is_lucky:
        col_g2.success(god_info['適用'])
    else:
        col_g2.error(god_info['適用'])
    
    

    # 3. 禁忌與斷語分析
    st.markdown("---")
    st.subheader("📋 擇日深度診斷")
    
    # 彭祖百忌分析
    day_gan = pillars["日柱"][0]
    day_zhi = pillars["日柱"][1]
    
    with st.expander("⚠️ 彭祖百忌叮嚀"):
        st.write(f"天干({day_gan})：{PENGZU_STEMS.get(day_gan, '無紀錄')}")
        st.write(f"地支({day_zhi})：{PENGZU_BRANCHES.get(day_zhi, '無紀錄')}")

    # 五不遇時分析 (重點修正：正確解開 Tuple)
    hour_idx = selected_hour // 2
    hour_gan_calculated, is_unsafe = TimeSafetyEngine.check_hour_safety(day_gan, hour_idx)
    
    if is_unsafe:
        st.error(f"❌ 當前時辰 ({hour_gan_calculated}時) 為『五不遇時』，傳統擇日建議避開！")
    else:
        st.success(f"✅ 當前時辰 ({hour_gan_calculated}時) 非五不遇時。")

    # 六十甲子斷語 (確保 GZ_RECORDS 已被正確 import)
    day_gz = pillars["日柱"]
    # 這裡確保您的 fengshui_db 中有定義 GZ_RECORDS
    #record = GZ_RECORDS.get(day_gz, {"吉凶": "平", "斷語": "無特別紀錄"})
    #st.info(f"**日課吉凶：{record.get('吉凶', '平')}** | {record.get('斷語', '無紀錄')}")
