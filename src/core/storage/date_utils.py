"""Utilitários de parsing, normalização de fuso horário e formatação amigável de datas."""
from datetime import datetime
from typing import Any


def _parse_datetime_naive(date_val: Any) -> datetime:
    """Converte a data para o horário local sem tzinfo (registros do Supabase vêm em UTC)."""
    if not date_val:
        return datetime.min
    if isinstance(date_val, datetime):
        dt = date_val
    else:
        s = str(date_val).strip()
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
            return datetime.min
    return dt.astimezone().replace(tzinfo=None) if dt.tzinfo else dt


def _get_sort_timestamp(date_val: Any) -> float:
    """Converte datas em qualquer formato para timestamp numérico civil."""
    dt = _parse_datetime_naive(date_val)
    if dt == datetime.min:
        return 0.0
    return dt.timestamp()


def format_display_date(date_val: Any) -> str:
    """Formata data para exibição amigável no formato DD/MM/YYYY HH:MM."""
    try:
        dt = _parse_datetime_naive(date_val)
        if dt != datetime.min:
            return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    return str(date_val)[:16].replace("T", " ")

