"""Meta Selic oficial (SGS 432) — decisões do Copom.

Fonte: SGS 432 "Meta para a taxa Selic" — série diária com o valor-alvo
       vigente a cada data, refletindo exatamente as deliberações do Copom.

Por que usar esta série e não SGS 11 (taxa Selic efetiva/over):
    - SGS 432: valor deliberado pelo Copom  → ex. dez/2019 = **4,50% a.a.**
    - SGS 11:  taxa efetiva overnight diária; annualização ≈ 4,40% (imprecisa)

A série é atualizada pelo próprio BCB após cada reunião do Copom.
"""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_SGS_META_SELIC = 432  # "Meta para a taxa Selic"
_BCB_SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


def fetch_meta_selic_sgs(
    start: date,
    end: date,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Retorna série diária da Meta Selic (SGS 432).

    Returns
    -------
    DataFrame com colunas:
        - ``data``            : date
        - ``meta_selic_pct``  : float — Meta Selic em % a.a.
    """
    sess = session or requests.Session()
    url = _BCB_SGS_URL.format(codigo=_SGS_META_SELIC)
    params = {
        "formato": "json",
        "dataInicial": start.strftime("%d/%m/%Y"),
        "dataFinal": end.strftime("%d/%m/%Y"),
    }
    logger.info(
        "Baixando Meta Selic SGS %d: %s → %s", _SGS_META_SELIC, start, end
    )
    r = sess.get(url, params=params, timeout=60)
    r.raise_for_status()
    rows = r.json()
    if not rows:
        logger.warning("SGS 432: nenhum dado retornado para o período.")
        return pd.DataFrame(columns=["data", "meta_selic_pct"])
    df = pd.DataFrame(rows)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y").dt.date
    df["meta_selic_pct"] = pd.to_numeric(df["valor"], errors="coerce")
    return df[["data", "meta_selic_pct"]].dropna().reset_index(drop=True)


def meta_selic_em_datas(
    datas: list[date],
    meta_df: pd.DataFrame,
) -> dict[date, float]:
    """Meta Selic vigente em cada data de referência (``merge_asof`` backward, SGS 432).

    Para cada data em ``datas``, retorna a meta Selic já deliberada pelo Copom
    e vigente naquele dia — sem look-ahead.
    """
    if not datas or meta_df.empty:
        return {}
    left = pd.DataFrame({"ref_date": pd.to_datetime(sorted(set(datas)))})
    right = meta_df.copy()
    right["ref_date"] = pd.to_datetime(right["data"])
    right = right.sort_values("ref_date")
    merged = pd.merge_asof(
        left.sort_values("ref_date"),
        right[["ref_date", "meta_selic_pct"]],
        on="ref_date",
        direction="backward",
    )
    out: dict[date, float] = {}
    for row in merged.itertuples(index=False):
        if pd.notna(row.meta_selic_pct):
            out[row.ref_date.date()] = float(row.meta_selic_pct)
    return out


def meta_selic_inicio_ano(
    start: date,
    end: date,
    *,
    session: requests.Session | None = None,
) -> dict[int, float]:
    """Retorna a Meta Selic vigente no início de cada ano (1º jan, SGS 432).

    Returns
    -------
    ``{ano: meta_selic_pct}``  ex.: {2019: 6.5, 2020: 4.5, ...}
    """
    df = fetch_meta_selic_sgs(start, end, session=session)
    if df.empty:
        return {}
    result: dict[int, float] = {}
    for year in range(start.year, end.year + 1):
        jan = df[
            (df["data"] >= date(year, 1, 1))
            & (df["data"] <= date(year, 1, 31))
        ]
        if not jan.empty:
            result[year] = float(jan["meta_selic_pct"].iloc[0])
    return result


def meta_selic_fim_ano(
    start: date,
    end: date,
    *,
    session: requests.Session | None = None,
    meta_df: pd.DataFrame | None = None,
) -> dict[int, float]:
    """Retorna a Meta Selic em 31/dez de cada ano no período [start, end].

    Reflete a última decisão do Copom do ano — valor exato do SGS 432.

    Returns
    -------
    ``{ano: meta_selic_pct}``  ex.: {2019: 4.5, 2020: 2.0, ...}
    """
    df = (
        meta_df
        if meta_df is not None
        else fetch_meta_selic_sgs(start, end, session=session)
    )
    if df.empty:
        return {}
    result: dict[int, float] = {}
    for year in range(start.year, end.year + 1):
        dez = df[
            (df["data"] >= date(year, 12, 1))
            & (df["data"] <= date(year, 12, 31))
        ]
        if not dez.empty:
            result[year] = float(dez["meta_selic_pct"].iloc[-1])
    return result


def meta_selic_por_mes(
    start: date,
    end: date,
    *,
    session: requests.Session | None = None,
) -> dict[int, float]:
    """Retorna a Meta Selic no último dia útil de cada mês.

    Returns
    -------
    ``{yyyymm: meta_selic_pct}``  ex.: {201912: 4.5, 202012: 2.0, ...}
    """
    df = fetch_meta_selic_sgs(start, end, session=session)
    if df.empty:
        return {}
    df["yyyymm"] = df["data"].map(lambda d: d.year * 100 + d.month)
    result: dict[int, float] = {}
    for yyyymm, group in df.groupby("yyyymm"):
        result[int(yyyymm)] = float(group["meta_selic_pct"].iloc[-1])
    return result
