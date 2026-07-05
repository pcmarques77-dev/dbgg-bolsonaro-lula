"""Exportação de gráficos com visual premium para publicação acadêmica.

Uso:
    python scripts/exportar_graficos_publicacao.py

Os PNGs são salvos em: output/publicacao/
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ── Garante imports da lib local ─────────────────────────────────────────────
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir / "src"))

OUT_DIR = root_dir.parent / "output" / "publicacao"
DATA_DIR = root_dir / "pib-focus-viz" / "public" / "data"

# ── Paleta e estilo premium ───────────────────────────────────────────────────
AZUL_FOCUS  = "#2563EB"   # Azul cobalto para expectativa Focus
CORAL       = "#DC2626"   # Vermelho coral para realizado IBGE
VERDE       = "#16A34A"   # Verde para erros negativos (otimismo correto)
CINZA_GRID  = "#E5E7EB"   # Cinza claro para linhas de grade
FUNDO       = "#FFFFFF"   # Fundo branco (padrão publicação)
FUNDO_PAINEL= "#F9FAFB"   # Fundo levemente acinzentado no painel do gráfico

FONTE_TITULO  = {"fontsize": 13, "fontweight": "bold",  "color": "#111827"}
FONTE_SUBTIT  = {"fontsize": 9.5, "color": "#6B7280", "style": "italic"}
FONTE_EIXO    = {"fontsize": 9,   "color": "#374151"}
FONTE_LEGENDA = {"size": 9}
FONTE_FONTE   = {"fontsize": 7.5, "color": "#9CA3AF", "style": "italic"}

DPI = 220  # Alta resolução para impressão


def _aplicar_estilo_base(fig: plt.Figure, ax: plt.Axes) -> None:
    """Aplica o estilo visual padrão a qualquer gráfico."""
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO_PAINEL)

    # Grade fina e discreta
    ax.grid(axis="y", color=CINZA_GRID, linewidth=0.7, zorder=0)
    ax.grid(axis="x", color=CINZA_GRID, linewidth=0.4, linestyle=":", zorder=0)

    # Remove bordas desnecessárias
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(CINZA_GRID)
    ax.spines["bottom"].set_color(CINZA_GRID)

    # Ticks discretos
    ax.tick_params(axis="both", which="both", length=0, labelsize=8.5, colors="#374151")


def _adicionar_nota_fonte(fig: plt.Figure, texto: str) -> None:
    """Adiciona nota de fonte no rodapé da figura."""
    fig.text(
        0.01, -0.02, texto,
        transform=fig.transFigure,
        **FONTE_FONTE,
        ha="left", va="top",
    )


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO: IPCA Mensal — Focus vs IBGE (2019–2022)
# ─────────────────────────────────────────────────────────────────────────────

def plot_ipca_mensal_publicacao(
    df: pd.DataFrame,
    out_png: Path,
    *,
    start_yyyymm: str = "201901",
    end_yyyymm: str = "202212",
) -> Path:
    """Gráfico de linhas duplo: expectativa Focus vs IBGE realizado, período mensal."""

    # Filtro de período
    df = df[
        (df["ref_yyyymm"].astype(str) >= start_yyyymm)
        & (df["ref_yyyymm"].astype(str) <= end_yyyymm)
    ].copy()

    if df.empty:
        print(f"[AVISO] Sem dados para o período {start_yyyymm}–{end_yyyymm}.")
        return out_png

    # Converte ref_yyyymm → datetime para eixo X
    df["data"] = pd.to_datetime(
        df["ref_yyyymm"].astype(str).apply(lambda s: f"{s[:4]}-{s[4:6]}-01")
    )
    df = df.sort_values("data")

    # ── Layout da figura ─────────────────────────────────────────────────────
    fig, (ax_main, ax_err) = plt.subplots(
        2, 1,
        figsize=(11, 6.5),
        gridspec_kw={"height_ratios": [3, 1.2], "hspace": 0.08},
        sharex=True,
    )
    fig.patch.set_facecolor(FUNDO)

    for ax in (ax_main, ax_err):
        _aplicar_estilo_base(fig, ax)

    # ── Painel superior: Focus vs IBGE ───────────────────────────────────────
    ax_main.plot(
        df["data"],
        df["ipca_focus_med_mensal_pct"],
        color=AZUL_FOCUS,
        linewidth=2.2,
        label="Focus — Mediana (último boletim antes do mês)",
        zorder=3,
        marker="o", markersize=3.5, markerfacecolor=AZUL_FOCUS, markeredgewidth=0,
    )
    ax_main.plot(
        df["data"],
        df["ipca_ibge_mensal_pct"],
        color=CORAL,
        linewidth=2.2,
        label="IBGE Realizado — IPCA mensal (SIDRA 1737)",
        zorder=3,
        marker="s", markersize=3.5, markerfacecolor=CORAL, markeredgewidth=0,
    )

    # Área sombreada entre as duas séries
    ax_main.fill_between(
        df["data"],
        df["ipca_focus_med_mensal_pct"],
        df["ipca_ibge_mensal_pct"],
        alpha=0.08,
        color=AZUL_FOCUS,
        zorder=1,
    )

    ax_main.set_ylabel("Variação Mensal (%)", **FONTE_EIXO)
    ax_main.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f%%"))
    ax_main.axhline(0, color="#9CA3AF", linewidth=0.8, linestyle="--", zorder=2)

    # Legenda
    ax_main.legend(
        loc="upper left",
        prop=FONTE_LEGENDA,
        framealpha=0.9,
        frameon=True,
        edgecolor=CINZA_GRID,
    )

    # Título principal
    ax_main.set_title(
        "IPCA Mensal: Expectativa Focus vs Realizado IBGE  |  2019–2022",
        pad=12,
        **FONTE_TITULO,
    )
    ax_main.text(
        0, 1.01,
        "Mediana das expectativas do último boletim Focus antes do início do mês de referência",
        transform=ax_main.transAxes,
        **FONTE_SUBTIT,
    )

    # Estatísticas no canto
    mae = df["erro_prev_menos_real_pp"].abs().mean()
    n = len(df)
    ax_main.text(
        0.99, 0.97,
        f"MAE = {mae:.3f} p.p.  |  n = {n} meses",
        transform=ax_main.transAxes,
        fontsize=8, color="#374151",
        ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=CINZA_GRID, alpha=0.9),
    )

    # ── Painel inferior: Erro de previsão ────────────────────────────────────
    erros = df["erro_prev_menos_real_pp"].values
    cores = [CORAL if e > 0 else VERDE for e in erros]

    ax_err.bar(
        df["data"],
        erros,
        width=20,              # largura em dias
        color=cores,
        alpha=0.85,
        zorder=3,
    )
    ax_err.axhline(0, color="#6B7280", linewidth=1.0, zorder=4)

    # Linha de MAE ± (referência)
    ax_err.axhline(mae, color=CORAL, linewidth=0.8, linestyle=":", alpha=0.6)
    ax_err.axhline(-mae, color=VERDE, linewidth=0.8, linestyle=":", alpha=0.6)

    ax_err.set_ylabel("Erro (p.p.)", **FONTE_EIXO)
    ax_err.yaxis.set_major_formatter(mticker.FormatStrFormatter("%+.2f"))

    # Patches para legenda do painel inferior
    from matplotlib.patches import Patch
    legenda_err = [
        Patch(facecolor=CORAL, alpha=0.85, label="Superestimativa (Focus > IBGE)"),
        Patch(facecolor=VERDE, alpha=0.85, label="Subestimativa (Focus < IBGE)"),
    ]
    ax_err.legend(
        handles=legenda_err,
        loc="lower left",
        prop={"size": 8},
        framealpha=0.9,
        frameon=True,
        edgecolor=CINZA_GRID,
    )

    # ── Eixo X compartilhado ─────────────────────────────────────────────────
    ax_err.xaxis.set_major_locator(mpl.dates.MonthLocator(bymonth=[1, 7]))
    ax_err.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b/%Y"))
    plt.setp(ax_err.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=8)

    # ── Nota de fonte ────────────────────────────────────────────────────────
    _adicionar_nota_fonte(
        fig,
        "Fonte: Banco Central do Brasil (Boletim Focus — Olinda API) e IBGE (SIDRA tabela 1737). "
        "Elaboração própria.",
    )

    # ── Salvar ───────────────────────────────────────────────────────────────
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=DPI, bbox_inches="tight", facecolor=FUNDO)
    plt.close(fig)
    print(f"[OK] Grafico salvo: {out_png}")
    return out_png


# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=== Exportando gráficos para publicação ===\n")

    # Carrega dados do CSV gerado pelo sync-data
    csv_path = DATA_DIR / "comparacao_ipca_mensal.csv"
    if not csv_path.exists():
        print(f"[ERRO] Arquivo não encontrado: {csv_path}")
        print("Execute primeiro: npm run sync-data  (dentro de v2/pib-focus-viz/)")
        sys.exit(1)

    df_ipca = pd.read_csv(csv_path, sep=";", decimal=",")

    # Gráfico IPCA Mensal 2019–2022
    plot_ipca_mensal_publicacao(
        df_ipca,
        OUT_DIR / "ipca_mensal_2019_2022.png",
        start_yyyymm="201901",
        end_yyyymm="202212",
    )

    print(f"\nArquivos salvos em: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
