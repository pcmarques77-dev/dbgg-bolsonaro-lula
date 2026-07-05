"""Comparacao PIB trimestral: expectativa Focus x realizado IBGE (volume, YoY)."""

from __future__ import annotations

from datetime import date

import pandas as pd

# Proxy calendario IBGE: 1T→jun, 2T→set, 3T→dez, 4T→mar(+1)
_DIVULG_MES: dict[int, tuple[int, int]] = {
    1: (0, 6),
    2: (0, 9),
    3: (0, 12),
    4: (1, 3),
}


def proxy_divulgacao_ibge(ano: int, tri: int) -> pd.Timestamp:
    """Primeiro dia do mes tipico de divulgacao CNT trimestral."""
    dy, mes = _DIVULG_MES[tri]
    return pd.Timestamp(ano + dy, mes, 1).normalize()


def filtrar_janela_trimestres(
    df: pd.DataFrame,
    *,
    ano_ini: int,
    tri_ini: int,
    ano_fim: int,
    tri_fim: int,
) -> pd.DataFrame:
    if df.empty or "ano_ref" not in df.columns or "tri_ref" not in df.columns:
        return df.copy()
    key_ini = ano_ini * 10 + tri_ini
    key_fim = ano_fim * 10 + tri_fim
    k = df["ano_ref"].astype(int) * 10 + df["tri_ref"].astype(int)
    return df.loc[(k >= key_ini) & (k <= key_fim)].reset_index(drop=True)


def montar_comparacao_por_trimestre(
    focus: pd.DataFrame,
    ibge: pd.DataFrame,
) -> pd.DataFrame:
    """Uma linha por trimestre: ultima mediana Focus pre-divulgacao vs IBGE YoY (6561)."""
    if ibge.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for _, ib in ibge.sort_values(["ano_ref", "tri_ref"]).iterrows():
        ano = int(ib["ano_ref"])
        tri = int(ib["tri_ref"])
        div = proxy_divulgacao_ibge(ano, tri)
        f = focus[(focus["ano_ref"] == ano) & (focus["tri_ref"] == tri)].copy()
        pre = f[f["survey_date"] < div].sort_values("survey_date")
        ult = pre.iloc[-1] if not pre.empty else None
        foc = float(ult["pib_focus_trim_med_pct"]) if ult is not None else None
        ibge_yoy = ib.get("pib_ibge_vol_yoy_trim_pct")
        rows.append(
            {
                "trimestre": f"{tri}T/{ano}",
                "ano_ref": ano,
                "tri_ref": tri,
                "divulgacao_ibge_aprox": div.date().isoformat(),
                "focus_ultima_mediana_pct": foc,
                "focus_ultima_survey_date": (
                    pd.Timestamp(ult["survey_date"]).date().isoformat() if ult is not None else None
                ),
                "focus_n_respondentes": (
                    int(ult["numeroRespondentes"]) if ult is not None and pd.notna(ult["numeroRespondentes"]) else None
                ),
                "n_surveys_focus": len(f),
                "ibge_vol_yoy_trim_pct": ibge_yoy,
                "ibge_vol_qoq_pct": ib.get("pib_ibge_vol_qoq_pct"),
                "ibge_vol_acum4_yoy_pct": ib.get("pib_ibge_vol_acum4_yoy_pct"),
                "erro_focus_vs_ibge_yoy_pp": (
                    None if foc is None or pd.isna(ibge_yoy) else foc - float(ibge_yoy)
                ),
            },
        )
    return pd.DataFrame(rows)


def juntar_focus_com_realizado(focus: pd.DataFrame, ibge: pd.DataFrame) -> pd.DataFrame:
    """Serie Focus longa com colunas IBGE realizadas do trimestre referenciado."""
    if focus.empty:
        return focus.copy()
    ib = ibge.rename(
        columns={
            "pib_ibge_vol_yoy_trim_pct": "ibge_vol_yoy_trim_pct",
            "pib_ibge_vol_qoq_pct": "ibge_vol_qoq_pct",
            "pib_ibge_vol_acum4_yoy_pct": "ibge_vol_acum4_yoy_pct",
            "pib_ibge_vol_ytd_yoy_pct": "ibge_vol_ytd_yoy_pct",
        },
    )
    return focus.merge(ib, on=["ano_ref", "tri_ref"], how="left").sort_values(
        ["survey_date", "ano_ref", "tri_ref"],
    )


def trimestre_fim_por_data(d: date) -> tuple[int, int]:
    """Ultimo trimestre de referencia plausivel ja encerrado na data ``d``."""
    if d.month <= 3:
        return d.year - 1, 4
    if d.month <= 6:
        return d.year, 1
    if d.month <= 9:
        return d.year, 2
    if d.month <= 12:
        return d.year, 3
    return d.year, 4
