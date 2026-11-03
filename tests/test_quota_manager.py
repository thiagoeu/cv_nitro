from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from src.core import quota_manager


class DummyModel(BaseModel):
    title: str
    items: list[str]


def test_record_and_get_quota_status(tmp_path):
    qfile = tmp_path / "quota.json"
    status_initial = quota_manager.get_quota_status(qfile)
    assert status_initial["gemini"]["remaining_pct"] == 100
    assert status_initial["gemini"]["used_tokens"] == 0
    assert status_initial["gemini"]["used_requests"] == 0
    assert status_initial["gemini"]["health"] == "healthy"

    # Registra consumo moderado
    quota_manager.record_llm_usage("gemini", tokens=25000, requests_count=25, quota_file=qfile)
    status_after = quota_manager.get_quota_status(qfile)
    assert status_after["gemini"]["used_tokens"] == 25000
    assert status_after["gemini"]["used_requests"] == 25
    assert status_after["gemini"]["remaining_pct"] == 90
    assert status_after["gemini"]["estimated_remaining_runs"] > 0


def test_quota_auto_resets_on_new_day(tmp_path):
    qfile = tmp_path / "quota.json"
    qfile.write_text(
        '{"date": "1999-01-01", "gemini": {"tokens": 200000, "requests": 240}}',
        encoding="utf-8",
    )
    status = quota_manager.get_quota_status(qfile)
    assert status["gemini"]["used_tokens"] == 0
    assert status["gemini"]["used_requests"] == 0
    assert status["gemini"]["remaining_pct"] == 100


def test_quota_critical_health_and_manual_reset(tmp_path):
    qfile = tmp_path / "quota.json"
    quota_manager.record_llm_usage("gemini", tokens=230000, requests_count=230, quota_file=qfile)
    status = quota_manager.get_quota_status(qfile)
    assert status["gemini"]["remaining_pct"] <= 15
    assert status["gemini"]["health"] == "critical"

    quota_manager.reset_daily_quota(qfile)
    reset_status = quota_manager.get_quota_status(qfile)
    assert reset_status["gemini"]["remaining_pct"] == 100
    assert reset_status["gemini"]["health"] == "healthy"


def test_extract_or_estimate_tokens():
    # 1. Com usage_metadata real (AIMessage)
    msg = MagicMock()
    msg.usage_metadata = {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
    assert quota_manager.extract_or_estimate_tokens(msg, "prompt") == 150

    # 2. Com objeto Pydantic (structured output)
    obj = DummyModel(title="Engenheiro Python", items=["FastAPI", "Docker"])
    est = quota_manager.extract_or_estimate_tokens(obj, "Analise esta vaga de Python")
    assert est > 5


def test_fetch_github_rate_limit():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "resources": {"core": {"limit": 5000, "remaining": 4500, "reset": 1700000000}}
    }
    with patch("requests.get", return_value=mock_resp):
        gh = quota_manager.fetch_github_rate_limit()
        assert gh["ok"] is True
        assert gh["limit"] == 5000
        assert gh["remaining"] == 4500
        assert gh["remaining_pct"] == 90


def test_nodes_record_quota_automatically():
    from src.agents.nodes.writer import resume_generator
    fake_resp = MagicMock()
    fake_resp.text = "# Candidato\nCurrículo gerado"
    fake_resp.usage_metadata = {"total_tokens": 1200}
    fake_resp.response_metadata = {"model_name": "gemini-3.8-flash"}

    with patch("src.agents.shared.llm.chat_model") as mock_llm:
        mock_llm.return_value.invoke.return_value = fake_resp
        resume_generator({"base_resume_md": "# Base", "job_description": "Vaga Python", "job_language": "pt"})

    status = quota_manager.get_quota_status()
    assert status["gemini"]["used_tokens"] == 1200
    assert status["gemini"]["used_requests"] == 1



def test_saved_history_file_does_not_double_count(tmp_path, monkeypatch):
    import datetime
    monkeypatch.chdir(tmp_path)
    qfile = tmp_path / "quota.json"
    for _ in range(4):
        quota_manager.record_llm_usage("gemini", tokens=1000, quota_file=qfile)
    hist = tmp_path / "history"
    hist.mkdir()
    (hist / f"{datetime.datetime.now():%Y%m%d_%H%M%S}_Vaga_abc123.md").write_text("<!--\n{}\n-->\n\nCV", encoding="utf-8")
    status = quota_manager.get_quota_status(qfile)
    assert status["gemini"]["used_requests"] == 4
    assert status["gemini"]["used_tokens"] == 4000


def test_concurrent_records_are_not_lost(tmp_path):
    import threading
    qfile = tmp_path / "quota.json"
    def worker():
        for _ in range(25):
            quota_manager.record_llm_usage("gemini", tokens=1, quota_file=qfile)
    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert quota_manager.get_quota_status(qfile)["gemini"]["used_requests"] == 200


def test_structured_output_from_groq_fallback_is_attributed_to_groq():
    from langchain_core.language_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda
    from src.agents.shared.llm import invoke_tracked

    def gemini_quota_error(_):
        raise RuntimeError("429 RESOURCE_EXHAUSTED")

    groq = GenericFakeChatModel(messages=iter([AIMessage(
        content='{"title": "Dev"}',
        usage_metadata={"input_tokens": 300, "output_tokens": 20, "total_tokens": 320},
        response_metadata={"model_name": "openai/gpt-oss-120b"},
    )]))
    # Modelo seguido de parser, como no with_structured_output: o resultado final é Pydantic, sem metadados
    chain = RunnableLambda(gemini_quota_error).with_fallbacks([groq]) | RunnableLambda(lambda m: DummyModel(title="Dev", items=[]))
    result = invoke_tracked(chain, "analise a vaga")

    assert isinstance(result, DummyModel)
    status = quota_manager.get_quota_status()
    assert (status["groq"]["used_requests"], status["groq"]["used_tokens"]) == (1, 320)
    assert status["gemini"]["used_requests"] == 0


def test_groq_usage_advances_after_live_probe_snapshot(tmp_path):
    import json
    qfile = tmp_path / "quota.json"
    quota_manager.record_llm_usage("groq", tokens=10, quota_file=qfile)
    data = json.loads(qfile.read_text(encoding="utf-8"))
    # Retrato de uma consulta ao vivo: 1000 de limite, 999 restantes, contador sincronizado em 1
    data["groq"].update({"live_limit_requests": 1000, "live_remaining_requests": 999, "requests": 1})
    qfile.write_text(json.dumps(data), encoding="utf-8")
    for _ in range(3):
        quota_manager.record_llm_usage("groq", tokens=10, quota_file=qfile)
    status = quota_manager.get_quota_status(qfile)["groq"]
    assert status["used_requests"] == 4
    assert status["request_limit"] == 1000
