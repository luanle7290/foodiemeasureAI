import streamlit as st
from google import genai
from PIL import Image, UnidentifiedImageError
import json
import re
import html as html_lib
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FoodieMeasure AI",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed"   # collapsed by default for mobile
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

    .component-row {
        background: #f8faf9;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        font-size: 0.9rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .alt-chip {
        display: inline-block;
        background: #e8f5e9;
        color: #1b4332;
        border: 1px solid #52b788;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        margin: 0.2rem 0.2rem 0.2rem 0;
        font-size: 0.85rem;
        font-weight: 600;
    }

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
    _genai_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Chưa cấu hình API Key. Vui lòng kiểm tra lại Secrets.")
    st.stop()

# --- CONSTANTS ---
DAILY_SCAN_LIMIT = 20   # max scans per session (soft quota guard)
HISTORY_MAX      = 50   # max entries kept in scan history

# --- SESSION STATE ---
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []
if "scan_count" not in st.session_state:
    st.session_state.scan_count = 0

# --- HELPER FUNCTIONS ---
def escape(text) -> str:
    """HTML-escape a value before injecting into unsafe_allow_html blocks."""
    return html_lib.escape(str(text))

# ── Purine level → visual styles (single source of truth) ──────────
#
#   PURINE_STYLES["low"|"medium"|"high"] = {emoji, card, badge}
#   _DEFAULT_STYLE used when level is unknown / unexpected.
#
PURINE_STYLES = {
    "low":    {"emoji": "🟢", "card": "purine-low",    "badge": "badge-low"},
    "medium": {"emoji": "🟡", "card": "purine-medium", "badge": "badge-medium"},
    "high":   {"emoji": "🔴", "card": "purine-high",   "badge": "badge-high"},
}
_DEFAULT_STYLE = PURINE_STYLES["high"]

def get_purine_emoji(level: str) -> str:
    return PURINE_STYLES.get(level.lower(), _DEFAULT_STYLE)["emoji"]

def get_card_class(level: str) -> str:
    return PURINE_STYLES.get(level.lower(), _DEFAULT_STYLE)["card"]

def get_badge_class(level: str) -> str:
    return PURINE_STYLES.get(level.lower(), _DEFAULT_STYLE)["badge"]


def safe_open_image(file_obj) -> "Image.Image | None":
    """
    Open an uploaded file as a PIL Image.
    Returns None (and shows a Streamlit error) on corrupt / unreadable files.
    Always converts to RGB so WEBP alpha channels don't trip up the Gemini API.
    """
    try:
        img = Image.open(file_obj)
        img.load()                  # force full decode — catches truncated files early
        return img.convert("RGB")   # normalise to RGB (handles WEBP, RGBA, P-mode, etc.)
    except UnidentifiedImageError:
        st.error("⚠️ Tệp ảnh không hợp lệ. Vui lòng chọn ảnh JPG, PNG hoặc WEBP hợp lệ.")
    except Image.DecompressionBombError:
        st.error("⚠️ Ảnh quá lớn để xử lý. Vui lòng chọn ảnh có kích thước nhỏ hơn.")
    except Exception:
        st.error("⚠️ Không thể đọc tệp ảnh. Vui lòng thử lại với ảnh khác.")
    return None


def resize_image(image: Image.Image, max_px: int = 1024) -> Image.Image:
    """Resize image so its longest side is at most max_px."""
    w, h = image.size
    if max(w, h) > max_px:
        scale = max_px / max(w, h)
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return image


def format_share_text(result: dict) -> str:
    """Format analysis result as plain text for sharing via Zalo/Messenger."""
    dish   = result.get("dish_name", result.get("food_name", "Không rõ"))
    level  = result.get("purine_level", "?")
    emoji  = get_purine_emoji(level)
    score  = result.get("gout_safety_score", "?")
    cals   = result.get("calories", "?")
    total  = result.get("total_purine_mg", result.get("purine_mg", "?"))
    can    = result.get("can_eat", True)
    advice = result.get("advice", "")

    lines = [
        "🥗 FoodieMeasure AI — Kết quả phân tích",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🍽️  Món ăn : {dish}",
        f"🔥  Calo   : {cals} kcal",
        f"⚗️  Purin  : {total} mg (ước tính)",
        f"{emoji}  Mức Purin: {level}",
        f"🛡️  An toàn: {score}/10",
        "",
    ]

    components = result.get("components", [])
    if components:
        lines.append("📋 Thành phần:")
        for c in components:
            e = get_purine_emoji(c.get("purine_level", "Low"))
            lines.append(f"   {e} {c.get('name','')} — ~{c.get('purine_mg','?')} mg")
        lines.append("")

    lines.append("⛔ Không nên ăn" if not can else "✅ Có thể ăn")

    alts = result.get("safe_alternatives", [])
    if alts and not can:
        lines.append(f"✅ Thay thế an toàn: {', '.join(alts)}")

    lines += ["", f"💊 Lời khuyên: {advice}", "",
              "⚠️ Chỉ mang tính tham khảo. Hỏi bác sĩ để được tư vấn y tế."]
    return "\n".join(lines)


# --- AI ANALYSIS ---
def analyze_food(image: Image.Image) -> dict:
    prompt = """Analyze this food image carefully for someone with Gout (hyperuricemia).
Identify ALL visible food components and ingredients in the dish.
Respond ONLY with valid JSON — no markdown, no extra text. Use this exact structure:

{
  "dish_name": "Tên món ăn tổng thể bằng tiếng Việt",
  "components": [
    {
      "name": "Tên thành phần bằng tiếng Việt",
      "purine_level": "Low",
      "purine_mg": 15,
      "note": "Ghi chú ngắn nếu cần (hoặc chuỗi rỗng)"
    }
  ],
  "total_purine_mg": 180,
  "calories": 450,
  "purine_level": "High",
  "gout_safety_score": 4,
  "safe_portion": "Mô tả khẩu phần an toàn bằng tiếng Việt",
  "advice": "Lời khuyên cụ thể 2–3 câu bằng tiếng Việt.",
  "can_eat": false,
  "safe_alternatives": ["Món thay thế 1", "Món thay thế 2", "Món thay thế 3"],
  "main_ingredients": ["nguyên liệu 1", "nguyên liệu 2", "nguyên liệu 3"]
}

Rules:
- purine_level (dish-level AND per component) must be exactly "Low", "Medium", or "High"
- components: list every distinct food component visible in the image (max 8 items)
- total_purine_mg: sum of component purines for a normal serving portion (integer)
- calories and purine_mg values are integers
- gout_safety_score: 1–10 (10 = safest for gout patients)
- can_eat: boolean
- safe_alternatives: 3 similar but gout-safer dishes — ONLY when can_eat is false; use [] when can_eat is true
- If the image is not food, return dish_name as "Không phải thức ăn", can_eat false, empty components []
"""

    response = _genai_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt, image],
    )

    # Guard: Gemini occasionally returns an empty / blocked response
    if not response.text:
        raise ValueError("Gemini trả về phản hồi trống. Vui lòng thử lại.")

    text = response.text.strip()
    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def fallback_analyze(image: Image.Image) -> str:
    """Plain-text fallback if JSON parsing fails."""
    prompt = """Phân tích ảnh món ăn này cho người bị bệnh Gout. Liệt kê từng thành phần thấy được, hàm lượng Purin của từng thành phần, rồi trình bày rõ ràng bằng tiếng Việt:
1. 🍽️ Tên món ăn
2. 📋 Thành phần & Purin từng loại (Thấp/Trung bình/Cao)
3. ⚗️ Tổng Purin ước tính (mg/khẩu phần)
4. 🔥 Ước tính Calo (kcal/khẩu phần)
5. 🛡️ Điểm an toàn Gout (1–10, 10 = an toàn nhất)
6. 🥄 Khẩu phần an toàn đề nghị
7. ✅ Món thay thế an toàn (nếu món này không nên ăn)
8. 💊 Lời khuyên cho người bệnh Gout (2–3 câu)"""
    response = _genai_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt, image],
    )
    if not response.text:
        raise ValueError("Gemini fallback returned an empty response.")
    return response.text


def display_result(result: dict):
    level     = result.get("purine_level", "Unknown")
    card_cls  = get_card_class(level)
    badge_cls = get_badge_class(level)
    emoji     = get_purine_emoji(level)
    can_eat   = result.get("can_eat", True)
    dish_name = escape(result.get("dish_name", result.get("food_name", "Không xác định")))

    eat_tag = (
        "<span style='color:#e63946;font-weight:700'>⛔ Không nên ăn</span>"
        if not can_eat else
        "<span style='color:#52b788;font-weight:700'>✅ Có thể ăn</span>"
    )

    # ── Header card ──────────────────────────────────────────────
    st.markdown(f"""
    <div class="result-card {card_cls}">
        <h2 style="margin:0 0 0.6rem 0">🍽️ {dish_name}</h2>
        <span class="badge {badge_cls}">{emoji} Purin: {escape(level)}</span>
        &nbsp;&nbsp;{eat_tag}
    </div>
    """, unsafe_allow_html=True)

    # ── Metrics ───────────────────────────────────────────────────
    total_purine = result.get("total_purine_mg", result.get("purine_mg", "?"))
    c1, c2 = st.columns(2)
    with c1: st.metric("🔥 Calories", f"{result.get('calories', '?')} kcal")
    with c2: st.metric("⚗️ Purin ước tính", f"{total_purine} mg / khẩu phần")

    # ── Safety score meter ────────────────────────────────────────
    score = result.get("gout_safety_score", 5)
    try:
        score_int = int(score)
        score_int = max(1, min(10, score_int))   # clamp — AI may return out-of-range values
    except (ValueError, TypeError):
        score_int = 5

    if score_int >= 8:
        meter_label = f"🛡️ Điểm an toàn: {score_int}/10 — ✅ Rất an toàn"
    elif score_int >= 5:
        meter_label = f"🛡️ Điểm an toàn: {score_int}/10 — ⚠️ Cần thận"
    else:
        meter_label = f"🛡️ Điểm an toàn: {score_int}/10 — ❌ Nguy hiểm"

    st.progress(score_int / 10, text=meter_label)

    # ── Component breakdown ───────────────────────────────────────
    components = result.get("components", [])
    if components:
        st.markdown("**📋 Thành phần trong món:**")
        for comp in components:
            comp_level  = comp.get("purine_level", "Low")
            comp_emoji  = get_purine_emoji(comp_level)
            comp_badge  = get_badge_class(comp_level)
            comp_name   = escape(comp.get("name", ""))
            comp_mg     = escape(str(comp.get("purine_mg", "?")))
            comp_note   = escape(comp.get("note", ""))
            note_html   = f"<br><small style='color:#888'>{comp_note}</small>" if comp_note else ""
            st.markdown(f"""
            <div class="component-row">
                <span>{comp_emoji} <strong>{comp_name}</strong>{note_html}</span>
                <span class="badge {comp_badge}">~{comp_mg} mg</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("")

    # ── Safe alternatives (only when can't eat) ───────────────────
    alts = result.get("safe_alternatives", [])
    if alts and not can_eat:
        chips = "".join(
            f'<span class="alt-chip">✅ {escape(a)}</span>' for a in alts
        )
        st.markdown(f"""
        <div class="result-card" style="border-left:6px solid #52b788; background:#f0faf5">
            <strong>💡 Món thay thế an toàn cho Gout:</strong><br><br>
            {chips}
        </div>
        """, unsafe_allow_html=True)

    # ── Safe portion & advice ─────────────────────────────────────
    safe_portion = escape(result.get("safe_portion", "Không có dữ liệu"))
    advice       = escape(result.get("advice", ""))
    st.markdown(f"""
    <div class="result-card">
        <strong>🥄 Khẩu phần an toàn:</strong><br>{safe_portion}
    </div>
    <div class="result-card">
        <strong>💊 Lời khuyên cho người Gout:</strong><br>{advice}
    </div>
    """, unsafe_allow_html=True)

    # ── Share result ──────────────────────────────────────────────
    with st.expander("📤 Chia sẻ kết quả (copy để gửi Zalo / Messenger)"):
        st.text_area(
            label="Chọn tất cả và copy:",
            value=format_share_text(result),
            height=260,
            label_visibility="collapsed",
        )


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
                {emoji} <strong>{escape(item['name'])}</strong><br>
                <small>{escape(item['time'])} &nbsp;·&nbsp; {escape(str(item['calories']))} kcal</small>
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
        st.caption(food)

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
        st.caption(food)

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

# Mobile quick-reference expander
with st.expander("⚠️ Xem thực phẩm cần tránh & an toàn cho Gout"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Cần tránh**")
        for food in [
            "🦐 Hải sản: tôm, cua, sò, mực",
            "🥩 Nội tạng: gan, thận, tim, phổi",
            "🐟 Cá trích, cá mòi, cá thu",
            "🍖 Thịt đỏ nhiều: bò, dê, trâu",
            "🍺 Bia, rượu bia các loại",
            "🫘 Đậu Hà Lan, đậu lăng",
            "🍄 Nấm (nhiều loại)",
        ]:
            st.caption(food)
    with col_b:
        st.markdown("**An toàn**")
        for food in [
            "🥚 Trứng, sữa ít béo, phô mai",
            "🫚 Dầu olive, bơ, các loại hạt",
            "🥬 Rau xanh (trừ rau bina)",
            "🍚 Cơm, bánh mì, mì, bún",
            "🍎 Trái cây tươi (cherry tốt nhất)",
            "🍗 Thịt gà, thịt lợn (ít, không da)",
            "💧 Uống ≥ 2 lít nước mỗi ngày",
        ]:
            st.caption(food)

st.markdown("---")

# ── Input mode ────────────────────────────────────────────────────
image = None

input_mode = st.radio(
    "Chọn cách nhập ảnh:",
    ["📷 Chụp ảnh trực tiếp", "📁 Tải ảnh từ thiết bị"],
    horizontal=True,
    label_visibility="collapsed"
)

if input_mode == "📷 Chụp ảnh trực tiếp":
    camera_photo = st.camera_input("Hướng camera vào món ăn và chụp", label_visibility="collapsed")
    if camera_photo:
        image = safe_open_image(camera_photo)
else:
    uploaded_file = st.file_uploader(
        "Chọn ảnh món ăn (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        image = safe_open_image(uploaded_file)

# ── Preview + Analyze ─────────────────────────────────────────────
if image:
    image = resize_image(image)   # resize before display and API call
    st.image(image, caption="Ảnh món ăn", use_container_width=True)

    # ── Session quota guard ───────────────────────────────────────
    if st.session_state.scan_count >= DAILY_SCAN_LIMIT:
        st.warning(
            f"⚠️ Bạn đã phân tích {DAILY_SCAN_LIMIT} món trong phiên này. "
            "Vui lòng làm mới trang để tiếp tục."
        )
    else:
        analyze_btn = st.button(
            "🔬 Phân tích ngay",
            type="primary",
            use_container_width=True
        )

        if analyze_btn:
            with st.spinner("🤖 AI đang phân tích món ăn của bạn... (thường mất 5–10 giây)"):
                try:
                    result = analyze_food(image)

                    st.divider()
                    st.markdown("## 📊 Kết quả phân tích")
                    with st.container(border=True):
                        display_result(result)

                    # Save to history (capped at HISTORY_MAX)
                    st.session_state.scan_history.append({
                        "name":     result.get("dish_name", result.get("food_name", "Không rõ")),
                        "level":    result.get("purine_level", "Unknown"),
                        "calories": result.get("calories", "?"),
                        "time":     datetime.now().strftime("%d/%m %H:%M"),
                    })
                    st.session_state.scan_history = st.session_state.scan_history[-HISTORY_MAX:]
                    st.session_state.scan_count += 1

                except (json.JSONDecodeError, KeyError, TypeError):
                    st.warning("⚠️ Hiển thị kết quả dạng văn bản (chế độ dự phòng)")
                    try:
                        fallback_text = fallback_analyze(image)
                        st.markdown(fallback_text)
                    except Exception as e2:
                        st.error(f"❌ Không thể phân tích: {e2}")

                except Exception as e:
                    err = str(e)
                    if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                        st.error("⏱️ Đã đạt giới hạn yêu cầu API. Vui lòng đợi 1 phút rồi thử lại.")
                        st.info("💡 Mẹo: Gemini miễn phí cho phép 15 yêu cầu/phút. Thử lại sau ít giây.")
                    else:
                        st.error(f"❌ Lỗi kết nối AI: {err}")

else:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🍜</div>
        <p>Chụp ảnh hoặc tải ảnh món ăn lên để bắt đầu phân tích</p>
        <small>FoodieMeasure AI sẽ phân tích từng thành phần món ăn, hàm lượng Purin và đưa ra lời khuyên dinh dưỡng phù hợp cho người bệnh Gout</small>
    </div>
    """, unsafe_allow_html=True)
