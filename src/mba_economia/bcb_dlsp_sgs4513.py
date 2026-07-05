"""DLSP (% PIB) — série SGS 4513 e agregação anual para confronto com Focus.

Conjunto oficial:
https://dadosabertos.bcb.gov.br/dataset/4513-divida-liquida-do-setor-publico--pib---total---setor-publico-consolidado

A série é mensal; para cada ano-calendário Y usa-se o fechamento de dezembro
(última observação do ano), padrão usual para razão dívida/PIB.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from .config import SeriesConfig
from .sgs_client import fetch_sgs_json


def _dezembro_por_ano(monthly: pd.DataFrame) -> pd.DataFrame:
    d = monthly.dropna(subset=["data_obs", "valor"]).copy()
    if d.empty:
        return pd.DataFrame(
            columns=["ano_ref", "dlsp_sgs_pct_pib", "data_obs", "dlsp_sgs_yoy_pp"],
        )
    d["ano_ref"] = d["data_obs"].dt.year.astype(int)
    d["mes"] = d["data_obs"].dt.month
    dez = d.loc[d["mes"] == 12].sort_values("data_obs")
    if dez.empty:
        dez = d.sort_values("data_obs").groupby("ano_ref", as_index=False).tail(1)
    else:
        dez = dez.groupby("ano_ref", as_index=False).tail(1)
    dez = dez.sort_values("ano_ref").reset_index(drop=True)
    dez["dlsp_sgs_pct_pib"] = dez["valor"].astype(float)
    dez["dlsp_sgs_yoy_pp"] = dez["dlsp_sgs_pct_pib"].diff()
    return dez[["ano_ref", "dlsp_sgs_pct_pib", "data_obs", "dlsp_sgs_yoy_pp"]]


def proxy_divulgacao_dlsp_anual(ano: int, cfg: SeriesConfig) -> pd.Timestamp:
    """Primeiro dia do mês tipico de divulgação consolidada do ano anterior."""
    return pd.Timestamp(
        ano + 1,
        cfg.dlsp_anual_divulgacao_mes_ano_seguinte,
        cfg.dlsp_anual_divulgacao_dia_mes,
    ).normalize()


def build_dlsp_anual_por_ano(
    monthly: pd.DataFrame,
    *,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    """Uma linha por ano: DLSP dez/Y (% PIB), variação YoY (p.p.) e proxy de divulgação."""
    dez = _dezembro_por_ano(monthly)
    if dez.empty:
        return pd.DataFrame(
            columns=[
                "ano_ref",
                "dlsp_sgs_pct_pib",
                "dlsp_sgs_yoy_pp",
                "dlsp_sgs_data_obs",
                "dlsp_divulgacao_aprox",
            ],
        )
    dez["dlsp_sgs_data_obs"] = dez["data_obs"].dt.date
    dez["dlsp_divulgacao_aprox"] = dez["ano_ref"].map(
        lambda y: proxy_divulgacao_dlsp_anual(int(y), cfg).date(),
    )
    return dez.drop(columns=["data_obs"]).reset_index(drop=True)


def fetch_dlsp_sgs4513_anual(
    ano_ini: int,
    ano_fim: int,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Baixa SGS ``sgs_codigo_dlsp_pct_pib`` e devolve tabela anual por ``ano_ref``."""
    start = date(ano_ini, 1, 1)
    end = date(ano_fim, 12, 31)
    raw = fetch_sgs_json(cfg.sgs_codigo_dlsp_pct_pib, start, end, session=session)
    return build_dlsp_anual_por_ano(raw, cfg=cfg)
