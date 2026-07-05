"""Consolidação multi-ano PIB Focus × IBGE 4T (pastas ``output/PIB/{ini}-{fim}/``)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import PIB_OUTPUT_DIR
from .pib_comparisons import pib_year_dir

logger = logging.getLogger(__name__)

BLOCO_2019_2022: tuple[int, ...] = (2019, 2020, 2021, 2022)
BLOCO_2023_2026: tuple[int, ...] = (2023, 2024, 2025, 2026)
PERIODO_2019_2026: tuple[int, ...] = tuple(range(2019, 2027))

REALIZADO_COL = "pib_ibge_4tri_yoy_pct"


def pib_period_dir(out_dir: Path, anos: tuple[int, ...]) -> Path:
    """Pasta consolidada (ex.: ``output/PIB/2019-2022/``)."""
    label = f"{min(anos)}-{max(anos)}"
    path = out_dir / PIB_OUTPUT_DIR / label
    path.mkdir(parents=True, exist_ok=True)
    return path


def _with_mes_calendario(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["mes_calendario"] = out["mes_publicacao_yyyymm"].astype(int) % 100
    return out


def _carregar_trajetoria_pib(out_dir: Path, ano: int) -> pd.DataFrame:
    base = pib_year_dir(out_dir, ano)
    for nome in (
        f"comparacao_pib_ano_trajetoria_{ano}.csv",
        f"{ano}-resumo-anual.csv",
    ):
        path = base / nome
        if path.is_file():
            return pd.read_csv(path, sep=";", decimal=",")
    raise FileNotFoundError(
        f"Dados PIB/{ano}/ ausentes. Rode --figure-extra pib-ano-trajetoria-ano.",
    )


def build_pib_periodo(out_dir: Path, anos: tuple[int, ...]) -> pd.DataFrame:
    """Concatena trajetórias anuais com ``mes_calendario`` (1–12)."""
    if len(anos) < 1:
        raise ValueError("Período exige pelo menos um ano.")
    frames = [_with_mes_calendario(_carregar_trajetoria_pib(out_dir, ano)) for ano in anos]
    out = pd.concat(frames, ignore_index=True)
    out["ano_ref"] = out["ano_ref"].astype(int)
    return out.sort_values(["ano_ref", "mes_publicacao_yyyymm"]).reset_index(drop=True)


def _row_no_mes(df: pd.DataFrame, ano: int, mes: int) -> pd.Series | None:
    ref = ano * 100 + mes
    sub = df[df["mes_publicacao_yyyymm"].astype(int) == ref]
    if sub.empty:
        return None
    return sub.iloc[0]


def summarize_pib_ano(df: pd.DataFrame, ano: int) -> dict[str, float | str | int]:
    """Estatísticas descritivas por ano (narrativa monografia)."""
    ordenado = df.sort_values("mes_publicacao_yyyymm")
    jan_row = _row_no_mes(df, ano, 1)
    jan = jan_row if jan_row is not None else ordenado.iloc[0]
    dez_row = _row_no_mes(df, ano, 12)
    ano_parcial = dez_row is None
    fim = dez_row if dez_row is not None else ordenado.iloc[-1]

    real = fim.get(REALIZADO_COL, float("nan"))
    erros = df["erro_prev_menos_real_pp"].dropna()

    return {
        "ano": str(ano),
        "n_meses_observados": int(len(df)),
        "ano_parcial": int(ano_parcial),
        "mes_fim_observacao": str(fim["mes_publicacao"]),
        "pib_focus_jan_pct": float(jan["pib_focus_ano_pct"]),
        "pib_focus_dez_pct": float(fim["pib_focus_ano_pct"]),
        "pib_ibge_4tri_realizado_pct": float(real) if pd.notna(real) else "",
        "erro_dez_pp": float(fim["erro_prev_menos_real_pp"])
        if pd.notna(fim.get("erro_prev_menos_real_pp"))
        else "",
        "erro_medio_pp": float(erros.mean()) if len(erros) else "",
        "erro_rmse_pp": float((erros**2).mean() ** 0.5) if len(erros) else "",
    }


def export_pib_periodo(
    anos: tuple[int, ...],
    out_dir: Path,
) -> tuple[pd.DataFrame, list[dict[str, float | str | int]], list[Path]]:
    """Comparações multi-ano em ``output/PIB/{ano_ini}-{ano_fim}/``."""
    from .figures import (
        plot_pib_periodo_erros,
        plot_pib_periodo_painel,
        plot_pib_periodo_trajetoria_focus,
        plot_pib_periodo_trajetoria_realizado,
    )

    label = f"{min(anos)}-{max(anos)}"
    combined = build_pib_periodo(out_dir, anos)
    stats_list = [
        summarize_pib_ano(combined[combined["ano_ref"] == ano], ano) for ano in anos
    ]
    out_periodo = pib_period_dir(out_dir, anos)
    paths: list[Path] = []

    anos_tag = "_".join(str(a) for a in anos)
    csv_path = out_periodo / f"comparacao_pib_{anos_tag}.csv"
    combined.to_csv(csv_path, index=False, decimal=",", sep=";")
    paths.append(csv_path)

    stats_path = out_periodo / f"{label}-resumo-estatistico.csv"
    pd.DataFrame(stats_list).to_csv(stats_path, index=False, decimal=",", sep=";")
    paths.append(stats_path)

    plot_specs: list[tuple[str, object]] = [
        (f"{label}-trajetoria-focus.png", plot_pib_periodo_trajetoria_focus),
        (f"{label}-trajetoria-focus-vs-realizado.png", plot_pib_periodo_trajetoria_realizado),
        (f"{label}-painel-pib.png", plot_pib_periodo_painel),
        (f"{label}-erros-focus-vs-realizado.png", plot_pib_periodo_erros),
    ]
    for nome, plot_fn in plot_specs:
        dest = out_periodo / nome
        if plot_fn(combined, anos, label, dest):
            paths.append(dest)

    logger.info(
        "PIB período %s: %s anos, %s observações mensais.",
        label,
        len(anos),
        len(combined),
    )
    return combined, stats_list, paths
