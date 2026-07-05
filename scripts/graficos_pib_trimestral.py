"""Gera graficos da comparacao PIB trimestral Focus x IBGE a partir de output/PIB/."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from mba_economia.config import SeriesConfig
from mba_economia.figures_pib_trimestral import gerar_figuras_pib_trimestral


def main() -> None:
    p = argparse.ArgumentParser(description="Gera PNGs PIB trimestral Focus x IBGE.")
    p.add_argument(
        "--pib-dir",
        type=Path,
        default=Path("output/PIB"),
        help="Pasta com CSVs exportados (comparacao + joined)",
    )
    args = p.parse_args()
    cfg = SeriesConfig()

    comp_path = args.pib_dir / "comparacao_focus_ibge_pib_trimestral.csv"
    joined_path = args.pib_dir / "focus_pib_total_com_ibge_realizado.csv"
    if not comp_path.is_file():
        raise SystemExit(f"Arquivo nao encontrado: {comp_path} (rode exportar_pib_trimestral.py antes)")
    if not joined_path.is_file():
        raise SystemExit(f"Arquivo nao encontrado: {joined_path}")

    comparacao = pd.read_csv(comp_path)
    joined = pd.read_csv(joined_path, parse_dates=["survey_date"])

    pngs = gerar_figuras_pib_trimestral(
        comparacao,
        joined,
        args.pib_dir,
        tabela_sidra=cfg.sidra_tab_pib_trim_vol,
        codigo_var_yoy=6561,
    )
    print(f"{len(pngs)} graficos em {args.pib_dir.resolve()}:")
    for pth in pngs:
        print(f"  {pth.name}")


if __name__ == "__main__":
    main()
