import os
import shutil
import pytest

@pytest.fixture(autouse=True)
def no_llm_fallback(monkeypatch):
    """Os testes mockam ChatGoogleGenerativeAI; o wrapper de fallback esconderia as chamadas ao mock."""
    monkeypatch.setattr("src.core.config.GEMINI_FALLBACK_MODEL", "")
    monkeypatch.setattr("src.core.config.GROQ_API_KEY", "")

@pytest.fixture(autouse=True)
def isolate_supabase_in_tests(monkeypatch):
    """
    Desconecta o Supabase real durante a execução de testes automatizados,
    garantindo que os testes utilizem o armazenamento local temporário
    sem inserir registros de teste na tabela de produção do usuário.
    """
    monkeypatch.setattr("src.core.history_manager.is_supabase_configured", lambda: False)
    monkeypatch.setattr("src.core.history_manager.get_supabase_client", lambda: None)

@pytest.fixture(autouse=True)
def isolate_test_history(tmp_path):
    """
    Garante que qualquer teste que utilize o history_manager utilize um diretório temporário,
    nunca poluindo a pasta 'history/' de produção do usuário.
    """
    test_dir = str(tmp_path / "test_history")
    os.makedirs(test_dir, exist_ok=True)
    
    old_val = os.environ.get("HISTORY_DIR")
    os.environ["HISTORY_DIR"] = test_dir
    
    yield test_dir
    
    # Restaura após o teste
    if old_val is not None:
        os.environ["HISTORY_DIR"] = old_val
    else:
        os.environ.pop("HISTORY_DIR", None)

