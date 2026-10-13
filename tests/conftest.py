import os
import shutil
import pytest

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
