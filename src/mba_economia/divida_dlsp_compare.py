"""Comparação anual: expectativa Focus (DLSP % PIB) x realizado SGS 4513."""

from __future__ import annotations

import pandas as pd

from .bcb_dlsp_sgs4513 import proxy_divulgacao_dlsp_anual
from .config import SeriesConfig


def filtrar_janela_anos(
    df: pd.DataFrame,
    *,
    ano_ini: int,
    ano_fim: int,
) -> pd.DataFrame:
    if df.empty or "ano_ref" not in df.columns:
        return df.copy()
    k = df["ano_ref"].astype(int)
    return df.loc[(k >= ano_ini) & (k <= ano_fim)].reset_index(drop=True)


def montar_comparacao_por_ano(
    focus: pd.DataFrame,
    realizado: pd.DataFrame,
    *,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    """Uma linha por ano: última mediana Focus pré-divulgação vs DLSP dez/Y (SGS 4513)."""
    if realizado.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for _, rt in realizado.sort_values("ano_ref").iterrows():
        ano = int(rt["ano_ref"])
        div = proxy_divulgacao_dlsp_anual(ano, cfg)
        f = focus[focus["ano_ref"] == ano].copy()
        pre = f[f["survey_date"] < div].sort_values("survey_date")
        ult = pre.iloc[-1] if not pre.empty else None
        foc = float(ult["dlsp_focus_med_pct_pib"]) if ult is not None else None
        real = rt.get("dlsp_sgs_pct_pib")
        real_yoy = rt.get("dlsp_sgs_yoy_pp")
        rows.append(
            {
                "ano": ano,
                "divulgacao_aprox": div.date().isoformat(),
                "focus_ultima_mediana_pct_pib": foc,
                "focus_ultima_survey_date": (
                    pd.Timestamp(ult["survey_date"]).date().isoformat() if ult is not None else None
                ),
                "focus_n_respondentes": (
                    int(ult["numeroRespondentes"])
                    if ult is not None and pd.notna(ult["numeroRespondentes"])
                    else None
                ),
                "n_surveys_focus": len(f),
                "dlsp_realizado_dez_pct_pib": real,
                "dlsp_realizado_yoy_pp": real_yoy,
                "dlsp_sgs_data_obs": rt.get("dlsp_sgs_data_obs"),
                "erro_focus_vs_realizado_pp": (
                    None if foc is None or pd.isna(real) else foc - float(real)
                ),
            },
        )
    return pd.DataFrame(rows)


def juntar_focus_com_realizado(focus: pd.DataFrame, realizado: pd.DataFrame) -> pd.DataFrame:
    """Série Focus longa com colunas do realizado anual do ano referenciado."""
    if focus.empty:
        return focus.copy()
    return focus.merge(realizado, on="ano_ref", how="left").sort_values(
        ["survey_date", "ano_ref"],
    )
