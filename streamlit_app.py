import streamlit as st
import pandas as pd
from datetime import datetime
from zhdate import ZhDate
import io
import re

# 設定網頁標題與圖示
st.set_page_config(page_title="萬年曆通用轉換系統", page_icon="📅", layout="wide")

st.title("🏮 跨世紀萬年曆自動轉換系統 (西元/民國通用版)")
st.markdown("本系統已全面優化！不論輸入**西元曆**（如 2026-07-10）或**中華民國曆**（如 115-07-10、1150710），皆可自動識別並精準轉換。")

# ==========================================
# 🧠 核心：西元/民國智慧識別過濾器
# ==========================================
def clean_and_parse_date(date_val):
    if pd.isna(date_val):
        return None
    
    # 狀況 1：如果已經是 Excel 的日期物件或 datetime 物件
    if isinstance(date_val, (datetime, pd.Timestamp)):
        if date_val.year < 1900:
            try:
                return datetime(date_val.year + 1911, date_val.month, date_val.day)
            except:
                return None
        return date_val.to_pydatetime() if hasattr(date_val, 'to_pydatetime') else date_val
    
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
# 📌 分頁一：單日萬能查詢（已新增 A、B 獨立按鈕）
# ==========================================
with tab1:
    st.header("單日國曆轉農曆 (支援自由文字輸入)")
    st.markdown("請選擇使用 **方法 A** 或 **方法 B** 輸入，並點擊下方的按鈕進行查詢。")
    
    col_input1, col_input2 = st.columns(2)
    
    # 建立兩個獨立的按鈕狀態旗標
    target_date = None
    is_triggered = False
    
    with col_input1:
        st.subheader("📍 方法 A")
        date_picker = st.date_input("用日曆選單選擇日期：", datetime.today())
        # 在 A 下面新增按鈕
        click_a = st.button("🚀 執行方法 A 查詢", use_container_width=True)
        if click_a:
            target_date = clean_and_parse_date(date_picker)
            is_triggered = True
            
    with col_input2:
        st.subheader("📍 方法 B")
        current_minguo_str = f"{datetime.today().year - 1911}/{datetime.today().strftime('%m/%d')}"
        date_text = st.text_input("直接打字輸入（西元/民國皆可）：", value=current_minguo_str, help="例如: 115/7/10, 2026-07-10, 1150710, 民國115年7月
