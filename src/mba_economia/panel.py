"""Alinha expectativas Focus a séries diárias (merge_asof)."""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd

from .config import SeriesConfig
from .sgs_client import preparar_selic_sgs11_diaria_para_painel

logger = logging.getLogger(__name__)


def _bd_offset(ts: pd.Timestamp, n: int) -> pd.Timestamp:
    ts0 = pd.Timestamp(ts).normalize()
    if n == 0:
        return ts0
    return ts0 - pd.offsets.BDay(n)


def _as_merge_key(series: pd.Series) -> pd.Series:
    """Unifica dtype temporal para ``merge_asof`` (datetime64[ns], timezone-naive)."""
    return pd.to_datetime(series).dt.normalize().astype("datetime64[ns]")


def generate_analysis_panel(
    df_focus: pd.DataFrame,
    df_market: pd.DataFrame,
    *,
    focus_date_col: str = "survey_date",
    market_date_col: str = "market_date",
    market_lag_bdias: int = 0,
) -> pd.DataFrame:
    """
    Combina Focus com mercado (yfinance) via ``merge_asof`` e injeta dummies (governo, pandemia).

    CRÍTICO: ambos os lados devem estar ordenados pela data antes do merge.

    Args:
        df_focus: expectativas Focus (wide).
        df_market: saída de ``fetch_market_data`` (Ibovespa, VIX, commodities).
        focus_date_col: coluna de data no Focus.
        market_date_col: coluna de data no mercado.
        market_lag_bdias: dias úteis de lag do pregão (0 = alinha na própria ``survey_date``).

    Returns:
        Painel com colunas de mercado e ``dummy_lula``, ``dummy_pandemia``.
    """
    df_focus = df_focus.copy()
    if df_market.empty:
        logger.warning("df_market vazio; retornando Focus apenas com dummies estruturais.")
        return _inject_structural_dummies(df_focus, focus_date_col)

    df_market = df_market.copy()

    df_focus[focus_date_col] = _as_merge_key(df_focus[focus_date_col])
    df_market[market_date_col] = _as_merge_key(df_market[market_date_col])

    df_focus = df_focus.sort_values(focus_date_col).reset_index(drop=True)
    df_market = df_market.sort_values(market_date_col).reset_index(drop=True)

    if market_lag_bdias > 0:
        merge_left_col = "_merge_asof_key"
        df_focus[merge_left_col] = _as_merge_key(
            df_focus[focus_date_col].map(lambda x: _bd_offset(x, market_lag_bdias)),
        )
        left_on = merge_left_col
    else:
        merge_left_col = None
        left_on = focus_date_col

    logger.info(
        "Alinhando painel. Focus: %s até %s (lag BD=%s)",
        df_focus[focus_date_col].min().strftime("%Y-%m-%d"),
        df_focus[focus_date_col].max().strftime("%Y-%m-%d"),
        market_lag_bdias,
    )

    df_panel = pd.merge_asof(
        df_focus,
        df_market,
        left_on=left_on,
        right_on=market_date_col,
        direction="backward",
        allow_exact_matches=True,
    )

    if merge_left_col is not None:
        df_panel = df_panel.drop(columns=[merge_left_col])

    df_panel = _inject_structural_dummies(df_panel, focus_date_col)

    market_value_cols = [
        c
        for c in df_market.columns
        if c != market_date_col and c in df_panel.columns
    ]
    if market_value_cols:
        nans_detected = int(df_panel[market_value_cols].isna().sum().max())
        if nans_detected > 0:
            logger.warning(
                "Detectadas %s linhas sem correspondência de mercado no início do painel. "
                "Normal se o histórico Focus for mais antigo que o de mercado (sem ffill).",
                nans_detected,
            )

    return _normalize_market_column_names(df_panel, market_date_col)


def _inject_structural_dummies(df: pd.DataFrame, focus_date_col: str) -> pd.DataFrame:
    """Dummy governo (Lula 2023+) e pandemia (mar/2020–dez/2021)."""
    logger.info("Injetando variáveis dummy de controle (Governo e Pandemia) no painel.")
    out = df.copy()
    out[focus_date_col] = _as_merge_key(out[focus_date_col])

    out["dummy_lula"] = (out[focus_date_col].dt.year >= 2023).astype(int)

    start_pandemic = pd.Timestamp("2020-03-01")
    end_pandemic = pd.Timestamp("2021-12-31")
    out["dummy_pandemia"] = (
        (out[focus_date_col] >= start_pandemic) & (out[focus_date_col] <= end_pandemic)
    ).astype(int)

    return out


def _normalize_market_column_names(
    df: pd.DataFrame,
    market_date_col: str,
) -> pd.DataFrame:
    """Mantém nomes legados do MVP (``ibov_fech``, ``*_trade_date``)."""
    out = df.copy()
    if "ibovespa" in out.columns:
        out["ibov_fech"] = pd.to_numeric(out["ibovespa"], errors="coerce")
    if market_date_col in out.columns:
        td = out[market_date_col]
        out["ibov_trade_date"] = td
        if "vix" in out.columns:
            out["vix_trade_date"] = td
        if "commodities" in out.columns:
            out["commodities_trade_date"] = td
    return out


def _merge_asof_side(
    left: pd.DataFrame,
    side: pd.DataFrame,
    *,
    right_on: str,
) -> pd.DataFrame:
    if side.empty:
        return left
    left = left.sort_values("merge_asof_key")
    return pd.merge_asof(
        left,
        side,
        left_on="merge_asof_key",
        right_on=right_on,
        direction="backward",
        allow_exact_matches=True,
    )


def attach_usd_daily(
    panel: pd.DataFrame,
    usd_daily: pd.DataFrame,
    *,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    """Anexa taxa USD diária (SGS) ao painel já mesclado com mercado."""
    if panel.empty or usd_daily.empty:
        return panel.copy()

    out = panel.copy()
    out["survey_date"] = pd.to_datetime(out["survey_date"]).dt.normalize()
    out["merge_asof_key"] = _as_merge_key(
        out["survey_date"].map(lambda x: _bd_offset(x, cfg.market_lag_bdias)),
    )
    usd_side = (
        usd_daily.assign(usd_trade_date=_as_merge_key(usd_daily["data_obs"]))
        .rename(columns={"valor": "usd_sgs_med"})
        .sort_values("usd_trade_date")[["usd_trade_date", "usd_sgs_med"]]
    )
    merged = _merge_asof_side(out.sort_values("merge_asof_key"), usd_side, right_on="usd_trade_date")
    return (
        merged.drop(columns=["merge_asof_key"])
        .sort_values("survey_date")
        .reset_index(drop=True)
    )


def attach_markets(
    focus: pd.DataFrame,
    *,
    usd_daily: pd.DataFrame,
    cfg: SeriesConfig,
    market_daily: pd.DataFrame | None = None,
    ibov_daily: pd.DataFrame | None = None,
    selic_daily: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Anexa USD (SGS), mercado yfinance (via ``generate_analysis_panel``) e Selic SGS 11 opcional.

    Chave temporal do USD/Selic: ``survey_date − market_lag_bdias`` (dias úteis).
    """
    if focus.empty:
        return focus.copy()

    merged = attach_usd_daily(focus, usd_daily, cfg=cfg)

    if market_daily is not None and not market_daily.empty:
        merged = generate_analysis_panel(
            merged,
            market_daily,
            market_lag_bdias=cfg.market_lag_bdias,
        )
    elif ibov_daily is not None and not ibov_daily.empty:
        legacy_market = ibov_daily.rename(
            columns={"data_obs": "market_date", "ibov_fech": "ibovespa"},
        )
        merged = generate_analysis_panel(
            merged,
            legacy_market[["market_date", "ibovespa"]],
            market_lag_bdias=cfg.market_lag_bdias,
        )
    else:
        merged = _inject_structural_dummies(merged, "survey_date")

    if selic_daily is not None and not selic_daily.empty:
        merged = attach_selic_daily(merged, selic_daily, cfg=cfg)

    return merged.sort_values("survey_date").reset_index(drop=True)


def attach_selic_daily(
    panel: pd.DataFrame,
    selic_daily: pd.DataFrame,
    *,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    """Anexa Selic diária SGS 11 (spot anualizado) ao painel."""
    if panel.empty or selic_daily.empty:
        return panel.copy()

    prep = preparar_selic_sgs11_diaria_para_painel(selic_daily)
    if prep.empty:
        return panel.copy()

    out = panel.copy()
    out["merge_asof_key"] = _as_merge_key(
        pd.to_datetime(out["survey_date"]).map(lambda x: _bd_offset(x, cfg.market_lag_bdias)),
    )
    sel_side = (
        prep.assign(selic_trade_date=_as_merge_key(prep["data_obs"]))
        .sort_values("selic_trade_date")[
            ["selic_trade_date", "selic_sgs_pct_ad", "selic_sgs_pct_aa_aprox"]
        ]
    )
    merged = _merge_asof_side(out.sort_values("merge_asof_key"), sel_side, right_on="selic_trade_date")
    return merged.drop(columns=["merge_asof_key"], errors="ignore").reset_index(drop=True)


def attach_ibge_ipca_acum12_como_realizado_conhecido(
    focus_panel: pd.DataFrame,
    ipca_sidra_monthly: pd.DataFrame,
    *,
    market_lag_bdias: int,
) -> pd.DataFrame:
    """Anexa IPCA oficial (% acum. em 12 meses) já conhecível na data-chave Focus.

    ``merge_asof`` traz o último mês SIDRA cuja ``disponivel_aprox`` é anterior
    ou igual a ``survey_date − market_lag_bdias`` (mesma convenção do USD/Ibov).
    """
    if focus_panel.empty:
        return focus_panel.copy()

    out = focus_panel.copy()
    if ipca_sidra_monthly.empty:
        out["ipca_ibge_acum12m_pct"] = float("nan")
        out["ipca_ibge_ref_yyyymm"] = pd.Series(pd.NA, index=out.index, dtype="string")
        return out

    side = (
        ipca_sidra_monthly.assign(
            disponivel_aprox=lambda d: pd.to_datetime(d["disponivel_aprox"]).dt.normalize(),
        )
        .rename(columns={"disponivel_aprox": "ibge_ipca_disponivel_aprox"})
        .sort_values("ibge_ipca_disponivel_aprox")[
            ["ibge_ipca_disponivel_aprox", "ipca_ibge_acum12m_pct", "ibge_period_yyyymm"]
        ]
    )

    out["survey_date"] = pd.to_datetime(out["survey_date"]).dt.normalize()
    out["_mk"] = out["survey_date"].map(lambda x: _bd_offset(x, market_lag_bdias))
    out = out.sort_values("_mk")

    merged = pd.merge_asof(
        out,
        side,
        left_on="_mk",
        right_on="ibge_ipca_disponivel_aprox",
        direction="backward",
        allow_exact_matches=True,
    )
    merged = merged.rename(columns={"ibge_period_yyyymm": "ipca_ibge_ref_yyyymm"})
    return (
        merged.drop(columns=["_mk", "ibge_ipca_disponivel_aprox"])
        .sort_values("survey_date")
        .reset_index(drop=True)
    )


def subset_window(
    df: pd.DataFrame,
    start: date | None,
    end_inclusive: date | None,
) -> pd.DataFrame:
    dd = pd.to_datetime(df["survey_date"]).dt.normalize()
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= dd >= pd.Timestamp(start)
    if end_inclusive is not None:
        mask &= dd <= pd.Timestamp(end_inclusive)
    return df.loc[mask].reset_index(drop=True)


def add_dbgg_and_desancoragem_columns(df_panel: pd.DataFrame, session=None) -> pd.DataFrame:
    """Anexa colunas de desancoragem do IPCA e expectativas de dívida bruta (DBGG)."""
    import logging
    logger = logging.getLogger(__name__)
    out = df_panel.copy()
    
    # 1. Obter e mesclar expectativas da DBGG
    try:
        from .divida_focus import fetch_dbgg_expectativa_anual
        min_date = pd.to_datetime(out["survey_date"]).min()
        df_dbgg = fetch_dbgg_expectativa_anual(filt_start=pd.Timestamp(min_date), session=session)
        if not df_dbgg.empty:
            df_dbgg["survey_date"] = pd.to_datetime(df_dbgg["survey_date"]).dt.normalize()
            df_dbgg = df_dbgg.rename(columns={"dbgg_focus_med_pct_pib": "dbgg_med_pct", "ano_ref": "dbgg_year_ref"})
            out["dbgg_year_ref"] = pd.to_datetime(out["survey_date"]).dt.year
            out = out.merge(
                df_dbgg[["survey_date", "dbgg_year_ref", "dbgg_med_pct"]],
                on=["survey_date", "dbgg_year_ref"],
                how="left",
            )
        else:
            out["dbgg_med_pct"] = float("nan")
            out["dbgg_year_ref"] = pd.to_datetime(out["survey_date"]).dt.year
    except Exception as e:
        logger.warning(f"Falha ao obter expectativas de DBGG: {e}")
        out["dbgg_med_pct"] = float("nan")
        out["dbgg_year_ref"] = pd.to_datetime(out["survey_date"]).dt.year

    # 2. Calcular a meta móvel de inflação (CMN) de 12 meses à frente
    # Busca metas reais do BCB (SGS 13521); fallback para valores históricos
    _FALLBACK_CMN = {
        2018: 4.50, 2019: 4.25, 2020: 4.00, 2021: 3.75, 2022: 3.50,
        2023: 3.25, 2024: 3.00, 2025: 3.00, 2026: 3.00, 2027: 3.00,
    }
    try:
        from .bcb_meta_inflacao import fetch_metas_inflacao_sgs, metas_como_dict
        from datetime import date as _date
        survey_dates_tmp = pd.to_datetime(out["survey_date"])
        _start = _date(int(survey_dates_tmp.dt.year.min()), 1, 1)
        _end = _date(int(survey_dates_tmp.dt.year.max()) + 1, 12, 31)
        _metas_df = fetch_metas_inflacao_sgs(_start, _end, session=session)
        if _metas_df.empty:
            raise ValueError("SGS 13521 retornou vazio")
        _metas_dict = metas_como_dict(_metas_df)
        CMN_TARGET_CENTERS = {y: v["centro"] for y, v in _metas_dict.items()}
        logger.info("Metas CMN carregadas do BCB SGS 13521: %s anos", len(CMN_TARGET_CENTERS))
    except Exception as _e:
        logger.warning("Falha ao buscar metas CMN do BCB: %s — usando fallback hardcoded.", _e)
        CMN_TARGET_CENTERS = _FALLBACK_CMN

    survey_dates = pd.to_datetime(out["survey_date"])
    years = survey_dates.dt.year
    months = survey_dates.dt.month
    
    centers = []
    inferiors = []
    superiors = []
    
    for y, m in zip(years, months):
        c_y = CMN_TARGET_CENTERS.get(y, 3.00)
        c_y1 = CMN_TARGET_CENTERS.get(y + 1, 3.00)
        
        # Meta ponderada: 12-m à frente
        center = ((12 - m) * c_y + m * c_y1) / 12.0
        centers.append(center)
        inferiors.append(center - 1.50)
        superiors.append(center + 1.50)
        
    out["ipca_meta_centro_12m"] = centers
    out["ipca_meta_inferior_12m"] = inferiors
    out["ipca_meta_superior_12m"] = superiors
    
    # Calcular desancoragem
    out["desancoragem_centro_12m"] = out["ipca_med12m"] - out["ipca_meta_centro_12m"]
    out["desancoragem_absoluta_12m"] = out["desancoragem_centro_12m"].abs()
    
    return out
