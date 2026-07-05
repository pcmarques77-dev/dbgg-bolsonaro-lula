"""Graficos DBGG e DLSP (Focus vs SGS)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_dlsp_anual_focus_vs_realizado(
    comparacao: pd.DataFrame,
    out_png: Path,
    *,
    codigo_sgs: int = 4513,
) -> bool:
    """Barras agrupadas: última mediana Focus pré-divulgação vs DLSP dez/ano (SGS)."""
    df = comparacao.sort_values("ano").copy()
    df = df.dropna(subset=["focus_ultima_mediana_pct_pib", "dlsp_realizado_dez_pct_pib"])
    if len(df) < 1:
        return False

    x = range(len(df))
    w = 0.38
    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.55), 5), layout="constrained")
    ax.bar(
        [i - w / 2 for i in x],
        df["focus_ultima_mediana_pct_pib"],
        width=w,
        label="Expectativa Focus (última mediana pré-divulgação)",
        color="tab:blue",
        alpha=0.85,
    )
    ax.bar(
        [i + w / 2 for i in x],
        df["dlsp_realizado_dez_pct_pib"],
        width=w,
        label=f"DLSP realizada dez/ano (SGS {codigo_sgs}, % PIB)",
        color="tab:orange",
        alpha=0.85,
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["ano"].astype(str), rotation=45, ha="right")
    ax.set_ylabel("% do PIB — dívida líquida do setor público")
    ax.set_title(
        "DLSP anual: Focus vs realizado\n"
        "Mediana Focus na última survey antes da divulgação fiscal anual (proxy: 01/05/ano+1)",
    )
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def plot_dlsp_anual_erro_previsao(comparacao: pd.DataFrame, out_png: Path) -> bool:
    """Erro de previsão (Focus − realizado) por ano, em p.p."""
    df = comparacao.sort_values("ano").dropna(subset=["erro_focus_vs_realizado_pp"])
    if len(df) < 1:
        return False

    cores = ["tab:red" if v > 0 else "tab:green" for v in df["erro_focus_vs_realizado_pp"]]
    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.55), 4.5), layout="constrained")
    x = range(len(df))
    ax.bar(x, df["erro_focus_vs_realizado_pp"], color=cores, alpha=0.85)
    ax.axhline(0, color="0.3", linewidth=1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["ano"].astype(str), rotation=45, ha="right")
    ax.set_ylabel("Erro (p.p.) = Focus − realizado")
    ax.set_title(
        "Erro de previsão DLSP (% PIB)\n"
        "Positivo = Focus superestimou a razão dívida/PIB; negativo = subestimou",
    )
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def plot_dlsp_convergencia_exemplo(
    joined: pd.DataFrame,
    out_png: Path,
    *,
    ano_ref: int,
) -> bool:
    """Trajetória da expectativa Focus para um ano até a divulgação."""
    df = joined[joined["ano_ref"] == ano_ref].copy()
    df = df.dropna(subset=["survey_date", "dlsp_focus_med_pct_pib"]).sort_values("survey_date")
    if len(df) < 2:
        return False

    real = df["dlsp_sgs_pct_pib"].dropna()
    real_val = float(real.iloc[0]) if not real.empty else None

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        df["survey_date"],
        df["dlsp_focus_med_pct_pib"],
        color="tab:blue",
        label="Mediana Focus (DLSP % PIB)",
    )
    if real_val is not None:
        ax.axhline(
            real_val,
            color="tab:orange",
            linestyle="--",
            linewidth=1.5,
            label=f"Realizado dez/{ano_ref} = {real_val:.1f}% PIB (SGS 4513)",
        )
    ax.set_title(f"Convergência da expectativa Focus — DLSP {ano_ref}")
    ax.set_xlabel("Data da survey Focus")
    ax.set_ylabel("% do PIB")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def gerar_figuras_divida_dlsp(
    comparacao: pd.DataFrame,
    joined: pd.DataFrame,
    out_dir: Path,
    *,
    codigo_sgs: int = 4513,
    anos_convergencia: list[int] | None = None,
) -> list[Path]:
    """Gera PNGs de comparação DLSP anual em ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    escritos: list[Path] = []

    specs: list[tuple[str, callable]] = [
        (
            "comparacao_focus_dlsp_anual.png",
            lambda p: plot_dlsp_anual_focus_vs_realizado(
                comparacao,
                p,
                codigo_sgs=codigo_sgs,
            ),
        ),
        ("erro_previsao_dlsp_anual.png", lambda p: plot_dlsp_anual_erro_previsao(comparacao, p)),
    ]
    for nome, fn in specs:
        caminho = out_dir / nome
        if fn(caminho):
            escritos.append(caminho)

    if anos_convergencia is None:
        anos_convergencia = [2019, 2020, 2023]
    for ano in anos_convergencia:
        caminho = out_dir / f"convergencia_focus_dlsp_{ano}.png"
        if plot_dlsp_convergencia_exemplo(joined, caminho, ano_ref=ano):
            escritos.append(caminho)

    return escritos


def plot_dbgg_anual_focus_vs_realizado(
    comparacao: pd.DataFrame,
    out_png: Path,
    *,
    codigo_sgs: int = 13762,
    titulo_periodo: str = "",
) -> bool:
    df = comparacao.sort_values("ano").copy()
    df = df.dropna(subset=["focus_ultima_mediana_pct_pib"])
    if df.empty:
        return False

    x = range(len(df))
    w = 0.38
    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.55), 5), layout="constrained")
    ax.bar(
        [i - w / 2 for i in x],
        df["focus_ultima_mediana_pct_pib"],
        width=w,
        label="Expectativa Focus (última mediana pré-divulgação)",
        color="tab:blue",
        alpha=0.85,
    )
    real_mask = df["dbgg_realizado_dez_pct_pib"].notna()
    if real_mask.any():
        labeled = False
        for idx, (_, row) in enumerate(df.iterrows()):
            if pd.notna(row["dbgg_realizado_dez_pct_pib"]):
                ax.bar(
                    idx + w / 2,
                    row["dbgg_realizado_dez_pct_pib"],
                    width=w,
                    label=(
                        f"DBGG realizada dez/ano (SGS {codigo_sgs}, % PIB)"
                        if not labeled
                        else None
                    ),
                    color="tab:orange",
                    alpha=0.85,
                )
                labeled = True
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["ano"].astype(str), rotation=45, ha="right")
    ax.set_ylabel("% do PIB — dívida bruta do governo geral")
    titulo = "DBGG anual: Focus vs realizado"
    if titulo_periodo:
        titulo += f" ({titulo_periodo})"
    ax.set_title(
        f"{titulo}\n"
        "Mediana Focus na última survey antes da divulgação fiscal anual (proxy: 01/05/ano+1)",
    )
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def plot_dbgg_anual_erro_previsao(
    comparacao: pd.DataFrame,
    out_png: Path,
    *,
    titulo_periodo: str = "",
) -> bool:
    df = comparacao.sort_values("ano").dropna(subset=["erro_focus_vs_realizado_pp"])
    if df.empty:
        return False

    cores = ["tab:red" if v > 0 else "tab:green" for v in df["erro_focus_vs_realizado_pp"]]
    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.55), 4.5), layout="constrained")
    x = range(len(df))
    ax.bar(x, df["erro_focus_vs_realizado_pp"], color=cores, alpha=0.85)
    ax.axhline(0, color="0.3", linewidth=1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["ano"].astype(str), rotation=45, ha="right")
    ax.set_ylabel("Erro (p.p.) = Focus − realizado")
    titulo = "Erro de previsão DBGG (% PIB)"
    if titulo_periodo:
        titulo += f" — {titulo_periodo}"
    ax.set_title(f"{titulo}\nPositivo = Focus superestimou; negativo = subestimou")
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def plot_dbgg_dispersao(
    comparacao: pd.DataFrame,
    out_png: Path,
    *,
    titulo_periodo: str = "",
) -> bool:
    df = comparacao.dropna(subset=["focus_ultima_mediana_pct_pib", "dbgg_realizado_dez_pct_pib"])
    if len(df) < 1:
        return False

    fig, ax = plt.subplots(figsize=(6, 6), layout="constrained")
    ax.scatter(
        df["dbgg_realizado_dez_pct_pib"],
        df["focus_ultima_mediana_pct_pib"],
        s=60,
        alpha=0.85,
    )
    lo = min(df["dbgg_realizado_dez_pct_pib"].min(), df["focus_ultima_mediana_pct_pib"].min())
    hi = max(df["dbgg_realizado_dez_pct_pib"].max(), df["focus_ultima_mediana_pct_pib"].max())
    pad = (hi - lo) * 0.08 or 1.0
    lim = (lo - pad, hi + pad)
    ax.plot(lim, lim, "k--", linewidth=1, alpha=0.5, label="Acerto perfeito (45°)")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    for _, r in df.iterrows():
        ax.annotate(
            str(int(r["ano"])),
            (r["dbgg_realizado_dez_pct_pib"], r["focus_ultima_mediana_pct_pib"]),
            fontsize=8,
            xytext=(3, 3),
            textcoords="offset points",
        )
    ax.set_xlabel("DBGG realizada dez/ano (% PIB)")
    ax.set_ylabel("Focus última mediana pré-divulgação (% PIB)")
    titulo = "DBGG: Focus vs realizado (dispersão por ano)"
    if titulo_periodo:
        titulo += f" — {titulo_periodo}"
    ax.set_title(titulo)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="box")
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def plot_dbgg_convergencia(
    joined: pd.DataFrame,
    out_png: Path,
    *,
    ano_ref: int,
) -> bool:
    df = joined[joined["ano_ref"] == ano_ref].copy()
    df = df.dropna(subset=["survey_date", "dbgg_focus_med_pct_pib"]).sort_values("survey_date")
    if len(df) < 2:
        return False

    real = df["dbgg_sgs_pct_pib"].dropna()
    real_val = float(real.iloc[0]) if not real.empty else None

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        df["survey_date"],
        df["dbgg_focus_med_pct_pib"],
        color="tab:blue",
        label="Mediana Focus (DBGG % PIB)",
    )
    if real_val is not None:
        ax.axhline(
            real_val,
            color="tab:orange",
            linestyle="--",
            linewidth=1.5,
            label=f"Realizado dez/{ano_ref} = {real_val:.1f}% PIB (SGS 13762)",
        )
    ax.set_title(f"Convergência da expectativa Focus — DBGG {ano_ref}")
    ax.set_xlabel("Data da survey Focus")
    ax.set_ylabel("% do PIB")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def gerar_figuras_divida_dbgg(
    comparacao: pd.DataFrame,
    joined: pd.DataFrame,
    out_dir: Path,
    *,
    codigo_sgs: int = 13762,
    titulo_periodo: str = "",
    anos_convergencia: list[int] | None = None,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    escritos: list[Path] = []

    specs: list[tuple[str, callable]] = [
        (
            "comparacao_focus_dbgg.png",
            lambda p: plot_dbgg_anual_focus_vs_realizado(
                comparacao,
                p,
                codigo_sgs=codigo_sgs,
                titulo_periodo=titulo_periodo,
            ),
        ),
        (
            "erro_previsao_dbgg.png",
            lambda p: plot_dbgg_anual_erro_previsao(comparacao, p, titulo_periodo=titulo_periodo),
        ),
        (
            "dispersao_focus_dbgg.png",
            lambda p: plot_dbgg_dispersao(comparacao, p, titulo_periodo=titulo_periodo),
        ),
    ]
    for nome, fn in specs:
        caminho = out_dir / nome
        if fn(caminho):
            escritos.append(caminho)

    if anos_convergencia is None:
        anos = comparacao["ano"].dropna().astype(int).tolist()
        anos_convergencia = [anos[0], anos[-1]] if len(anos) >= 2 else anos
    for ano in anos_convergencia:
        caminho = out_dir / f"convergencia_focus_dbgg_{ano}.png"
        if plot_dbgg_convergencia(joined, caminho, ano_ref=int(ano)):
            escritos.append(caminho)

    return escritos
