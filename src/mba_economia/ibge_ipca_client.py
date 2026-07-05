"""Séries oficiais IPCA via API SIDRA do IBGE (tabela 1737)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from .config import SIDRA_IBGE_VALUES_BASE


def _d3_to_period(ts: pd.Timestamp) -> pd.Period:
    return ts.to_period("M")


def _period_range_codes(start: pd.Period, end: pd.Period) -> tuple[str, str]:
    if start > end:
        start, end = end, start
    return start.strftime("%Y%m"), end.strftime("%Y%m")


def _disponivel_aprox(d3_yyyymm: str, dia_mes_seguinte: int) -> pd.Timestamp:
    y = int(d3_yyyymm[:4])
    mo = int(d3_yyyymm[4:6])
    if mo == 12:
        return pd.Timestamp(year=y + 1, month=1, day=dia_mes_seguinte)
    return pd.Timestamp(year=y, month=mo + 1, day=dia_mes_seguinte)


def fetch_ipca_sidra_var_pct(
    start: date,
    end: date,
    *,
    tabela: int,
    codigo_variavel: int,
    valor_col: str,
    dia_public_approx_mes_seguinte: int,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Uma variável da tabela 1737; retorna ``ibge_period_yyyymm``, ``disponivel_aprox``, ``valor_col``."""
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", "mba-economia-fipe/0.1")
    pad = pd.Timedelta(days=400)
    p0 = _d3_to_period(pd.Timestamp(start) - pad)
    p1 = _d3_to_period(pd.Timestamp(end))
    desde, ate = _period_range_codes(p0, p1)
    u = (
        f"{SIDRA_IBGE_VALUES_BASE}/t/{tabela}/n1/1"
        f"/v/{codigo_variavel}/p/{desde}-{ate}/h/n/f/c"
    )
    r = sess.get(u, timeout=120)
    r.raise_for_status()
    rows = r.json()
    cols = ["ibge_period_yyyymm", "disponivel_aprox", valor_col]
    if not isinstance(rows, list) or len(rows) < 1:
        return pd.DataFrame(columns=cols)

    dados: list[dict] = []
    for row in rows:
        d3 = row.get("D3C")
        v_raw = row.get("V")
        if not d3 or str(d3).lower() == "valor":
            continue
        if isinstance(v_raw, str) and v_raw.strip() in ("...", "..", "", "-"):
            continue
        val = pd.to_numeric(v_raw, errors="coerce")
        if val is pd.NA or (isinstance(val, float) and pd.isna(val)):
            continue
        dados.append(
            {
                "ibge_period_yyyymm": str(d3),
                "disponivel_aprox": _disponivel_aprox(str(d3), dia_public_approx_mes_seguinte),
                valor_col: float(val),
            },
        )
    out = pd.DataFrame(dados)
    if out.empty:
        return out
    return (
        out.sort_values("disponivel_aprox")
        .reset_index(drop=True)
        .assign(ibge_period_yyyymm=lambda d: d["ibge_period_yyyymm"].astype(str))
    )


def fetch_ipca_sidra_acum12m_pct(
    start: date,
    end: date,
    *,
    tabela: int,
    codigo_variavel: int,
    dia_public_approx_mes_seguinte: int,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Variação acumulada em 12 meses (%)."""
    return fetch_ipca_sidra_var_pct(
        start,
        end,
        tabela=tabela,
        codigo_variavel=codigo_variavel,
        valor_col="ipca_ibge_acum12m_pct",
        dia_public_approx_mes_seguinte=dia_public_approx_mes_seguinte,
        session=session,
    )


def fetch_ipca_ibge_mensal_pct(
    start: date,
    end: date,
    *,
    tabela: int,
    codigo_variavel: int,
    dia_public_approx_mes_seguinte: int,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Variação mensal do IPCA (%), mês de referência em ``ibge_period_yyyymm``."""
    return fetch_ipca_sidra_var_pct(
        start,
        end,
        tabela=tabela,
        codigo_variavel=codigo_variavel,
        valor_col="ipca_ibge_mensal_pct",
        dia_public_approx_mes_seguinte=dia_public_approx_mes_seguinte,
        session=session,
    )


def fetch_ipca_ibge_acum_ano_pct(
    start: date,
    end: date,
    *,
    tabela: int,
    codigo_variavel: int,
    dia_public_approx_mes_seguinte: int,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Variação acumulada no ano-calendário (%); dezembro = inflação jan–dez do ano."""
    df = fetch_ipca_sidra_var_pct(
        start,
        end,
        tabela=tabela,
        codigo_variavel=codigo_variavel,
        valor_col="ipca_ibge_acum_ano_pct",
        dia_public_approx_mes_seguinte=dia_public_approx_mes_seguinte,
        session=session,
    )
    if df.empty:
        return df
    return df.assign(ano_ref=lambda d: d["ibge_period_yyyymm"].str[:4].astype(int))
