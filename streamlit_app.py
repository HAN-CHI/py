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

st.title("🏮 跨世紀萬年曆自動轉換系統 (西元/民國/祭祀通用版)")
st.markdown(
    "本系統支援西元曆、中華民國曆自動識別轉換，"
    "並內建傳統民俗頭七、百日、對年之精準祭祀時間計算。"
)

# ==========================================
# 🔮 智慧演算法：精準計算天干地支與生肖
# ==========================================
def get_ganzhi_zodiac(lunar_year):
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    zodiacs = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]
    
    stem_idx = (lunar_year - 4) % 10
    branch_idx = (lunar_year - 4) % 12
    
    return f"{stems[stem_idx]}{branches[branch_idx]}年 ({zodiacs[branch_idx]})"

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
# 建立網頁分頁（已新增第三個分頁）
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "📌 單日萬能查詢", 
    "📊 Excel 混合批次轉換", 
    "🕯️ 頭七/百日/對年計算機"
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
        date_picker = st.date_input("用日曆選單選擇日期：", date.today())
        click_a = st.button("🚀 執行方法 A 查詢", use_container_width=True)
        if click_a:
            target_date = clean_and_parse_date(date_picker)
            is_triggered = True
            
    with col_input2:
        st.subheader("📍 方法 B")
        current_minguo_str = f"{date.today().year - 1911}/{date.today().strftime('%m/%d')}"
        date_text = st.text_input(
            "直接打字輸入（西元/民國皆可）：", 
            value=current_minguo_str, 
            help="範例: 115/7/10 或 2026-07-10"
        )
        click_b = st.button("🚀 執行方法 B 查詢", use_container_width=True)
        if click_b:
            target_date = clean_and_parse_date(date_text)
            is_triggered = True
        
    if is_triggered:
        if target_date:
            try:
                lunar = ZhDate.from_datetime(target_date)
                minguo_year = target_date.year - 1911
                
                leap_prefix = "閏 " if lunar.leap_month else ""
                lunar_display = f"{leap_prefix}{lunar.lunar_month}月{lunar.lunar_day}日"
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
        type=["xlsx", "xls"]
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("📂 原始資料預覽（前 5 筆）：")
            st.dataframe(df.head(5))
            
            columns = df.columns.tolist()
            date_col = st.selectbox("請選擇包含『國曆日期欄位』的名稱：", columns)
            
            if st.button("🚀 開始智慧識別並批次轉換"):
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
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
        except Exception as e:
            st.error(f"💥 處理檔案時發生預期外的錯誤: {e}")

# ==========================================
# 🕯️ 分頁三：頭七/百日/對年計算機 (全新加入)
# ==========================================
with tab3:
    st.header("🕯️ 傳統祭祀時間計算機")
    st.markdown("傳統習俗中，**往生當天即算作「第 1 天」**。本計算機依此基準精確推算。")
    
    # 讓使用者選擇往生日期
    death_date = st.date_input("請選擇「國曆往生日期」：", date.today())
    
    if death_date:
        p_dt = datetime(death_date.year, death_date.month, death_date.day)
        
        # 建立星期對照表
        week_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        
        # 輔助函式：取得農曆顯示字串
        def get_lunar_str(dt_obj):
            try:
                l = ZhDate.from_datetime(dt_obj)
                lp = "閏" if l.leap_month else ""
                return f"農曆 {lp}{l.lunar_month}月{l.lunar_day}日"
            except:
                return "無法計算"
                
        # 1. 往生當天 (第 1 天)
        p_lunar = get_lunar_str(p_dt)
        
        # 2. 頭七 (第 7 天) -> 往生 + 6 天
        t7_dt = p_dt + timedelta(days=6)
        t7_lunar = get_lunar_str(t7_dt)
        
        # 3. 百日 (第 100 天) -> 往生 + 99 天
        b100_dt = p_dt + timedelta(days=99)
        b100_lunar = get_lunar_str(b100_dt)
        
        # 4. 對年 (隔年農曆同月同日)
        dn_dt_display = "無法計算"
        dn_lunar_display = "無法計算"
        dn_week_display = "無法計算"
        try:
            lunar_now = ZhDate.from_datetime(p_dt)
            dn_y = lunar_now.lunar_year + 1
            dn_m = lunar_now.lunar_month
            dn_d = lunar_now.lunar_day
            
            # 防錯滾動機制：如果隔年的這個月只有29天而沒30天，會自動往前找最後一天
            for offset in range(5):
                try:
                    test_lunar = ZhDate(dn_y, dn_m, dn_d - offset)
                    test_dt = test_lunar.to_datetime()
                    
                    dn_dt_display = test_dt.strftime('%Y-%m-%d')
                    dn_week_display = week_names[test_dt.weekday()]
                    
                    lp = "閏" if test_lunar.leap_month else ""
                    dn_lunar_display = f"農曆 {lp}{test_lunar.lunar_month}月{test_lunar.lunar_day}日"
                    break
                except:
                    continue
        except:
            pass
            
        # 彙整成表格資料
        calc_data = {
            "祭祀項目": ["往生當天 (第 1 天)", "頭七 (第 7 天)", "百日 (第 100 天)", "對年 (隔年農曆同日)"],
            "國曆日期": [
                p_dt.strftime('%Y-%m-%d'),
                t7_dt.strftime('%Y-%m-%d'),
                b100_dt.strftime('%Y-%m-%d'),
                dn_dt_display
            ],
            "星期": [
                week_names[p_dt.weekday()],
                week_names[t7_dt.weekday()],
                week_names[b100_dt.weekday()],
                dn_week_display
            ],
            "對應農曆": [
                p_lunar,
                t7_lunar,
                b100_lunar,
                dn_lunar_display
            ]
        }
        
        st.markdown("---")
        st.subheader("📋 智能化祭祀日期推算結果表")
        
        # 顯示互動式表格
        st.dataframe(pd.DataFrame(calc_data), use_container_width=True)
        
        st.info(
            "💡 備註：傳統民間習俗各地方可能因應性別、家族內規、是否有閏月"
            "而有提早一天（如：切七、做百日）或調整對年日期的彈性做法。"
            "以上提供之結果為內政部民俗標準之基本精確日期，僅供家族排程參考。"
        )
