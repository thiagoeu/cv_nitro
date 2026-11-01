import os
import shutil
import pytest

# Antes de qualquer import de src.core.config (app.py exige o segredo ao ser importado)
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-key")

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


class _FakeQuery:
    """Query PostgREST mínima: aplica filtros eq/limit sobre tabelas em memória."""
    def __init__(self, store, table, op, payload=None):
        self.store, self.table, self.op, self.payload = store, table, op, payload
        self.filters, self.limit_n = [], None
        store.calls.append(self)

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, n):
        self.limit_n = n
        return self

    def _match(self, row):
        return all(str(row.get(c)) == str(v) for c, v in self.filters)

    def execute(self):
        from types import SimpleNamespace
        if self.store.fail:
            raise Exception("falha simulada do Supabase")
        rows = self.store.tables.setdefault(self.table, [])
        if self.op == "insert":
            row = {"id": f"id-{len(rows) + 1}", **self.payload}
            rows.append(row)
            data = [row]
        elif self.op == "upsert":
            self.store.tables[self.table] = [r for r in rows if r.get("user_id") != self.payload.get("user_id")] + [dict(self.payload)]
            data = [self.payload]
        elif self.op == "select":
            data = [r for r in rows if self._match(r)][:self.limit_n]
        elif self.op == "update":
            data = [r for r in rows if self._match(r)]
            for r in data:
                r.update(self.payload)
        else:  # delete
            data = [r for r in rows if self._match(r)]
            self.store.tables[self.table] = [r for r in rows if not self._match(r)]
        return SimpleNamespace(data=data)

class _FakeTable:
    def __init__(self, store, name):
        self.store, self.name = store, name

    def select(self, columns="*"):
        return _FakeQuery(self.store, self.name, "select", columns)

    def insert(self, payload):
        return _FakeQuery(self.store, self.name, "insert", payload)

    def update(self, payload):
        return _FakeQuery(self.store, self.name, "update", payload)

    def upsert(self, payload):
        return _FakeQuery(self.store, self.name, "upsert", payload)

    def delete(self):
        return _FakeQuery(self.store, self.name, "delete")

class FakeSupabase:
    def __init__(self):
        self.tables, self.calls, self.fail = {}, [], False

    def table(self, name):
        return _FakeTable(self, name)

@pytest.fixture
def fake_supabase(monkeypatch):
    """Supabase em memória ligado ao history_manager (modo nuvem ativo)."""
    fake = FakeSupabase()
    monkeypatch.setattr("src.core.history_manager.is_supabase_configured", lambda: True)
    monkeypatch.setattr("src.core.history_manager.get_supabase_client", lambda: fake)
    return fake
