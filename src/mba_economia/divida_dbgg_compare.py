"""Comparação anual: expectativa Focus (DBGG % PIB) x realizado SGS 13762."""

from __future__ import annotations

import pandas as pd

from .bcb_dlsp_sgs4513 import proxy_divulgacao_dlsp_anual
from .config import SeriesConfig
from .divida_dlsp_compare import filtrar_janela_anos


def montar_comparacao_por_ano(
    focus: pd.DataFrame,
    realizado: pd.DataFrame,
    *,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    if realizado.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for _, rt in realizado.sort_values("ano_ref").iterrows():
        ano = int(rt["ano_ref"])
        div = proxy_divulgacao_dlsp_anual(ano, cfg)
        f = focus[focus["ano_ref"] == ano].copy()
        pre = f[f["survey_date"] < div].sort_values("survey_date")
        ult = pre.iloc[-1] if not pre.empty else None
        foc = float(ult["dbgg_focus_med_pct_pib"]) if ult is not None else None
        real = rt.get("dbgg_sgs_pct_pib")
        real_yoy = rt.get("dbgg_sgs_yoy_pp")
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
                "dbgg_realizado_dez_pct_pib": real,
                "dbgg_realizado_yoy_pp": real_yoy,
                "dbgg_sgs_data_obs": rt.get("dbgg_sgs_data_obs"),
                "dbgg_sgs_codigo": cfg.sgs_codigo_dbgg_pct_pib,
                "erro_focus_vs_realizado_pp": (
                    None if foc is None or pd.isna(real) else foc - float(real)
                ),
            },
        )
    return pd.DataFrame(rows)


def juntar_focus_com_realizado(focus: pd.DataFrame, realizado: pd.DataFrame) -> pd.DataFrame:
    if focus.empty:
        return focus.copy()
    return focus.merge(realizado, on="ano_ref", how="left").sort_values(
        ["survey_date", "ano_ref"],
    )


def complementar_anos_apenas_focus(
    comparacao: pd.DataFrame,
    focus: pd.DataFrame,
    *,
    ano_ini: int,
    ano_fim: int,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    """Inclui anos com Focus mas sem realizado SGS (ex.: 2026)."""
    from .bcb_dlsp_sgs4513 import proxy_divulgacao_dlsp_anual

    presentes = set(comparacao["ano"].astype(int).tolist()) if not comparacao.empty else set()
    extras: list[dict] = []
    for ano in range(ano_ini, ano_fim + 1):
        if ano in presentes:
            continue
        f = focus[focus["ano_ref"] == ano].copy()
        if f.empty:
            continue
        div = proxy_divulgacao_dlsp_anual(ano, cfg)
        pre = f[f["survey_date"] < div].sort_values("survey_date")
        ult = pre.iloc[-1] if not pre.empty else None
        if ult is None:
            continue
        extras.append(
            {
                "ano": ano,
                "divulgacao_aprox": div.date().isoformat(),
                "focus_ultima_mediana_pct_pib": float(ult["dbgg_focus_med_pct_pib"]),
                "focus_ultima_survey_date": pd.Timestamp(ult["survey_date"]).date().isoformat(),
                "focus_n_respondentes": (
                    int(ult["numeroRespondentes"])
                    if pd.notna(ult["numeroRespondentes"])
                    else None
                ),
                "n_surveys_focus": len(f),
                "dbgg_realizado_dez_pct_pib": None,
                "dbgg_realizado_yoy_pp": None,
                "dbgg_sgs_data_obs": None,
                "dbgg_sgs_codigo": cfg.sgs_codigo_dbgg_pct_pib,
                "erro_focus_vs_realizado_pp": None,
            },
        )
    if not extras:
        return comparacao.copy()
    out = pd.concat([comparacao, pd.DataFrame(extras)], ignore_index=True)
    return out.sort_values("ano").reset_index(drop=True)


__all__ = [
    "filtrar_janela_anos",
    "montar_comparacao_por_ano",
    "juntar_focus_com_realizado",
    "complementar_anos_apenas_focus",
]
