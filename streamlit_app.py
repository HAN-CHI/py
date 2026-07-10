import streamlit as st
import pandas as pd
from datetime import datetime, date
from zhdate import ZhDate
import io
import re

# 設定網頁標題與圖示
st.set_page_config(page_title="萬年曆通用轉換系統", page_icon="📅", layout="wide")

st.title("🏮 跨世紀萬年曆自動轉換系統 (西元/民國通用版)")
st.markdown("本系統已全面優化！不論輸入**西元曆**（如 2026-07-10）或**中華民國曆**（如 115-07-10、1150710），皆可自動識別並精準轉換。")

# ==========================================
# 🔮 智慧演算法：精準計算天干地支與生肖
# ==========================================
def get_ganzhi_zodiac(lunar_year):
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    zodiacs = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]
    
    # 萬年曆干支公式基準
    stem_idx = (lunar_year - 4) % 10
    branch_idx = (lunar_year - 4) % 12
    
    return f"{stems[stem_idx]}{branches[branch_idx]}年 ({zodiacs[branch_idx]})"

# ==========================================
# 🧠 核心：西元/民國智慧識別過濾器
# ==========================================
def clean_and_parse_date(date_val):
    if pd.isna(date_val):
        return None
    
    # 狀況 1：如果是 Python 的日期或時間物件
    if isinstance(date_val, (datetime, date, pd.Timestamp)):
        y, m, d = date_val.year, date_val.month, date_val.day
        if y < 1900:
            y += 1911
        try:
            return datetime(y, m, d)
        except:
            return None
    
    # 狀況 2：如果是純數字
    if isinstance(date_val, (int, float)):
        date_val = str(int(date_val))
        
    # 狀況 3：如果是字串
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
tab1, tab2 = st.tabs(["📌 單日萬能查詢", "📊 Excel 混合批次轉換"])

# ==========================================
# 📌 分頁一：單日萬能查詢
# ==========================================
with tab1:
    st.header("單日國曆轉農曆 (支援自由文字輸入)")
    st.markdown("請選擇使用 **方法 A** 或 **方法 B** 輸入，並點擊下方的按鈕進行查詢。")
    
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
        date_text = st.text_input("直接打字輸入（西元/民國皆可）：", value=current_minguo_str, help="範例: 115/7/10 或 2026-07-10")
        click_b = st.button("🚀 執行方法 B 查詢", use_container_width=True)
        if click_b:
            target_date = clean_and_parse_date(date_text)
            is_triggered = True
        
    # ==========================================
    # 📊 顯示 A 或 B 的查詢結果
    # ==========================================
    if is_triggered:
        if target_date:
            try:
                lunar = ZhDate.from_datetime(target_date)
                minguo_year = target_date.year - 1911
                
                # 處理閏月前綴
                leap_prefix = "閏 " if lunar.is_leap else ""
                lunar_display = f"{leap_prefix}{lunar.lunar_month}月{lunar.lunar_day}日"
                
                # 使用我們寫好的安全公式計算生肖與干支
                ganzhi_display = get_ganzhi_zodiac(lunar.lunar_year)
                
                st.markdown("---")
                st.subheader("🔮 查詢對照結果：")
                
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric(label="解析後西元國曆", value=target_date.strftime('%Y-%m-%d'))
                with c2:
                    st.metric(label="對應中華民國曆", value=f"民國 {minguo_year} 年")
                with c3:
                    st.metric(label="計算後農曆", value=lunar_display)
                with c4:
                    st.metric(label="歲次干支 (生肖)", value=ganzhi_display)
                    
                st.success(f"💡 完整農曆中文表示：{lunar.chinese()}")
            except Exception as e:
                # 🛠️ 這裡修改：精準回報錯誤原因，不再盲目瞎猜
                st.error(f"❌ 轉換時發生錯誤！錯誤訊息: {e}。請確認輸入年份是否在西元 1900~2100 年之間。")
        else:
            st.warning("⚠️ 無法識別此日期格式，請重新輸入（例如：115/7/10 或 2026/7/10）")

# ==========================================
# 📊 分頁二：Excel 混合批次轉換
# ==========================================
with tab2:
    st.header("Excel 欄位混雜轉換器")
    st.markdown("管他 Excel 欄位裡是寫 `115/07/10` 還是 `2026-07-10`，丟上來系統自動幫你全部看懂！")
    
    uploaded_file = st.file_uploader("請選擇要上傳的 Excel 檔案 (.xlsx, .xls)", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("📂 原始資料預覽（前 5 筆）：")
            st.dataframe(df.head(5))
            
            columns = df.columns.tolist()
            date_col = st.selectbox("請選擇包含『國曆日期欄位』的名稱：", columns)
            
            if st.button("🚀 開始智慧識別並批次轉換"):
                with st.spinner('AI 引擎正在通靈識別西元與民國格式...'):
                    
                    def batch_convert(row_val):
                        dt = clean_and_parse_date(row_val)
                        if dt:
                            try:
                                mingo = f"民國 {dt.year - 1911} 年"
                                lunar_obj = ZhDate.from_datetime(dt)
                                leap_prefix = "閏" if lunar_obj.is_leap else ""
                                
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
                    
                    st.success("🎉 東西全算好了！民國和西元都幫你整理得整
