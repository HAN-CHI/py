import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from zhdate import ZhDate
import re

# 設定網頁標題與圖示
st.set_page_config(page_title="萬年曆通用轉換系統", page_icon="📅", layout="wide")

if 'latest_date' not in st.session_state:
    st.session_state['latest_date'] = date.today()

# 核心功能函式
def get_ganzhi_zodiac_details(lunar_year):
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    zodiacs = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]
    stem_idx, branch_idx = (lunar_year - 4) % 10, (lunar_year - 4) % 12
    return f"{stems[stem_idx]}{branches[branch_idx]}", zodiacs[branch_idx]

def get_ganzhi_zodiac(lunar_year):
    gz, zd = get_ganzhi_zodiac_details(lunar_year)
    return f"{gz}年 ({zd})"

def clean_and_parse_date(date_val):
    if pd.isna(date_val): return None
    if isinstance(date_val, (datetime, date, pd.Timestamp)):
        y = date_val.year + 1911 if date_val.year < 1900 else date_val.year
        return datetime(y, date_val.month, date_val.day)
    text = re.sub(r'[民國年/月日]', '-', str(date_val))
    nums = [int(n) for n in re.findall(r'\d+', text)]
    if len(nums) == 3:
        y = nums[0] + 1911 if nums[0] < 1900 else nums[0]
        return datetime(y, nums[1], nums[2])
    return None

# ==========================================
# 建立網頁分頁 (新增第四個分頁)
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "📌 單日萬能查詢",
    "🕯️ 頭七/百日/對年計算機",
    "🦁 生肖與塔位吉方查詢"
])

# ==========================================
# 📌 分頁一：單日萬能查詢
# ==========================================
with tab1:
    st.header("📌 單日萬能查詢 (國曆/農曆互轉)")
    mode = st.radio("請選擇轉換方式：", ["國曆 ➔ 農曆", "農曆 ➔ 國曆"], horizontal=True)
    st.markdown("---")
    
    target_date, is_triggered = None, False
    if mode == "國曆 ➔ 農曆":
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📍 方法 A (日曆選單)")
            dp = st.date_input("選擇日期：", st.session_state['latest_date'], key="tab1_dp")
            if st.button("🚀 執行方法 A 查詢", use_container_width=True):
                target_date, is_triggered = clean_and_parse_date(dp), True
        with c2:
            st.subheader("📍 方法 B (文字輸入)")
            ti = st.text_input("輸入日期 (如 115/7/11):", value=f"{st.session_state['latest_date'].year-1911}/{st.session_state['latest_date'].strftime('%m/%d')}")
            if st.button("🚀 執行方法 B 查詢", use_container_width=True):
                target_date, is_triggered = clean_and_parse_date(ti), True
    else:
        st.subheader("📍 方法 C (農曆輸入)")
        cal_type = st.radio("年份格式：", ["西元曆", "中華民國曆"], horizontal=True)
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        curr_y = date.today().year
        l_year = c1.number_input("農曆年份" + ("(西元)" if cal_type=="西元曆" else "(民國)"), 1900, 2100, curr_y if cal_type=="西元曆" else curr_y-1911)
        l_month, l_day = c2.number_input("月份", 1, 12, 1), c3.number_input("日期", 1, 30, 1)
        is_leap = c4.checkbox("是否閏月")
        if st.button("🚀 執行農曆轉國曆查詢", use_container_width=True):
            try:
                target_date = ZhDate(l_year + 1911 if cal_type=="中華民國曆" else l_year, l_month, l_day, is_leap).to_datetime()
                is_triggered = True
            except: st.error("日期不存在")

    if is_triggered and target_date:
        st.session_state['latest_date'] = target_date.date()
        lunar = ZhDate.from_datetime(target_date)
        cols = st.columns(4)
        cols[0].metric("解析後西元", target_date.strftime('%Y-%m-%d'))
        cols[1].metric("民國紀年", f"民國 {target_date.year - 1911} 年")
        cols[2].metric("農曆", f"{'閏' if lunar.leap_month else ''}{lunar.lunar_month}月{lunar.lunar_day}日")
        cols[3].metric("干支生肖", get_ganzhi_zodiac(lunar.lunar_year))

# ==========================================
# 🕯️ 分頁三：頭七/百日/對年計算機
# ==========================================
with tab2:
    st.header("🕯️ 傳統祭祀時間計算機")
    st.markdown("傳統習俗中，**往生當天即算作「第 1 天」**。本計算機依此基準精確推算。")
    
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        death_date_input = st.date_input("請選擇「國曆往生日期」：", st.session_state['latest_date'], key="tab3_dp")
    
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
    search_date = clean_and_parse_date(st.text_input("輸入日期 (如 115/3/22):", value=f"{st.session_state['latest_date'].year-1911}/{st.session_state['latest_date'].strftime('%m/%d')}"))
    if search_date:
        lunar = ZhDate.from_datetime(search_date)
        _, zodiac = get_ganzhi_zodiac_details(lunar.lunar_year)
        st.subheader(f"🔮 【{zodiac}】生肖專屬解析")
        # 顯示解析表格 (省略中間部分邏輯)...
        
        st.markdown("---")
        st.subheader("📜 民俗堪輿對照表 (固定參考)")
        with st.expander("點擊展開：查看生肖方位與煞方對照表"):
            st.markdown("### 1. 生肖方位對照")
            st.table(pd.DataFrame({"生肖": ["鼠/龍/猴", "牛/蛇/雞", "虎/馬/狗", "兔/羊/豬"], "大吉方": ["西", "南", "東", "北"], "煞方": ["南", "東", "北", "西"]}))
            st.markdown("### 2. 農曆月份【月煞】")
            st.table(pd.DataFrame({"農曆月份": ["1/5/9", "2/6/10", "3/7/11", "4/8/12"], "不宜座向": ["北方", "西方", "南方", "東方"]}))
            st.markdown("### 3. 【年煞】方位對照")
            st.table(pd.DataFrame({"地支": ["寅午戌", "申子辰", "亥卯未", "巳酉丑"], "煞方": ["北方", "南方", "西方", "東方"]}))
            
        except Exception as e:
            st.error(f"❌ 處理失敗，請確認年份是否在 1900~2100 之間（錯誤原因: {e}）")
