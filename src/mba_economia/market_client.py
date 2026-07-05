from __future__ import annotations

import logging
from datetime import date
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Mapeamento de nomes descritivos para os tickers reais do Yahoo Finance
DEFAULT_TICKERS: Dict[str, str] = {
    "ibovespa": "^BVSP",
    "vix": "^VIX",
    "commodities": "DBC",  # Invesco DB Commodity Index (proxy confiável para CRB)
}


def fetch_market_data(
    start_date: str,
    end_date: str,
    tickers_map: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Baixa dados de fechamento diário do mercado financeiro e variáveis de controle global.

    Args:
        start_date: Data de início no formato 'YYYY-MM-DD'.
        end_date: Data de fim no formato 'YYYY-MM-DD' (exclusiva no yfinance, como na CLI).
        tickers_map: Dicionário opcional mapeando {nome_amigavel: ticker_yfinance}.

    Returns:
        pd.DataFrame com a data (market_date) timezone-naive e colunas para cada ativo.
    """
    import yfinance as yf

    if tickers_map is None:
        tickers_map = DEFAULT_TICKERS

    symbols = list(tickers_map.values())
    logger.info("Baixando dados via yfinance para os tickers: %s", symbols)

    try:
        df_raw = yf.download(
            symbols,
            start=start_date,
            end=end_date,
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        if df_raw.empty:
            logger.warning("Nenhum dado retornado pelo yfinance para as datas especificadas.")
            return pd.DataFrame()

        if isinstance(df_raw.columns, pd.MultiIndex):
            lvl0 = set(df_raw.columns.get_level_values(0))
            field = "Close" if "Close" in lvl0 else "Adj Close"
            df_close = df_raw.xs(field, axis=1, level=0).copy()
        else:
            df_close = df_raw.get("Close", df_raw.get("Adj Close", df_raw)).copy()
            if isinstance(df_close, pd.Series):
                df_close = df_close.to_frame(name=symbols[0])

        if isinstance(df_close, pd.Series):
            df_close = df_close.to_frame()
            df_close.columns = [symbols[0]]

        inv_map = {ticker: name for name, ticker in tickers_map.items()}
        df_close = df_close.rename(columns=inv_map)

        df_final = df_close.reset_index()
        date_col = "Date" if "Date" in df_final.columns else df_final.columns[0]
        df_final["market_date"] = pd.to_datetime(df_final[date_col]).dt.tz_localize(None)

        if date_col != "market_date":
            df_final = df_final.drop(columns=[date_col])

        cols = ["market_date"] + [c for c in df_final.columns if c != "market_date"]
        df_final = df_final[cols]
        df_final = df_final.sort_values("market_date").reset_index(drop=True)

        return df_final

    except Exception as e:
        logger.error("Falha ao extrair dados de mercado: %s", e)
        raise


def fetch_ibovespa_close(
    start: date,
    end_exclusive: date,
    *,
    symbol: str,
) -> pd.DataFrame:
    """Fechamentos diários via yfinance (proxy B3).

    Nota metodológica: índice oficial B3 pode divergir marginalmente; cite o símbolo.
    """
    empty = pd.DataFrame(columns=["data_obs", "ibov_fech"]).astype({"ibov_fech": float})

    try:
        wide = fetch_market_data(
            start.isoformat(),
            pd.Timestamp(end_exclusive).date().isoformat(),
            tickers_map={"ibovespa": symbol},
        )
    except Exception:
        return empty

    if wide.empty or "ibovespa" not in wide.columns:
        return empty

    serie = (
        wide.rename(columns={"market_date": "data_obs", "ibovespa": "ibov_fech"})[
            ["data_obs", "ibov_fech"]
        ]
        .assign(ibov_fech=lambda d: pd.to_numeric(d["ibov_fech"], errors="coerce"))
        .dropna(subset=["ibov_fech"])
        .sort_values("data_obs")
        .reset_index(drop=True)
    )
    return serie
