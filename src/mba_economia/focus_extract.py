"""Extrai série semanal/agregada de expectativas a partir das tabelas Olinda."""

from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

from .config import OLINDA_BASE, SeriesConfig
from .olinda_client import fetch_odata_resource

logger = logging.getLogger(__name__)


_DATAMM = re.compile(r"^\s*(\d{1,2})\s*/\s*(\d{4})\s*$")
_SELIC = re.compile(r"^\s*R\s*(\d+)\s*/\s*(\d{4})\s*$", re.IGNORECASE)


def _parse_survey_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.normalize()


def _prefer_base_calculo(df: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    """Mantém ``baseCalculo`` 0 ou 1 e, quando houver duplicata na mesma chave, prioriza 1."""
    if df.empty:
        return df
    bc = pd.to_numeric(df["baseCalculo"], errors="coerce")
    idx = bc.isin({0.0, 1.0})
    out = df.loc[idx].copy()
    if out.empty:
        return df.iloc[:0].copy()
    out["_pref_bc1"] = bc.loc[out.index].eq(1)
    out = out.sort_values(subset + ["_pref_bc1"], ascending=[True] * len(subset) + [False])
    return out.drop_duplicates(subset, keep="first").drop(columns=["_pref_bc1"])


def _odata_filter_indicador_data(
    indicador_contains: str,
    filt_start: pd.Timestamp | None,
) -> str:
    """Monta ``$filter`` OData: indicador + opcional corte em ``Data`` (servidor)."""
    parts = [f"contains(Indicador,'{indicador_contains}')"]
    if filt_start is not None:
        iso = filt_start.normalize().strftime("%Y-%m-%dT00:00:00")
        parts.append(f"Data ge datetime'{iso}'")
    return " and ".join(parts)


def _period_from_ref(mm_yyyy: str) -> pd.Period | None:
    if not isinstance(mm_yyyy, str):
        return None
    m = _DATAMM.match(mm_yyyy)
    if not m:
        return None
    mes, ano = int(m.group(1)), int(m.group(2))
    if not (1 <= mes <= 12):
        return None
    return pd.Timestamp(year=ano, month=mes, day=1).to_period("M")


def fetch_ipca_expectativa_12m(
    *,
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """IPCA próximos 12 meses, série não suavizada (Suavizada == ``N``), priorizando ``baseCalculo`` 1."""
    f1 = "contains(Indicador,'IPCA')"
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoInflacao12Meses",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["survey_date"])
    df = df[
        (df["Indicador"].astype(str) == "IPCA")
        & (df["Suavizada"].astype(str) == "N")
    ]
    df = _prefer_base_calculo(df, ["Data"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]
    out = pd.DataFrame(
        {
            "survey_date": df["survey_date"],
            "ipca_med12m": pd.to_numeric(df["Mediana"], errors="coerce"),
            "ipca_med12m_nresp": pd.to_numeric(
                df["numeroRespondentes"],
                errors="coerce",
            ).astype("Int64"),
        },
    )
    return (
        out.sort_values("survey_date")
        .drop_duplicates("survey_date", keep="last")
        .reset_index(drop=True)
    )


def fetch_selic_by_last_meeting_of_year(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """Para cada ``Data`` da pesquisa, última ``Reuniao`` daquele ano-calendário."""
    f1 = "contains(Indicador,'Selic')"
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoSelic",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["survey_date"])
    df = df.loc[df["Indicador"].astype(str) == "Selic"].copy()
    df = _prefer_base_calculo(df, ["Data", "Reuniao"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]

    def _parse_selic(rr: object) -> tuple[int | None, int | None]:
        if not isinstance(rr, str):
            return None, None
        mm = _SELIC.match(rr)
        if not mm:
            return None, None
        return int(mm.group(1)), int(mm.group(2))

    def pick_group(sub: pd.DataFrame) -> pd.Series:
        d0 = int(pd.Timestamp(sub["survey_date"].iloc[0]).year)
        rows_y: list[tuple[int, str, float]] = []
        for _, r in sub.iterrows():
            n_meet, ano = _parse_selic(r["Reuniao"])
            if n_meet is None or ano is None:
                continue
            if ano == d0:
                rows_y.append((n_meet, str(r["Reuniao"]), float(r["Mediana"])))
        if not rows_y:
            return pd.Series({"selic_mediana_pct": np.nan, "selic_meeting_used": ""})
        _n_last, tag, med = sorted(rows_y, key=lambda x: x[0])[-1]
        return pd.Series({"selic_mediana_pct": med, "selic_meeting_used": tag})

    agg: list[dict] = []
    for k, block in df.groupby(df["survey_date"], sort=False):
        sel = pick_group(block).to_dict()
        agg.append({"survey_date": k, **sel})
    return pd.DataFrame(agg).sort_values("survey_date").reset_index(drop=True)


def fetch_selic_expectativa_ano_ref_long(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """Selic (long): mediana por ``survey_date``, reunião (``Reuniao``) e ano de referência.

    Fonte: Olinda ``ExpectativasMercadoSelic`` — [Expectativas de Mercado](https://dadosabertos.bcb.gov.br/dataset/expectativas-mercado).
    """
    f1 = "contains(Indicador,'Selic')"
    logger.info(
        "Baixando Selic longo (ExpectativasMercadoSelic)%s...",
        f" (filtro Data no cliente desde {filt_start.date()})" if filt_start is not None else "",
    )
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoSelic",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "survey_date",
                "selic_year_ref",
                "n_reuniao",
                "reuniao",
                "selic_focus_pct",
                "selic_focus_nresp",
            ],
        )
    df = df.loc[df["Indicador"].astype(str) == "Selic"].copy()
    df = _prefer_base_calculo(df, ["Data", "Reuniao"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]

    def _parse_reuniao(rr: object) -> tuple[int | None, int | None]:
        if not isinstance(rr, str):
            return None, None
        mm = _SELIC.match(rr)
        if not mm:
            return None, None
        return int(mm.group(1)), int(mm.group(2))

    parsed = df["Reuniao"].map(_parse_reuniao)
    df["n_reuniao"] = [p[0] for p in parsed]
    df["selic_year_ref"] = [p[1] for p in parsed]
    df = df.dropna(subset=["n_reuniao", "selic_year_ref"])
    df["selic_year_ref"] = df["selic_year_ref"].astype(int)
    df["n_reuniao"] = df["n_reuniao"].astype(int)

    out = pd.DataFrame(
        {
            "survey_date": df["survey_date"],
            "selic_year_ref": df["selic_year_ref"],
            "n_reuniao": df["n_reuniao"],
            "reuniao": df["Reuniao"].astype(str),
            "selic_focus_pct": pd.to_numeric(df["Mediana"], errors="coerce"),
            "selic_focus_nresp": pd.to_numeric(
                df["numeroRespondentes"],
                errors="coerce",
            ).astype("Int64"),
        },
    )
    return out.sort_values(["selic_year_ref", "survey_date", "n_reuniao"]).reset_index(drop=True)


def fetch_cambio_mensal_mediana_horizon_months_after(
    months_ahead: int,
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """Câmbio: mediana esperada em horizonte aproximado ``months_ahead`` após a survey."""
    f1 = "contains(Indicador,'Câmbio')"
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativaMercadoMensais",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["survey_date"])
    df = df[
        (df["Indicador"].astype(str) == "Câmbio")
    ].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]

    def pick_fwd(sub: pd.DataFrame) -> pd.Series:
        d0 = pd.Timestamp(sub["survey_date"].iloc[0])
        target = (d0 + pd.DateOffset(months=months_ahead)).to_period("M")
        best = None
        best_diff = None
        best_ref = None
        for _, r in sub.iterrows():
            per = _period_from_ref(str(r["DataReferencia"]))
            if per is None:
                continue
            diff = abs((per.year - target.year) * 12 + (per.month - target.month))
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best = float(r["Mediana"])
                best_ref = str(r["DataReferencia"])
        return pd.Series(
            {
                "usdbrl_med_fwd": best if best is not None else np.nan,
                "cambio_ref_used": best_ref or "",
            },
        )

    out_rows: list[dict] = []
    for k, block in df.groupby(df["survey_date"], sort=False):
        row = pick_fwd(block).to_dict()
        out_rows.append({"survey_date": k, **row})
    return pd.DataFrame(out_rows).sort_values("survey_date").reset_index(drop=True)


def fetch_ipca_expectativa_mensal_long(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """IPCA mensal (Focus): mediana por ``survey_date`` e mês de referência (``MM/AAAA``).

    Fonte: Olinda ``ExpectativaMercadoMensais``, indicador IPCA.
    """
    # ExpectativaMercadoMensais rejeita $filter com ``Data ge`` (HTTP 400); corta no cliente.
    f1 = _odata_filter_indicador_data("IPCA", None)
    logger.info(
        "Baixando IPCA mensal (ExpectativaMercadoMensais)%s...",
        f" (filtro Data no cliente desde {filt_start.date()})" if filt_start is not None else "",
    )
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativaMercadoMensais",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "survey_date",
                "ref_yyyymm",
                "ipca_focus_med_mensal_pct",
                "ipca_focus_mensal_nresp",
            ],
        )
    df = df[(df["Indicador"].astype(str) == "IPCA")].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]
    df["ref_period"] = df["DataReferencia"].map(_period_from_ref)
    df = df.dropna(subset=["ref_period"])
    df["ref_yyyymm"] = df["ref_period"].astype(str).str.replace("-", "")
    out = pd.DataFrame(
        {
            "survey_date": df["survey_date"],
            "ref_yyyymm": df["ref_yyyymm"],
            "ipca_focus_med_mensal_pct": pd.to_numeric(df["Mediana"], errors="coerce"),
            "ipca_focus_mensal_nresp": pd.to_numeric(
                df["numeroRespondentes"],
                errors="coerce",
            ).astype("Int64"),
        },
    )
    return out.sort_values(["ref_yyyymm", "survey_date"]).reset_index(drop=True)


def fetch_ipca_expectativa_ano_calendario(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """IPCA ano-calendário corrente: mediana Focus para o ano igual ao da ``survey_date``.

    Fonte: Olinda ``ExpectativasMercadoAnuais``, ``DataReferencia`` = AAAA.
    """
    # ExpectativasMercadoAnuais rejeita $filter com ``Data ge`` (HTTP 400); corta no cliente.
    f1 = _odata_filter_indicador_data("IPCA", None)
    logger.info(
        "Baixando IPCA ano-calendário (ExpectativasMercadoAnuais)%s...",
        f" desde {filt_start.date()}" if filt_start is not None else "",
    )
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoAnuais",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=["survey_date", "ipca_focus_ano_pct", "ipca_year_ref", "ipca_focus_ano_nresp"],
        )
    df = df[(df["Indicador"].astype(str) == "IPCA")].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]

    def pick_ano_corrente(sub: pd.DataFrame) -> pd.Series:
        y = str(pd.Timestamp(sub["survey_date"].iloc[0]).year)
        suby = sub[sub["DataReferencia"].astype(str) == y]
        if suby.empty:
            return pd.Series(
                {
                    "ipca_focus_ano_pct": np.nan,
                    "ipca_year_ref": y,
                    "ipca_focus_ano_nresp": pd.NA,
                },
            )
        r = suby.sort_values(["Data"]).iloc[-1]
        return pd.Series(
            {
                "ipca_focus_ano_pct": float(r["Mediana"]),
                "ipca_year_ref": y,
                "ipca_focus_ano_nresp": pd.to_numeric(
                    r["numeroRespondentes"],
                    errors="coerce",
                ),
            },
        )

    agg: list[dict] = []
    for k, block in df.groupby(df["survey_date"], sort=False):
        agg.append({"survey_date": k, **pick_ano_corrente(block).to_dict()})
    return pd.DataFrame(agg).sort_values("survey_date").reset_index(drop=True)


def fetch_ipca_expectativa_ano_ref_long(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """IPCA ano-calendário (long): mediana por ``survey_date`` e ``DataReferencia`` (AAAA).

    Fonte: Olinda ``ExpectativasMercadoAnuais`` — [Expectativas de Mercado](https://dadosabertos.bcb.gov.br/dataset/expectativas-mercado).
    """
    # ExpectativasMercadoAnuais rejeita $filter com ``Data ge`` (HTTP 400); corta no cliente.
    f1 = _odata_filter_indicador_data("IPCA", None)
    logger.info(
        "Baixando IPCA ano-calendário longo (ExpectativasMercadoAnuais)%s...",
        f" (filtro Data no cliente desde {filt_start.date()})" if filt_start is not None else "",
    )
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoAnuais",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "survey_date",
                "ipca_year_ref",
                "ipca_focus_ano_pct",
                "ipca_focus_ano_nresp",
            ],
        )
    df = df[(df["Indicador"].astype(str) == "IPCA")].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]
    df["ipca_year_ref"] = pd.to_numeric(df["DataReferencia"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["ipca_year_ref"])
    out = pd.DataFrame(
        {
            "survey_date": df["survey_date"],
            "ipca_year_ref": df["ipca_year_ref"].astype(int),
            "ipca_focus_ano_pct": pd.to_numeric(df["Mediana"], errors="coerce"),
            "ipca_focus_ano_nresp": pd.to_numeric(
                df["numeroRespondentes"],
                errors="coerce",
            ).astype("Int64"),
        },
    )
    return out.sort_values(["ipca_year_ref", "survey_date"]).reset_index(drop=True)


def fetch_pib_expectativa_ano_ref_long(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """PIB Total ano-calendário (long): mediana por ``survey_date`` e ``DataReferencia`` (AAAA).

    Fonte: Olinda ``ExpectativasMercadoAnuais``, ``Indicador == 'PIB Total'``.
    """
    f1 = "contains(Indicador,'PIB')"
    logger.info(
        "Baixando PIB Total ano-calendário longo (ExpectativasMercadoAnuais)%s...",
        f" (filtro Data no cliente desde {filt_start.date()})" if filt_start is not None else "",
    )
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoAnuais",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "survey_date",
                "pib_year_ref",
                "pib_focus_ano_pct",
                "pib_focus_ano_nresp",
            ],
        )
    df = df[(df["Indicador"].astype(str) == "PIB Total")].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]
    df["pib_year_ref"] = pd.to_numeric(df["DataReferencia"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["pib_year_ref"])
    out = pd.DataFrame(
        {
            "survey_date": df["survey_date"],
            "pib_year_ref": df["pib_year_ref"].astype(int),
            "pib_focus_ano_pct": pd.to_numeric(df["Mediana"], errors="coerce"),
            "pib_focus_ano_nresp": pd.to_numeric(
                df["numeroRespondentes"],
                errors="coerce",
            ).astype("Int64"),
        },
    )
    return out.sort_values(["pib_year_ref", "survey_date"]).reset_index(drop=True)


def _parse_trimestre_data_referencia(ref: object) -> tuple[int, int] | None:
    """``DataReferencia`` trimestral Focus (ex.: ``1/2023`` → tri=1, ano=2023)."""
    m = _DATAMM.match(str(ref))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def fetch_pib_total_expectativa_trimestral(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """PIB Total trimestral (long): mediana por survey e trimestre de referência.

    Fonte: Olinda ``ExpectativasMercadoTrimestrais``, ``Indicador == 'PIB Total'``.
    """
    f1 = "contains(Indicador,'PIB')"
    logger.info(
        "Baixando PIB Total trimestral (ExpectativasMercadoTrimestrais)%s...",
        f" (filtro Data no cliente desde {filt_start.date()})" if filt_start is not None else "",
    )
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoTrimestrais",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "survey_date",
                "tri_ref",
                "ano_ref",
                "pib_focus_trim_med_pct",
                "numeroRespondentes",
            ],
        )
    df = df[(df["Indicador"].astype(str) == "PIB Total")].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]
    parsed = df["DataReferencia"].map(_parse_trimestre_data_referencia)
    df["tri_ref"] = parsed.map(lambda x: x[0] if x else np.nan)
    df["ano_ref"] = parsed.map(lambda x: x[1] if x else np.nan)
    df = df.dropna(subset=["tri_ref", "ano_ref"])
    out = pd.DataFrame(
        {
            "survey_date": df["survey_date"],
            "tri_ref": df["tri_ref"].astype(int),
            "ano_ref": df["ano_ref"].astype(int),
            "pib_focus_trim_med_pct": pd.to_numeric(df["Mediana"], errors="coerce"),
            "numeroRespondentes": pd.to_numeric(
                df["numeroRespondentes"],
                errors="coerce",
            ).astype("Int64"),
        },
    )
    return out.sort_values(["ano_ref", "tri_ref", "survey_date"]).reset_index(drop=True)


def fetch_pib_total_expectativa_calendar_year_same_as_survey(
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    """PIB Total: mediana esperada para o **ano-calendário** igual ao ano da própria ``Data``."""
    f1 = "contains(Indicador,'PIB')"
    rows = fetch_odata_resource(
        OLINDA_BASE,
        "ExpectativasMercadoAnuais",
        filt=f1,
        orderby="Data",
        session=session,
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["survey_date"])
    df = df[
        (df["Indicador"].astype(str) == "PIB Total")
    ].copy()
    df = _prefer_base_calculo(df, ["Data", "DataReferencia"])
    df["survey_date"] = _parse_survey_date(df["Data"])
    if filt_start is not None:
        df = df[df["survey_date"] >= filt_start.normalize()]

    def pick_calendar(sub: pd.DataFrame) -> pd.Series:
        y = str(pd.Timestamp(sub["survey_date"].iloc[0]).year)
        suby = sub[sub["DataReferencia"].astype(str) == y]
        if suby.empty:
            return pd.Series({"pib_med_pct": np.nan, "pib_year_ref": y})
        r = suby.sort_values(["Data"]).iloc[-1]
        return pd.Series({"pib_med_pct": float(r["Mediana"]), "pib_year_ref": y})

    agg: list[dict] = []
    for k, block in df.groupby(df["survey_date"], sort=False):
        agg.append({"survey_date": k, **pick_calendar(block)})
    return pd.DataFrame(agg).sort_values("survey_date").reset_index(drop=True)


def build_focus_wide(
    cfg: SeriesConfig,
    *,
    filt_start: pd.Timestamp | None = None,
    session=None,
) -> pd.DataFrame:
    pieces: dict[str, pd.DataFrame] = {
        "ipca": fetch_ipca_expectativa_12m(filt_start=filt_start, session=session),
        "selic": fetch_selic_by_last_meeting_of_year(
            filt_start=filt_start,
            session=session,
        ),
        "cambio": fetch_cambio_mensal_mediana_horizon_months_after(
            cfg.months_ahead_cambio,
            filt_start=filt_start,
            session=session,
        ),
        "pib": fetch_pib_total_expectativa_calendar_year_same_as_survey(
            filt_start=filt_start,
            session=session,
        ),
    }
    merged = pieces["ipca"].copy()
    merged = merged.merge(pieces["selic"], on="survey_date", how="outer")
    merged = merged.merge(pieces["cambio"], on="survey_date", how="outer")
    merged = merged.merge(pieces["pib"], on="survey_date", how="outer")
    return merged.sort_values("survey_date").reset_index(drop=True)
