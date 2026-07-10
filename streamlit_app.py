import streamlit as st
import pandas as pd
from datetime import datetime
from zhdate import ZhDate

# 設定網頁標題
st.set_page_config(page_title="快速堪輿煞方查詢", layout="wide")

# 核心邏輯：計算該年三煞方
def get_year_three_shashang(lunar_year):
    branch_idx = (lunar_year - 4) % 12
    zodiacs = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]
    zodiac = zodiacs[branch_idx]
    if zodiac in ["虎", "馬", "狗"]: return "北方"
    if zodiac in ["猴", "鼠", "龍"]: return "南方"
    if zodiac in ["豬", "兔", "羊"]: return "西方"
    if zodiac in ["蛇", "雞", "牛"]: return "東方"
    return "無"

# 核心邏輯：計算該月月煞方
def get_lunar_month_shashang(lunar_month):
    mapping = {1:"北方", 5:"北方", 9:"北方", 2:"西方", 6:"西方", 10:"西方", 
               3:"南方", 7:"南方", 11:"南方", 4:"東方", 8:"東方", 12:"東方"}
    return mapping.get(lunar_month, "無")

# 核心邏輯：根據生肖推算吉方
def get_tower_orientation(zodiac):
    data = {
        "鼠": {"吉方": ["北", "東"], "煞方": ["南"]},
        "牛": {"吉方": ["北", "西"], "煞方": ["西南"]},
        "虎": {"吉方": ["東", "南"], "煞方": ["西"]},
        "兔": {"吉方": ["東", "北"], "煞方": ["西"]},
        "龍": {"吉方": ["東", "北"], "煞方": ["西北"]},
        "蛇": {"吉方": ["南", "西"], "煞方": ["西北"]},
        "馬": {"吉方": ["南", "西"], "煞方": ["北"]},
        "羊": {"吉方": ["南", "東"], "煞方": ["東北"]},
        "猴": {"吉方": ["西", "北"], "煞方": ["東"]},
        "雞": {"吉方": ["西", "南"], "煞方": ["東"]},
        "狗": {"吉方": ["西", "南"], "煞方": ["東南"]},
        "豬": {"吉方": ["北", "東"], "煞方": ["北"]}
    }
    return data.get(zodiac, {"吉方": [], "煞方": []})

# --- UI 介面 ---
st.header("🦁 快速煞方對照查詢 (以日期為主)")
user_date = st.date_input("請選擇日期：")

if st.button("🚀 查詢該日煞方資訊"):
    # 轉換為農曆
    lunar_obj = ZhDate.from_datetime(datetime(user_date.year, user_date.month, user_date.day))
    
    # 計算各項煞方
    y_shashang = get_year_three_shashang(lunar_obj.lunar_year)
    m_shashang = get_lunar_month_shashang(lunar_obj.lunar_month)
    
    # 取得當年年份生肖 (用於展示參考)
    branch_idx = (lunar_obj.lunar_year - 4) % 12
    zodiacs = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]
    current_year_zodiac = zodiacs[branch_idx]
    
    st.markdown("---")
    st.info(f"📅 **查詢日期：{user_date} (農曆 {lunar_obj.lunar_month} 月)**")
    
    # 顯示煞方資訊
    col1, col2 = st.columns(2)
    with col1:
        st.metric("本年三煞方 (流年)", y_shashang)
    with col2:
        st.metric("本月月煞方", m_shashang)
        
    st.markdown("---")
    st.write("### 💡 實務提醒：")
    st.write(f"1. **流年資訊**：{user_date.year} 年為{current_year_zodiac}年。")
    st.write(f"2. **避煞原則**：挑選塔位時，請務必避開【{y_shashang}】(年煞) 與【{m_shashang}】(月煞) 方向。")
    st.write("3. **生肖確認**：若後續取得使用人生肖，可再對應其本命吉方篩選。")
