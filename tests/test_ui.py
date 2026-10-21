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
