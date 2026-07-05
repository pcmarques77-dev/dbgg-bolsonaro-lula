"""Metas de Inflação CMN — BCB SGS 13521.

SGS 13521: Centro da meta de inflação (IPCA), fixada anualmente pelo
Conselho Monetário Nacional (CMN). Uma observação por ano (01/jan do ano).

Tolerância padrão: ±1,5 p.p. (vigente desde 2017 e mantida até 2026+).
"""
from __future__ import annotations

import logging
from datetime import date

import pandas as pd

from .sgs_client import fetch_sgs_json

logger = logging.getLogger(__name__)

# SGS 13521 — Centro da meta anual de inflação (IPCA), fixada pelo CMN
_SGS_META_CENTRO = 13521

# Tolerância padrão em vigor (±1,5 p.p.)
_TOLERANCIA_PP = 1.5


def fetch_metas_inflacao_sgs(
    start: date,
    end: date,
    *,
    tolerancia_pp: float = _TOLERANCIA_PP,
    session=None,
) -> pd.DataFrame:
    """Retorna DataFrame anual com centro, inferior e superior da meta CMN.

    Colunas:
        ano         : int — ano de referência
        meta_centro : float — centro da meta (% a.a.)
        meta_inferior : float — centro − tolerância_pp
        meta_superior : float — centro + tolerância_pp
    """
    # O SGS 13521 só tem dados até o ano corrente; limita para evitar 404
    end_capped = min(end, date.today())
    raw = fetch_sgs_json(_SGS_META_CENTRO, start, end_capped, session=session)
    if raw.empty:
        logger.warning("SGS %d retornou vazio para metas de inflação.", _SGS_META_CENTRO)
        return pd.DataFrame(columns=["ano", "meta_centro", "meta_inferior", "meta_superior"])

    df = raw.copy()
    df["data_obs"] = pd.to_datetime(df["data_obs"], dayfirst=True, errors="coerce")
    df["ano"] = df["data_obs"].dt.year
    df["meta_centro"] = pd.to_numeric(df["valor"], errors="coerce")
    df["meta_inferior"] = df["meta_centro"] - tolerancia_pp
    df["meta_superior"] = df["meta_centro"] + tolerancia_pp

    result = (
        df[["ano", "meta_centro", "meta_inferior", "meta_superior"]]
        .dropna(subset=["meta_centro"])
        .sort_values("ano")
        .reset_index(drop=True)
    )
    logger.info(
        "Metas CMN carregadas: %d anos (%d–%d)",
        len(result),
        result["ano"].min() if not result.empty else 0,
        result["ano"].max() if not result.empty else 0,
    )
    return result


def metas_como_dict(
    metas_df: pd.DataFrame,
) -> dict[int, dict[str, float]]:
    """Converte DataFrame de metas em ``{ano: {centro, inferior, superior}}``."""
    return {
        int(row["ano"]): {
            "centro": float(row["meta_centro"]),
            "inferior": float(row["meta_inferior"]),
            "superior": float(row["meta_superior"]),
        }
        for _, row in metas_df.iterrows()
    }


__all__ = ["fetch_metas_inflacao_sgs", "metas_como_dict"]
