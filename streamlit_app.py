import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from zhdate import ZhDate
import io
import re

# 設定網頁標題與圖示
st.set_page_config(
    page_title="萬年曆通用轉換系統", 
    page_icon="📅", 
    layout="wide"
)

# 核心同步機制：初始化全域「最新日期」記憶庫，預設為今天
if 'latest_date' not in st.session_state:
    st.session_state['latest_date'] = date.today()

st.title("🏮 跨世紀萬年曆自動轉換系統 (西元/民國/祭祀/雙重避煞塔位通用版)")
st.markdown(
    "本系統支援西元曆、中華民國曆自動識別轉換，"
    "內建傳統頭七、百日、對年精算，並全面整合**「生肖吉方」、「動態年煞」與「農曆月煞」**之三合一塔位決策導航。"
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
    data = {
        "鼠": {"吉方": "坐正北朝正南、坐正東朝正西", "次吉": "坐正西朝正東", "煞方": "忌坐正南朝正北（生肖相沖）"},
        "牛": {"吉方": "坐北朝南、坐西朝東", "次吉": "坐東南朝西北", "煞方": "忌坐西南朝東北（生肖相沖）"},
        "虎": {"吉方": "坐東朝西、坐南朝北", "次吉": "坐西北朝東南", "煞方": "忌坐正西朝正東（生肖相沖）"},
        "兔": {"吉方": "坐正東朝正西、坐正北朝正南", "次吉": "坐正南朝正北", "煞方": "忌坐正西朝正東（生肖相沖）"},
        "龍": {"吉方": "坐東朝西、坐北朝南", "次吉": "坐西朝東", "煞方": "忌坐西北朝東南（生肖相沖）"},
        "蛇": {"吉方": "坐南朝北、坐西朝東", "次吉": "坐東北朝西南", "煞方": "忌坐西北朝東南（生肖相沖）"},
        "馬": {"吉方": "坐正南朝正北、坐正西朝正東", "次吉": "坐正東朝正西", "煞方": "忌坐正北朝正南（生肖相沖）"},
        "羊": {"吉方": "坐南朝北、坐東朝西", "次吉": "坐西北朝東南", "煞方": "忌坐東北朝西南（生肖相沖）"},
        "猴": {"吉方": "坐西朝東、坐北朝南", "次吉": "坐東南朝西北", "煞方": "忌坐正東朝正西（生肖相沖）"},
        "雞": {"吉方": "坐正西朝正東、坐正南朝正北", "次吉": "坐東南朝西北", "煞方": "忌坐正東朝正西（生肖相沖）"},
        "狗": {"吉方": "坐西朝東、坐南朝北", "次吉": "坐東北朝西南", "煞方": "忌坐東南朝西北（生肖相沖）"},
        "豬": {"吉方": "坐北朝南、坐東朝西", "次吉": "坐西南朝東北", "煞方": "忌坐正北朝正南（生肖相沖）"}
    }
    return data.get(zodiac, {"吉方": "通用方位", "次吉": "通用方位", "煞方": "無特殊禁忌"})

# ==========================================
# 📋 依據使用者提供之圖表一：農曆月份不宜座向 (月煞)
# ==========================================
def get_lunar_month_shashang(lunar_month):
    if lunar_month in [1, 5, 9]:
        return "北方"
    elif lunar_month in [2, 6, 10]:
        return "西方"
    elif lunar_month in [3, 7, 11]:
        return "南方"
    elif lunar_month in [4, 8, 12]:
        return "東方"
    return "無特殊限制"

# ==========================================
# 📋 依據使用者提供之圖表二：西元年份四年輪流規則 (年煞)
# ==========================================
def get_yearly_shashang(year):
    # 2026=北, 2027=西, 2028=南, 2029=東，以此類推循環
    cycle = ["北方", "西方", "南方", "東方"]
    idx = (year - 2026) % 4
    return cycle[idx]

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
# 建立網頁分頁
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📌 單日萬能查詢", 
    "📊 Excel 混合批次轉換", 
    "🕯️ 頭七/百日/對年計算機",
    "🦁 生肖與塔位吉方查詢"
])

# ==========================================
# 📌 分頁一：單日萬能查詢
# ==========================================
with tab1:
    st.header("單日國曆轉農曆 (支援自由文字輸入)")
    st.markdown("請選擇使用 方法 A 或 方法 B 輸入，並點擊下方按鈕查詢。")
    
    col_input1, col_input2 = st.columns(2)
    target_date = None
    is_triggered = False
    
    with col_input1:
        st.subheader("📍 方法 A")
        date_picker = st.date_input("用日曆選單選擇日期：", st.session_state['latest_date'], key="tab1_dp")
        click_a = st.button("🚀 執行方法 A 查詢", use_container_width=True, key="tab1_btn_a")
        if click_a:
            target_date = clean_and_parse_date(date_picker)
            if target_date:
                st.session_state['latest_date'] = target_date.date()
            is_triggered = True
            
    with col_input2:
        st.subheader("📍 方法 B")
        ld = st.session_state['latest_date']
        current_minguo_str = f"{ld.year - 1911}/{ld.strftime('%m/%d')}"
        date_text = st.text_input(
            "直接打字輸入（西元/民國皆可）：", 
            value=current_minguo_str, 
            help="範例: 115/7/10 或 2026-07-10",
            key="tab1_ti"
        )
        click_b = st.button("🚀 執行方法 B 查詢", use_container_width=True, key="tab1_btn_b")
        if click_b:
            target_date = clean_and_parse_date(date_text)
            if target_date:
                st.session_state['latest_date'] = target_date.date()
            is_triggered = True
        
    if is_triggered:
        if target_date:
            try:
                lunar = ZhDate.from_datetime(target_date)
                minguo_year = target_date.year - 1911
                
                leap_prefix = "閏" if lunar.leap_month else ""
                lunar_display = f"農曆 {leap_prefix}{lunar.lunar_month}月{lunar.lunar_day}日"
                ganzhi_display = get_ganzhi_zodiac(lunar.lunar_year)
                
                st.markdown("---")
                st.subheader("🔮 查詢對照結果：")
                
                cols = st.columns(4)
                with cols[0]:
                    st.metric(label="解析後西元國曆", value=target_date.strftime('%Y-%m-%d'))
                with cols[1]:
                    st.metric(label="對應中華民國曆", value=f"民國 {minguo_year} 年")
                with cols[2]:
                    st.metric(label="計算後農曆", value=lunar_display)
                with cols[3]:
                    st.metric(label="歲次干支 (生肖)", value=ganzhi_display)
                    
                st.success(f"💡 完整農曆中文表示：{lunar.chinese()}")
            except Exception as e:
                st.error(f"❌ 轉換錯誤: {e}。請確認年份是否在 1900~2100 之間。")
        else:
            st.warning("⚠️ 無法識別此日期格式，請重新輸入（例如：115/7/10）")

# ==========================================
# 📊 分頁二：Excel 混合批次轉換
# ==========================================
with tab2:
    st.header("Excel 欄位混雜轉換器")
    st.markdown("支援 Excel 內同時存在西元與民國格式，上傳後自動識別。")
    
    uploaded_file = st.file_uploader(
        "請選擇要上傳的 Excel 檔案 (.xlsx, .xls)", 
        type=["xlsx", "xls"],
        key="tab2_uploader"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("📂 原始資料預覽（前 5 筆）：")
            st.dataframe(df.head(5))
            
            columns = df.columns.tolist()
            date_col = st.selectbox("請選擇包含『國曆日期欄位』的名稱：", columns, key="tab2_select")
            
            if st.button("🚀 開始智慧識別並批次轉換", key="tab2_run"):
                with st.spinner('AI 引擎正在識別格式...'):
                    
                    def batch_convert(row_val):
                        dt = clean_and_parse_date(row_val)
                        if dt:
                            try:
                                mingo = f"民國 {dt.year - 1911} 年"
                                lunar_obj = ZhDate.from_datetime(dt)
                                leap_prefix = "閏" if lunar_obj.leap_month else ""
                                
                                return pd.Series([
                                    dt.strftime('%Y-%m-%d'),
                                    mingo,
                                    f"農曆{leap_prefix}{lunar_obj.lunar_month}月{lunar_obj.lunar_day}日",
                                    get_ganzhi_zodiac(lunar_obj.lunar_year)
                                ])
                            except:
                                return pd.Series(["超出計算範圍", "無法計算", "無法計算", "無法計算"])
                        else:
                            return pd.Series(["格式錯誤", "無法識別", "無法識別", "無法識別"])
                    
                    df[['標準西元', '標準民國', '轉換農曆', '歲次干支(生肖)']] = df[date_col].apply(batch_convert)
                    
                    st.success("🎉 資料已全部轉換完成！")
                    st.dataframe(df.head(10))
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='智慧萬年曆結果')
                    processed_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 下載轉換後的通用萬年曆 Excel",
                        data=processed_data,
                        file_name=f"萬年曆轉換結果_{datetime.now().strftime('%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="tab2_download"
                    )
                    
        except Exception as e:
            st.error(f"💥 處理檔案時發生預期外的錯誤: {e}")

# ==========================================
# 🕯️ 分頁三：頭七/百日/對年計算機
# ==========================================
with tab3:
    st.header("🕯️ 傳統祭祀時間計算機")
    st.markdown("傳統習俗中，**往生當天即算作「第 1 天」**。本計算機依此基準精確推算。")
    
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        death_date_input = st.date_input("請選擇「國曆往生日期」：", st.session_state['latest_date'], key="tab3_dp")
    
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

# ==========================================
# 🦁 分頁四：生肖與塔位吉方查詢 (結合年煞、月煞全面避向機制)
# ==========================================
with tab4:
    st.header("🦁 生肖與晉塔適宜方位查詢 (年煞/月煞雙重防護)")
    st.markdown("輸入欲查詢之日期（西元/民國皆可），系統會自動換算為**農曆月份與生肖**，並動態交叉比對您提供之「年煞」與「月煞」不宜座向。")
    
    col_t4_1, col_t4_2 = st.columns(2)
    search_date = None
    
    with col_t4_1:
        st.subheader("📍 方式一：用日曆選單選擇")
        dp_t4 = st.date_input("選擇日期：", st.session_state['latest_date'], key="tab4_dp")
        if st.button("🚀 依選單日期查詢", use_container_width=True, key="tab4_btn_a"):
            search_date = clean_and_parse_date(dp_t4)
            
    with col_t4_2:
        st.subheader("📍 方式二：直接文字輸入")
        ld_t4 = st.session_state['latest_date']
        minguo_str_t4 = f"{ld_t4.year - 1911}/{ld_t4.strftime('%m/%d')}"
        ti_t4 = st.text_input(
            "輸入西元或中華民國曆（如 115/7/11 或 2026-07-11）：", 
            value=minguo_str_t4, 
            key="tab4_ti"
        )
        if st.button("🚀 依打字日期查詢", use_container_width=True, key="tab4_btn_b"):
            search_date = clean_and_parse_date(ti_t4)
            
    if search_date:
        try:
            # 1. 轉換為農曆以確認精準生肖、歲次與農曆月份
            lunar_t4 = ZhDate.from_datetime(search_date)
            gz_name, zodiac_name = get_ganzhi_zodiac_details(lunar_t4.lunar_year)
            orientations = get_tower_orientation(zodiac_name)
            
            # 2. 核心命理規則計算 (年煞 + 月煞)
            year_shashang = get_yearly_shashang(search_date.year)
            month_shashang = get_lunar_month_shashang(lunar_t4.lunar_month)
            
            st.session_state['latest_date'] = search_date.date()
            
            st.markdown("---")
            st.subheader(f"🔮 【西元 {search_date.year} 年 / 農曆 {lunar_t4.lunar_month} 月・生肖 {zodiac_name}】雙重避煞精算")
            
            # 以卡片清楚呈現四大核心指標
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("查詢西元年度", f"{search_date.year} 年")
            with c2:
                st.metric("對應農曆月份", f"農曆 {lunar_t4.lunar_month} 月")
            with c3:
                st.metric("🚨 該年煞方 (四年輪替)", year_shashang)
            with c4:
                st.metric("🚨 該月煞方 (月份對應)", month_shashang)
                
            # 3. 建立並呈現綜合判定表格
            oriented_data = {
                "評等分類": [
                    "🟢 最佳首選吉方 (大吉)", 
                    "🟡 次佳配選方位 (中吉)", 
                    "🔴 絕不可選：生肖相沖方",
                    "❌ 絕不可選：本年大煞方位",
                    "⚠️ 絕不可選：本月煞傷方位"
                ],
                "建議塔位坐向 (白話地理方位)": [
                    orientations["吉方"], 
                    orientations["次吉"], 
                    orientations["煞方"],
                    f"忌坐【{year_shashang}】",
                    f"忌坐【{month_shashang}】"
                ],
                "風水堪輿說明": [
                    "此為本命三合、三會、或相生之本命祿位，進塔後最利於骨灰安穩、福廕子孫。",
                    "此方位雖非最優，但若與家族墓園、現成塔位環境衝突時，可作為折衷妥協之選。",
                    "此方向與本命生肖直接相沖（地支沖煞），民俗上認為磁場嚴重不合，務必避開。",
                    f"依據年三煞規則，西元 {search_date.year} 年煞方落在【{year_shashang}】，此年內進塔切勿選擇此坐向。",
                    f"依據月煞規則，農曆 {lunar_t4.lunar_month} 月份不宜選擇坐【{month_shashang}】之塔位。"
                ]
            }
            st.dataframe(pd.DataFrame(oriented_data), use_container_width=True)
            
            # 4. 智慧衝突交叉檢查與主動警告
            conflict_warnings = []
            
            # 檢查生肖吉方是否踩到年煞或月煞
            for direction in ["正北", "北", "正南", "南", "正東", "東", "正西", "西"]:
                if direction in orientations["吉方"]:
                    if direction in year_shashang:
                        conflict_warnings.append(f"❌ **嚴重衝突：** 本命首選吉方包含【{direction}】，但該方位剛好是當年【{year_shashang}年煞】，**此年內絕對不可以用此方位！**")
                    if direction in month_shashang:
                        conflict_warnings.append(f"⚠️ **月份衝突：** 本命首選吉方包含【{direction}】，但因進塔時間為農曆 {lunar_t4.lunar_month} 月（月煞為【{month_shashang}】），**此月份內建議避開此方位，或改用次佳方位。**")
            
            # 呈現警告區塊
            if conflict_warnings:
                st.markdown("### 🔔 智能堪輿衝突提示：")
                for warning in conflict_warnings:
                    st.error(warning)
            else:
                st.success("🎉 經全自動交叉覆核：該日期的年煞、月煞方位與您的生肖吉方無直接衝突，可放心參考上述首選吉方挑選塔位！")
            
            st.caption(
                "💡 **地理小知識：** 這裡所說的『坐向』是指骨灰罈入塔位後，其『刻字正面（或照片正面）』所面朝的反方向。例如：『坐北朝南』意即逝者照片背對北方，面向南方看出去。"
            )
            
        except Exception as e:
            st.error(f"❌ 處理失敗，請確認年份是否在 1900~2100 之間（錯誤原因: {e}）")
