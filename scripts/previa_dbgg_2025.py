"""Prévia: DBGG — expectativa Focus x realizado SGS 13762 (delega ao exportador)."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from exportar_dbgg_anual import exportar_dbgg_por_ano


def main() -> None:
    p = argparse.ArgumentParser(description="Prévia DBGG Focus x SGS para um ano.")
    p.add_argument("--ano", type=int, default=2025)
    p.add_argument("--base-dir", type=Path, default=Path("output/DIVIDA"))
    args = p.parse_args()

    exportar_dbgg_por_ano(
        ano_ini=args.ano,
        ano_fim=args.ano,
        base_dir=args.base_dir,
    )
    path = args.base_dir / str(args.ano) / "comparacao_focus_dbgg.csv"
    df = pd.read_csv(path)
    print(f"Prévia salva em {path}\n")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
