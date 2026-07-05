"""Gera gráficos da comparação DLSP anual Focus x SGS a partir de output/DIVIDA/."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from mba_economia.config import SeriesConfig
from mba_economia.figures_divida import gerar_figuras_divida_dlsp


def main() -> None:
    p = argparse.ArgumentParser(description="Gera PNGs DLSP anual Focus x SGS 4513.")
    p.add_argument(
        "--divida-dir",
        type=Path,
        default=Path("output/DIVIDA"),
        help="Pasta com CSVs exportados (comparacao + joined)",
    )
    args = p.parse_args()
    cfg = SeriesConfig()

    comp_path = args.divida_dir / "comparacao_focus_dlsp_anual.csv"
    joined_path = args.divida_dir / "focus_dlsp_com_realizado.csv"
    if not comp_path.is_file():
        raise SystemExit(f"Arquivo não encontrado: {comp_path} (rode exportar_divida_dlsp.py antes)")
    if not joined_path.is_file():
        raise SystemExit(f"Arquivo não encontrado: {joined_path}")

    comparacao = pd.read_csv(comp_path)
    joined = pd.read_csv(joined_path, parse_dates=["survey_date"])

    pngs = gerar_figuras_divida_dlsp(
        comparacao,
        joined,
        args.divida_dir,
        codigo_sgs=cfg.sgs_codigo_dlsp_pct_pib,
    )
    print(f"{len(pngs)} gráficos em {args.divida_dir.resolve()}:")
    for pth in pngs:
        print(f"  {pth.name}")


if __name__ == "__main__":
    main()
