import pytest
from unittest.mock import patch, MagicMock
import app

def test_app_views_smoke():
    with patch("streamlit.sidebar.radio", return_value="📊 Dashboard Executivo"), \
         patch("streamlit.sidebar.title"), \
         patch("streamlit.sidebar.caption"), \
         patch("streamlit.sidebar.markdown"), \
         patch("streamlit.sidebar.subheader"), \
         patch("src.core.history_manager.list_resumes", return_value=[]), \
         patch("streamlit.markdown"), \
         patch("streamlit.caption"), \
         patch("streamlit.info"):
        
        # Test sidebar
        page = app.render_sidebar()
        assert page == "📊 Dashboard Executivo"

        # Test empty dashboard
        app.render_dashboard([])

        # Test settings
        app.render_settings()

        # Test empty applications list
        app.render_applications_list([])
