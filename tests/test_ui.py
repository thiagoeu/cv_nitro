from src.ui.diagnostic_view import render_ats_diagnostic_panel
from unittest.mock import patch, MagicMock

def test_diagnostic_panel_with_data():
    sample_diagnostic = {
        "ats_score": 92,
        "matched_keywords": ["Python", "FastAPI", "Docker"],
        "applied_changes": ["Formatação em Markdown ATS", "Habilidades em 2 colunas"],
        "reviewer_summary": "Currículo atende plenamente aos requisitos da vaga."
    }
    
    def fake_columns(spec):
        count = len(spec) if isinstance(spec, list) else spec
        return [MagicMock() for _ in range(count)]

    with patch("streamlit.metric") as mock_metric, \
         patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.info") as mock_info, \
         patch("streamlit.columns", side_effect=fake_columns):
        render_ats_diagnostic_panel(sample_diagnostic)
        assert mock_metric.called
        assert mock_info.called

def test_diagnostic_panel_with_empty_data():
    with patch("streamlit.info") as mock_info:
        render_ats_diagnostic_panel({})
        assert mock_info.called

def test_theme_tokens_and_apply_theme():
    from src.ui.components import THEME_TOKENS, apply_theme
    assert THEME_TOKENS["bg_neutral"] == "#F8FAFC"
    assert THEME_TOKENS["bg_surface"] == "#F1F5F9"
    assert THEME_TOKENS["text_primary"] == "#0F172A"
    assert THEME_TOKENS["border"] == "#CBD5E1"
    assert THEME_TOKENS["accent_mint"] == "#10B981"
    assert THEME_TOKENS["accent_cyan"] == "#0EA5E9"

    with patch("streamlit.markdown") as mock_markdown:
        apply_theme()
        assert mock_markdown.called
        css_injected = mock_markdown.call_args[0][0]
        assert "#CBD5E1" in css_injected
        assert "#10B981" in css_injected
