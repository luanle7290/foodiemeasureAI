"""
pytest configuration for FoodieMeasure AI tests.

app.py executes top-level Streamlit calls (st.set_page_config, st.secrets, etc.)
at import time. We stub the entire streamlit and google.generativeai modules
before any test imports app.py, so pure helper functions can be tested without
a running Streamlit server or a real API key.
"""

import sys
import types
import unittest.mock as mock


def _make_streamlit_stub():
    """Return a MagicMock that looks enough like streamlit to survive app.py import."""
    st = mock.MagicMock()

    # st.secrets behaves like a dict — "GOOGLE_API_KEY" in st.secrets must return True
    st.secrets = {"GOOGLE_API_KEY": "test-key-not-real"}

    # st.stop() raises SystemExit so app.py doesn't continue past the API-key guard
    st.stop.side_effect = SystemExit(0)

    # st.columns(n) must return an iterable of n MagicMocks so tuple-unpacking works.
    # e.g.  col_a, col_b = st.columns(2)
    def _columns(n, *args, **kwargs):
        return [mock.MagicMock() for _ in range(n)]
    st.columns.side_effect = _columns

    # st.radio / st.expander / st.sidebar must also return context-manager-compatible mocks
    st.sidebar.__enter__ = mock.MagicMock(return_value=mock.MagicMock())
    st.sidebar.__exit__ = mock.MagicMock(return_value=False)

    return st


def _make_genai_stub():
    """Minimal stub for google.generativeai so the import doesn't fail."""
    genai = types.ModuleType("google.generativeai")
    genai.configure = mock.MagicMock()
    genai.GenerativeModel = mock.MagicMock()
    return genai


# Install stubs before any test module imports app.py
_st_stub = _make_streamlit_stub()
sys.modules.setdefault("streamlit", _st_stub)

_genai_stub = _make_genai_stub()
sys.modules.setdefault("google.generativeai", _genai_stub)
# google namespace package
_google = types.ModuleType("google")
_google.generativeai = _genai_stub
sys.modules.setdefault("google", _google)
