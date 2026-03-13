import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. CẤU HÌNH BẢO MẬT ---
# Khi chạy local: File này sẽ tìm key trong thư mục .streamlit/secrets.toml
# Khi deploy: File này sẽ tìm key trong phần 'Secrets' của Streamlit Cloud
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Chưa cấu hình API Key. Vui lòng kiểm tra lại Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. GIAO DIỆN APP ---
st.set_page_config(page_title="Foodiemeasure AI", page_icon="🥗")
st.title("🥗 Foodiemeasure AI")
st.markdown("### Chuyên gia dinh dưỡng cho người bị Gout")

uploaded_file = st.file_uploader("Chụp hoặc chọn ảnh món ăn...", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Ảnh đã tải lên', use_container_width=True)
    
    if st.button("Phân tích dinh dưỡng"):
        with st.spinner('Đang kết nối với trí tuệ nhân tạo...'):
            try:
                # Dùng model Flash để tốc độ nhanh nhất (Free)
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                prompt = """Phân tích ảnh món ăn này cho người bị bệnh Gout:
                1. Tên món ăn.
                2. Ước tính Calo (kcal).
                3. Hàm lượng Purin (Thấp/Trung bình/Cao) và lời khuyên.
                Trình bày xuống dòng sạch sẽ, có icon 🍴, 🔥, ⚠️."""
                
                response = model.generate_content([prompt, image])
                st.success("Hoàn tất!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Lỗi phân tích: {e}")