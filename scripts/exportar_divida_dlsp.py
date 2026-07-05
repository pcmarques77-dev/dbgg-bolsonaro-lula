"""Baixa DLSP Focus + SGS 4513 (2019–hoje) e exporta comparação em output/DIVIDA."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from mba_economia.bcb_dlsp_sgs4513 import fetch_dlsp_sgs4513_anual
from mba_economia.config import SeriesConfig
from mba_economia.divida_dlsp_compare import (
    filtrar_janela_anos,
    juntar_focus_com_realizado,
    montar_comparacao_por_ano,
)
from mba_economia.divida_focus import fetch_dlsp_expectativa_anual


def exportar_divida_dlsp(
    *,
    ano_ini: int = 2019,
    ano_fim: int | None = None,
    out_dir: Path = Path("output/DIVIDA"),
    session: requests.Session | None = None,
) -> dict[str, Path]:
    cfg = SeriesConfig()
    sess = session or requests.Session()
    hoje = date.today()
    if ano_fim is None:
        ano_fim = hoje.year

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Baixando SGS {cfg.sgs_codigo_dlsp_pct_pib} (DLSP % PIB, fechamento dez/ano)...")
    real_all = fetch_dlsp_sgs4513_anual(ano_ini, ano_fim, cfg, session=sess)
    realizado = filtrar_janela_anos(real_all, ano_ini=ano_ini, ano_fim=ano_fim)
    real_path = out_dir / "dlsp_sgs4513_anual.csv"
    realizado.to_csv(real_path, index=False)
    print(f"  {len(realizado)} anos -> {real_path}")

    print("Baixando Focus (ExpectativasMercadoAnuais, Dívida líquida do setor público)...")
    focus_all = fetch_dlsp_expectativa_anual(
        filt_start=pd.Timestamp(ano_ini - 1, 1, 1),
        session=sess,
    )
    focus = filtrar_janela_anos(focus_all, ano_ini=ano_ini, ano_fim=ano_fim)
    focus_path = out_dir / "focus_dlsp_anual.csv"
    focus.to_csv(focus_path, index=False)
    print(f"  {len(focus)} linhas -> {focus_path}")

    print("Montando comparação (última Focus pré-divulgação x DLSP dez/ano)...")
    comp = montar_comparacao_por_ano(focus, realizado, cfg=cfg)
    comp_path = out_dir / "comparacao_focus_dlsp_anual.csv"
    comp.to_csv(comp_path, index=False)
    print(f"  {len(comp)} anos -> {comp_path}")

    joined = juntar_focus_com_realizado(focus, realizado)
    joined_path = out_dir / "focus_dlsp_com_realizado.csv"
    joined.to_csv(joined_path, index=False)
    print(f"  série longa -> {joined_path}")

    meta_path = out_dir / "metadados_divida_dlsp.txt"
    meta_path.write_text(
        "\n".join(
            [
                "DLSP anual — export batch",
                f"janela_referencia: {ano_ini} a {ano_fim}",
                f"data_export: {hoje.isoformat()}",
                "",
                "Expectativa (Focus): Olinda ExpectativasMercadoAnuais",
                "  indicador: Dívida líquida do setor público",
                "  dlsp_focus_med_pct_pib = mediana (% do PIB)",
                "  fonte: https://dadosabertos.bcb.gov.br/dataset/expectativas-mercado",
                "",
                "Realizado: BC SGS 4513 — DLSP (% PIB), setor público consolidado",
                "  dlsp_sgs_pct_pib = fechamento de dezembro do ano (última obs. do ano)",
                "  dlsp_sgs_yoy_pp = variação em pontos percentuais vs dezembro anterior",
                "  fonte: https://dadosabertos.bcb.gov.br/dataset/4513-divida-liquida-do-setor-publico--pib---total---setor-publico-consolidado",
                "",
                "Nota: o Tesouro Transparente publica estoque da DPF (dívida federal mobiliária);",
                "  DLSP é conceito mais amplo (setor público consolidado), divulgado pelo BC/STN.",
                "",
                "comparacao_focus_dlsp_anual.csv:",
                f"  última mediana Focus antes de {cfg.dlsp_anual_divulgacao_dia_mes:02d}/"
                f"{cfg.dlsp_anual_divulgacao_mes_ano_seguinte:02d}/(ano+1) (proxy divulgação fiscal anual)",
                "  erro_focus_vs_realizado_pp = focus_ultima_mediana_pct_pib - dlsp_realizado_dez_pct_pib",
            ],
        ),
        encoding="utf-8",
    )
    print(f"  metadados -> {meta_path}")

    return {
        "realizado": real_path,
        "focus": focus_path,
        "comparacao": comp_path,
        "joined": joined_path,
        "metadados": meta_path,
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description="Exporta DLSP anual Focus + SGS 4513 e comparação para output/DIVIDA.",
    )
    p.add_argument("--ano-ini", type=int, default=2019)
    p.add_argument("--ano-fim", type=int, default=None)
    p.add_argument("--out-dir", type=Path, default=Path("output/DIVIDA"))
    args = p.parse_args()

    paths = exportar_divida_dlsp(
        ano_ini=args.ano_ini,
        ano_fim=args.ano_fim,
        out_dir=args.out_dir,
    )
    print("\nConcluído. Arquivos:")
    for k, v in paths.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
