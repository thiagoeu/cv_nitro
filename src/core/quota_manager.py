import datetime
import json
import pathlib
import re
from typing import Any, Dict, Optional
import requests
from src.core import config

_DEFAULT_QUOTA_FILE = pathlib.Path("profiles/quota_usage.json")
QUOTA_FILE = _DEFAULT_QUOTA_FILE
HISTORY_DIR = pathlib.Path("history")
AVG_TOKENS_PER_OPTIMIZATION = 4500
AVG_REQUESTS_PER_OPTIMIZATION = 4

LLM_AGENT_STEPS = {
    "job_analyzer",
    "resume_generator",
    "section_patcher",
    "quality_reviewer",
    "cover_letter_generator",
}


def _today_str() -> str:
    return datetime.date.today().isoformat()


def _default_usage(date_str: str) -> Dict[str, Any]:
    return {
        "date": date_str,
        "gemini": {"tokens": 0, "requests": 0, "live_exhausted": False, "live_status": ""},
        "groq": {
            "tokens": 0,
            "requests": 0,
            "live_limit_requests": None,
            "live_remaining_requests": None,
            "live_limit_tokens": None,
            "live_remaining_tokens": None,
            "live_reset_requests": "",
            "live_status": "",
        },
        "synced_history_files": [],
        "last_updated": datetime.datetime.now().isoformat(),
    }


def _estimate_history_file_usage(md_path: pathlib.Path) -> Dict[str, int]:
    """
    Estima tokens e requisições de um currículo salvo em history/ hoje,
    lendo o metadado JSON e o corpo do documento.
    """
    try:
        raw = md_path.read_text(encoding="utf-8")
    except Exception:
        return {"tokens": AVG_TOKENS_PER_OPTIMIZATION, "requests": AVG_REQUESTS_PER_OPTIMIZATION}

    requests_count = AVG_REQUESTS_PER_OPTIMIZATION
    m = re.match(r"^<!--\s*(\{.*?\})\s*-->", raw, flags=re.DOTALL)
    if m:
        try:
            meta = json.loads(m.group(1))
            diag = meta.get("diagnostic") or {}
            trace = diag.get("agent_trace") or []
            if trace:
                llm_steps = [
                    step for step in trace
                    if isinstance(step, dict) and step.get("agent") in LLM_AGENT_STEPS
                ]
                # Se rodou em modo econômico sem LLM no revisor, desconta 1 se parecer determinístico
                rev_summary = str(diag.get("reviewer_summary") or "")
                reqs = len(llm_steps)
                if "modo econômico" in rev_summary.lower() and reqs > 2:
                    reqs -= 1
                requests_count = max(2, reqs)
            elif meta.get("has_cover_letter"):
                requests_count = 4
            else:
                requests_count = 3
        except Exception:
            pass

    # Cada chamada envia prompt + contexto; estimamos tokens totais proporcionalmente ao tamanho do arquivo e etapas
    estimated_tokens = max(2500, min(18000, (len(raw) // 4) + (requests_count * 900)))
    return {"tokens": estimated_tokens, "requests": requests_count}


def _sync_today_history_into_usage(
    data: Dict[str, Any],
    quota_file: Optional[pathlib.Path] = None,
) -> bool:
    """
    Sincroniza automaticamente os currículos gerados hoje na pasta history/
    que ainda não foram contabilizados no arquivo de cota (ex.: gerados antes do monitor).
    Apenas executa para o arquivo de produção padrão (QUOTA_FILE) para não afetar testes isolados.
    """
    target_path = quota_file or QUOTA_FILE
    if target_path != _DEFAULT_QUOTA_FILE or not HISTORY_DIR.exists():
        return False

    today_compact = datetime.date.today().strftime("%Y%m%d")
    synced = set(data.get("synced_history_files") or [])
    changed = False

    for md_file in sorted(HISTORY_DIR.glob(f"{today_compact}_*.md")):
        if md_file.name in synced:
            continue
        est = _estimate_history_file_usage(md_file)
        gem = data.setdefault("gemini", {"tokens": 0, "requests": 0})
        gem["tokens"] = int(gem.get("tokens", 0)) + est["tokens"]
        gem["requests"] = int(gem.get("requests", 0)) + est["requests"]
        synced.add(md_file.name)
        changed = True

    if changed:
        data["synced_history_files"] = sorted(synced)
    return changed


def _load_usage(quota_file: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    path = quota_file or QUOTA_FILE
    today = _today_str()
    if not path.exists():
        data = _default_usage(today)
        if _sync_today_history_into_usage(data, path):
            _save_usage(data, path)
        return data
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("date") != today:
            data = _default_usage(today)
            if _sync_today_history_into_usage(data, path):
                _save_usage(data, path)
            return data
        data.setdefault("gemini", {"tokens": 0, "requests": 0})
        data.setdefault("groq", {"tokens": 0, "requests": 0})
        data.setdefault("synced_history_files", [])
        if not data.get("manual_reset") and _sync_today_history_into_usage(data, path):
            _save_usage(data, path)
        return data
    except Exception:
        return _default_usage(today)


def _save_usage(data: Dict[str, Any], quota_file: Optional[pathlib.Path] = None) -> None:
    path = quota_file or QUOTA_FILE
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data["last_updated"] = datetime.datetime.now().isoformat()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Aviso ao salvar uso de cota: {e}")


def extract_or_estimate_tokens(response: Any, prompt_text: str = "") -> int:
    """
    Extrai total_tokens de response.usage_metadata (LangChain AIMessage) ou estima
    por contagem de caracteres (~4 caracteres por token) para saídas estruturadas Pydantic.
    """
    usage = getattr(response, "usage_metadata", None)
    if isinstance(usage, dict) and usage.get("total_tokens"):
        return max(1, int(usage["total_tokens"]))

    resp_meta = getattr(response, "response_metadata", None)
    if isinstance(resp_meta, dict):
        token_usage = resp_meta.get("token_usage") or resp_meta.get("usage")
        if isinstance(token_usage, dict) and token_usage.get("total_tokens"):
            return max(1, int(token_usage["total_tokens"]))

    if hasattr(response, "model_dump_json") and callable(response.model_dump_json):
        try:
            out_str = response.model_dump_json()
        except Exception:
            out_str = str(response)
    elif hasattr(response, "content") and isinstance(response.content, str):
        out_str = response.content
    elif hasattr(response, "text") and isinstance(response.text, str):
        out_str = response.text
    else:
        out_str = str(response or "")

    total_chars = len(prompt_text or "") + len(out_str)
    return max(1, total_chars // 4)


def detect_provider_from_response(response: Any) -> str:
    """Identifica se a resposta veio do Groq ou do Gemini (padrão 'gemini')."""
    resp_meta = getattr(response, "response_metadata", None)
    if isinstance(resp_meta, dict):
        model_name = str(resp_meta.get("model_name") or resp_meta.get("model") or "").lower()
        if "groq" in model_name or "llama" in model_name or "gpt-oss" in model_name:
            return "groq"
    return "gemini"


def record_llm_usage(
    provider: str = "gemini",
    tokens: int = 0,
    requests_count: int = 1,
    quota_file: Optional[pathlib.Path] = None,
) -> Dict[str, Any]:
    """Registra consumo de tokens e requisições do dia atual para o provedor informado."""
    prov = "groq" if (provider or "").lower() == "groq" else "gemini"
    data = _load_usage(quota_file)
    entry = data.setdefault(prov, {"tokens": 0, "requests": 0})
    entry["tokens"] = int(entry.get("tokens", 0)) + max(0, int(tokens))
    entry["requests"] = int(entry.get("requests", 0)) + max(0, int(requests_count))
    if prov == "gemini":
        entry["live_exhausted"] = False
    _save_usage(data, quota_file)
    return data


def reset_daily_quota(quota_file: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """Zera manualmente os contadores de consumo do dia."""
    data = _default_usage(_today_str())
    data["manual_reset"] = True
    if HISTORY_DIR.exists():
        today_compact = datetime.date.today().strftime("%Y%m%d")
        data["synced_history_files"] = sorted(
            f.name for f in HISTORY_DIR.glob(f"{today_compact}_*.md")
        )
    _save_usage(data, quota_file)
    return data


def _compute_provider_metrics(
    used_tokens: int,
    used_requests: int,
    token_limit: int,
    request_limit: int,
    live_exhausted: bool = False,
    live_status: str = "",
    source: str = "local",
) -> Dict[str, Any]:
    token_limit = max(1, int(token_limit))
    request_limit = max(1, int(request_limit))
    rem_tokens = 0 if live_exhausted else max(0, token_limit - used_tokens)
    rem_requests = 0 if live_exhausted else max(0, request_limit - used_requests)

    rem_tokens_pct = round((rem_tokens / token_limit) * 100)
    rem_requests_pct = round((rem_requests / request_limit) * 100)
    remaining_pct = 0 if live_exhausted else max(0, min(100, min(rem_tokens_pct, rem_requests_pct)))
    used_pct = 100 - remaining_pct

    est_runs_by_tokens = rem_tokens // AVG_TOKENS_PER_OPTIMIZATION
    est_runs_by_reqs = rem_requests // AVG_REQUESTS_PER_OPTIMIZATION
    estimated_remaining_runs = 0 if live_exhausted else max(0, min(est_runs_by_tokens, est_runs_by_reqs))

    if remaining_pct <= 15:
        health = "critical"
    elif remaining_pct <= 35:
        health = "warning"
    else:
        health = "healthy"

    return {
        "used_tokens": used_tokens,
        "token_limit": token_limit,
        "remaining_tokens": rem_tokens,
        "remaining_tokens_pct": rem_tokens_pct,
        "used_requests": used_requests,
        "request_limit": request_limit,
        "remaining_requests": rem_requests,
        "remaining_requests_pct": rem_requests_pct,
        "remaining_pct": remaining_pct,
        "used_pct": used_pct,
        "estimated_remaining_runs": estimated_remaining_runs,
        "health": health,
        "live_exhausted": live_exhausted,
        "live_status": live_status,
        "source": source,
    }


def get_quota_status(quota_file: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """Retorna o status consolidado de cota diária para Gemini e Groq."""
    data = _load_usage(quota_file)
    gem = data.get("gemini", {})
    grq = data.get("groq", {})

    gemini_metrics = _compute_provider_metrics(
        used_tokens=int(gem.get("tokens", 0)),
        used_requests=int(gem.get("requests", 0)),
        token_limit=config.GEMINI_DAILY_TOKEN_LIMIT,
        request_limit=config.GEMINI_DAILY_REQUEST_LIMIT,
        live_exhausted=bool(gem.get("live_exhausted", False)),
        live_status=str(gem.get("live_status", "")),
        source="histórico + local" if data.get("synced_history_files") else "local",
    )

    # Se Groq tiver cabeçalhos reais de rate-limit consultados na API, usa os limites reais!
    grq_req_limit = int(grq.get("live_limit_requests") or config.GROQ_DAILY_REQUEST_LIMIT)
    if grq.get("live_remaining_requests") is not None:
        grq_used_reqs = max(0, grq_req_limit - int(grq["live_remaining_requests"]))
        grq_source = "API ao vivo (headers Groq)"
    else:
        grq_used_reqs = int(grq.get("requests", 0))
        grq_source = "local"

    groq_metrics = _compute_provider_metrics(
        used_tokens=int(grq.get("tokens", 0)),
        used_requests=grq_used_reqs,
        token_limit=config.GROQ_DAILY_TOKEN_LIMIT,
        request_limit=grq_req_limit,
        live_status=str(grq.get("live_status", "")),
        source=grq_source,
    )

    return {
        "date": data.get("date", _today_str()),
        "last_updated": data.get("last_updated", ""),
        "synced_history_count": len(data.get("synced_history_files") or []),
        "gemini": gemini_metrics,
        "groq": groq_metrics,
    }


def probe_live_llm_quotas(quota_file: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """
    Consulta ativamente as APIs configuradas:
    - Groq: lê os cabeçalhos HTTP oficiais `x-ratelimit-limit-requests` e `x-ratelimit-remaining-requests` (cota real no servidor).
    - Gemini: faz um ping de 1 token na API para verificar se a chave está operacional (200 OK) ou em bloqueio de cota (429 RESOURCE_EXHAUSTED).
    Nota: O Google AI Studio não expõe endpoint REST de saldo numérico de tokens diários; por isso o saldo do Gemini combina
    a verificação ao vivo (200 vs 429) com os currículos gerados hoje em `history/` e no rastreador local.
    """
    data = _load_usage(quota_file)
    results: Dict[str, Any] = {"gemini": {}, "groq": {}}

    # 1. Probe Groq (retorna headers x-ratelimit-* exatos do servidor)
    if config.GROQ_API_KEY:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.GROQ_MODEL,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
                timeout=(3.0, 6.0),
            )
            hdrs = resp.headers
            lim_req = hdrs.get("x-ratelimit-limit-requests")
            rem_req = hdrs.get("x-ratelimit-remaining-requests")
            lim_tok = hdrs.get("x-ratelimit-limit-tokens")
            rem_tok = hdrs.get("x-ratelimit-remaining-tokens")
            rst_req = hdrs.get("x-ratelimit-reset-requests", "")

            grq_entry = data.setdefault("groq", {"tokens": 0, "requests": 0})
            if lim_req is not None and rem_req is not None:
                grq_entry["live_limit_requests"] = int(lim_req)
                grq_entry["live_remaining_requests"] = int(rem_req)
                grq_entry["requests"] = max(0, int(lim_req) - int(rem_req))
            if lim_tok is not None and rem_tok is not None:
                grq_entry["live_limit_tokens"] = int(lim_tok)
                grq_entry["live_remaining_tokens"] = int(rem_tok)
            grq_entry["live_reset_requests"] = rst_req
            if resp.status_code == 200:
                grq_entry["live_status"] = f"Online (200 OK) · {rem_req}/{lim_req} req restantes no servidor Groq"
            elif resp.status_code == 429:
                grq_entry["live_remaining_requests"] = 0
                grq_entry["live_status"] = f"Limite atingido na API Groq (HTTP 429) · reset em {rst_req}"
            else:
                grq_entry["live_status"] = f"HTTP {resp.status_code}"
            results["groq"] = {"ok": resp.status_code == 200, "status_code": resp.status_code}
        except Exception as e:
            results["groq"] = {"ok": False, "error": str(e)}

    # 2. Probe Gemini via :countTokens (rápido < 0.5s e não gasta cota de geração)
    if config.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:countTokens?key={config.GEMINI_API_KEY}"
            resp = requests.post(
                url,
                json={"contents": [{"parts": [{"text": "ok"}]}]},
                timeout=(3.0, 5.0),
            )
            gem_entry = data.setdefault("gemini", {"tokens": 0, "requests": 0})
            if resp.status_code == 200:
                gem_entry["live_exhausted"] = False
                gem_entry["live_status"] = f"Online na Google (200 OK · modelo {config.GEMINI_MODEL} ativo)"
                results["gemini"] = {"ok": True, "status_code": 200}
            elif resp.status_code == 429:
                gem_entry["live_exhausted"] = True
                gem_entry["live_status"] = "Cota bloqueada na Google (HTTP 429 RESOURCE_EXHAUSTED)"
                results["gemini"] = {"ok": False, "status_code": 429}
            else:
                gem_entry["live_status"] = f"Resposta da API Google: HTTP {resp.status_code}"
                results["gemini"] = {"ok": False, "status_code": resp.status_code}
        except Exception as e:
            results["gemini"] = {"ok": False, "error": str(e)}

    _save_usage(data, quota_file)
    return results


def fetch_github_rate_limit() -> Dict[str, Any]:
    """Consulta em tempo real o endpoint /rate_limit da API do GitHub."""
    headers = {"Accept": "application/vnd.github+json"}
    token = config.GITHUB_TOKEN
    if token and "your_github_token" not in token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get("https://api.github.com/rate_limit", headers=headers, timeout=(3.0, 5.0))
        if resp.status_code == 200:
            core = resp.json().get("resources", {}).get("core", {}) or resp.json().get("rate", {})
            limit = max(1, int(core.get("limit", 60)))
            remaining = max(0, int(core.get("remaining", 0)))
            reset_ts = int(core.get("reset", 0))
            remaining_pct = max(0, min(100, round((remaining / limit) * 100)))
            reset_str = (
                datetime.datetime.fromtimestamp(reset_ts).strftime("%H:%M")
                if reset_ts
                else ""
            )
            return {
                "ok": True,
                "limit": limit,
                "remaining": remaining,
                "used": max(0, limit - remaining),
                "remaining_pct": remaining_pct,
                "reset_time": reset_str,
            }
        return {
            "ok": False,
            "limit": 60,
            "remaining": 0,
            "used": 60,
            "remaining_pct": 0,
            "error": f"HTTP {resp.status_code}",
        }
    except Exception as e:
        return {
            "ok": False,
            "limit": 60,
            "remaining": 0,
            "used": 0,
            "remaining_pct": 0,
            "error": str(e),
        }
