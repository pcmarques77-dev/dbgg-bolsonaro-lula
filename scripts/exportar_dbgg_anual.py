"""Exporta DBGG anual Focus + SGS 13762 (2019–2025) em output/DIVIDA/{ano}/."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from mba_economia.bcb_dbgg_sgs13762 import fetch_dbgg_mensal_sgs, fetch_dbgg_sgs13762_anual
from mba_economia.config import SeriesConfig
from mba_economia.divida_dbgg_compare import (
    complementar_anos_apenas_focus,
    filtrar_janela_anos,
    juntar_focus_com_realizado,
    montar_comparacao_por_ano,
)
from mba_economia.divida_focus import fetch_dbgg_expectativa_anual


def _metadados_ano(ano: int, cfg: SeriesConfig) -> str:
    return "\n".join(
        [
            f"DBGG {ano} — Focus x SGS",
            "",
            "Focus: Olinda ExpectativasMercadoAnuais",
            "  indicador: Dívida bruta do governo geral",
            "  dbgg_focus_med_pct_pib = mediana (% do PIB)",
            "  fonte: https://dadosabertos.bcb.gov.br/dataset/expectativas-mercado",
            "",
            f"Realizado: BC SGS {cfg.sgs_codigo_dbgg_pct_pib} — DBGG (% PIB), metodologia a partir de 2008",
            "  dbgg_sgs_pct_pib = fechamento de dezembro do ano",
            "  fonte: https://dadosabertos.bcb.gov.br/dataset/13762-divida-bruta-do-governo-geral--pib---metodologia-utilizada-a-partir-de-2008",
            "",
            "comparacao_focus_dbgg.csv:",
            f"  última mediana Focus antes de {cfg.dlsp_anual_divulgacao_dia_mes:02d}/"
            f"{cfg.dlsp_anual_divulgacao_mes_ano_seguinte:02d}/(ano+1) (proxy divulgação fiscal anual)",
            "  erro_focus_vs_realizado_pp = focus_ultima_mediana_pct_pib - dbgg_realizado_dez_pct_pib",
        ],
    )


def exportar_dbgg_por_ano(
    *,
    ano_ini: int = 2019,
    ano_fim: int = 2025,
    base_dir: Path = Path("output/DIVIDA"),
    session: requests.Session | None = None,
) -> dict[int, dict[str, Path]]:
    cfg = SeriesConfig()
    sess = session or requests.Session()
    hoje = date.today()

    print(f"Baixando SGS {cfg.sgs_codigo_dbgg_pct_pib} (DBGG % PIB)...")
    real_all = fetch_dbgg_sgs13762_anual(ano_ini, ano_fim, cfg, session=sess)
    realizado = filtrar_janela_anos(real_all, ano_ini=ano_ini, ano_fim=ano_fim)

    print("Baixando Focus (ExpectativasMercadoAnuais, Dívida bruta do governo geral)...")
    focus_all = fetch_dbgg_expectativa_anual(
        filt_start=pd.Timestamp(ano_ini - 1, 1, 1),
        session=sess,
    )
    focus = filtrar_janela_anos(focus_all, ano_ini=ano_ini, ano_fim=ano_fim)

    mensal = fetch_dbgg_mensal_sgs(ano_ini, ano_fim, cfg, session=sess)

    comp_all = montar_comparacao_por_ano(focus, realizado, cfg=cfg)
    comp_all = complementar_anos_apenas_focus(
        comp_all,
        focus,
        ano_ini=ano_ini,
        ano_fim=ano_fim,
        cfg=cfg,
    )
    resumo_path = base_dir / "comparacao_focus_dbgg_anual.csv"
    base_dir.mkdir(parents=True, exist_ok=True)
    comp_all.to_csv(resumo_path, index=False)
    print(f"  resumo {len(comp_all)} anos -> {resumo_path}")

    paths_por_ano: dict[int, dict[str, Path]] = {}
    for ano in range(ano_ini, ano_fim + 1):
        ano_dir = base_dir / str(ano)
        ano_dir.mkdir(parents=True, exist_ok=True)

        f_ano = focus[focus["ano_ref"] == ano].copy()
        r_ano = realizado[realizado["ano_ref"] == ano].copy()
        m_ano = mensal[mensal["ano_ref"] == ano][
            ["data_obs", "mes", "dbgg_sgs_pct_pib"]
        ].copy()
        c_ano = comp_all[comp_all["ano"] == ano].copy()
        j_ano = juntar_focus_com_realizado(f_ano, r_ano)

        p_focus = ano_dir / "focus_dbgg.csv"
        p_real = ano_dir / "dbgg_sgs13762_anual.csv"
        p_mensal = ano_dir / "dbgg_sgs13762_mensal.csv"
        p_comp = ano_dir / "comparacao_focus_dbgg.csv"
        p_join = ano_dir / "focus_dbgg_com_realizado.csv"
        p_meta = ano_dir / "metadados_dbgg.txt"

        f_ano.to_csv(p_focus, index=False)
        r_ano.to_csv(p_real, index=False)
        m_ano.to_csv(p_mensal, index=False)
        c_ano.to_csv(p_comp, index=False)
        j_ano.to_csv(p_join, index=False)
        p_meta.write_text(_metadados_ano(ano, cfg), encoding="utf-8")

        paths_por_ano[ano] = {
            "focus": p_focus,
            "realizado_anual": p_real,
            "realizado_mensal": p_mensal,
            "comparacao": p_comp,
            "joined": p_join,
            "metadados": p_meta,
        }
        print(f"  {ano}/ -> comparacao + {len(f_ano)} linhas Focus")

    meta_global = base_dir / "metadados_dbgg_anual.txt"
    meta_global.write_text(
        "\n".join(
            [
                "DBGG anual — export por ano",
                f"janela: {ano_ini} a {ano_fim}",
                f"data_export: {hoje.isoformat()}",
                f"pasta por ano: {base_dir}/{{ano}}/",
                f"resumo consolidado: {resumo_path.name}",
            ],
        ),
        encoding="utf-8",
    )

    return paths_por_ano


def main() -> None:
    p = argparse.ArgumentParser(
        description="Exporta DBGG Focus x SGS 13762 em output/DIVIDA/{ano}/.",
    )
    p.add_argument("--ano-ini", type=int, default=2019)
    p.add_argument("--ano-fim", type=int, default=2025)
    p.add_argument("--base-dir", type=Path, default=Path("output/DIVIDA"))
    args = p.parse_args()

    paths = exportar_dbgg_por_ano(
        ano_ini=args.ano_ini,
        ano_fim=args.ano_fim,
        base_dir=args.base_dir,
    )
    print("\nConcluído. Pastas:")
    for ano, files in paths.items():
        print(f"  {args.base_dir / str(ano)} ({len(files)} arquivos)")


if __name__ == "__main__":
    main()
