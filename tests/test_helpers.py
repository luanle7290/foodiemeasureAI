"""
Unit tests for pure helper functions in app.py.
Run with: pytest tests/test_helpers.py -v

These tests cover only functions with zero Streamlit dependency,
so no mocking of st.* is needed.
"""

import sys
import os

# Allow importing app.py from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from PIL import Image
from app import (
    escape,
    get_purine_emoji,
    get_card_class,
    get_badge_class,
    resize_image,
    format_share_text,
    PURINE_STYLES,
)


# ── escape() ──────────────────────────────────────────────────────

class TestEscape:
    def test_plain_string_unchanged(self):
        assert escape("Phở bò") == "Phở bò"

    def test_xss_script_tag(self):
        assert escape("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"

    def test_html_special_chars(self):
        assert "&" in escape("A & B") == False or escape("A & B") == "A &amp; B"

    def test_quotes_escaped(self):
        result = escape('"hello"')
        assert '"' not in result

    def test_non_string_input_coerced(self):
        assert escape(42) == "42"
        assert escape(None) == "None"


# ── get_purine_emoji / get_card_class / get_badge_class ───────────

class TestPurineStyleHelpers:
    """All three helpers delegate to PURINE_STYLES — test each level."""

    @pytest.mark.parametrize("level,expected", [
        ("low",    "🟢"),
        ("Low",    "🟢"),   # case-insensitive
        ("LOW",    "🟢"),
        ("medium", "🟡"),
        ("Medium", "🟡"),
        ("high",   "🔴"),
        ("High",   "🔴"),
        ("unknown","🔴"),   # falls back to "high" default
        ("",       "🔴"),
    ])
    def test_get_purine_emoji(self, level, expected):
        assert get_purine_emoji(level) == expected

    @pytest.mark.parametrize("level,expected", [
        ("low",    "purine-low"),
        ("medium", "purine-medium"),
        ("high",   "purine-high"),
        ("random", "purine-high"),  # default
    ])
    def test_get_card_class(self, level, expected):
        assert get_card_class(level) == expected

    @pytest.mark.parametrize("level,expected", [
        ("low",    "badge-low"),
        ("medium", "badge-medium"),
        ("high",   "badge-high"),
        ("??",     "badge-high"),   # default
    ])
    def test_get_badge_class(self, level, expected):
        assert get_badge_class(level) == expected

    def test_purine_styles_keys_complete(self):
        """PURINE_STYLES must define emoji, card, and badge for every level."""
        for level, styles in PURINE_STYLES.items():
            assert "emoji" in styles, f"Missing 'emoji' for level '{level}'"
            assert "card"  in styles, f"Missing 'card' for level '{level}'"
            assert "badge" in styles, f"Missing 'badge' for level '{level}'"


# ── resize_image() ────────────────────────────────────────────────

class TestResizeImage:
    def _make_image(self, w, h):
        return Image.new("RGB", (w, h), color=(100, 149, 237))

    def test_large_image_resized_to_max(self):
        img = self._make_image(2048, 2048)
        result = resize_image(img, max_px=1024)
        assert max(result.size) == 1024

    def test_wide_image_longest_side_bounded(self):
        img = self._make_image(2000, 800)
        result = resize_image(img, max_px=1024)
        assert result.size[0] == 1024
        assert result.size[1] < 1024

    def test_tall_image_longest_side_bounded(self):
        img = self._make_image(600, 2400)
        result = resize_image(img, max_px=1024)
        assert result.size[1] == 1024

    def test_small_image_not_upscaled(self):
        img = self._make_image(400, 300)
        result = resize_image(img, max_px=1024)
        assert result.size == (400, 300)

    def test_exact_max_size_unchanged(self):
        img = self._make_image(1024, 768)
        result = resize_image(img, max_px=1024)
        assert result.size == (1024, 768)

    def test_aspect_ratio_preserved(self):
        img = self._make_image(2000, 1000)
        result = resize_image(img, max_px=1000)
        w, h = result.size
        assert abs(w / h - 2.0) < 0.01


# ── format_share_text() ───────────────────────────────────────────

class TestFormatShareText:
    def _base_result(self, **overrides):
        base = {
            "dish_name": "Phở bò",
            "purine_level": "High",
            "gout_safety_score": 3,
            "calories": 500,
            "total_purine_mg": 320,
            "can_eat": False,
            "advice": "Hạn chế ăn món này.",
            "components": [
                {"name": "Thịt bò", "purine_level": "High", "purine_mg": 200},
            ],
            "safe_alternatives": ["Phở gà", "Bún bò chay"],
        }
        base.update(overrides)
        return base

    def test_dish_name_in_output(self):
        text = format_share_text(self._base_result())
        assert "Phở bò" in text

    def test_safe_alternatives_shown_when_cannot_eat(self):
        text = format_share_text(self._base_result(can_eat=False))
        assert "Phở gà" in text

    def test_safe_alternatives_hidden_when_can_eat(self):
        """Alternatives must NOT appear when can_eat=True."""
        text = format_share_text(self._base_result(
            can_eat=True,
            safe_alternatives=["Phở gà", "Bún chay"],
        ))
        assert "Phở gà" not in text
        assert "Bún chay" not in text

    def test_disclaimer_always_present(self):
        text = format_share_text(self._base_result())
        assert "tham khảo" in text

    def test_component_purines_listed(self):
        text = format_share_text(self._base_result())
        assert "Thịt bò" in text

    def test_missing_keys_handled_gracefully(self):
        """format_share_text must not raise on a nearly-empty result dict."""
        text = format_share_text({})
        assert isinstance(text, str)
        assert len(text) > 0

    def test_calories_shown(self):
        text = format_share_text(self._base_result(calories=450))
        assert "450" in text
