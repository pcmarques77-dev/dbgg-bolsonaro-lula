"""Gráficos PIB trimestral Focus × IBGE (módulo isolado de ``figures.py``)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _ordenar_trimestres(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["_ord"] = out["ano_ref"].astype(int) * 10 + out["tri_ref"].astype(int)
    return out.sort_values("_ord").drop(columns=["_ord"])


def plot_pib_trimestral_focus_vs_ibge(
    comparacao: pd.DataFrame,
    out_png: Path,
    *,
    tabela_sidra: int = 5932,
    codigo_var_yoy: int = 6561,
) -> bool:
    df = _ordenar_trimestres(comparacao)
    df = df.dropna(subset=["focus_ultima_mediana_pct", "ibge_vol_yoy_trim_pct"])
    if len(df) < 2:
        return False

    x = range(len(df))
    w = 0.38
    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.42), 5), layout="constrained")
    ax.bar([i - w / 2 for i in x], df["focus_ultima_mediana_pct"], width=w, label="Focus", color="tab:blue")
    ax.bar([i + w / 2 for i in x], df["ibge_vol_yoy_trim_pct"], width=w, label="IBGE YoY", color="tab:orange")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["trimestre"], rotation=45, ha="right")
    ax.set_title(
        "PIB trimestral — Focus (pré-divulgação) × IBGE volume YoY\n"
        f"IBGE SIDRA t{tabela_sidra}, var. {codigo_var_yoy}; Focus ExpectativasMercadoTrimestrais"
    )
    ax.set_ylabel("Variação (%)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_trimestral_erro_previsao(comparacao: pd.DataFrame, out_png: Path) -> bool:
    df = _ordenar_trimestres(comparacao).dropna(subset=["erro_focus_vs_ibge_yoy_pp"])
    if len(df) < 2:
        return False

    cores = ["tab:red" if e > 0 else "tab:green" for e in df["erro_focus_vs_ibge_yoy_pp"]]
    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.42), 4.5), layout="constrained")
    x = range(len(df))
    ax.bar(x, df["erro_focus_vs_ibge_yoy_pp"], color=cores, alpha=0.85)
    ax.axhline(0, color="0.3", linewidth=1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["trimestre"], rotation=45, ha="right")
    ax.set_title("Erro de previsão PIB trimestral (Focus − IBGE YoY, p.p.)")
    ax.set_ylabel("Erro (p.p.)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_trimestral_dispersao(comparacao: pd.DataFrame, out_png: Path) -> bool:
    df = comparacao.dropna(subset=["focus_ultima_mediana_pct", "ibge_vol_yoy_trim_pct"])
    if len(df) < 3:
        return False

    fig, ax = plt.subplots(figsize=(6, 5), layout="constrained")
    ax.scatter(df["ibge_vol_yoy_trim_pct"], df["focus_ultima_mediana_pct"], alpha=0.75)
    lo = min(df["ibge_vol_yoy_trim_pct"].min(), df["focus_ultima_mediana_pct"].min()) - 1
    hi = max(df["ibge_vol_yoy_trim_pct"].max(), df["focus_ultima_mediana_pct"].max()) + 1
    ax.plot([lo, hi], [lo, hi], "k--", alpha=0.4, label="45° (acerto perfeito)")
    ax.set_xlabel("IBGE realizado YoY (%)")
    ax.set_ylabel("Focus última mediana (%)")
    ax.set_title("Dispersão Focus × IBGE — PIB trimestral")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_trimestral_convergencia_exemplo(
    joined: pd.DataFrame,
    out_png: Path,
    *,
    ano_ref: int,
    tri_ref: int,
) -> bool:
    sub = joined[(joined["ano_ref"] == ano_ref) & (joined["tri_ref"] == tri_ref)].copy()
    if sub.empty:
        return False
    sub = sub.sort_values("survey_date")
    ibge = sub["ibge_vol_yoy_trim_pct"].dropna()
    if ibge.empty:
        return False
    real = float(ibge.iloc[-1])

    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    ax.plot(sub["survey_date"], sub["pib_focus_trim_med_pct"], "o-", label="Focus mediana")
    ax.axhline(real, color="tab:orange", linestyle="--", label=f"IBGE YoY {real:.1f}%")
    ax.set_title(f"Convergência Focus — {tri_ref}T/{ano_ref}")
    ax.set_xlabel("Data survey")
    ax.set_ylabel("Variação (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def gerar_figuras_pib_trimestral(
    comparacao: pd.DataFrame,
    joined: pd.DataFrame,
    out_dir: Path,
    *,
    tabela_sidra: int = 5932,
    codigo_var_yoy: int = 6561,
    trimestres_convergencia: tuple[tuple[int, int], ...] = (
        (2, 2020),
        (1, 2023),
        (4, 2024),
    ),
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    escritos: list[Path] = []

    for nome, fn, kwargs in (
        (
            "comparacao_focus_ibge_pib_trimestral.png",
            plot_pib_trimestral_focus_vs_ibge,
            {"tabela_sidra": tabela_sidra, "codigo_var_yoy": codigo_var_yoy},
        ),
        ("erro_previsao_pib_trimestral.png", plot_pib_trimestral_erro_previsao, {}),
        ("dispersao_focus_ibge_pib_trimestral.png", plot_pib_trimestral_dispersao, {}),
    ):
        dest = out_dir / nome
        if fn(comparacao, dest, **kwargs):
            escritos.append(dest)

    for tri, ano in trimestres_convergencia:
        dest = out_dir / f"convergencia_focus_pib_{tri}t{ano}.png"
        if plot_pib_trimestral_convergencia_exemplo(joined, dest, ano_ref=ano, tri_ref=tri):
            escritos.append(dest)

    return escritos
