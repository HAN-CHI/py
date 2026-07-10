import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from zhdate import ZhDate
import io
import re

# 設定網頁標題
st.set_page_config(page_title="專業堪輿塔位決策系統", layout="wide")

if 'latest_date' not in st.session_state:
    st.session_state['latest_date'] = date.today()

# ==========================================
# 🔮 核心演算法：年煞、月煞、生肖吉方
# ==========================================

# 1. 計算該年三煞方 (依據地支三合)
def get_year_three_shashang(lunar_year):
    branch_idx = (lunar_year - 4) % 12
    zodiacs = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]
    zodiac = zodiacs[branch_idx]
    
    if zodiac in ["虎", "馬", "狗"]: return "北方"
    if zodiac in ["猴", "鼠", "龍"]: return "南方"
    if zodiac in ["豬", "兔", "羊"]: return "西方"
    if zodiac in ["蛇", "雞", "牛"]: return "東方"
    return "無"

# 2. 計算該月月煞方
def get_lunar_month_shashang(lunar_month):
    mapping = {1:"北方", 5:"北方", 9:"北方", 2:"西方", 6:"西方", 10:"西方", 
               3:"南方", 7:"南方", 11:"南方", 4:"東方", 8:"東方", 12:"東方"}
    return mapping.get(lunar_month, "無")

# 3. 生肖吉方資料庫
def get_tower_orientation(zodiac):
    data = {
        "鼠": {"吉方": ["正北", "正東"], "次吉": ["正西"], "煞方": ["正南"]},
        "牛": {"吉方": ["北", "西"], "次吉": ["東南"], "煞方": ["西南"]},
        "虎": {"吉方": ["東", "南"], "次吉": ["西北"], "煞方": ["正西"]},
        "兔": {"吉方": ["正東", "正北"], "次吉": ["正南"], "煞方": ["正西"]},
        "龍": {"吉方": ["東", "北"], "次吉": ["西"], "煞方": ["西北"]},
        "蛇": {"吉方": ["南", "西"], "次吉": ["東北"], "煞方": ["西北"]},
        "馬": {"吉方": ["正南", "正西"], "次吉": ["正東"], "煞方": ["正北"]},
        "羊": {"吉方": ["南", "東"], "次吉": ["西北"], "煞方": ["東北"]},
        "猴": {"吉方": ["西", "北"], "次吉": ["東南"], "煞方": ["正東"]},
        "雞": {"吉方": ["正西", "正南"], "次吉": ["東南"], "煞方": ["正東"]},
        "狗": {"吉方": ["西", "南"], "次吉": ["東北"], "煞方": ["東南"]},
        "豬": {"吉方": ["北", "東"], "次吉": ["西南"], "煞方": ["正北"]}
    }
    return data.get(zodiac, {"吉方": [], "次吉": [], "煞方": []})

# ==========================================
# 🦁 分頁：專業塔位決策 (核心)
# ==========================================
st.header("🦁 專業塔位擇位決策系統")
col1, col2 = st.columns(2)

with col1:
    user_date = st.date_input("選擇進塔日期：")
    user_zodiac = st.selectbox("請選擇『往生者』本命生肖：", 
                               ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"])

if st.button("🚀 進行風水與煞方交叉比對"):
    lunar_obj = ZhDate.from_datetime(datetime(user_date.year, user_date.month, user_date.day))
    year_shashang = get_year_three_shashang(lunar_obj.lunar_year)
    month_shashang = get_lunar_month_shashang(lunar_obj.lunar_month)
    orientations = get_tower_orientation(user_zodiac)
    
    st.markdown("---")
    st.subheader(f"分析報告：{user_date.year}年(流年三煞{year_shashang}) / 農曆{lunar_obj.lunar_month}月(月煞{month_shashang})")
    
    # 邏輯判斷：將吉方與煞方比對
    final_recs = []
    for g in orientations["吉方"]:
        if g not in [year_shashang, month_shashang] and g not in orientations["煞方"]:
            final_recs.append(f"🟢 {g} (適合)")
        else:
            final_recs.append(f"❌ {g} (與年/月煞衝突)")
            
    st.write("### ✅ 針對該逝者生肖的吉方篩選結果：")
    st.write(final_recs)
    
    st.warning(f"⚠️ 注意：該年三煞方為【{year_shashang}】，該月月煞方為【{month_shashang}】。塔位若朝向此方位，應依實務避開。")
