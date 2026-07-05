"""PIB em R$ correntes (SGS) e derivacao de YoY nominal para confronto com Focus.

Codigo oficial no portal de dados abertos do BC:
https://dadosabertos.bcb.gov.br/dataset/1207-sgs

A serie é anual em valores nominais; a variação % ano/ano nominal é
(valor_Y / valor_{Y-1} - 1) * 100. A disponibilidade do número do ano Y
(usada para só preencher o painel após a primeira divulgacao típica) é
proximada por ``31/12/Y + dias_apos_referencia`` (ver ``SeriesConfig``).
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import requests

from .config import SeriesConfig
from .panel import _bd_offset
from .sgs_client import fetch_sgs_json


def _um_nivel_por_ano(levels: pd.DataFrame) -> pd.DataFrame:
    d = levels.dropna(subset=["data_obs", "valor"]).copy()
    if d.empty:
        return pd.DataFrame(columns=["ano", "valor", "data_obs"])
    d["ano"] = d["data_obs"].dt.year
    return (
        d.sort_values("data_obs")
        .groupby("ano", as_index=False)
        .tail(1)[["ano", "valor", "data_obs"]]
        .sort_values("ano")
        .reset_index(drop=True)
    )


def build_pib_nominal_yoy_por_ano_calendario(
    levels: pd.DataFrame,
    *,
    dias_apos_31dez_para_divulgacao_yoy: int,
) -> pd.DataFrame:
    """Uma linha por ano de referencia Y (crescimento nominal Y sobre Y-1).

    Colunas: ``ano_ref``, ``pib_sgs_nominal_yoy_pct``, ``pib_sgs_yoy_disponivel``.
    """
    by = _um_nivel_por_ano(levels)
    if len(by) < 2:
        return pd.DataFrame(
            columns=["ano_ref", "pib_sgs_nominal_yoy_pct", "pib_sgs_yoy_disponivel"],
        )
    by = by.sort_values("ano")
    by["valor_ant"] = by["valor"].shift(1)
    by["pib_sgs_nominal_yoy_pct"] = (by["valor"] / by["valor_ant"] - 1.0) * 100.0
    by["ano_ref"] = by["ano"].astype(int)
    fim = pd.to_datetime(by["ano_ref"].astype(str) + "-12-31")
    by["pib_sgs_yoy_disponivel"] = fim + pd.to_timedelta(
        dias_apos_31dez_para_divulgacao_yoy,
        unit="D",
    )
    out = by.loc[by["valor_ant"].notna() & (by["valor_ant"] > 0), [
        "ano_ref",
        "pib_sgs_nominal_yoy_pct",
        "pib_sgs_yoy_disponivel",
    ]].copy()
    out["pib_sgs_yoy_disponivel"] = pd.to_datetime(out["pib_sgs_yoy_disponivel"]).dt.normalize()
    return out.reset_index(drop=True)


def fetch_pib_sgs1207_e_yoy(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Baixa SGS ``sgs_codigo_pib_rs_correntes`` e devolve tabela YoY por ``ano_ref``."""
    extra_years = 3
    sgs_start = date(max(1, start.year - extra_years), 1, 1)
    raw = fetch_sgs_json(
        cfg.sgs_codigo_pib_rs_correntes,
        sgs_start,
        end,
        session=session,
    )
    return build_pib_nominal_yoy_por_ano_calendario(
        raw,
        dias_apos_31dez_para_divulgacao_yoy=cfg.sgs_pib1207_dias_apos_31dez_divulgacao,
    )


def colar_yoy_nas_linhas_focus(
    painel: pd.DataFrame,
    yoy_por_ano: pd.DataFrame,
    *,
    market_lag_bdias: int,
) -> pd.DataFrame:
    """Acrescenta ``pib_sgs_nominal_yoy_pct`` via último comunicado já conhecido na data‑chave Focus."""

    out = painel.copy()
    for dropc in ("pib_sgs_nominal_yoy_pct", "pib_sgs_nominal_ano_sidra"):
        if dropc in out.columns:
            out = out.drop(columns=[dropc])

    if yoy_por_ano.empty or "survey_date" not in out.columns:
        out["pib_sgs_nominal_yoy_pct"] = np.nan
        out["pib_sgs_nominal_ano_sidra"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
        return out

    side = (
        yoy_por_ano.assign(
            s_disp=lambda d: pd.to_datetime(d["pib_sgs_yoy_disponivel"]).dt.normalize(),
        )
        .sort_values("s_disp")[
            ["s_disp", "pib_sgs_nominal_yoy_pct", "ano_ref"]
        ]
        .rename(
            columns={
                "pib_sgs_nominal_yoy_pct": "sg_pct",
                "ano_ref": "sg_ano_sidra",
            },
        )
    )
    left = out.copy()
    left["__mk"] = left["survey_date"].map(lambda x: _bd_offset(pd.Timestamp(x), market_lag_bdias))
    m = pd.merge_asof(
        left.sort_values("__mk"),
        side,
        left_on="__mk",
        right_on="s_disp",
        direction="backward",
        allow_exact_matches=True,
    ).sort_values("survey_date")

    drop_tmp = {"__mk", "s_disp"}
    return (
        m.drop(columns=[c for c in drop_tmp if c in m.columns])
        .rename(
            columns={
                "sg_pct": "pib_sgs_nominal_yoy_pct",
                "sg_ano_sidra": "pib_sgs_nominal_ano_sidra",
            },
        )
        .assign(
            pib_sgs_nominal_ano_sidra=lambda d: pd.to_numeric(d["pib_sgs_nominal_ano_sidra"], errors="coerce").astype(
                "Int64",
            ),
        )
        .reset_index(drop=True)
    )
