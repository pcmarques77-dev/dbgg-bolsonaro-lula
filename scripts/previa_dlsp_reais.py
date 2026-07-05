"""Prévia: DLSP em R$ (SGS 4478) + % PIB (SGS 4513), dez/ano, 2019–."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from mba_economia.bcb_dlsp_sgs4513 import fetch_dlsp_sgs4513_anual
from mba_economia.config import SeriesConfig
from mba_economia.sgs_client import fetch_sgs_json

# https://dadosabertos.bcb.gov.br/dataset/4478-divida-liquida-do-setor-publico---saldos-em-rs-milhoes---total---setor-publico-consolidado
SGS_DLSP_RS_MILHOES = 4478


def previa_dlsp_reais(
    *,
    ano_ini: int = 2019,
    ano_fim: int | None = None,
    out_dir: Path = Path("output/DIVIDA"),
    session: requests.Session | None = None,
) -> Path:
    cfg = SeriesConfig()
    sess = session or requests.Session()
    if ano_fim is None:
        ano_fim = date.today().year

    raw = fetch_sgs_json(SGS_DLSP_RS_MILHOES, date(ano_ini, 1, 1), date(ano_fim, 12, 31), session=sess)
    dez = raw.loc[raw["data_obs"].dt.month == 12].copy()
    dez["ano"] = dez["data_obs"].dt.year.astype(int)
    dez = dez.groupby("ano", as_index=False).tail(1)
    dez = dez[(dez["ano"] >= ano_ini) & (dez["ano"] <= ano_fim)]

    pct = fetch_dlsp_sgs4513_anual(ano_ini, ano_fim, cfg, session=sess)
    prev = dez.merge(
        pct[["ano_ref", "dlsp_sgs_pct_pib"]],
        left_on="ano",
        right_on="ano_ref",
        how="left",
    ).sort_values("ano")

    prev["dlsp_rs_milhoes"] = prev["valor"].astype(float)
    prev["dlsp_rs_bi"] = prev["dlsp_rs_milhoes"] / 1000.0
    prev["dlsp_rs_trilhoes"] = prev["dlsp_rs_milhoes"] / 1_000_000.0
    prev["dlsp_yoy_pct_nominal"] = prev["dlsp_rs_milhoes"].pct_change() * 100.0
    prev["dlsp_yoy_pp_pib"] = prev["dlsp_sgs_pct_pib"].diff()

    out = prev[
        [
            "ano",
            "dlsp_rs_milhoes",
            "dlsp_rs_bi",
            "dlsp_rs_trilhoes",
            "dlsp_sgs_pct_pib",
            "dlsp_yoy_pct_nominal",
            "dlsp_yoy_pp_pib",
            "data_obs",
        ]
    ].rename(columns={"dlsp_sgs_pct_pib": "dlsp_pct_pib", "data_obs": "referencia_dez"})

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "previa_dlsp_reais.csv"
    out.to_csv(path, index=False)
    return path


def main() -> None:
    p = argparse.ArgumentParser(description="Prévia DLSP em R$ (SGS 4478 + 4513).")
    p.add_argument("--ano-ini", type=int, default=2019)
    p.add_argument("--ano-fim", type=int, default=None)
    p.add_argument("--out-dir", type=Path, default=Path("output/DIVIDA"))
    args = p.parse_args()
    path = previa_dlsp_reais(ano_ini=args.ano_ini, ano_fim=args.ano_fim, out_dir=args.out_dir)
    df = pd.read_csv(path)
    print(f"Prévia salva em {path}\n")
    print(df.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))


if __name__ == "__main__":
    main()
