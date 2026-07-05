"""Comparativos DBGG por período (CSV + gráficos) em output/DIVIDA/periodos/{ini}-{fim}/."""
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
from mba_economia.figures_divida import gerar_figuras_divida_dbgg
from mba_economia.divida_focus import fetch_dbgg_expectativa_anual

PERIODOS_PADRAO: list[tuple[int, int]] = [
    (2019, 2022),
    (2023, 2026),
    (2019, 2026),
]


def _carregar_ou_baixar_dados(
    ano_ini: int,
    ano_fim: int,
    base_dir: Path,
    *,
    session: requests.Session,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cfg = SeriesConfig()
    resumo = base_dir / "comparacao_focus_dbgg_anual.csv"
    if resumo.is_file():
        comp_full = pd.read_csv(resumo)
        max_ano = int(comp_full["ano"].max())
        if max_ano >= ano_fim:
            focus_parts: list[pd.DataFrame] = []
            join_parts: list[pd.DataFrame] = []
            for ano in range(ano_ini, ano_fim + 1):
                p_focus = base_dir / str(ano) / "focus_dbgg.csv"
                p_join = base_dir / str(ano) / "focus_dbgg_com_realizado.csv"
                if p_focus.is_file():
                    focus_parts.append(pd.read_csv(p_focus, parse_dates=["survey_date"]))
                if p_join.is_file():
                    join_parts.append(pd.read_csv(p_join, parse_dates=["survey_date"]))
            if focus_parts and join_parts:
                return (
                    comp_full,
                    pd.concat(focus_parts, ignore_index=True),
                    pd.concat(join_parts, ignore_index=True),
                )

    real_all = fetch_dbgg_sgs13762_anual(ano_ini, ano_fim, cfg, session=session)
    realizado = filtrar_janela_anos(real_all, ano_ini=ano_ini, ano_fim=ano_fim)
    focus_all = fetch_dbgg_expectativa_anual(
        filt_start=pd.Timestamp(ano_ini - 1, 1, 1),
        session=session,
    )
    focus = filtrar_janela_anos(focus_all, ano_ini=ano_ini, ano_fim=ano_fim)
    comp_full = montar_comparacao_por_ano(focus, realizado, cfg=cfg)
    comp_full = complementar_anos_apenas_focus(
        comp_full,
        focus,
        ano_ini=ano_ini,
        ano_fim=ano_fim,
        cfg=cfg,
    )
    joined = juntar_focus_com_realizado(focus, realizado)
    return comp_full, focus, joined


def gerar_comparativo_periodo(
    ano_ini: int,
    ano_fim: int,
    *,
    comp_full: pd.DataFrame,
    joined_full: pd.DataFrame,
    out_dir: Path,
    cfg: SeriesConfig,
) -> dict[str, Path]:
    label = f"{ano_ini}-{ano_fim}"
    periodo_dir = out_dir / label
    periodo_dir.mkdir(parents=True, exist_ok=True)

    comp = comp_full[(comp_full["ano"] >= ano_ini) & (comp_full["ano"] <= ano_fim)].copy()
    comp = comp.sort_values("ano").reset_index(drop=True)

    joined = joined_full[
        (joined_full["ano_ref"] >= ano_ini) & (joined_full["ano_ref"] <= ano_fim)
    ].copy()

    p_comp = periodo_dir / "comparacao_focus_dbgg.csv"
    p_join = periodo_dir / "focus_dbgg_com_realizado.csv"
    comp.to_csv(p_comp, index=False)
    joined.to_csv(p_join, index=False)

    anos_conv = [ano_ini, ano_fim]
    pngs = gerar_figuras_divida_dbgg(
        comp,
        joined,
        periodo_dir,
        codigo_sgs=cfg.sgs_codigo_dbgg_pct_pib,
        titulo_periodo=label,
        anos_convergencia=anos_conv,
    )

    n_com_erro = comp["erro_focus_vs_realizado_pp"].notna().sum()
    n_sem_real = comp["dbgg_realizado_dez_pct_pib"].isna().sum()
    meta = periodo_dir / "metadados_periodo.txt"
    meta.write_text(
        "\n".join(
            [
                f"DBGG — comparativo {label}",
                f"data_export: {date.today().isoformat()}",
                f"anos_na_tabela: {len(comp)}",
                f"anos_com_realizado_e_erro: {n_com_erro}",
                f"anos_apenas_focus (sem realizado): {n_sem_real}",
                "",
                "Arquivos:",
                "  comparacao_focus_dbgg.csv",
                "  focus_dbgg_com_realizado.csv",
                "  comparacao_focus_dbgg.png",
                "  erro_previsao_dbgg.png",
                "  dispersao_focus_dbgg.png",
                f"  convergencia_focus_dbgg_{ano_ini}.png",
                f"  convergencia_focus_dbgg_{ano_fim}.png",
            ],
        ),
        encoding="utf-8",
    )

    paths: dict[str, Path] = {
        "comparacao": p_comp,
        "joined": p_join,
        "metadados": meta,
    }
    for i, png in enumerate(pngs):
        paths[f"grafico_{i}"] = png
    return paths


def gerar_comparativos_periodos(
    periodos: list[tuple[int, int]] | None = None,
    *,
    base_dir: Path = Path("output/DIVIDA"),
    out_dir: Path | None = None,
    session: requests.Session | None = None,
) -> dict[str, dict[str, Path]]:
    periodos = periodos or PERIODOS_PADRAO
    sess = session or requests.Session()
    cfg = SeriesConfig()
    out_root = out_dir or (base_dir / "periodos")

    ano_min = min(a for a, _ in periodos)
    ano_max = max(b for _, b in periodos)

    print(f"Carregando dados DBGG {ano_min}–{ano_max}...")
    comp_full, _focus, joined = _carregar_ou_baixar_dados(
        ano_min,
        ano_max,
        base_dir,
        session=sess,
    )

    resultados: dict[str, dict[str, Path]] = {}
    for ano_ini, ano_fim in periodos:
        label = f"{ano_ini}-{ano_fim}"
        print(f"Gerando período {label}...")
        resultados[label] = gerar_comparativo_periodo(
            ano_ini,
            ano_fim,
            comp_full=comp_full,
            joined_full=joined,
            out_dir=out_root,
            cfg=cfg,
        )
        print(f"  -> {out_root / label}")

    return resultados


def main() -> None:
    p = argparse.ArgumentParser(description="Comparativos DBGG por período com gráficos.")
    p.add_argument("--base-dir", type=Path, default=Path("output/DIVIDA"))
    p.add_argument("--out-dir", type=Path, default=None)
    args = p.parse_args()

    resultados = gerar_comparativos_periodos(
        base_dir=args.base_dir,
        out_dir=args.out_dir,
    )
    print("\nConcluído:")
    for label, files in resultados.items():
        pngs = [v.name for k, v in files.items() if str(v).endswith(".png")]
        print(f"  {label}: {len(pngs)} gráficos + CSVs")


if __name__ == "__main__":
    main()
