import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FoodieMeasure AI",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1b4332, #40916c);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .main-header h1 { margin: 0; font-size: 2.2rem; font-weight: 700; }
    .main-header p { margin: 0.4rem 0 0; opacity: 0.88; font-size: 1rem; }

    .result-card {
        background: white;
        border: 1px solid #e8e8e8;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.6rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .purine-low    { border-left: 6px solid #52b788; background: #f0faf5; }
    .purine-medium { border-left: 6px solid #f4a261; background: #fff9f2; }
    .purine-high   { border-left: 6px solid #e63946; background: #fff5f5; }

    .badge {
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-low    { background: #52b788; color: white; }
    .badge-medium { background: #f4a261; color: white; }
    .badge-high   { background: #e63946; color: white; }

    .history-item {
        background: #f8faf9;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        margin: 0.35rem 0;
        font-size: 0.88rem;
        border-left: 3px solid #40916c;
    }

    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #999;
    }
    .empty-state .icon { font-size: 4rem; }
    .empty-state p    { font-size: 1.05rem; margin-top: 0.8rem; }
    .empty-state small { font-size: 0.85rem; }

    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- API CONFIG ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Chưa cấu hình API Key. Vui lòng kiểm tra lại Secrets.")
    st.stop()

# --- SESSION STATE ---
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []

# --- HELPER FUNCTIONS ---
def get_purine_emoji(level: str) -> str:
    l = level.lower()
    if l == "low":    return "🟢"
    if l == "medium": return "🟡"
    return "🔴"

def get_card_class(level: str) -> str:
    l = level.lower()
    if l == "low":    return "purine-low"
    if l == "medium": return "purine-medium"
    return "purine-high"

def get_badge_class(level: str) -> str:
    l = level.lower()
    if l == "low":    return "badge-low"
    if l == "medium": return "badge-medium"
    return "badge-high"

# --- AI ANALYSIS ---
def analyze_food(image: Image.Image) -> dict | None:
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = """Analyze this food image carefully for someone with Gout (hyperuricemia).
Respond ONLY with valid JSON — no markdown, no extra text. Use this exact structure:

{
  "food_name": "Tên món ăn bằng tiếng Việt",
  "calories": 350,
  "purine_level": "Low",
  "purine_mg": 45,
  "gout_safety_score": 8,
  "safe_portion": "Mô tả khẩu phần an toàn bằng tiếng Việt",
  "main_ingredients": ["nguyên liệu 1", "nguyên liệu 2", "nguyên liệu 3"],
  "advice": "Lời khuyên cụ thể cho người bệnh Gout, 2-3 câu, bằng tiếng Việt.",
  "can_eat": true
}

Rules:
- purine_level must be exactly "Low", "Medium", or "High"
- calories and purine_mg are integers
- gout_safety_score is 1–10 (10 = safest for gout patients)
- can_eat is a boolean
- If the image is not food, return food_name as "Không phải thức ăn" with can_eat false
"""

    response = model.generate_content([prompt, image])
    text = response.text.strip()
    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def fallback_analyze(image: Image.Image) -> str:
    """Plain-text fallback if JSON parsing fails."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """Phân tích ảnh món ăn này cho người bị bệnh Gout. Trình bày rõ ràng bằng tiếng Việt:
1. 🍽️ Tên món ăn
2. 🔥 Ước tính Calo (kcal/khẩu phần)
3. ⚗️ Hàm lượng Purin: Thấp / Trung bình / Cao (ước tính mg/100g)
4. 🛡️ Điểm an toàn Gout (1–10, 10 = an toàn nhất)
5. 🥄 Khẩu phần an toàn đề nghị
6. 💊 Lời khuyên cho người bệnh Gout (2–3 câu)"""
    response = model.generate_content([prompt, image])
    return response.text


def display_result(result: dict):
    level     = result.get("purine_level", "Unknown")
    card_cls  = get_card_class(level)
    badge_cls = get_badge_class(level)
    emoji     = get_purine_emoji(level)
    can_eat   = result.get("can_eat", True)

    eat_tag = (
        "<span style='color:#e63946;font-weight:700'>⛔ Không nên ăn</span>"
        if not can_eat else
        "<span style='color:#52b788;font-weight:700'>✅ Có thể ăn</span>"
    )

    st.markdown(f"""
    <div class="result-card {card_cls}">
        <h2 style="margin:0 0 0.6rem 0">🍽️ {result.get('food_name', 'Không xác định')}</h2>
        <span class="badge {badge_cls}">{emoji} Purin: {level}</span>
        &nbsp;&nbsp;{eat_tag}
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("🔥 Calories",         f"{result.get('calories', '?')} kcal")
    with c2: st.metric("⚗️ Purin ước tính",   f"{result.get('purine_mg', '?')} mg/100g")
    with c3: st.metric("🛡️ Điểm an toàn Gout", f"{result.get('gout_safety_score', '?')} / 10")

    st.markdown(f"""
    <div class="result-card">
        <strong>🥄 Khẩu phần an toàn:</strong><br>
        {result.get('safe_portion', 'Không có dữ liệu')}
    </div>
    <div class="result-card">
        <strong>💊 Lời khuyên cho người Gout:</strong><br>
        {result.get('advice', '')}
    </div>
    """, unsafe_allow_html=True)

    ingredients = result.get("main_ingredients", [])
    if ingredients:
        st.markdown(f"""
        <div class="result-card">
            <strong>🧺 Nguyên liệu chính:</strong> {', '.join(ingredients)}
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🥗 FoodieMeasure AI")
    st.caption("Chuyên gia dinh dưỡng Gout · Powered by Gemini")
    st.divider()

    # Scan History
    st.markdown("#### 📋 Lịch sử quét")
    if st.session_state.scan_history:
        for item in reversed(st.session_state.scan_history[-8:]):
            emoji = get_purine_emoji(item["level"])
            st.markdown(f"""
            <div class="history-item">
                {emoji} <strong>{item['name']}</strong><br>
                <small>{item['time']} &nbsp;·&nbsp; {item['calories']} kcal</small>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("")
        if st.button("🗑️ Xóa lịch sử", use_container_width=True):
            st.session_state.scan_history = []
            st.rerun()
    else:
        st.caption("Chưa có lịch sử quét nào.")

    st.divider()

    # Quick Reference
    st.markdown("#### ⚠️ Thực phẩm cần tránh")
    for food in [
        "🦐 Hải sản: tôm, cua, sò, mực",
        "🥩 Nội tạng: gan, thận, tim, phổi",
        "🐟 Cá trích, cá mòi, cá thu",
        "🍖 Thịt đỏ nhiều: bò, dê, trâu",
        "🍺 Bia, rượu bia các loại",
        "🫘 Đậu Hà Lan, đậu lăng",
        "🍄 Nấm (nhiều loại)",
    ]:
        st.markdown(f"<small>{food}</small>", unsafe_allow_html=True)

    st.divider()

    st.markdown("#### ✅ Thực phẩm an toàn")
    for food in [
        "🥚 Trứng, sữa ít béo, phô mai",
        "🫚 Dầu olive, bơ, các loại hạt",
        "🥬 Rau xanh (trừ rau bina)",
        "🍚 Cơm, bánh mì, mì, bún",
        "🍎 Trái cây tươi (cherry tốt nhất)",
        "🍗 Thịt gà, thịt lợn (ít, không da)",
        "💧 Uống ≥ 2 lít nước mỗi ngày",
    ]:
        st.markdown(f"<small>{food}</small>", unsafe_allow_html=True)

    st.divider()
    st.caption("⚠️ Ứng dụng chỉ mang tính tham khảo. Hãy hỏi ý kiến bác sĩ cho tư vấn y tế chính thức.")


# ═══════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>🥗 FoodieMeasure AI</h1>
    <p>Phân tích dinh dưỡng thông minh dành riêng cho người bệnh Gout</p>
</div>
""", unsafe_allow_html=True)

# Input tabs
tab1, tab2 = st.tabs(["📷 Chụp ảnh trực tiếp", "📁 Tải ảnh từ thiết bị"])

image = None

with tab1:
    camera_photo = st.camera_input("Hướng camera vào món ăn và chụp")
    if camera_photo:
        image = Image.open(camera_photo)

with tab2:
    uploaded_file = st.file_uploader(
        "Chọn ảnh món ăn (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        image = Image.open(uploaded_file)

# Image preview + Analyze button
if image:
    col_img, col_btn = st.columns([3, 1])
    with col_img:
        st.image(image, caption="Ảnh món ăn", use_container_width=True)
    with col_btn:
        st.markdown("<br><br>", unsafe_allow_html=True)
        analyze_btn = st.button(
            "🔬 Phân tích ngay",
            type="primary",
            use_container_width=True
        )

    if analyze_btn:
        with st.spinner("🤖 AI đang phân tích món ăn của bạn..."):
            try:
                result = analyze_food(image)

                st.divider()
                st.markdown("## 📊 Kết quả phân tích")
                display_result(result)

                # Save to history
                st.session_state.scan_history.append({
                    "name":     result.get("food_name", "Không rõ"),
                    "level":    result.get("purine_level", "Unknown"),
                    "calories": result.get("calories", "?"),
                    "time":     datetime.now().strftime("%H:%M"),
                })

            except (json.JSONDecodeError, KeyError, TypeError):
                # Fallback to plain text if JSON fails
                st.warning("⚠️ Hiển thị kết quả dạng văn bản (chế độ dự phòng)")
                try:
                    fallback_text = fallback_analyze(image)
                    st.markdown(fallback_text)
                except Exception as e2:
                    st.error(f"❌ Không thể phân tích: {e2}")

            except Exception as e:
                st.error(f"❌ Lỗi kết nối AI: {str(e)}")

else:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🍜</div>
        <p>Chụp ảnh hoặc tải ảnh món ăn lên để bắt đầu phân tích</p>
        <small>FoodieMeasure AI sẽ phân tích hàm lượng Purin và đưa ra lời khuyên dinh dưỡng phù hợp cho người bệnh Gout</small>
    </div>
    """, unsafe_allow_html=True)
