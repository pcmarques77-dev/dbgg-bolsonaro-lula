"""Baixa PIB trimestral IBGE + Focus (2019–hoje) e exporta comparacao em output/PIB."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from mba_economia.config import SeriesConfig
from mba_economia.focus_extract import fetch_pib_total_expectativa_trimestral
from mba_economia.ibge_pib_volume_trimestral_client import fetch_pib_ibge_vol_trim_lut
from mba_economia.pib_trimestral_compare import (
    filtrar_janela_trimestres,
    juntar_focus_com_realizado,
    montar_comparacao_por_trimestre,
    trimestre_fim_por_data,
)


def exportar_pib_trimestral(
    *,
    ano_ini: int = 2019,
    tri_ini: int = 1,
    ano_fim: int | None = None,
    tri_fim: int | None = None,
    out_dir: Path = Path("output/PIB"),
    session: requests.Session | None = None,
) -> dict[str, Path]:
    cfg = SeriesConfig()
    sess = session or requests.Session()
    hoje = date.today()
    if ano_fim is None or tri_fim is None:
        ano_fim, tri_fim = trimestre_fim_por_data(hoje)

    out_dir.mkdir(parents=True, exist_ok=True)

    print("Baixando IBGE SIDRA t5932 (PIB a precos de mercado, volume)...")
    ibge_all = fetch_pib_ibge_vol_trim_lut(cfg, session=sess)
    ibge = filtrar_janela_trimestres(
        ibge_all,
        ano_ini=ano_ini,
        tri_ini=tri_ini,
        ano_fim=ano_fim,
        tri_fim=tri_fim,
    )
    ibge_path = out_dir / "ibge_pib_mercado_volume_trimestral.csv"
    ibge.to_csv(ibge_path, index=False)
    print(f"  {len(ibge)} trimestres -> {ibge_path}")

    print("Baixando Focus (ExpectativasMercadoTrimestrais, PIB Total)...")
    focus_all = fetch_pib_total_expectativa_trimestral(
        filt_start=pd.Timestamp(ano_ini, tri_ini, 1) - pd.DateOffset(months=6),
        session=sess,
    )
    focus = filtrar_janela_trimestres(
        focus_all,
        ano_ini=ano_ini,
        tri_ini=tri_ini,
        ano_fim=ano_fim,
        tri_fim=tri_fim,
    )
    focus_path = out_dir / "focus_pib_total_trimestral.csv"
    focus.to_csv(focus_path, index=False)
    print(f"  {len(focus)} linhas -> {focus_path}")

    print("Montando comparacao (ultima Focus pre-divulgacao x IBGE YoY)...")
    comp = montar_comparacao_por_trimestre(focus, ibge)
    comp_path = out_dir / "comparacao_focus_ibge_pib_trimestral.csv"
    comp.to_csv(comp_path, index=False)
    print(f"  {len(comp)} trimestres -> {comp_path}")

    joined = juntar_focus_com_realizado(focus, ibge)
    joined_path = out_dir / "focus_pib_total_com_ibge_realizado.csv"
    joined.to_csv(joined_path, index=False)
    print(f"  serie longa -> {joined_path}")

    meta_path = out_dir / "metadados_pib_trimestral.txt"
    meta_path.write_text(
        "\n".join(
            [
                "PIB trimestral — export batch",
                f"janela_referencia: {tri_ini}T/{ano_ini} a {tri_fim}T/{ano_fim}",
                f"data_export: {hoje.isoformat()}",
                "",
                "IBGE: SIDRA t5932, classificacao c11255, setor 90707 (PIB a precos de mercado)",
                "  pib_ibge_vol_yoy_trim_pct = variavel 6561 (YoY mesmo trimestre, volume)",
                "  pib_ibge_vol_qoq_pct      = variavel 6564 (QoQ t/t-1)",
                "",
                "Focus: Olinda ExpectativasMercadoTrimestrais, indicador PIB Total",
                "  pib_focus_trim_med_pct = mediana; comparavel ao IBGE YoY (6561)",
                "",
                "comparacao_focus_ibge_pib_trimestral.csv:",
                "  ultima mediana Focus antes da divulgacao IBGE (proxy: 1T->jun, 2T->set, 3T->dez, 4T->mar+1)",
                "  erro_focus_vs_ibge_yoy_pp = focus_ultima_mediana_pct - ibge_vol_yoy_trim_pct",
                "  (IBGE pode refletir revisoes posteriores a divulgacao)",
            ],
        ),
        encoding="utf-8",
    )
    print(f"  metadados -> {meta_path}")

    return {
        "ibge": ibge_path,
        "focus": focus_path,
        "comparacao": comp_path,
        "joined": joined_path,
        "metadados": meta_path,
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description="Exporta PIB trimestral IBGE + Focus e comparacao para output/PIB.",
    )
    p.add_argument("--ano-ini", type=int, default=2019)
    p.add_argument("--tri-ini", type=int, default=1, choices=(1, 2, 3, 4))
    p.add_argument("--ano-fim", type=int, default=None)
    p.add_argument("--tri-fim", type=int, default=None, choices=(1, 2, 3, 4))
    p.add_argument("--out-dir", type=Path, default=Path("output/PIB"))
    args = p.parse_args()

    paths = exportar_pib_trimestral(
        ano_ini=args.ano_ini,
        tri_ini=args.tri_ini,
        ano_fim=args.ano_fim,
        tri_fim=args.tri_fim,
        out_dir=args.out_dir,
    )
    print("\nConcluido. Arquivos:")
    for k, v in paths.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
