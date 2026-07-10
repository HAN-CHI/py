import streamlit as st
import pandas as pd
from datetime import datetime
from zhdate import ZhDate
import io

# 設定網頁標題與圖示
st.set_page_config(page_title="萬年曆雲端轉換系統", page_icon="📅", layout="wide")

st.title("🏮 跨世紀萬年曆自動轉換系統")
st.markdown("本系統支援 1900-2100 年之陰陽合曆精準轉換，提供**單日查詢**與**Excel 批次處理**雙模組。")

# 建立網頁分頁 (Tabs)
tab1, tab2 = st.tabs(["📌 單日快速查詢", "📊 Excel 批次轉換對照"])

# ==========================================
# 📌 分頁一：單日快速查詢
# ==========================================
with tab1:
    st.header("單日國曆轉農曆")
    # 日期選擇器组件
    input_date = st.date_input("請選擇或輸入國曆日期：", datetime.today())
    
    if input_date:
        try:
            # 轉換核心
            lunar = ZhDate.from_datetime(input_date)
            
            # 美化輸出畫面
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="輸入國曆", value=input_date.strftime('%Y-%m-%d'))
            with col2:
                st.metric(label="對應農曆", value=f"{lunar.lunar_month}月{lunar.lunar_day}日")
            with col3:
                st.metric(label="歲次干支 (生肖)", value=lunar.chinese().split()[1])
                
            st.success(st.success(f"完整結果：{lunar.chinese()}"))
        except Exception as e:
            st.error(f"轉換失敗，請確認日期是否在 1900-2100 年範圍內。")

# ==========================================
# 📊 分頁二：Excel 批次轉換
# ==========================================
with tab2:
    st.header("Excel 檔案批次轉換")
    st.markdown("請上傳包含**國曆日期欄位**的 Excel 檔案，系統會自動在右側加入農曆資訊並提供下載。")
    
    # 檔案上傳組件
    uploaded_file = st.file_uploader("請選擇要上傳的 Excel 檔案 (.xlsx, .xls)", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            # 讀取 Excel 檔案
            df = pd.read_excel(uploaded_file)
            st.write("📂 成功讀取檔案！原始資料預覽：")
            st.dataframe(df.head(5)) # 預覽前五筆
            
            # 讓使用者選擇哪一個欄位是「國曆日期」
            columns = df.columns.tolist()
            date_col = st.selectbox("請選擇包含『國曆日期』的欄位名稱：", columns)
            
            if st.button("🚀 開始批次轉換並生成報表"):
                with st.spinner('天文軌道數學公式計算中，請稍候...'):
                    
                    # 定義轉換邏輯函數
                    def convert_row(date_val):
                        try:
                            # 確保轉換為 Python datetime 物件
                            dt = pd.to_datetime(date_val).to_pydatetime()
                            lunar_obj = ZhDate.from_datetime(dt)
                            return pd.Series([
                                f"農曆{lunar_obj.lunar_month}月{lunar_obj.lunar_day}日",
                                lunar_obj.chinese().split()[1] # 取得生肖干支
                            ])
                        except:
                            return pd.Series(["無法轉換", "無法轉換"])
                    
                    # 執行批次運算，產生新欄位
                    df[['對應農曆', '歲次干支(生肖)']] = df[date_col].apply(convert_row)
                    
                    st.success("🎉 全數轉換完成！")
                    st.write("轉換後資料預覽：")
                    st.dataframe(df.head(10))
                    
                    # 將結果轉回 Excel 二進位流，供使用者下載
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='萬年曆轉換結果')
                    processed_data = output.getvalue()
                    
                    # 下載按鈕
                    st.download_button(
                        label="📥 下載轉換後的 Excel 報表",
                        data=processed_data,
                        file_name=f"萬年曆轉換結果_{datetime.now().strftime('%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
        except Exception as e:
            st.error(f"讀取檔案或轉換過程中發生錯誤: {e}")
