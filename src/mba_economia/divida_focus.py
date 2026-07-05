"""Expectativas Focus para DLSP e DBGG (Olinda anuais)."""

from __future__ import annotations

import pandas as pd

from .config import OLINDA_BASE
from .focus_extract import _prefer_base_calculo, _parse_survey_date
from .olinda_client import fetch_odata_resource


def fetch_dlsp_expectativa_anual(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """Dívida líquida do setor público (% PIB): mediana Focus por ano de referência."""
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoAnuais",
        filt="contains(Indicador,'Dívida')",
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=["survey_date", "ano_ref", "dlsp_focus_med_pct_pib", "numeroRespondentes"],
        )
    df = df[df["Indicador"].astype(str) == "Dívida líquida do setor público"].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]
    df["ano_ref"] = pd.to_numeric(df["DataReferencia"], errors="coerce").astype("Int64")
    return (
        pd.DataFrame(
            {
                "survey_date": df["survey_date"],
                "ano_ref": df["ano_ref"],
                "dlsp_focus_med_pct_pib": pd.to_numeric(df["Mediana"], errors="coerce"),
                "numeroRespondentes": pd.to_numeric(df["numeroRespondentes"], errors="coerce").astype(
                    "Int64",
                ),
            },
        )
        .sort_values(["survey_date", "ano_ref"])
        .reset_index(drop=True)
    )


def fetch_dbgg_expectativa_anual(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """Dívida bruta do governo geral (% PIB): mediana Focus por ano de referência."""
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoAnuais",
        filt="contains(Indicador,'bruta')",
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=["survey_date", "ano_ref", "dbgg_focus_med_pct_pib", "numeroRespondentes"],
        )
    df = df[df["Indicador"].astype(str) == "Dívida bruta do governo geral"].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]
    df["ano_ref"] = pd.to_numeric(df["DataReferencia"], errors="coerce").astype("Int64")
    return (
        pd.DataFrame(
            {
                "survey_date": df["survey_date"],
                "ano_ref": df["ano_ref"],
                "dbgg_focus_med_pct_pib": pd.to_numeric(df["Mediana"], errors="coerce"),
                "numeroRespondentes": pd.to_numeric(df["numeroRespondentes"], errors="coerce").astype(
                    "Int64",
                ),
            },
        )
        .sort_values(["survey_date", "ano_ref"])
        .reset_index(drop=True)
    )
