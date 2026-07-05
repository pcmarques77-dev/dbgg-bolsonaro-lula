"""Cruzamento exploratório IPCA ano-calendário × Selic fim de ano (dados já em ``output/``)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import (
    IPCA_ANUAL_OUTPUT_DIR,
    IPCA_SELIC_CROSS_OUTPUT_DIR,
    SELIC_ANUAL_OUTPUT_DIR,
)

logger = logging.getLogger(__name__)

# Blocos para comparativo governamental (descritivo; 2026 parcial)
BLOCO_2019_2022: tuple[int, ...] = (2019, 2020, 2021, 2022)
BLOCO_2023_2026: tuple[int, ...] = (2023, 2024, 2025, 2026)


def ipca_selic_cross_year_dir(out_dir: Path, ano: int) -> Path:
    path = out_dir / IPCA_SELIC_CROSS_OUTPUT_DIR / str(ano)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ipca_selic_cross_period_dir(out_dir: Path, anos: tuple[int, ...]) -> Path:
    """Pasta consolidada (ex.: ``output/IPCA x Selic/2020-2021/``)."""
    label = f"{min(anos)}-{max(anos)}"
    path = out_dir / IPCA_SELIC_CROSS_OUTPUT_DIR / label
    path.mkdir(parents=True, exist_ok=True)
    return path


def _with_mes_calendario(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["mes_calendario"] = out["mes_publicacao_yyyymm"].astype(int) % 100
    return out


def _ipca_anual_year_dir(out_dir: Path, ano: int) -> Path:
    return out_dir / IPCA_ANUAL_OUTPUT_DIR / str(ano)


def _selic_anual_year_dir(out_dir: Path, ano: int) -> Path:
    return out_dir / SELIC_ANUAL_OUTPUT_DIR / str(ano)


def _carregar_trajetoria_ipca_anual(out_dir: Path, ano: int) -> pd.DataFrame:
    base = _ipca_anual_year_dir(out_dir, ano)
    for nome in (
        f"comparacao_ipca_ano_trajetoria_{ano}.csv",
        f"{ano}-resumo-anual.csv",
    ):
        path = base / nome
        if path.is_file():
            return pd.read_csv(path, sep=";", decimal=",")
    raise FileNotFoundError(
        f"Dados IPCA Anual/{ano}/ ausentes. Rode --figure-extra ipca-anual-trajetoria-ano.",
    )


def _carregar_trajetoria_selic_anual(out_dir: Path, ano: int) -> pd.DataFrame:
    base = _selic_anual_year_dir(out_dir, ano)
    for nome in (
        f"comparacao_selic_ano_trajetoria_{ano}.csv",
        f"{ano}-resumo-anual.csv",
    ):
        path = base / nome
        if path.is_file():
            return pd.read_csv(path, sep=";", decimal=",")
    raise FileNotFoundError(
        f"Dados Selic Anual/{ano}/ ausentes. Rode --figure-extra selic-anual-trajetoria-ano.",
    )


def build_ipca_selic_cross_merged(out_dir: Path, ano: int) -> pd.DataFrame:
    """Junta trajetórias mensais Focus de IPCA ano-calendário e Selic fim de ano."""
    ipca = _carregar_trajetoria_ipca_anual(out_dir, ano)
    selic = _carregar_trajetoria_selic_anual(out_dir, ano)

    key = "mes_publicacao_yyyymm"
    merged = ipca.merge(
        selic,
        on=key,
        how="inner",
        suffixes=("_ipca", "_selic"),
    )
    if merged.empty:
        raise ValueError(f"Sem meses em comum para cruzamento IPCA×Selic em {ano}.")

    merged = merged.sort_values(key).reset_index(drop=True)
    merged["ano_ref"] = ano
    if "mes_publicacao_ipca" in merged.columns:
        merged["mes_publicacao"] = merged["mes_publicacao_ipca"]
    merged["spread_selic_menos_ipca_pp"] = (
        merged["selic_focus_pct"] - merged["ipca_focus_ano_pct"]
    )
    merged["erro_ipca_prev_menos_real_pp"] = merged["erro_prev_menos_real_pp_ipca"]
    merged["erro_selic_prev_menos_real_pp"] = merged["erro_prev_menos_real_pp_selic"]
    return merged


def _row_no_mes(merged: pd.DataFrame, ano: int, mes: int) -> pd.Series | None:
    ref = ano * 100 + mes
    sub = merged[merged["mes_publicacao_yyyymm"].astype(int) == ref]
    if sub.empty:
        return None
    return sub.iloc[0]


def summarize_ipca_selic_cross(merged: pd.DataFrame, ano: int) -> dict[str, float | str]:
    """Estatísticas descritivas para narrativa da monografia.

    Anos parciais (ex.: 2026 em maio): ``dez`` usa a última observação disponível;
    realizados podem ser ``NaN`` até fechamento de dezembro.
    """
    ordenado = merged.sort_values("mes_publicacao_yyyymm")
    jan_row = _row_no_mes(merged, ano, 1)
    jan = jan_row if jan_row is not None else ordenado.iloc[0]
    dez_row = _row_no_mes(merged, ano, 12)
    ano_parcial = dez_row is None
    fim = dez_row if dez_row is not None else ordenado.iloc[-1]

    ipca_min = merged.loc[merged["ipca_focus_ano_pct"].idxmin()]
    selic_max = merged.loc[merged["selic_focus_pct"].idxmax()]

    corr = float(merged["ipca_focus_ano_pct"].corr(merged["selic_focus_pct"]))
    ipca_real = fim["ipca_ibge_acum_ano_dez_pct"]
    selic_real = fim["selic_sgs_pct_aa_aprox"]

    return {
        "ano": str(ano),
        "n_meses_observados": int(len(merged)),
        "ano_parcial": int(ano_parcial),
        "mes_fim_observacao": str(fim["mes_publicacao"]),
        "ipca_focus_jan_pct": float(jan["ipca_focus_ano_pct"]),
        "ipca_focus_dez_pct": float(fim["ipca_focus_ano_pct"]),
        "ipca_focus_min_pct": float(ipca_min["ipca_focus_ano_pct"]),
        "ipca_focus_min_mes": str(ipca_min["mes_publicacao"]),
        "ipca_ibge_realizado_pct": float(ipca_real) if pd.notna(ipca_real) else "",
        "selic_focus_jan_pct": float(jan["selic_focus_pct"]),
        "selic_focus_dez_pct": float(fim["selic_focus_pct"]),
        "selic_focus_max_pct": float(selic_max["selic_focus_pct"]),
        "selic_focus_max_mes": str(selic_max["mes_publicacao"]),
        "selic_sgs_realizado_pct": float(selic_real) if pd.notna(selic_real) else "",
        "corr_ipca_selic_focus": corr,
        "spread_jan_pp": float(jan["spread_selic_menos_ipca_pp"]),
        "spread_dez_pp": float(fim["spread_selic_menos_ipca_pp"]),
    }


def export_ipca_selic_cross_ano(ano: int, out_dir: Path) -> tuple[pd.DataFrame, dict[str, float | str], list[Path]]:
    """Gera CSV, resumo numérico e PNGs em ``output/IPCA x Selic/{ano}/``."""
    from .figures import (
        plot_ipca_selic_cross_erros_realizado,
        plot_ipca_selic_cross_scatter,
        plot_ipca_selic_cross_spread,
        plot_ipca_selic_cross_trajetoria_focus,
        plot_ipca_selic_cross_trajetoria_realizado,
    )

    merged = build_ipca_selic_cross_merged(out_dir, ano)
    stats = summarize_ipca_selic_cross(merged, ano)
    out_ano = ipca_selic_cross_year_dir(out_dir, ano)
    paths: list[Path] = []

    csv_path = out_ano / f"comparacao_ipca_selic_{ano}.csv"
    merged.to_csv(csv_path, index=False, decimal=",", sep=";")
    paths.append(csv_path)

    stats_path = out_ano / f"{ano}-resumo-estatistico.csv"
    pd.DataFrame([stats]).to_csv(stats_path, index=False, decimal=",", sep=";")
    paths.append(stats_path)

    plot_specs: list[tuple[str, object]] = [
        (f"{ano}-trajetoria-focus-ipca-selic.png", plot_ipca_selic_cross_trajetoria_focus),
        (f"{ano}-trajetoria-focus-vs-realizado.png", plot_ipca_selic_cross_trajetoria_realizado),
        (f"{ano}-scatter-ipca-vs-selic.png", plot_ipca_selic_cross_scatter),
        (f"{ano}-spread-selic-menos-ipca.png", plot_ipca_selic_cross_spread),
        (f"{ano}-erros-focus-vs-realizado.png", plot_ipca_selic_cross_erros_realizado),
    ]
    for nome, plot_fn in plot_specs:
        dest = out_ano / nome
        if plot_fn(merged, ano, dest):
            paths.append(dest)

    logger.info(
        "IPCA×Selic %s: %s meses, corr(Focus)=%.3f, IPCA real=%.2f%%, Selic SGS=%.2f%%.",
        ano,
        len(merged),
        stats["corr_ipca_selic_focus"],
        stats["ipca_ibge_realizado_pct"],
        stats["selic_sgs_realizado_pct"],
    )
    return merged, stats, paths


def build_ipca_selic_cross_periodo(
    out_dir: Path,
    anos: tuple[int, ...],
) -> pd.DataFrame:
    """Concatena cruzamentos anuais com coluna ``mes_calendario`` (1–12) para alinhar anos."""
    if len(anos) < 2:
        raise ValueError("Período exige pelo menos dois anos.")
    frames = [_with_mes_calendario(build_ipca_selic_cross_merged(out_dir, ano)) for ano in anos]
    return pd.concat(frames, ignore_index=True)


def export_ipca_selic_cross_periodo(
    anos: tuple[int, ...],
    out_dir: Path,
) -> tuple[pd.DataFrame, list[dict[str, float | str]], list[Path]]:
    """Comparações multi-ano em ``output/IPCA x Selic/{ano_ini}-{ano_fim}/``."""
    from .figures import (
        plot_ipca_selic_cross_periodo_erros,
        plot_ipca_selic_cross_periodo_painel,
        plot_ipca_selic_cross_periodo_realizado,
        plot_ipca_selic_cross_periodo_scatter,
        plot_ipca_selic_cross_periodo_spread,
        plot_ipca_selic_cross_periodo_trajetoria_focus,
    )

    label = f"{min(anos)}-{max(anos)}"
    combined = build_ipca_selic_cross_periodo(out_dir, anos)
    stats_list = [summarize_ipca_selic_cross(combined[combined["ano_ref"] == ano], ano) for ano in anos]
    out_periodo = ipca_selic_cross_period_dir(out_dir, anos)
    paths: list[Path] = []

    anos_tag = "_".join(str(a) for a in anos)
    csv_path = out_periodo / f"comparacao_ipca_selic_{anos_tag}.csv"
    combined.to_csv(csv_path, index=False, decimal=",", sep=";")
    paths.append(csv_path)

    stats_path = out_periodo / f"{label}-resumo-estatistico.csv"
    pd.DataFrame(stats_list).to_csv(stats_path, index=False, decimal=",", sep=";")
    paths.append(stats_path)

    plot_specs: list[tuple[str, object]] = [
        (f"{label}-trajetoria-focus-ipca-selic.png", plot_ipca_selic_cross_periodo_trajetoria_focus),
        (f"{label}-trajetoria-focus-vs-realizado.png", plot_ipca_selic_cross_periodo_realizado),
        (f"{label}-painel-ipca-selic.png", plot_ipca_selic_cross_periodo_painel),
        (f"{label}-scatter-ipca-vs-selic.png", plot_ipca_selic_cross_periodo_scatter),
        (f"{label}-spread-selic-menos-ipca.png", plot_ipca_selic_cross_periodo_spread),
        (f"{label}-erros-focus-vs-realizado.png", plot_ipca_selic_cross_periodo_erros),
    ]
    for nome, plot_fn in plot_specs:
        dest = out_periodo / nome
        if plot_fn(combined, anos, label, dest):
            paths.append(dest)

    logger.info(
        "IPCA×Selic período %s: %s anos, %s observações mensais.",
        label,
        len(anos),
        len(combined),
    )
    return combined, stats_list, paths


def ipca_selic_cross_comparativo_dir(
    out_dir: Path,
    bloco_a: tuple[int, ...],
    bloco_b: tuple[int, ...],
) -> Path:
    label = f"{min(bloco_a)}-{max(bloco_a)}-vs-{min(bloco_b)}-{max(bloco_b)}"
    path = out_dir / IPCA_SELIC_CROSS_OUTPUT_DIR / label
    path.mkdir(parents=True, exist_ok=True)
    return path


def _media_mensal_bloco(combined: pd.DataFrame, anos: tuple[int, ...], bloco_id: str) -> pd.DataFrame:
    sub = combined[combined["ano_ref"].isin(anos)]
    media = (
        sub.groupby("mes_calendario", as_index=False)
        .agg(
            ipca_focus_ano_pct=("ipca_focus_ano_pct", "mean"),
            selic_focus_pct=("selic_focus_pct", "mean"),
            spread_selic_menos_ipca_pp=("spread_selic_menos_ipca_pp", "mean"),
            erro_ipca_prev_menos_real_pp=("erro_ipca_prev_menos_real_pp", "mean"),
            erro_selic_prev_menos_real_pp=("erro_selic_prev_menos_real_pp", "mean"),
            n_obs=("ano_ref", "count"),
        )
        .sort_values("mes_calendario")
    )
    media["bloco"] = bloco_id
    return media


def summarize_ipca_selic_bloco(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    bloco_id: str,
) -> dict[str, float | str | int]:
    """Agrega estatísticas de um bloco de anos (médias entre observações e entre anos)."""
    sub = combined[combined["ano_ref"].isin(anos)].copy()
    if sub.empty:
        raise ValueError(f"Bloco {bloco_id} sem dados.")

    stats_anuais = [
        summarize_ipca_selic_cross(sub[sub["ano_ref"] == ano], ano) for ano in anos
    ]
    corrs = [float(s["corr_ipca_selic_focus"]) for s in stats_anuais]
    spreads_dez = [float(s["spread_dez_pp"]) for s in stats_anuais if not s["ano_parcial"]]

    erros_ipca = sub["erro_ipca_prev_menos_real_pp"].dropna()
    erros_selic = sub["erro_selic_prev_menos_real_pp"].dropna()

    return {
        "bloco": bloco_id,
        "anos": ",".join(str(a) for a in anos),
        "n_anos": len(anos),
        "n_observacoes_mensais": int(len(sub)),
        "n_anos_parciais": int(sum(s["ano_parcial"] for s in stats_anuais)),
        "corr_media_entre_anos": float(sum(corrs) / len(corrs)),
        "corr_min_anual": float(min(corrs)),
        "corr_max_anual": float(max(corrs)),
        "ipca_focus_media_obs_pct": float(sub["ipca_focus_ano_pct"].mean()),
        "selic_focus_media_obs_pct": float(sub["selic_focus_pct"].mean()),
        "spread_medio_obs_pp": float(sub["spread_selic_menos_ipca_pp"].mean()),
        "spread_fim_ano_medio_pp": float(sum(spreads_dez) / len(spreads_dez)) if spreads_dez else "",
        "erro_ipca_medio_pp": float(erros_ipca.mean()) if len(erros_ipca) else "",
        "erro_selic_medio_pp": float(erros_selic.mean()) if len(erros_selic) else "",
        "erro_ipca_rmse_pp": float((erros_ipca**2).mean() ** 0.5) if len(erros_ipca) else "",
        "erro_selic_rmse_pp": float((erros_selic**2).mean() ** 0.5) if len(erros_selic) else "",
    }


def export_ipca_selic_cross_comparativo_blocos(
    out_dir: Path,
    bloco_a: tuple[int, ...] = BLOCO_2019_2022,
    bloco_b: tuple[int, ...] = BLOCO_2023_2026,
) -> tuple[pd.DataFrame, list[dict[str, float | str | int]], list[Path]]:
    """Comparativo entre dois blocos em ``output/IPCA x Selic/{blocoA}-vs-{blocoB}/``."""
    from .figures import (
        plot_ipca_selic_cross_comparativo_blocos_erros,
        plot_ipca_selic_cross_comparativo_blocos_metricas,
        plot_ipca_selic_cross_comparativo_blocos_painel,
        plot_ipca_selic_cross_comparativo_blocos_scatter,
        plot_ipca_selic_cross_comparativo_blocos_spread,
    )

    label_a = f"{min(bloco_a)}-{max(bloco_a)}"
    label_b = f"{min(bloco_b)}-{max(bloco_b)}"
    id_a, id_b = label_a, label_b

    combined_a = build_ipca_selic_cross_periodo(out_dir, bloco_a)
    combined_b = build_ipca_selic_cross_periodo(out_dir, bloco_b)
    combined_a["bloco"] = id_a
    combined_b["bloco"] = id_b
    combined = pd.concat([combined_a, combined_b], ignore_index=True)

    media_a = _media_mensal_bloco(combined, bloco_a, id_a)
    media_b = _media_mensal_bloco(combined, bloco_b, id_b)
    media = pd.concat([media_a, media_b], ignore_index=True)

    resumo_a = summarize_ipca_selic_bloco(combined, bloco_a, id_a)
    resumo_b = summarize_ipca_selic_bloco(combined, bloco_b, id_b)

    out_cmp = ipca_selic_cross_comparativo_dir(out_dir, bloco_a, bloco_b)
    paths: list[Path] = []

    cmp_label = f"{label_a}-vs-{label_b}"
    combined.to_csv(out_cmp / f"comparacao_ipca_selic_{cmp_label}.csv", index=False, decimal=",", sep=";")
    paths.append(out_cmp / f"comparacao_ipca_selic_{cmp_label}.csv")

    media.to_csv(out_cmp / f"{cmp_label}-media-mensal-por-bloco.csv", index=False, decimal=",", sep=";")
    paths.append(out_cmp / f"{cmp_label}-media-mensal-por-bloco.csv")

    resumo_path = out_cmp / f"{cmp_label}-resumo-blocos.csv"
    pd.DataFrame([resumo_a, resumo_b]).to_csv(resumo_path, index=False, decimal=",", sep=";")
    paths.append(resumo_path)

    plot_specs: list[tuple[str, object]] = [
        (f"{cmp_label}-painel-blocos.png", plot_ipca_selic_cross_comparativo_blocos_painel),
        (f"{cmp_label}-metricas-blocos.png", plot_ipca_selic_cross_comparativo_blocos_metricas),
        (f"{cmp_label}-scatter-blocos.png", plot_ipca_selic_cross_comparativo_blocos_scatter),
        (f"{cmp_label}-spread-medio-mensal.png", plot_ipca_selic_cross_comparativo_blocos_spread),
        (f"{cmp_label}-erros-medio-mensal.png", plot_ipca_selic_cross_comparativo_blocos_erros),
    ]
    for nome, plot_fn in plot_specs:
        dest = out_cmp / nome
        if plot_fn(combined, media, resumo_a, resumo_b, id_a, id_b, cmp_label, dest):
            paths.append(dest)

    logger.info(
        "Comparativo %s vs %s: %s vs %s observações mensais.",
        id_a,
        id_b,
        resumo_a["n_observacoes_mensais"],
        resumo_b["n_observacoes_mensais"],
    )
    return combined, [resumo_a, resumo_b], paths
