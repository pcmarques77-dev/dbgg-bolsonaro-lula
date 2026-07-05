"""PIB - variacao em volume (% ao ano), contas anuais, via API SIDRA (IBGE).

Tabela SIDRA **6784**, variavel **9810** (PIB - variacao em volume), Brasil.
Base alinhada as Contas Nacionais do IBGE (mesma linha de produto das series
historicamente divulgadas no portal das contas nacionais trimestrais/anuais):
https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9300-contas-nacionais-trimestrais.html
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import requests

from .config import SIDRA_IBGE_VALUES_BASE, SeriesConfig
from .panel import _bd_offset


def _disponivel_variacao_vol_apos_ano_ref(ano_ref: int, dias_apos_31dez: int) -> pd.Timestamp:
    fim = pd.Timestamp(ano_ref, 12, 31)
    return (fim + pd.Timedelta(days=dias_apos_31dez)).normalize()


def fetch_pib_sidra_variacao_volume_anual(
    start: date,
    end: date,
    *,
    tabela: int,
    codigo_variavel: int,
    dias_apos_31dez_divulgacao: int,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Retorna uma linha por ano de referencia: ``ano_ref``, ``pib_ibge_vol_yoy_pct``, ``disponivel_aprox``.

    ``disponivel_aprox``: proxy da data em que a taxa oficial do ano Y tende a
    estar publicada (`31/12/Y` + `dias_apos_31dez_divulgacao`).
    """
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", "mba-economia-fipe/0.1")
    y0 = start.year - 2
    y1 = max(start.year - 2, end.year + 2)
    desde, ate = f"{max(1950, y0)}", f"{y1}"
    u = (
        f"{SIDRA_IBGE_VALUES_BASE}/t/{tabela}/n1/1/v/{codigo_variavel}"
        f"/p/{desde}-{ate}/h/n/f/c"
    )
    r = sess.get(u, timeout=120)
    r.raise_for_status()
    rows = r.json()
    dados: list[dict] = []
    if isinstance(rows, list):
        for row in rows:
            d3 = row.get("D3C")
            v_raw = row.get("V")
            if not d3 or str(d3).lower() == "valor":
                continue
            if isinstance(v_raw, str) and v_raw.strip() in ("...", "..", "", "-"):
                continue
            val = pd.to_numeric(v_raw, errors="coerce")
            if val is pd.NA or (isinstance(val, float) and np.isnan(val)):
                continue
            try:
                ano = int(str(d3))
            except ValueError:
                continue
            dados.append(
                {
                    "ano_ref": ano,
                    "pib_ibge_vol_yoy_pct": float(val),
                    "disponivel_aprox": _disponivel_variacao_vol_apos_ano_ref(
                        ano,
                        dias_apos_31dez_divulgacao,
                    ),
                },
            )
    out = pd.DataFrame(dados).sort_values("disponivel_aprox").reset_index(drop=True)
    return out


def fetch_pib_ibge_vol_lut(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    return fetch_pib_sidra_variacao_volume_anual(
        start,
        end,
        tabela=cfg.sidra_tab_pib_anual_vol,
        codigo_variavel=cfg.sidra_codigo_var_pib_vol_anual_pct,
        dias_apos_31dez_divulgacao=cfg.sidra_pib_vol_anual_dias_apos_31dez,
        session=session,
    )


def colar_ibge_vol_nas_linhas_focus(
    painel: pd.DataFrame,
    vol_por_ano: pd.DataFrame,
    *,
    market_lag_bdias: int,
) -> pd.DataFrame:
    """Último PIB (variação em volume oficial) já conhecível em cada ``survey_date − lag``.

    Usa ``merge_asof`` para trazer, em cada linha Focus, o último comunicado SIDRA cuja
    ``disponivel_aprox`` é anterior ou igual à chave temporal (pregão até N dias úteis
    antes da survey). Isso permite visualizar uma linha IBGE mesmo quando a expectativa
    Focus mede ano-calendário ainda incompleto (``pib_year_ref`` alinhado à data Focus).
    A coluna ``pib_ibge_vol_ano_sidra`` informa qual ano contábil o percentual refere-se.

    Conceito econômico: laranja = último resultado anual já divulgado; azul =
    expectativa mediana contemporânea (horizonte `pib_year_ref`) — leituras com
    defasagem devem aparecer nos textos MBA.
    """
    out = painel.copy()
    for dropc in ("pib_ibge_vol_yoy_pct", "pib_ibge_vol_ano_sidra"):
        if dropc in out.columns:
            out = out.drop(columns=[dropc])

    if vol_por_ano.empty or "survey_date" not in out.columns:
        out["pib_ibge_vol_yoy_pct"] = np.nan
        out["pib_ibge_vol_ano_sidra"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
        return out

    side = (
        vol_por_ano.assign(
            ib_disp=lambda d: pd.to_datetime(d["disponivel_aprox"]).dt.normalize(),
        )
        .sort_values("ib_disp")[["ib_disp", "pib_ibge_vol_yoy_pct", "ano_ref"]]
        .rename(columns={"pib_ibge_vol_yoy_pct": "ib_pct", "ano_ref": "ib_ano_sidra"})
    )
    left = out.copy()
    left["__mk"] = left["survey_date"].map(lambda x: _bd_offset(pd.Timestamp(x), market_lag_bdias))
    m = pd.merge_asof(
        left.sort_values("__mk"),
        side,
        left_on="__mk",
        right_on="ib_disp",
        direction="backward",
        allow_exact_matches=True,
    ).sort_values("survey_date")

    drop_tmp = {"__mk", "ib_disp"}
    return (
        m.drop(columns=[c for c in drop_tmp if c in m.columns])
        .rename(columns={"ib_pct": "pib_ibge_vol_yoy_pct", "ib_ano_sidra": "pib_ibge_vol_ano_sidra"})
        .assign(
            pib_ibge_vol_ano_sidra=lambda d: pd.to_numeric(d["pib_ibge_vol_ano_sidra"], errors="coerce").astype(
                "Int64",
            ),
        )
        .reset_index(drop=True)
    )
