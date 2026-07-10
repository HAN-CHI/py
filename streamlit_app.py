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
        # 有時候 Excel 把民國 115 年誤認成西元 0115 年，在這邊校正
        if date_val.year < 1900:
            try:
                return datetime(date_val.year + 1911, date_val.month, date_val.day)
            except:
                return None
        return date_val.to_pydatetime() if hasattr(date_val, 'to_pydatetime') else date_val
    
    # 狀況 2：如果是純數字（例如 Excel 裡的 1150710 變成 float/int）
    if isinstance(date_val, (int, float)):
        date_val = str(int(date_val))
        
    # 狀況 3：如果是字串（最常見，各種亂七八糟格式）
    if isinstance(date_val, str):
        text = date_val.strip()
        # 濾掉中文前綴
        text = text.replace("民國", "").replace("西元", "").replace("Minguo", "")
        # 把中文字轉換為常規分隔符
        text = text.replace("年", "-").replace("月", "-").replace("日", "")
        
        # 用正規表示式抓出裡面所有的數字群
        nums = re.findall(r'\d+', text)
        
        # 如果有三個數字群 (年月日)
        if len(nums) == 3:
            y, m, d = int(nums[0]), int(nums[1]), int(nums[2])
            if y < 1900:  # 判定為民國年
                y += 1911
            try:
                return datetime(y, m, d)
            except:
                return None
                
        # 如果數字是連在一起的 (例如 1150710 或 20260710)
        elif len(nums) == 1 and len(nums[0]) in [6, 7, 8]:
            s = nums[0]
            try:
                if len(s) == 7:    # 民國 3 位數年: 1150710
                    return datetime(int(s[:3]) + 1911, int(s[3:5]), int(s[5:]) or 1)
                elif len(s) == 6:  # 民國 2 位數年: 990710
                    return datetime(int(s[:2]) + 1911, int(s[2:4]), int(s[4:]) or 1)
                elif len(s) == 8:  # 西元 4 位數年: 20260710
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
    st.markdown("你可以用滑鼠選日期，或者在下方**直接打字**（支援民國或西元格式）。")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        date_picker = st.date_input("方法 A：用日曆選單選擇", datetime.today())
    with col_input2:
        # 提供台灣人最愛的文字輸入範例
        current_minguo_str = f"{datetime.today().year - 1911}/{datetime.today().strftime('%m/%d')}"
        date_text = st.text_input("方法 B：直接打字輸入（西元/民國皆可）", value=current_minguo_str, help="例如: 115/7/10, 2026-07-10, 1150710, 民國115年7月10日")
    
    # 優先採用打字的內容，如果沒打字就用選單的
    target_date = None
    if date_text:
        target_date = clean_and_parse_date(date_text)
    else:
        target_date = clean_and_parse_date(date_picker)
        
    if target_date:
        try:
            # 轉換為農曆
            lunar = ZhDate.from_datetime(target_date)
            minguo_year = target_date.year - 1911
            
            st.markdown("---")
            st.subheader("🔮 智慧解析對照結果：")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric(label="解析後西元國曆", value=target_date.strftime('%Y-%m-%d'))
            with c2:
                st.metric(label="對應中華民國曆", value=f"民國 {minguo_year} 年")
            with c3:
                st.metric(label="計算後農曆", value=f"{lunar.lunar_month}月{lunar.lunar_day}日")
            with c4:
                st.metric(label="歲次干支 (生肖)", value=lunar.chinese().split()[1])
                
            st.success(f"💡 完整農曆資訊：{lunar.chinese()}")
        except Exception as e:
            st.error("❌ 經解析後的年份超出農曆計算範圍 (必須在西元 1900~2100 年之間)！")
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
                    
                    # 批量轉換邏輯
                    def batch_convert(row_val):
                        dt = clean_and_parse_date(row_val)
                        if dt:
                            try:
                                mingo = f"民國 {dt.year - 1911} 年"
                                lunar_obj = ZhDate.from_datetime(dt)
                                return pd.Series([
                                    dt.strftime('%Y-%m-%d'),
                                    mingo,
                                    f"農曆{lunar_obj.lunar_month}月{lunar_obj.lunar_day}日",
                                    lunar_obj.chinese().split()[1]
                                ])
                            except:
                                return pd.Series(["超出計算範圍", "無法計算", "無法計算", "無法計算"])
                        else:
                            return pd.Series(["格式錯誤", "無法識別", "無法識別", "無法識別"])
                    
                    # 產生 4 個全新的標準化對照欄位
                    df[['標準西元', '標準民國', '轉換農曆', '歲次干支(生肖)']] = df[date_col].apply(batch_convert)
                    
                    st.success("🎉 東西全算好了！民國和西元都幫你整理得整整齊齊！")
                    st.dataframe(df.head(10))
                    
                    # 打包下載
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='智慧萬年曆結果')
                    processed_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 下載轉換後的通用萬年曆 Excel",
                        data=processed_data,
                        file_name=f"通用萬年曆轉換結果_{datetime.now().strftime('%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
        except Exception as e:
            st.error(f"💥 處理檔案時發生預期外的錯誤: {e}")
