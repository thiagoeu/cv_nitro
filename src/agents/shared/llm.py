"""Cliente LLM (Gemini com reservas), invocação com registro de cota e leitura das respostas."""
import re
from typing import Optional
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from src.core import config, quota_manager

LLM_TIMEOUT_SECONDS = 120


def chat_model(temperature: float, thinking_level: Optional[str] = "low") -> ChatGoogleGenerativeAI:
    """Cliente Gemini único: timeout/retries limitados evitam travar a UI; thinking 'low' corta a latência nas tarefas curtas."""
    extra = {"thinking_level": thinking_level} if thinking_level else {}
    # 120s por tentativa e 1 retry por modelo: a cadeia de fallbacks cuida do resto (pior caso ~12 min, não ~45)
    def make(model: str) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, timeout=LLM_TIMEOUT_SECONDS, max_retries=1, **extra)
    fallbacks = []
    if config.GEMINI_FALLBACK_MODEL and config.GEMINI_FALLBACK_MODEL != config.GEMINI_MODEL:
        fallbacks.append(make(config.GEMINI_FALLBACK_MODEL))
    if config.GROQ_API_KEY:
        # Tokens de raciocínio contam no limite por minuto do Groq; só o gpt-oss aceita "low".
        groq_extra = {"reasoning_effort": thinking_level} if thinking_level and config.GROQ_MODEL.startswith("openai/gpt-oss") else {}
        fallbacks.append(ChatGroq(model=config.GROQ_MODEL, temperature=temperature, timeout=LLM_TIMEOUT_SECONDS, max_retries=1, **groq_extra))
    if not fallbacks:
        return make(config.GEMINI_MODEL)
    # Cadeia plana (with_fallbacks aninhado perde os reservas no with_structured_output).
    # Qualquer erro troca de modelo: a cota 429 do free tier do Gemini é por modelo e estoura rápido.
    return make(config.GEMINI_MODEL).with_fallbacks(fallbacks)


def response_text(response) -> str:
    """Extrai o texto puro de respostas de LLM (Gemini, Groq, AIMessage). Remove cercas ```markdown."""
    if hasattr(response, "text") and isinstance(response.text, str):
        text = response.text
    elif hasattr(response, "content"):
        if isinstance(response.content, str):
            text = response.content
        elif isinstance(response.content, list):
            parts = []
            for item in response.content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            text = "".join(parts)
        else:
            text = str(response.content)
    else:
        text = str(response)
    return re.sub(r"^```(?:markdown|md)?\s*\n(.*?)\n?```$", r"\1", text.strip(), flags=re.DOTALL).strip()


def invoke_tracked(runnable, payload, prompt_text: str = ""):
    """
    Invoca o modelo e registra o consumo de quem de fato respondeu: o callback do LangChain vê o AIMessage
    mesmo dentro de with_structured_output e da cadeia de fallbacks. Sem metadados (ex.: mocks), estima.
    """
    with get_usage_metadata_callback() as cb:
        result = runnable.invoke(payload)
    if cb.usage_metadata:
        for model_name, usage in cb.usage_metadata.items():
            quota_manager.record_llm_usage(provider=quota_manager.provider_from_model_name(model_name),
                                           tokens=usage.get("total_tokens", 0))
    else:
        quota_manager.record_llm_usage(provider=quota_manager.detect_provider_from_response(result),
                                       tokens=quota_manager.extract_or_estimate_tokens(result, prompt_text))
    return result


def is_truncated(response) -> bool:
    """Saída cortada pelo limite de tokens: 'MAX_TOKENS' no Gemini, 'length' no Groq."""
    meta = getattr(response, "response_metadata", None)
    return isinstance(meta, dict) and meta.get("finish_reason") in ("MAX_TOKENS", "length")
