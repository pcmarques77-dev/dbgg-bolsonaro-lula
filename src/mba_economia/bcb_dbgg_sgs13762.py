"""DBGG (% PIB) — série SGS 13762 e agregação anual para confronto com Focus."""

from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from .bcb_dlsp_sgs4513 import proxy_divulgacao_dlsp_anual
from .config import SeriesConfig
from .sgs_client import fetch_sgs_json


def _dezembro_por_ano(monthly: pd.DataFrame) -> pd.DataFrame:
    d = monthly.dropna(subset=["data_obs", "valor"]).copy()
    if d.empty:
        return pd.DataFrame(
            columns=["ano_ref", "dbgg_sgs_pct_pib", "data_obs", "dbgg_sgs_yoy_pp"],
        )
    d["ano_ref"] = d["data_obs"].dt.year.astype(int)
    d["mes"] = d["data_obs"].dt.month
    dez = d.loc[d["mes"] == 12].sort_values("data_obs")
    if dez.empty:
        dez = d.sort_values("data_obs").groupby("ano_ref", as_index=False).tail(1)
    else:
        dez = dez.groupby("ano_ref", as_index=False).tail(1)
    dez = dez.sort_values("ano_ref").reset_index(drop=True)
    dez["dbgg_sgs_pct_pib"] = dez["valor"].astype(float)
    dez["dbgg_sgs_yoy_pp"] = dez["dbgg_sgs_pct_pib"].diff()
    return dez[["ano_ref", "dbgg_sgs_pct_pib", "data_obs", "dbgg_sgs_yoy_pp"]]


def build_dbgg_anual_por_ano(
    monthly: pd.DataFrame,
    *,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    dez = _dezembro_por_ano(monthly)
    if dez.empty:
        return pd.DataFrame(
            columns=[
                "ano_ref",
                "dbgg_sgs_pct_pib",
                "dbgg_sgs_yoy_pp",
                "dbgg_sgs_data_obs",
                "dbgg_divulgacao_aprox",
            ],
        )
    dez["dbgg_sgs_data_obs"] = dez["data_obs"].dt.date
    dez["dbgg_divulgacao_aprox"] = dez["ano_ref"].map(
        lambda y: proxy_divulgacao_dlsp_anual(int(y), cfg).date(),
    )
    return dez.drop(columns=["data_obs"]).reset_index(drop=True)


def fetch_dbgg_mensal_sgs(
    ano_ini: int,
    ano_fim: int,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    raw = fetch_sgs_json(
        cfg.sgs_codigo_dbgg_pct_pib,
        date(ano_ini, 1, 1),
        date(ano_fim, 12, 31),
        session=session,
    )
    if raw.empty:
        return raw
    out = raw.copy()
    out["ano_ref"] = out["data_obs"].dt.year.astype(int)
    out["mes"] = out["data_obs"].dt.month
    out = out.rename(columns={"valor": "dbgg_sgs_pct_pib"})
    return out.sort_values("data_obs").reset_index(drop=True)


def fetch_dbgg_sgs13762_anual(
    ano_ini: int,
    ano_fim: int,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    raw = fetch_sgs_json(
        cfg.sgs_codigo_dbgg_pct_pib,
        date(ano_ini, 1, 1),
        date(ano_fim, 12, 31),
        session=session,
    )
    return build_dbgg_anual_por_ano(raw, cfg=cfg)
