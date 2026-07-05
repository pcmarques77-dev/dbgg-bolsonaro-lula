"""Gráficos de conferência sobre o ``painel`` tabular."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .config import IPCA_ANOS_CALENDARIO_GRAFICOS

logger = logging.getLogger(__name__)


def plot_cambio_validacao(df: pd.DataFrame, out_png: Path, codigo_usd: int) -> None:
    """Expectativa média de câmbio (Focus) × USD realizada (SGS), cada uma onde existir valor."""
    if len(df) < 2:
        return

    fwd = df.dropna(subset=["survey_date", "usdbrl_med_fwd"]).copy()
    spot = df.dropna(subset=["survey_date", "usd_sgs_med"]).copy()

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    plotted = False
    if len(fwd) >= 2:
        ax.plot(
            fwd["survey_date"],
            fwd["usdbrl_med_fwd"],
            label="Expectativa média de câmbio (Focus, horiz. configurável)",
        )
        plotted = True
    if len(spot) >= 2:
        ax.plot(
            spot["survey_date"],
            spot["usd_sgs_med"],
            label=f"USD/BRL SGS código {codigo_usd}",
        )
        plotted = True
    if not plotted:
        plt.close(fig)
        return

    ax.set_title(
        "Checagem: expectativa de câmbio vs série diária "
        "(pregão até N dias úteis antes da survey)",
    )
    ax.set_xlabel("Data Focus")
    ax.set_ylabel("R$ / USD")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def plot_focus_ipca_vs_ibge_sidra(
    df: pd.DataFrame,
    out_png: Path,
    *,
    tabela_sidra: int,
    codigo_var: int,
    dia_public_approx: int,
) -> bool:
    """Expectativa Focus (próximos 12m) × IPCA oficial acumulado em 12 meses conhecido até a chave.

    Retorna ``True`` se escreveu o PNG.
    """
    if len(df) < 2:
        return False

    exp = df.dropna(subset=["survey_date", "ipca_med12m"]).copy()
    real = df.dropna(subset=["survey_date", "ipca_ibge_acum12m_pct"]).copy()
    if len(exp) < 2 and len(real) < 2:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    plotted = False
    if len(exp) >= 2:
        ax.plot(
            exp["survey_date"],
            exp["ipca_med12m"],
            label="Expectativa IPCA 12m (Focus — mediana)",
            color="tab:blue",
        )
        plotted = True
    if len(real) >= 2:
        ax.plot(
            real["survey_date"],
            real["ipca_ibge_acum12m_pct"],
            label=("IPCA oficial — var. acumulada em 12m (IBGE SIDRA)"),
            color="tab:orange",
        )
        plotted = True
    if not plotted:
        plt.close(fig)
        return False

    sub = (
        f"SIDRA tabela {tabela_sidra}, variável {codigo_var}; "
        f"disponibilidade aprox. = dia {dia_public_approx} "
        "do mês seguinte ao mês de referência (para merge_asof na chave Focus − lag)."
    )
    ax.set_title("Focus vs IPCA oficial (acumulado em 12 meses)\n" + sub)
    ax.set_xlabel("Data Focus")
    ax.set_ylabel("% a.a. (conceitos diferentes — leitura exploratória)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def plot_ipca_mes_focus_semanas(
    semanas: pd.DataFrame,
    linha_comparacao: pd.Series,
    out_png: Path,
) -> bool:
    """Mediana Focus semanal no mês de referência; destaca a última (usada na comparação)."""
    if semanas.empty or len(semanas) < 1:
        return False

    ref = str(linha_comparacao["ref_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    ultima_data = pd.Timestamp(linha_comparacao["survey_date_previsao"])

    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    ax.plot(
        semanas["survey_date"],
        semanas["ipca_focus_med_mensal_pct"],
        "o-",
        color="tab:blue",
        label="Mediana Focus (semanal)",
        markersize=7,
    )
    ult = semanas[semanas["survey_date"] == ultima_data]
    if not ult.empty:
        ax.scatter(
            ult["survey_date"],
            ult["ipca_focus_med_mensal_pct"],
            s=120,
            color="tab:red",
            zorder=5,
            label=f"Última do mês ({ultima_data.strftime('%d/%m/%Y')})",
        )

    ax.set_title(
        f"Focus — IPCA mensal previsto para {m:02d}/{y}\n"
        f"Boletim Focus semanal (ref. {m:02d}/{y}) — {len(semanas)} edição(ões) no mês "
        "(segunda ou 1º dia útil após)"
    )
    ax.set_xlabel("Data da survey Focus")
    ax.set_ylabel("Variação mensal esperada (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_mes_ibge_ponto(linha_comparacao: pd.Series, out_png: Path) -> bool:
    """IPCA realizado IBGE (var. mensal %) para o mês de referência."""
    if pd.isna(linha_comparacao.get("ipca_ibge_mensal_pct")):
        return False

    ref = str(linha_comparacao["ref_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    val = float(linha_comparacao["ipca_ibge_mensal_pct"])

    fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
    ax.bar(["IBGE"], [val], color="tab:orange", width=0.45)
    ax.set_title(
        f"IBGE — IPCA realizado {m:02d}/{y}\n"
        "SIDRA 1737, variável 63 (variação mensal %)"
    )
    ax.set_ylabel("Variação mensal (%)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_mes_comparacao_barras(linha_comparacao: pd.Series, out_png: Path) -> bool:
    """Barras: última mediana Focus no mês vs IPCA IBGE realizado."""
    if pd.isna(linha_comparacao.get("ipca_focus_med_mensal_pct")) or pd.isna(
        linha_comparacao.get("ipca_ibge_mensal_pct"),
    ):
        return False

    ref = str(linha_comparacao["ref_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    f_val = float(linha_comparacao["ipca_focus_med_mensal_pct"])
    i_val = float(linha_comparacao["ipca_ibge_mensal_pct"])
    s_date = pd.Timestamp(linha_comparacao["survey_date_previsao"]).strftime("%d/%m/%Y")
    erro = float(linha_comparacao["erro_prev_menos_real_pp"])

    fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    ax.bar(
        ["Focus\n(última semana)", "IBGE\n(realizado)"],
        [f_val, i_val],
        color=["tab:blue", "tab:orange"],
        width=0.5,
    )
    ax.set_title(
        f"IPCA {m:02d}/{y}: Focus × IBGE\n"
        f"Focus: mediana em {s_date} | Erro (Focus−IBGE): {erro:+.2f} p.p."
    )
    ax.set_ylabel("Variação mensal (%)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def _meses_eixo_resumo_anual(df: pd.DataFrame) -> pd.Series:
    if "mes_referencia" in df.columns:
        return pd.to_datetime(df["mes_referencia"].astype(str) + "-01")
    return pd.to_datetime(df["ref_yyyymm"].astype(str), format="%Y%m")


def plot_ipca_anual_focus_resumo_mensal(
    resumo: pd.DataFrame,
    ano: int,
    out_png: Path,
) -> bool:
    """Série anual: última edição semanal Focus por mês (consolidado mensal)."""
    df = resumo.dropna(subset=["ipca_focus_med_mensal_pct"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_resumo_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["ipca_focus_med_mensal_pct"],
        "o-",
        color="tab:blue",
        markersize=6,
        label="Focus — última edição semanal do mês",
    )
    ax.set_title(
        f"IPCA {ano} — expectativas Focus (mensal, mediana)\n"
        "Última publicação semanal (segunda ou 1º dia útil após) em cada mês"
    )
    ax.set_xlabel("Mês de referência")
    ax.set_ylabel("Variação mensal esperada (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_anual_ibge_resumo_mensal(
    resumo: pd.DataFrame,
    ano: int,
    out_png: Path,
) -> bool:
    """Série anual: IPCA mensal realizado IBGE (consolidado)."""
    df = resumo.dropna(subset=["ipca_ibge_mensal_pct"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_resumo_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["ipca_ibge_mensal_pct"],
        "s-",
        color="tab:orange",
        markersize=6,
        label="IBGE SIDRA — variação mensal realizada (%)",
    )
    ax.set_title(f"IPCA {ano} — realizado IBGE (mensal)\nSIDRA 1737, variável 63")
    ax.set_xlabel("Mês de referência")
    ax.set_ylabel("Variação mensal (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_anual_comparacao_resumo_mensal(
    resumo: pd.DataFrame,
    ano: int,
    out_png: Path,
) -> bool:
    """Comparação anual: Focus × IBGE mês a mês (12 pontos)."""
    df = resumo.dropna(subset=["ipca_focus_med_mensal_pct", "ipca_ibge_mensal_pct"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_resumo_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["ipca_focus_med_mensal_pct"],
        "o-",
        color="tab:blue",
        markersize=5,
        label="Focus — última edição semanal do mês",
    )
    ax.plot(
        x,
        df["ipca_ibge_mensal_pct"],
        "s-",
        color="tab:orange",
        markersize=5,
        label="IBGE — variação mensal realizada",
    )
    ax.set_title(
        f"IPCA {ano}: Focus × IBGE (comparação mensal)\n"
        "Mediana Focus (boletim semanal) vs SIDRA 1737/v.63"
    )
    ax.set_xlabel("Mês de referência")
    ax.set_ylabel("Variação mensal (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def _meses_eixo_trajetoria_anual(df: pd.DataFrame) -> pd.Series:
    if "mes_referencia" in df.columns:
        return pd.to_datetime(df["mes_referencia"].astype(str) + "-01")
    if "mes_publicacao" in df.columns:
        return pd.to_datetime(df["mes_publicacao"].astype(str) + "-01")
    if "mes_publicacao_yyyymm" in df.columns:
        return pd.to_datetime(df["mes_publicacao_yyyymm"].astype(str), format="%Y%m")
    return pd.to_datetime(df["ref_yyyymm"].astype(str), format="%Y%m")


def plot_ipca_ano_trajetoria_focus_semanas(
    semanas: pd.DataFrame,
    linha_comparacao: pd.Series,
    out_png: Path,
) -> bool:
    """Expectativa Focus para IPCA jan–dez do ano; edições semanais no mês de publicação."""
    if semanas.empty:
        return False

    ref = str(linha_comparacao["mes_publicacao_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = int(linha_comparacao["ano_ref"])
    ultima_data = pd.Timestamp(linha_comparacao["survey_date_previsao"])

    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    ax.plot(
        semanas["survey_date"],
        semanas["ipca_focus_ano_pct"],
        "o-",
        color="tab:blue",
        label="Mediana Focus (semanal)",
        markersize=7,
    )
    ult = semanas[semanas["survey_date"] == ultima_data]
    if not ult.empty:
        ax.scatter(
            ult["survey_date"],
            ult["ipca_focus_ano_pct"],
            s=120,
            color="tab:red",
            zorder=5,
            label=f"Última do mês ({ultima_data.strftime('%d/%m/%Y')})",
        )
    ax.set_title(
        f"Focus — IPCA ano-calendário {ano_ref} (publicação {m:02d}/{y})\n"
        f"ExpectativasMercadoAnuais, DataReferencia={ano_ref} — "
        f"{len(semanas)} edição(ões) no mês"
    )
    ax.set_xlabel("Data da survey Focus")
    ax.set_ylabel("Variação acumulada no ano esperada (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_ano_trajetoria_ibge_ponto(linha_comparacao: pd.Series, out_png: Path) -> bool:
    """IPCA realizado jan–dez do ano de referência (SIDRA var. 69, dezembro)."""
    if pd.isna(linha_comparacao.get("ipca_ibge_acum_ano_dez_pct")):
        return False

    ano_ref = int(linha_comparacao["ano_ref"])
    val = float(linha_comparacao["ipca_ibge_acum_ano_dez_pct"])

    fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
    ax.bar(["IBGE jan–dez"], [val], color="tab:orange", width=0.45)
    ax.set_title(
        f"IBGE — IPCA realizado {ano_ref} (acumulado jan–dez)\n"
        f"SIDRA 1737, variável 69 — divulgado ~jan/{ano_ref + 1}"
    )
    ax.set_ylabel("Variação acumulada no ano (%)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_ano_trajetoria_comparacao_barras(
    linha_comparacao: pd.Series,
    out_png: Path,
) -> bool:
    """Barras: expectativa Focus no mês de publicação vs IPCA jan–dez realizado."""
    if pd.isna(linha_comparacao.get("ipca_focus_ano_pct")) or pd.isna(
        linha_comparacao.get("ipca_ibge_acum_ano_dez_pct"),
    ):
        return False

    ref = str(linha_comparacao["mes_publicacao_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = int(linha_comparacao["ano_ref"])
    f_val = float(linha_comparacao["ipca_focus_ano_pct"])
    i_val = float(linha_comparacao["ipca_ibge_acum_ano_dez_pct"])
    s_date = pd.Timestamp(linha_comparacao["survey_date_previsao"]).strftime("%d/%m/%Y")
    erro = float(linha_comparacao["erro_prev_menos_real_pp"])

    fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    ax.bar(
        [f"Focus\n({m:02d}/{y})", f"IBGE\n{ano_ref} jan–dez"],
        [f_val, i_val],
        color=["tab:blue", "tab:orange"],
        width=0.5,
    )
    ax.set_title(
        f"IPCA {ano_ref}: expectativa em {m:02d}/{y} × realizado\n"
        f"Focus: mediana em {s_date} | Erro (Focus−IBGE): {erro:+.2f} p.p."
    )
    ax.set_ylabel("Variação acumulada no ano (%)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_anual_trajetoria_focus(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["ipca_focus_ano_pct"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_trajetoria_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["ipca_focus_ano_pct"],
        "o-",
        color="tab:blue",
        markersize=6,
        label="Focus — última edição semanal do mês de publicação",
    )
    ax.set_title(
        f"IPCA {ano_ref} — expectativa Focus ao longo de {ano_ref}\n"
        "Expectativa para inflação jan–dez (ExpectativasMercadoAnuais)"
    )
    ax.set_xlabel("Mês de publicação do boletim")
    ax.set_ylabel("Variação acumulada no ano esperada (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_anual_trajetoria_ibge(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["ipca_ibge_acum_ano_dez_pct"]).copy()
    if df.empty:
        return False
    x = _meses_eixo_trajetoria_anual(df)
    val = float(df["ipca_ibge_acum_ano_dez_pct"].iloc[0])

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.axhline(val, color="tab:orange", linestyle="--", linewidth=2, label=f"IBGE jan–dez {ano_ref}: {val:.2f}%")
    ax.set_xlim(x.min(), x.max())
    ax.set_title(
        f"IPCA {ano_ref} — realizado IBGE (referência única)\n"
        "SIDRA 1737, variável 69 — acumulado no ano-calendário"
    )
    ax.set_xlabel("Mês de publicação (eixo alinhado à trajetória Focus)")
    ax.set_ylabel("Variação acumulada no ano (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_anual_trajetoria_comparacao(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(
        subset=["ipca_focus_ano_pct", "ipca_ibge_acum_ano_dez_pct"],
    ).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_trajetoria_anual(df)
    ibge_val = float(df["ipca_ibge_acum_ano_dez_pct"].iloc[0])

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["ipca_focus_ano_pct"],
        "o-",
        color="tab:blue",
        markersize=5,
        label="Focus — expectativa jan–dez",
    )
    ax.axhline(
        ibge_val,
        color="tab:orange",
        linestyle="--",
        linewidth=2,
        label=f"IBGE realizado jan–dez {ano_ref}",
    )
    ax.set_title(
        f"IPCA {ano_ref}: trajetória Focus × realizado IBGE\n"
        "Expectativa mensal (boletim) vs IPCA acumulado jan–dez"
    )
    ax.set_xlabel("Mês de publicação do boletim Focus")
    ax.set_ylabel("Variação acumulada no ano (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_ano_trajetoria_focus_semanas(
    semanas: pd.DataFrame,
    linha_comparacao: pd.Series,
    out_png: Path,
) -> bool:
    """Expectativa Focus para PIB Total do ano; edições semanais no mês de publicação."""
    if semanas.empty:
        return False

    ref = str(linha_comparacao["mes_publicacao_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = int(linha_comparacao["ano_ref"])
    ultima_data = pd.Timestamp(linha_comparacao["survey_date_previsao"])
    col = "pib_focus_med_mensal_pct" if "pib_focus_med_mensal_pct" in semanas.columns else "pib_focus_ano_pct"

    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    ax.plot(
        semanas["survey_date"],
        semanas[col],
        "o-",
        color="tab:blue",
        label="Mediana Focus (semanal)",
        markersize=7,
    )
    ult = semanas[semanas["survey_date"] == ultima_data]
    if not ult.empty:
        ax.scatter(
            ult["survey_date"],
            ult[col],
            s=120,
            color="tab:red",
            zorder=5,
            label=f"Última do mês ({ultima_data.strftime('%d/%m/%Y')})",
        )
    ax.set_title(
        f"Focus — PIB Total {ano_ref} (publicação {m:02d}/{y})\n"
        f"ExpectativasMercadoAnuais, DataReferencia={ano_ref} — "
        f"{len(semanas)} edição(ões) no mês"
    )
    ax.set_xlabel("Data da survey Focus")
    ax.set_ylabel("Variação do PIB esperada (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_ano_trajetoria_ibge_ponto(linha_comparacao: pd.Series, out_png: Path) -> bool:
    """PIB realizado: taxa acumulada em 4 trimestres do 4T (IBGE Contas Nacionais)."""
    for col in ("pib_ibge_4tri_yoy_pct", "pib_sgs_nominal_yoy_pct", "pib_ibge_vol_yoy_pct"):
        if col in linha_comparacao.index and pd.notna(linha_comparacao.get(col)):
            real_col = col
            break
    else:
        return False

    ano_ref = int(linha_comparacao["ano_ref"])
    val = float(linha_comparacao[real_col])

    fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
    ax.bar(["IBGE 4T acum."], [val], color="tab:orange", width=0.45)
    ax.set_title(
        f"IBGE — PIB {ano_ref} (4T, taxa acum. 4 trimestres)\n"
        "Contas Nacionais Trimestrais — preços de mercado"
    )
    ax.set_ylabel("Variação % (acumulada 4 trimestres)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_ano_trajetoria_comparacao_barras(
    linha_comparacao: pd.Series,
    out_png: Path,
) -> bool:
    """Barras: expectativa Focus vs PIB IBGE 4T acumulado do ano."""
    real_col = None
    for col in ("pib_ibge_4tri_yoy_pct", "pib_sgs_nominal_yoy_pct", "pib_ibge_vol_yoy_pct"):
        if col in linha_comparacao.index and pd.notna(linha_comparacao.get(col)):
            real_col = col
            break
    if real_col is None or pd.isna(linha_comparacao.get("pib_focus_ano_pct")):
        return False

    ref = str(linha_comparacao["mes_publicacao_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = int(linha_comparacao["ano_ref"])
    f_val = float(linha_comparacao["pib_focus_ano_pct"])
    r_val = float(linha_comparacao[real_col])
    s_date = pd.Timestamp(linha_comparacao["survey_date_previsao"]).strftime("%d/%m/%Y")
    erro = float(linha_comparacao["erro_prev_menos_real_pp"])

    fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    ax.bar(
        [f"Focus\n({m:02d}/{y})", f"IBGE\n4T {ano_ref}"],
        [f_val, r_val],
        color=["tab:blue", "tab:orange"],
        width=0.5,
    )
    ax.set_title(
        f"PIB {ano_ref}: expectativa em {m:02d}/{y} × realizado IBGE\n"
        f"Focus: mediana em {s_date} | Erro (Focus−IBGE): {erro:+.2f} p.p."
    )
    ax.set_ylabel("Variação do PIB (%)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_anual_trajetoria_focus(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["pib_focus_ano_pct"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_trajetoria_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["pib_focus_ano_pct"],
        "o-",
        color="tab:blue",
        markersize=6,
        label="Focus — última edição semanal do mês de publicação",
    )
    ax.set_title(
        f"PIB {ano_ref} — expectativa Focus ao longo de {ano_ref}\n"
        "Expectativa para PIB Total ano-calendário (ExpectativasMercadoAnuais)"
    )
    ax.set_xlabel("Mês de publicação do boletim")
    ax.set_ylabel("Variação do PIB esperada (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


_PIB_REALIZADO_DEFAULTS = {
    2018: 1.8,
    2019: 1.2,
    2020: -3.3,
    2021: 4.8,
    2022: 3.0,
    2023: 3.2,
    2024: 3.4,
    2025: 2.3,
}


def plot_pib_anual_trajetoria_ibge(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    real_col = None
    for col in ("pib_ibge_4tri_yoy_pct", "pib_sgs_nominal_yoy_pct", "pib_ibge_vol_yoy_pct"):
        if col in resumo.columns:
            real_col = col
            break
    if real_col is None:
        return False
    df = resumo.dropna(subset=[real_col]).copy()
    if df.empty:
        return False
    x = _meses_eixo_trajetoria_anual(df)
    val = float(df[real_col].iloc[0])

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    prev_val = _PIB_REALIZADO_DEFAULTS.get(ano_ref - 1)
    if prev_val is not None:
        ax.plot(
            [x.iloc[0], x.iloc[-1]],
            [prev_val, val],
            "o--",
            color="tab:orange",
            linewidth=2,
            label=f"IBGE Realizado ({ano_ref - 1}: {prev_val:.2f}% -> {ano_ref}: {val:.2f}%)",
        )
    else:
        ax.axhline(
            val,
            color="tab:orange",
            linestyle="--",
            linewidth=2,
            label=f"IBGE 4T acum. {ano_ref}: {val:.2f}%",
        )
    ax.set_xlim(x.min(), x.max())
    ax.set_title(
        f"PIB {ano_ref} — realizado IBGE (referência única)\n"
        "Taxa acumulada em 4 trimestres — 4º trimestre do ano"
    )
    ax.set_xlabel("Mês de publicação (eixo alinhado à trajetória Focus)")
    ax.set_ylabel("Variação % (acumulada 4 trimestres)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_anual_trajetoria_comparacao(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    real_col = None
    for col in ("pib_ibge_4tri_yoy_pct", "pib_sgs_nominal_yoy_pct", "pib_ibge_vol_yoy_pct"):
        if col in resumo.columns:
            real_col = col
            break
    if real_col is None:
        return False
    df = resumo.dropna(
        subset=["pib_focus_ano_pct", real_col],
    ).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_trajetoria_anual(df)
    ibge_val = float(df[real_col].iloc[0])

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["pib_focus_ano_pct"],
        "o-",
        color="tab:blue",
        markersize=5,
        label="Focus — expectativa PIB Total",
    )
    prev_val = _PIB_REALIZADO_DEFAULTS.get(ano_ref - 1)
    if prev_val is not None:
        ax.plot(
            [x.iloc[0], x.iloc[-1]],
            [prev_val, ibge_val],
            "o--",
            color="tab:orange",
            linewidth=2,
            label=f"IBGE Realizado ({ano_ref - 1}: {prev_val:.2f}% -> {ano_ref}: {ibge_val:.2f}%)",
        )
    else:
        ax.axhline(
            ibge_val,
            color="tab:orange",
            linestyle="--",
            linewidth=2,
            label=f"IBGE 4T acum. {ano_ref}",
        )
    ax.set_title(
        f"PIB {ano_ref}: trajetória Focus × realizado IBGE\n"
        "Expectativa mensal (boletim) vs taxa acumulada 4 trimestres (4T)"
    )
    ax.set_xlabel("Mês de publicação do boletim Focus")
    ax.set_ylabel("Variação do PIB (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_periodo_trajetoria_focus(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    df = combined.dropna(subset=["pib_focus_ano_pct"]).copy()
    if df.empty:
        return False

    fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
    _plot_series_por_ano(ax, df, anos, "pib_focus_ano_pct")
    ax.set_title(
        f"{periodo_label}: expectativa Focus PIB Total (eixo = mês de publicação)\n"
        "ExpectativasMercadoAnuais — DataReferencia = ano-calendário"
    )
    ax.set_xlabel("Mês de publicação do boletim Focus")
    ax.set_ylabel("Variação do PIB esperada (%)")
    ax.legend(loc="upper left", ncol=min(len(anos), 4), fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_periodo_trajetoria_realizado(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    n = len(anos)
    if n < 1:
        return False

    ncols = min(4, n)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 3.5 * nrows), layout="constrained")
    axes_flat = axes.flatten() if n > 1 else [axes]

    for j, ano in enumerate(anos):
        sub = combined[combined["ano_ref"] == ano].sort_values("mes_calendario")
        ax = axes_flat[j]
        if sub.empty:
            ax.set_visible(False)
            continue
        real = sub["pib_ibge_4tri_yoy_pct"].iloc[0] if "pib_ibge_4tri_yoy_pct" in sub.columns else float("nan")
        ax.plot(sub["mes_calendario"], sub["pib_focus_ano_pct"], "o-", color="tab:blue")
        if pd.notna(real):
            ax.axhline(float(real), color="tab:orange", linestyle="--", linewidth=2)
            ax.set_title(f"PIB {ano} — Focus × IBGE 4T {float(real):.2f}%")
        else:
            ax.set_title(f"PIB {ano} — Focus (realizado pendente)")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(_MESES_CALENDARIO, rotation=45, ha="right", fontsize=8)
        ax.grid(True, alpha=0.3)

    for k in range(n, len(axes_flat)):
        axes_flat[k].set_visible(False)

    fig.suptitle(
        f"{periodo_label}: trajetórias Focus vs IBGE 4T acumulado (exploratório)",
        fontsize=11,
    )
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_periodo_painel(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    df = combined.dropna(subset=["pib_focus_ano_pct"]).copy()
    if df.empty:
        return False

    fig, (ax_focus, ax_erro) = plt.subplots(2, 1, figsize=(10, 7), layout="constrained", sharex=True)
    _plot_series_por_ano(ax_focus, df, anos, "pib_focus_ano_pct")
    ax_focus.set_ylabel("PIB Focus (%)")
    ax_focus.set_title(f"{periodo_label} — expectativa PIB Total ano-calendário")
    ax_focus.legend(loc="upper left", ncol=min(len(anos), 4), fontsize=8)
    ax_focus.grid(True, alpha=0.3)

    df_erro = combined.dropna(subset=["erro_prev_menos_real_pp"]).copy()
    if not df_erro.empty:
        _plot_series_por_ano(ax_erro, df_erro, anos, "erro_prev_menos_real_pp", marker="s")
    ax_erro.axhline(0, color="gray", linewidth=0.8)
    ax_erro.set_ylabel("Erro (p.p.)")
    ax_erro.set_xlabel("Mês de publicação do boletim Focus")
    ax_erro.set_title(f"{periodo_label} — erro Focus − IBGE 4T")
    ax_erro.legend(loc="upper right", ncol=min(len(anos), 4), fontsize=8)
    ax_erro.grid(True, alpha=0.3)

    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_pib_periodo_erros(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    df = combined.dropna(subset=["erro_prev_menos_real_pp"]).copy()
    if df.empty:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    _plot_series_por_ano(ax, df, anos, "erro_prev_menos_real_pp", marker="s")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title(
        f"{periodo_label}: erro Focus − IBGE 4T (p.p.)\n"
        "Comparação exploratória — trajetória mensal de publicação"
    )
    ax.set_xlabel("Mês de publicação do boletim Focus")
    ax.set_ylabel("Erro (Focus − realizado, p.p.)")
    ax.legend(loc="upper right", ncol=min(len(anos), 4))
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_mes_focus_semanas(
    semanas: pd.DataFrame,
    linha_comparacao: pd.Series,
    out_png: Path,
) -> bool:
    """Mediana Focus semanal no mês de referência da reunião Copom."""
    if semanas.empty:
        return False

    ref = str(linha_comparacao["ref_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    ultima_data = pd.Timestamp(linha_comparacao["survey_date_previsao"])
    col = "selic_focus_pct" if "selic_focus_pct" in semanas.columns else "ipca_focus_med_mensal_pct"

    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    ax.plot(
        semanas["survey_date"],
        semanas[col],
        "o-",
        color="tab:blue",
        label="Mediana Focus (semanal)",
        markersize=7,
    )
    ult = semanas[semanas["survey_date"] == ultima_data]
    if not ult.empty:
        ax.scatter(
            ult["survey_date"],
            ult[col],
            s=120,
            color="tab:red",
            zorder=5,
            label=f"Última do mês ({ultima_data.strftime('%d/%m/%Y')})",
        )
    reuniao = linha_comparacao.get("reuniao_focus", "")
    ax.set_title(
        f"Focus — Selic reunião {m:02d}/{y}\n"
        f"ExpectativasMercadoSelic, {reuniao} — {len(semanas)} edição(ões) no mês"
    )
    ax.set_xlabel("Data da survey Focus")
    ax.set_ylabel("Taxa esperada (% a.a.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_mes_sgs_ponto(linha_comparacao: pd.Series, out_png: Path) -> bool:
    if pd.isna(linha_comparacao.get("selic_sgs_pct_aa_aprox")):
        return False

    ref = str(linha_comparacao["ref_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    val = float(linha_comparacao["selic_sgs_pct_aa_aprox"])

    fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
    ax.bar(["SGS 11"], [val], color="tab:green", width=0.45)
    ax.set_title(
        f"SGS — Selic realizada {m:02d}/{y}\n"
        "Última observação do mês, % a.a. anualizada (252 d.u.)"
    )
    ax.set_ylabel("Taxa (% a.a.)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_mes_comparacao_barras(linha_comparacao: pd.Series, out_png: Path) -> bool:
    if pd.isna(linha_comparacao.get("selic_focus_pct")) or pd.isna(
        linha_comparacao.get("selic_sgs_pct_aa_aprox"),
    ):
        return False

    ref = str(linha_comparacao["ref_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    f_val = float(linha_comparacao["selic_focus_pct"])
    i_val = float(linha_comparacao["selic_sgs_pct_aa_aprox"])
    s_date = pd.Timestamp(linha_comparacao["survey_date_previsao"]).strftime("%d/%m/%Y")
    erro = float(linha_comparacao["erro_prev_menos_real_pp"])

    fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    ax.bar(
        ["Focus\n(última semana)", "SGS\n(realizado)"],
        [f_val, i_val],
        color=["tab:blue", "tab:green"],
        width=0.5,
    )
    ax.set_title(
        f"Selic {m:02d}/{y}: Focus × SGS\n"
        f"Focus: mediana em {s_date} | Erro (Focus−SGS): {erro:+.2f} p.p."
    )
    ax.set_ylabel("Taxa (% a.a.)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_anual_focus_resumo_mensal(
    resumo: pd.DataFrame,
    ano: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["selic_focus_pct"]).copy()
    if len(df) < 1:
        return False
    x = _meses_eixo_trajetoria_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["selic_focus_pct"],
        "o-",
        color="tab:blue",
        markersize=6,
        label="Focus — última edição semanal do mês",
    )
    ax.set_title(
        f"Selic {ano} — expectativas Focus por reunião (mensal)\n"
        "Última publicação semanal (segunda ou 1º dia útil após) em cada mês"
    )
    ax.set_xlabel("Mês de referência (reunião)")
    ax.set_ylabel("Taxa esperada (% a.a.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_anual_sgs_resumo_mensal(
    resumo: pd.DataFrame,
    ano: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["selic_sgs_pct_aa_aprox"]).copy()
    if len(df) < 1:
        return False
    x = _meses_eixo_trajetoria_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["selic_sgs_pct_aa_aprox"],
        "s-",
        color="tab:green",
        markersize=6,
        label="SGS 11 — fechamento do mês",
    )
    ax.set_title(f"Selic {ano} — realizada SGS (mensal)\nÚltima observação do mês, % a.a. anualizada")
    ax.set_xlabel("Mês de referência")
    ax.set_ylabel("Taxa (% a.a.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_anual_comparacao_resumo_mensal(
    resumo: pd.DataFrame,
    ano: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["selic_focus_pct", "selic_sgs_pct_aa_aprox"]).copy()
    if len(df) < 1:
        return False
    x = _meses_eixo_trajetoria_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["selic_focus_pct"],
        "o-",
        color="tab:blue",
        markersize=5,
        label="Focus — última edição semanal do mês",
    )
    ax.plot(
        x,
        df["selic_sgs_pct_aa_aprox"],
        "s-",
        color="tab:green",
        markersize=5,
        label="SGS — fechamento do mês",
    )
    ax.set_title(
        f"Selic {ano}: Focus × SGS (comparação mensal)\n"
        "Mediana Focus (boletim semanal) vs SGS 11 no fechamento do mês"
    )
    ax.set_xlabel("Mês de referência")
    ax.set_ylabel("Taxa (% a.a.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_ano_trajetoria_focus_semanas(
    semanas: pd.DataFrame,
    linha_comparacao: pd.Series,
    out_png: Path,
) -> bool:
    """Expectativa Focus Selic fim de ano; edições semanais no mês de publicação."""
    if semanas.empty:
        return False

    ref = str(linha_comparacao["mes_publicacao_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = int(linha_comparacao["ano_ref"])
    ultima_data = pd.Timestamp(linha_comparacao["survey_date_previsao"])
    col = "selic_focus_pct" if "selic_focus_pct" in semanas.columns else "ipca_focus_med_mensal_pct"

    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    ax.plot(
        semanas["survey_date"],
        semanas[col],
        "o-",
        color="tab:blue",
        label="Mediana Focus (semanal)",
        markersize=7,
    )
    ult = semanas[semanas["survey_date"] == ultima_data]
    if not ult.empty:
        ax.scatter(
            ult["survey_date"],
            ult[col],
            s=120,
            color="tab:red",
            zorder=5,
            label=f"Última do mês ({ultima_data.strftime('%d/%m/%Y')})",
        )
    reuniao = linha_comparacao.get("reuniao_focus", "")
    ax.set_title(
        f"Focus — Selic fim de {ano_ref} (publicação {m:02d}/{y})\n"
        f"ExpectativasMercadoSelic, {reuniao} — {len(semanas)} edição(ões) no mês"
    )
    ax.set_xlabel("Data da survey Focus")
    ax.set_ylabel("Taxa esperada (% a.a.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_ano_trajetoria_sgs_ponto(linha_comparacao: pd.Series, out_png: Path) -> bool:
    """Selic SGS 11 — última obs. de dezembro do ano, anualizada."""
    if pd.isna(linha_comparacao.get("selic_sgs_pct_aa_aprox")):
        return False

    ano_ref = int(linha_comparacao["ano_ref"])
    val = float(linha_comparacao["selic_sgs_pct_aa_aprox"])

    fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
    ax.bar(["SGS 11\ndez."], [val], color="tab:green", width=0.45)
    ax.set_title(
        f"SGS — Selic realizada {ano_ref}\n"
        f"Última observação de dez./{ano_ref}, % a.a. anualizada (252 d.u.)"
    )
    ax.set_ylabel("Taxa (% a.a.)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_ano_trajetoria_comparacao_barras(
    linha_comparacao: pd.Series,
    out_png: Path,
) -> bool:
    if pd.isna(linha_comparacao.get("selic_focus_pct")) or pd.isna(
        linha_comparacao.get("selic_sgs_pct_aa_aprox"),
    ):
        return False

    ref = str(linha_comparacao["mes_publicacao_yyyymm"])
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = int(linha_comparacao["ano_ref"])
    f_val = float(linha_comparacao["selic_focus_pct"])
    i_val = float(linha_comparacao["selic_sgs_pct_aa_aprox"])
    s_date = pd.Timestamp(linha_comparacao["survey_date_previsao"]).strftime("%d/%m/%Y")
    erro = float(linha_comparacao["erro_prev_menos_real_pp"])

    fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    ax.bar(
        [f"Focus\n({m:02d}/{y})", f"SGS\n{ano_ref} dez."],
        [f_val, i_val],
        color=["tab:blue", "tab:green"],
        width=0.5,
    )
    ax.set_title(
        f"Selic {ano_ref}: expectativa em {m:02d}/{y} × realizada\n"
        f"Focus: mediana em {s_date} | Erro (Focus−SGS): {erro:+.2f} p.p."
    )
    ax.set_ylabel("Taxa (% a.a.)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.bar_label(ax.containers[0], fmt="%.2f%%")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_anual_trajetoria_focus(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["selic_focus_pct"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_trajetoria_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["selic_focus_pct"],
        "o-",
        color="tab:blue",
        markersize=6,
        label="Focus — última edição semanal do mês",
    )
    ax.set_title(
        f"Selic {ano_ref} — expectativa Focus ao longo de {ano_ref}\n"
        "Mediana na última reunião do ano-calendário (ExpectativasMercadoSelic)"
    )
    ax.set_xlabel("Mês de publicação do boletim")
    ax.set_ylabel("Taxa esperada (% a.a.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_anual_trajetoria_sgs(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["selic_sgs_pct_aa_aprox"]).copy()
    if df.empty:
        return False
    x = _meses_eixo_trajetoria_anual(df)
    val = float(df["selic_sgs_pct_aa_aprox"].iloc[0])

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.axhline(
        val,
        color="tab:green",
        linestyle="--",
        linewidth=2,
        label=f"SGS 11 dez./{ano_ref}: {val:.2f}% a.a.",
    )
    ax.set_xlim(x.min(), x.max())
    ax.set_title(
        f"Selic {ano_ref} — realizada SGS (referência única)\n"
        "Última observação de dezembro, taxa diária anualizada"
    )
    ax.set_xlabel("Mês de publicação (eixo alinhado à trajetória Focus)")
    ax.set_ylabel("Taxa (% a.a.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_selic_anual_trajetoria_comparacao(
    resumo: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = resumo.dropna(subset=["selic_focus_pct", "selic_sgs_pct_aa_aprox"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_trajetoria_anual(df)
    sgs_val = float(df["selic_sgs_pct_aa_aprox"].iloc[0])

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["selic_focus_pct"],
        "o-",
        color="tab:blue",
        markersize=5,
        label="Focus — Selic fim de ano",
    )
    ax.axhline(
        sgs_val,
        color="tab:green",
        linestyle="--",
        linewidth=2,
        label=f"SGS realizada dez./{ano_ref}",
    )
    ax.set_title(
        f"Selic {ano_ref}: trajetória Focus × SGS\n"
        "Expectativa mensal (boletim) vs fechamento dezembro (exploratório)"
    )
    ax.set_xlabel("Mês de publicação do boletim Focus")
    ax.set_ylabel("Taxa (% a.a.)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_mensal_focus_vs_ibge(
    comparacao: pd.DataFrame,
    out_png: Path,
) -> bool:
    """Última mediana Focus no mês de referência × IPCA mensal realizado (IBGE var. 63)."""
    if len(comparacao) < 2:
        return False
    df = comparacao.dropna(
        subset=["ipca_focus_med_mensal_pct", "ipca_ibge_mensal_pct"],
    ).copy()
    if len(df) < 2:
        return False

    x = pd.to_datetime(df["ref_yyyymm"].astype(str), format="%Y%m")
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        x,
        df["ipca_focus_med_mensal_pct"],
        "o-",
        label="Focus — última mediana no mês de referência",
        color="tab:blue",
        markersize=4,
    )
    ax.plot(
        x,
        df["ipca_ibge_mensal_pct"],
        "s-",
        label="IBGE SIDRA — variação mensal realizada (%)",
        color="tab:orange",
        markersize=4,
    )
    ax.set_title(
        "IPCA mensal: previsão Focus (mês de referência) × realizado IBGE\n"
        "Par conceitual: ExpectativaMercadoMensais vs SIDRA 1737/v.63"
    )
    ax.set_xlabel("Mês de referência")
    ax.set_ylabel("Variação mensal (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_ano_focus(comparacao: pd.DataFrame, out_png: Path) -> bool:
    """Expectativa Focus semanal — IPCA ano-calendário corrente (mediana)."""
    exp = comparacao.dropna(subset=["survey_date", "ipca_focus_ano_pct"]).copy()
    if len(exp) < 2:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        exp["survey_date"],
        exp["ipca_focus_ano_pct"],
        color="tab:blue",
        label="Focus — IPCA ano-calendário corrente (mediana)",
    )
    ax.set_title(
        "Focus — IPCA ano-calendário corrente (mediana semanal)\n"
        "ExpectativasMercadoAnuais (ano da survey = ano de referência)"
    )
    ax.set_xlabel("Data Focus")
    ax.set_ylabel("Inflação esperada (% no ano)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_ano_ibge(comparacao: pd.DataFrame, out_png: Path) -> bool:
    """IPCA realizado IBGE — acumulado jan–dez (SIDRA v.69), em degraus após divulgação."""
    real = comparacao.dropna(subset=["survey_date", "ipca_ibge_acum_ano_dez_pct"]).copy()
    if len(real) < 2:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(
        real["survey_date"],
        real["ipca_ibge_acum_ano_dez_pct"],
        drawstyle="steps-post",
        color="tab:orange",
        label="IBGE — acumulado no ano (dez.; SIDRA 1737/v.69)",
    )
    ax.set_title(
        "IBGE — IPCA acumulado no ano-calendário (jan–dez)\n"
        "Série em degraus: valor entra após proxy de divulgação (~jan do ano seguinte)"
    )
    ax.set_xlabel("Data Focus (eixo temporal do painel)")
    ax.set_ylabel("Inflação realizada (% no ano)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_ano_por_ano_calendario(
    comparacao: pd.DataFrame,
    out_dir: Path,
    *,
    anos: tuple[int, ...] = IPCA_ANOS_CALENDARIO_GRAFICOS,
) -> list[Path]:
    """Um PNG por ``ipca_year_ref``: expectativa Focus semanal × IBGE (jan–dez) naquele ano."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if comparacao.empty:
        return []

    df = comparacao.copy()
    df["survey_date"] = pd.to_datetime(df["survey_date"])
    df["ipca_year_ref"] = pd.to_numeric(df["ipca_year_ref"], errors="coerce").astype("Int64")

    escritos: list[Path] = []
    for ano in anos:
        sub = df[df["ipca_year_ref"] == ano].sort_values("survey_date")
        exp = sub.dropna(subset=["ipca_focus_ano_pct"])
        real = sub.dropna(subset=["ipca_ibge_acum_ano_dez_pct"])
        if len(exp) < 2 and len(real) < 1:
            logger.warning(
                "ipca-ano-por-ano: sem dados para %s (use --start-date 2018-01-01 ou anterior se faltar 2018)",
                ano,
            )
            continue

        fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
        if len(exp) >= 2:
            ax.plot(
                exp["survey_date"],
                exp["ipca_focus_ano_pct"],
                color="tab:blue",
                label="Focus — mediana ano-calendário",
            )
        if len(real) >= 1:
            ax.plot(
                real["survey_date"],
                real["ipca_ibge_acum_ano_dez_pct"],
                drawstyle="steps-post",
                color="tab:orange",
                label="IBGE — acum. jan–dez (SIDRA v.69)",
            )

        ax.set_title(
            f"IPCA ano-calendário {ano}: expectativa Focus × realizado IBGE\n"
            f"Surveys com referência {ano} (ExpectativasMercadoAnuais)"
        )
        ax.set_xlabel("Data Focus")
        ax.set_ylabel("Inflação (% no ano)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        out_png = out_dir / f"ipca_ano_calendario_{ano}.png"
        fig.savefig(out_png, dpi=300)
        plt.close(fig)
        escritos.append(out_png)
        logger.info("Gráfico ano %s: %s", ano, out_png.name)

    return escritos


def plot_ipca_ano_calendario_focus_vs_ibge(
    comparacao: pd.DataFrame,
    out_png: Path,
) -> bool:
    """Trajetória semanal Focus (IPCA fim do ano corrente) × realizado dezembro (acum. no ano)."""
    exp = comparacao.dropna(subset=["survey_date", "ipca_focus_ano_pct"]).copy()
    real = comparacao.dropna(subset=["survey_date", "ipca_ibge_acum_ano_dez_pct"]).copy()
    if len(exp) < 2 and len(real) < 2:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    plotted = False
    if len(exp) >= 2:
        ax.plot(
            exp["survey_date"],
            exp["ipca_focus_ano_pct"],
            label="Focus — IPCA ano-calendário corrente (mediana)",
            color="tab:blue",
        )
        plotted = True
    if len(real) >= 2:
        ax.plot(
            real["survey_date"],
            real["ipca_ibge_acum_ano_dez_pct"],
            drawstyle="steps-post",
            label="IBGE — acumulado no ano (dez.; SIDRA 1737/v.69)",
            color="tab:orange",
        )
        plotted = True
    if not plotted:
        plt.close(fig)
        return False

    ax.set_title(
        "IPCA fim de ano: expectativa Focus semanal × realizado IBGE (jan–dez)\n"
        "ExpectativasMercadoAnuais (ano da survey) vs acumulado no ano em dezembro"
    )
    ax.set_xlabel("Data Focus")
    ax.set_ylabel("Inflação (% no ano)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_focus_pib_vs_bcb_sgs1207_nominal_yoy(
    df: pd.DataFrame,
    out_png: Path,
    *,
    codigo_sgs: int,
    dias_divulgacao_pos_31dez: int,
) -> bool:
    """Expectativa Focus (PIB Total %, ano-calendario) vs YoY nominal SGS nivel 1207 (%)."""

    if len(df) < 2:
        return False
    exp = df.dropna(subset=["survey_date", "pib_med_pct"]).copy()
    real = df.dropna(subset=["survey_date", "pib_sgs_nominal_yoy_pct"]).copy()
    if len(exp) < 2 and len(real) < 2:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    plotted = False
    if len(exp) >= 2:
        ax.plot(
            exp["survey_date"],
            exp["pib_med_pct"],
            label="Expectativa PIB Total (Focus - mediana, % ano)",
            color="tab:blue",
        )
        plotted = True
    if len(real) >= 2:
        ax.plot(
            real["survey_date"],
            real["pib_sgs_nominal_yoy_pct"],
            label=f"YoY nominal PIB R$ correntes (SGS {codigo_sgs}), steps-post",
            color="tab:orange",
            drawstyle="steps-post",
        )
        plotted = True
    if not plotted:
        plt.close(fig)
        return False

    sub = (
        f"SGS {codigo_sgs} (PIB R$ correntes, anual); YoY = (V_t/V_t-1-1)*100; "
        f"realizado só após ~{dias_divulgacao_pos_31dez} dias de 31/12 do ano-ref. "
        "Focus costuma referir variação a preços de mercado com metodologia SCN - "
        "não confundir com crescimento nominal."
    )
    ax.set_title("Focus PIB vs PIB nominal BC (var. % a.a.)\n" + sub)
    ax.set_xlabel("Data Focus")
    ax.set_ylabel("% (leitura exploratória)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def plot_focus_selic_vs_bcb_sgs11(
    df: pd.DataFrame,
    out_png: Path,
    *,
    codigo_sgs: int,
    market_lag_bdias: int,
) -> bool:
    """Expectativa Focus (Selic fim‑ano convênção reuniões) × Selic SGS (spot diário anualizado)."""

    if len(df) < 2:
        return False

    exp = df.dropna(subset=["survey_date", "selic_mediana_pct"]).copy()
    real = df.dropna(subset=["survey_date", "selic_sgs_pct_aa_aprox"]).copy()
    if len(exp) < 2 and len(real) < 2:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    plotted = False
    if len(exp) >= 2:
        ax.plot(
            exp["survey_date"],
            exp["selic_mediana_pct"],
            label="Selic esperada — mediana Focus (último R*/ano do ano‑calendário da survey)",
            color="tab:blue",
        )
        plotted = True
    if len(real) >= 2:
        ax.plot(
            real["survey_date"],
            real["selic_sgs_pct_aa_aprox"],
            label=f"Selic realizada — SGS {codigo_sgs}, % diária anualizada (1+r_d)^252−1",
            color="tab:orange",
        )
        plotted = True
    if not plotted:
        plt.close(fig)
        return False

    sub = (
        f"Chave temporal: último pregão ≤ survey menos {market_lag_bdias} BD. "
        "Focus: nível esperado ao fim do ano por convenção Focus (ver selic_meeting_used). "
        "Laranja: taxa corrente (não nível médio‑ano): só comparações exploratórias."
    )
    ax.set_title("Focus Selic × Selic efetiva (SGS)\n" + sub)
    ax.set_xlabel("Data Focus")
    ax.set_ylabel("% ao ano proxy (exploratório)")
    ax.legend(fontsize="small")
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def plot_focus_pib_vs_ibge_volume_anual(
    df: pd.DataFrame,
    out_png: Path,
    *,
    tabela_sidra: int,
    codigo_var: int,
    dias_pos_31dez: int,
) -> bool:
    """Expectativa Focus (PIB % ano-cal.) vs SIDRA ``PIB - variacao em volume`` anual."""

    if len(df) < 2:
        return False
    exp = df.dropna(subset=["survey_date", "pib_med_pct"]).copy()
    real = df.dropna(subset=["survey_date", "pib_ibge_vol_yoy_pct"]).copy()
    if len(exp) < 2 and len(real) < 2:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    plotted = False
    if len(exp) >= 2:
        ax.plot(
            exp["survey_date"],
            exp["pib_med_pct"],
            label="Expectativa PIB Total (Focus - mediana, % ano)",
            color="tab:blue",
        )
        plotted = True
    if len(real) >= 2:
        ax.plot(
            real["survey_date"],
            real["pib_ibge_vol_yoy_pct"],
            label=f"Ultimo oficial IBGE (SIDRA {tabela_sidra}/v.{codigo_var}), por data-chave",
            color="tab:orange",
            drawstyle="steps-post",
        )
        plotted = True
    if not plotted:
        plt.close(fig)
        return False

    sub = (
        f"Laranja: merge_asof backward - ultimo PIB ({tabela_sidra}/v.{codigo_var}) cujo calendário de "
        "comunicado (aprox.) já ficou menor ou igual à data pregão (survey menos lag BD). "
        f"Cada platô refere-se ao ano contábil do % (consulte pib_ibge_vol_ano_sidra nas tabelas; "
        f"prox. divulgação = 31/12 do ano+N dias, N="
        f"{dias_pos_31dez}). Azul = mediana Focus (pib_year_ref)."
    )
    ax.set_title("Focus vs PIB realizado IBGE - variacao anual em volume\n" + sub)
    ax.set_xlabel("Data Focus")
    ax.set_ylabel("% a.a.")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def _plot_um_indicador(
    df: pd.DataFrame,
    *,
    coluna: str,
    titulo: str,
    ylab: str,
    legenda_serie: str,
    subtitulo: str | None,
    out_png: Path,
    min_pts: int = 2,
) -> bool:
    d = df.dropna(subset=["survey_date", coluna]).copy()
    if len(d) < min_pts:
        return False
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(d["survey_date"], d[coluna], label=legenda_serie, color="tab:blue")
    ax.set_title(titulo + (f"\n{subtitulo}" if subtitulo else ""))
    ax.set_xlabel("Data Focus")
    ax.set_ylabel(ylab)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return True


def escrever_figuras_por_indicador(
    painel: pd.DataFrame,
    out_dir: Path,
    *,
    market_lag_bdias: int,
    simbolo_ibov: str,
) -> list[Path]:
    """Um PNG por coluna principal de expectativa/mercado (além da validação de câmbio)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    lag_txt = (
        f"Mercado diário mostrado no pregão ≤ survey_date menos {market_lag_bdias} "
        "dia(s) útil(is) configurado(s)."
    )
    escritos: list[Path] = []

    specs: list[tuple[str, Path, str, str, str, str | None]] = [
        (
            "ipca_med12m",
            out_dir / "focus_expectativa_ipca_12m.png",
            "Focus — IPCA próximos 12 meses (mediana)",
            "Mediana (%)",
            "Expectativa média de IPCA nos próximos 12 meses",
            None,
        ),
        (
            "selic_mediana_pct",
            out_dir / "focus_expectativa_selic.png",
            "Focus — Selic (convênção: última reunião R*/ano igual ao ano da survey)",
            "Mediana (%) ao ano na reunião indicada em selic_meeting_used",
            "Taxa esperada pela mediana Focus",
            None,
        ),
        (
            "pib_med_pct",
            out_dir / "focus_expectativa_pib_total.png",
            "Focus — Variação anual esperada do PIB Total (ano‑calendário = ano(Data))",
            "Mediana (%)",
            "PIB esperado para o mesmo ano‑calendário da data Focus",
            None,
        ),
        (
            "ibov_fech",
            out_dir / "mercado_ibovespa_fechamento.png",
            "Ibovespa — fechamento (proxy Yahoo)",
            "Pontos de índice",
            simbolo_ibov,
            lag_txt,
        ),
    ]

    for col, caminho, ttl, ylab, leg, subt in specs:
        if _plot_um_indicador(
            painel,
            coluna=col,
            titulo=ttl,
            ylab=ylab,
            legenda_serie=leg,
            subtitulo=subt,
            out_png=caminho,
        ):
            escritos.append(caminho)

    return escritos


def plot_ipca_selic_cross_trajetoria_focus(
    merged: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    """Trajetória mensal Focus: inflação jan–dez × Selic fim de ano (mesmo ano de publicação)."""
    df = merged.dropna(subset=["ipca_focus_ano_pct", "selic_focus_pct"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_trajetoria_anual(df)

    fig, ax1 = plt.subplots(figsize=(10, 4.5), layout="constrained")
    ax1.plot(
        x,
        df["ipca_focus_ano_pct"],
        "o-",
        color="tab:orange",
        markersize=5,
        label="Focus — IPCA acum. jan–dez",
    )
    ax1.set_ylabel("Inflação esperada (% no ano)", color="tab:orange")
    ax1.tick_params(axis="y", labelcolor="tab:orange")

    ax2 = ax1.twinx()
    ax2.plot(
        x,
        df["selic_focus_pct"],
        "s-",
        color="tab:blue",
        markersize=5,
        label="Focus — Selic fim de ano",
    )
    ax2.set_ylabel("Selic esperada (% a.a.)", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    ax1.set_title(
        f"{ano_ref}: expectativas Focus de inflação e juros ao longo do ano\n"
        "Última edição semanal do boletim em cada mês (IPCA Anual × Selic Anual)"
    )
    ax1.set_xlabel("Mês de publicação do boletim Focus")
    ax1.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_trajetoria_realizado(
    merged: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    """Focus mensal + linhas de referência IBGE (IPCA) e SGS (Selic dez.)."""
    df = merged.dropna(subset=["ipca_focus_ano_pct", "selic_focus_pct"]).copy()
    if len(df) < 2:
        return False
    x = _meses_eixo_trajetoria_anual(df)
    ipca_real = df["ipca_ibge_acum_ano_dez_pct"].iloc[0]
    selic_real = df["selic_sgs_pct_aa_aprox"].iloc[0]

    fig, (ax_ipca, ax_selic) = plt.subplots(
        2,
        1,
        figsize=(10, 7),
        layout="constrained",
        sharex=True,
    )
    ax_ipca.plot(x, df["ipca_focus_ano_pct"], "o-", color="tab:orange", label="Focus IPCA ano")
    if pd.notna(ipca_real):
        ax_ipca.axhline(
            float(ipca_real),
            color="tab:green",
            linestyle="--",
            linewidth=2,
            label=f"IBGE realizado dez./{ano_ref}: {float(ipca_real):.2f}%",
        )
    ax_ipca.set_ylabel("Inflação (% no ano)")
    ax_ipca.set_title(f"IPCA {ano_ref} — trajetória Focus × realizado")
    ax_ipca.legend()
    ax_ipca.grid(True, alpha=0.3)

    ax_selic.plot(x, df["selic_focus_pct"], "s-", color="tab:blue", label="Focus Selic fim ano")
    if pd.notna(selic_real):
        ax_selic.axhline(
            float(selic_real),
            color="tab:green",
            linestyle="--",
            linewidth=2,
            label=f"SGS dez./{ano_ref}: {float(selic_real):.2f}% a.a.",
        )
    ax_selic.set_ylabel("Taxa (% a.a.)")
    ax_selic.set_xlabel("Mês de publicação do boletim Focus")
    titulo_selic = (
        f"Selic {ano_ref} — trajetória Focus × SGS (exploratório)"
        if pd.notna(selic_real)
        else f"Selic {ano_ref} — trajetória Focus (realizado pendente)"
    )
    ax_selic.set_title(titulo_selic)
    ax_selic.legend()
    ax_selic.grid(True, alpha=0.3)

    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_scatter(
    merged: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = merged.dropna(subset=["ipca_focus_ano_pct", "selic_focus_pct"]).copy()
    if len(df) < 2:
        return False

    fig, ax = plt.subplots(figsize=(7, 6), layout="constrained")
    ax.scatter(
        df["ipca_focus_ano_pct"],
        df["selic_focus_pct"],
        c=range(len(df)),
        cmap="viridis",
        s=60,
        zorder=3,
    )
    for _, row in df.iterrows():
        mes_col = "mes_publicacao" if "mes_publicacao" in df.columns else "mes_publicacao_ipca"
        mes = str(row[mes_col])[-2:]
        ax.annotate(
            mes,
            (row["ipca_focus_ano_pct"], row["selic_focus_pct"]),
            textcoords="offset points",
            xytext=(4, 4),
            fontsize=8,
        )
    ax.set_xlabel("Focus — IPCA acum. jan–dez (% no ano)")
    ax.set_ylabel("Focus — Selic fim de ano (% a.a.)")
    ax.set_title(
        f"{ano_ref}: relação inflação × juros nas expectativas Focus\n"
        "Rótulos = mês de publicação do boletim"
    )
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_spread(
    merged: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    """Spread exploratório Selic Focus − IPCA Focus (p.p.; não é taxa real ex-ante)."""
    df = merged.dropna(subset=["ipca_focus_ano_pct", "selic_focus_pct"]).copy()
    if len(df) < 2:
        return False
    df = df.copy()
    df["spread_selic_menos_ipca_pp"] = df["selic_focus_pct"] - df["ipca_focus_ano_pct"]
    x = _meses_eixo_trajetoria_anual(df)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.plot(x, df["spread_selic_menos_ipca_pp"], "o-", color="tab:purple", markersize=5)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle=":")
    ax.set_title(
        f"{ano_ref}: spread Focus (Selic − IPCA ano), em p.p.\n"
        "Proxy descritivo; conceitos e horizontes diferem (exploratório)"
    )
    ax.set_xlabel("Mês de publicação do boletim Focus")
    ax.set_ylabel("Selic − IPCA (% p.p.)")
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_erros_realizado(
    merged: pd.DataFrame,
    ano_ref: int,
    out_png: Path,
) -> bool:
    df = merged.dropna(
        subset=["erro_ipca_prev_menos_real_pp", "erro_selic_prev_menos_real_pp"],
    ).copy()
    if len(df) < 1:
        return False
    x = _meses_eixo_trajetoria_anual(df)
    w = 12

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.bar(x - pd.Timedelta(days=w), df["erro_ipca_prev_menos_real_pp"], width=w, label="IPCA (Focus−IBGE)")
    ax.bar(x + pd.Timedelta(days=w), df["erro_selic_prev_menos_real_pp"], width=w, label="Selic (Focus−SGS)")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title(
        f"{ano_ref}: erro de previsão Focus vs realizado (p.p.)\n"
        "IPCA: mediana ano-calendário − IBGE dez.; Selic: fim de ano − SGS dez. (exploratório)"
    )
    ax.set_xlabel("Mês de publicação do boletim Focus")
    ax.set_ylabel("Erro (p.p.)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


_MESES_CALENDARIO = (
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez",
)
_CORES_ANO_PERIOD = ("tab:blue", "tab:red", "tab:green", "tab:purple", "tab:olive", "tab:brown")


def _plot_series_por_ano(
    ax: plt.Axes,
    df: pd.DataFrame,
    anos: tuple[int, ...],
    coluna: str,
    *,
    marker: str = "o",
) -> None:
    for i, ano in enumerate(anos):
        sub = df[df["ano_ref"] == ano].sort_values("mes_calendario")
        if sub.empty:
            continue
        ax.plot(
            sub["mes_calendario"],
            sub[coluna],
            f"{marker}-",
            color=_CORES_ANO_PERIOD[i % len(_CORES_ANO_PERIOD)],
            markersize=5,
            label=str(ano),
        )
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(_MESES_CALENDARIO)


def plot_ipca_selic_cross_periodo_trajetoria_focus(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    df = combined.dropna(subset=["ipca_focus_ano_pct", "selic_focus_pct"]).copy()
    if df.empty:
        return False

    fig, ax1 = plt.subplots(figsize=(10, 4.5), layout="constrained")
    _plot_series_por_ano(ax1, df, anos, "ipca_focus_ano_pct", marker="o")
    ax1.set_ylabel("Inflação esperada (% no ano)", color="tab:orange")
    ax1.tick_params(axis="y", labelcolor="tab:orange")

    ax2 = ax1.twinx()
    _plot_series_por_ano(ax2, df, anos, "selic_focus_pct", marker="s")
    ax2.set_ylabel("Selic esperada (% a.a.)", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", ncol=2, fontsize=8)

    ax1.set_title(
        f"{periodo_label}: expectativas Focus de inflação e juros (eixo = mês de publicação)\n"
        "Comparação pandemia — IPCA Anual × Selic Anual"
    )
    ax1.set_xlabel("Mês de publicação do boletim Focus")
    ax1.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_periodo_painel(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    df = combined.dropna(subset=["ipca_focus_ano_pct", "selic_focus_pct"]).copy()
    if df.empty:
        return False

    fig, (ax_ipca, ax_selic) = plt.subplots(2, 1, figsize=(10, 7), layout="constrained", sharex=True)
    _plot_series_por_ano(ax_ipca, df, anos, "ipca_focus_ano_pct")
    ax_ipca.set_ylabel("IPCA Focus (% no ano)")
    ax_ipca.set_title(f"{periodo_label} — inflação esperada jan–dez")
    ax_ipca.legend(loc="upper left", ncol=len(anos))
    ax_ipca.grid(True, alpha=0.3)

    _plot_series_por_ano(ax_selic, df, anos, "selic_focus_pct", marker="s")
    ax_selic.set_ylabel("Selic Focus (% a.a.)")
    ax_selic.set_xlabel("Mês de publicação do boletim Focus")
    ax_selic.set_title(f"{periodo_label} — Selic fim de ano esperada")
    ax_selic.legend(loc="upper left", ncol=len(anos))
    ax_selic.grid(True, alpha=0.3)

    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_periodo_realizado(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    n = len(anos)
    if n < 1:
        return False

    fig, axes = plt.subplots(2, n, figsize=(5 * n, 7), layout="constrained", squeeze=False)
    for j, ano in enumerate(anos):
        sub = combined[combined["ano_ref"] == ano].sort_values("mes_calendario")
        if sub.empty:
            continue
        ipca_real = sub["ipca_ibge_acum_ano_dez_pct"].iloc[0]
        selic_real = sub["selic_sgs_pct_aa_aprox"].iloc[0]

        ax_i = axes[0, j]
        ax_i.plot(sub["mes_calendario"], sub["ipca_focus_ano_pct"], "o-", color="tab:orange")
        if pd.notna(ipca_real):
            ax_i.axhline(float(ipca_real), color="tab:green", linestyle="--", linewidth=2)
            ax_i.set_title(f"IPCA {ano} — Focus × IBGE {float(ipca_real):.2f}%")
        else:
            ax_i.set_title(f"IPCA {ano} — Focus (realizado pendente)")
        ax_i.set_xticks(range(1, 13))
        ax_i.set_xticklabels(_MESES_CALENDARIO, rotation=45, ha="right")
        ax_i.grid(True, alpha=0.3)

        ax_s = axes[1, j]
        ax_s.plot(sub["mes_calendario"], sub["selic_focus_pct"], "s-", color="tab:blue")
        if pd.notna(selic_real):
            ax_s.axhline(float(selic_real), color="tab:green", linestyle="--", linewidth=2)
            ax_s.set_title(f"Selic {ano} — Focus × SGS {float(selic_real):.2f}%")
        else:
            ax_s.set_title(f"Selic {ano} — Focus (realizado pendente)")
        ax_s.set_xticks(range(1, 13))
        ax_s.set_xticklabels(_MESES_CALENDARIO, rotation=45, ha="right")
        ax_s.grid(True, alpha=0.3)

    fig.suptitle(f"{periodo_label}: trajetórias Focus vs realizados (exploratório)", fontsize=11)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_periodo_scatter(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    df = combined.dropna(subset=["ipca_focus_ano_pct", "selic_focus_pct"]).copy()
    if df.empty:
        return False

    fig, ax = plt.subplots(figsize=(7, 6), layout="constrained")
    for i, ano in enumerate(anos):
        sub = df[df["ano_ref"] == ano]
        ax.scatter(
            sub["ipca_focus_ano_pct"],
            sub["selic_focus_pct"],
            color=_CORES_ANO_PERIOD[i % len(_CORES_ANO_PERIOD)],
            s=60,
            label=str(ano),
            zorder=3,
        )
    ax.set_xlabel("Focus — IPCA acum. jan–dez (% no ano)")
    ax.set_ylabel("Focus — Selic fim de ano (% a.a.)")
    ax.set_title(f"{periodo_label}: inflação × juros nas expectativas Focus")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_periodo_spread(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    df = combined.dropna(subset=["spread_selic_menos_ipca_pp"]).copy()
    if df.empty:
        return False

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    _plot_series_por_ano(ax, df, anos, "spread_selic_menos_ipca_pp")
    ax.axhline(0, color="gray", linewidth=0.8, linestyle=":")
    ax.set_title(
        f"{periodo_label}: spread Focus (Selic − IPCA ano), p.p.\n"
        "Proxy descritivo; conceitos diferem (exploratório)"
    )
    ax.set_xlabel("Mês de publicação do boletim Focus")
    ax.set_ylabel("Selic − IPCA (p.p.)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_periodo_erros(
    combined: pd.DataFrame,
    anos: tuple[int, ...],
    periodo_label: str,
    out_png: Path,
) -> bool:
    df = combined.dropna(
        subset=["erro_ipca_prev_menos_real_pp", "erro_selic_prev_menos_real_pp"],
    ).copy()
    if df.empty:
        return False

    fig, (ax_ipca, ax_selic) = plt.subplots(2, 1, figsize=(10, 7), layout="constrained", sharex=True)
    _plot_series_por_ano(ax_ipca, df, anos, "erro_ipca_prev_menos_real_pp")
    ax_ipca.axhline(0, color="gray", linewidth=0.8)
    ax_ipca.set_ylabel("Erro IPCA (p.p.)")
    ax_ipca.set_title(f"{periodo_label} — erro Focus − IBGE dez.")
    ax_ipca.legend(loc="upper right", ncol=len(anos))
    ax_ipca.grid(True, alpha=0.3)

    _plot_series_por_ano(ax_selic, df, anos, "erro_selic_prev_menos_real_pp", marker="s")
    ax_selic.axhline(0, color="gray", linewidth=0.8)
    ax_selic.set_ylabel("Erro Selic (p.p.)")
    ax_selic.set_xlabel("Mês de publicação do boletim Focus")
    ax_selic.set_title(f"{periodo_label} — erro Focus − SGS dez. (exploratório)")
    ax_selic.legend(loc="upper right", ncol=len(anos))
    ax_selic.grid(True, alpha=0.3)

    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


_CORES_BLOCO_CMP = ("tab:blue", "tab:red")


def _plot_media_bloco(
    ax: plt.Axes,
    media: pd.DataFrame,
    bloco_id: str,
    coluna: str,
    *,
    marker: str = "o",
    color: str,
) -> None:
    sub = media[media["bloco"] == bloco_id].sort_values("mes_calendario")
    if sub.empty:
        return
    ax.plot(
        sub["mes_calendario"],
        sub[coluna],
        f"{marker}-",
        color=color,
        markersize=5,
        label=bloco_id,
    )
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(_MESES_CALENDARIO)


def plot_ipca_selic_cross_comparativo_blocos_painel(
    combined: pd.DataFrame,
    media: pd.DataFrame,
    resumo_a: dict,
    resumo_b: dict,
    id_a: str,
    id_b: str,
    cmp_label: str,
    out_png: Path,
) -> bool:
    if media.empty:
        return False

    fig, (ax_ipca, ax_selic) = plt.subplots(2, 1, figsize=(10, 7), layout="constrained", sharex=True)
    _plot_media_bloco(ax_ipca, media, id_a, "ipca_focus_ano_pct", color=_CORES_BLOCO_CMP[0])
    _plot_media_bloco(ax_ipca, media, id_b, "ipca_focus_ano_pct", color=_CORES_BLOCO_CMP[1])
    ax_ipca.set_ylabel("IPCA Focus médio (% no ano)")
    ax_ipca.set_title(f"{cmp_label} — média mensal IPCA (por mês de publicação)")
    ax_ipca.legend()
    ax_ipca.grid(True, alpha=0.3)

    _plot_media_bloco(ax_selic, media, id_a, "selic_focus_pct", marker="s", color=_CORES_BLOCO_CMP[0])
    _plot_media_bloco(ax_selic, media, id_b, "selic_focus_pct", marker="s", color=_CORES_BLOCO_CMP[1])
    ax_selic.set_ylabel("Selic Focus média (% a.a.)")
    ax_selic.set_xlabel("Mês de publicação do boletim Focus")
    ax_selic.set_title(f"{cmp_label} — média mensal Selic fim de ano")
    ax_selic.legend()
    ax_selic.grid(True, alpha=0.3)

    if resumo_b.get("n_anos_parciais"):
        fig.suptitle(
            f"{id_b}: inclui 2026 parcial ({resumo_b['n_observacoes_mensais']} obs.)",
            fontsize=9,
            y=1.02,
        )

    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_comparativo_blocos_metricas(
    combined: pd.DataFrame,
    media: pd.DataFrame,
    resumo_a: dict,
    resumo_b: dict,
    id_a: str,
    id_b: str,
    cmp_label: str,
    out_png: Path,
) -> bool:
    metricas = [
        ("Corr. média\n(anual)", "corr_media_entre_anos"),
        ("IPCA Focus\nmédio (%)", "ipca_focus_media_obs_pct"),
        ("Selic Focus\nmédia (%)", "selic_focus_media_obs_pct"),
        ("Spread médio\n(p.p.)", "spread_medio_obs_pp"),
        ("Spread fim ano\nmédio (p.p.)", "spread_fim_ano_medio_pp"),
        ("Erro IPCA\nmédio (p.p.)", "erro_ipca_medio_pp"),
        ("Erro Selic\nmédio (p.p.)", "erro_selic_medio_pp"),
    ]
    labels = [m[0] for m in metricas]
    x = range(len(labels))
    w = 0.35
    vals_a = [float(resumo_a[k]) if resumo_a[k] != "" else 0.0 for _, k in metricas]
    vals_b = [float(resumo_b[k]) if resumo_b[k] != "" else 0.0 for _, k in metricas]

    fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
    ax.bar([i - w / 2 for i in x], vals_a, width=w, label=id_a, color=_CORES_BLOCO_CMP[0])
    ax.bar([i + w / 2 for i in x], vals_b, width=w, label=id_b, color=_CORES_BLOCO_CMP[1])
    ax.axhline(0, color="gray", linewidth=0.6)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(
        f"{cmp_label}: métricas agregadas por bloco\n"
        "Médias entre observações mensais; corr. = média das correlações anuais"
    )
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_comparativo_blocos_scatter(
    combined: pd.DataFrame,
    media: pd.DataFrame,
    resumo_a: dict,
    resumo_b: dict,
    id_a: str,
    id_b: str,
    cmp_label: str,
    out_png: Path,
) -> bool:
    fig, ax = plt.subplots(figsize=(7, 6), layout="constrained")
    for bloco_id, cor in ((id_a, _CORES_BLOCO_CMP[0]), (id_b, _CORES_BLOCO_CMP[1])):
        sub = combined[combined["bloco"] == bloco_id].dropna(
            subset=["ipca_focus_ano_pct", "selic_focus_pct"],
        )
        if sub.empty:
            continue
        ax.scatter(
            sub["ipca_focus_ano_pct"],
            sub["selic_focus_pct"],
            color=cor,
            s=45,
            alpha=0.65,
            label=f"{bloco_id} (n={len(sub)})",
        )
    ax.set_xlabel("Focus — IPCA acum. jan–dez (% no ano)")
    ax.set_ylabel("Focus — Selic fim de ano (% a.a.)")
    ax.set_title(f"{cmp_label}: nuvem inflação × juros por bloco")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_comparativo_blocos_spread(
    combined: pd.DataFrame,
    media: pd.DataFrame,
    resumo_a: dict,
    resumo_b: dict,
    id_a: str,
    id_b: str,
    cmp_label: str,
    out_png: Path,
) -> bool:
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    _plot_media_bloco(ax, media, id_a, "spread_selic_menos_ipca_pp", color=_CORES_BLOCO_CMP[0])
    _plot_media_bloco(ax, media, id_b, "spread_selic_menos_ipca_pp", color=_CORES_BLOCO_CMP[1])
    ax.axhline(0, color="gray", linewidth=0.8, linestyle=":")
    ax.set_title(f"{cmp_label}: spread médio mensal (Selic − IPCA), p.p.")
    ax.set_xlabel("Mês de publicação")
    ax.set_ylabel("p.p.")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True


def plot_ipca_selic_cross_comparativo_blocos_erros(
    combined: pd.DataFrame,
    media: pd.DataFrame,
    resumo_a: dict,
    resumo_b: dict,
    id_a: str,
    id_b: str,
    cmp_label: str,
    out_png: Path,
) -> bool:
    fig, (ax_ipca, ax_selic) = plt.subplots(2, 1, figsize=(10, 7), layout="constrained", sharex=True)
    for ax, col, tit in (
        (ax_ipca, "erro_ipca_prev_menos_real_pp", "IPCA (Focus − IBGE)"),
        (ax_selic, "erro_selic_prev_menos_real_pp", "Selic (Focus − SGS)"),
    ):
        sub_a = media[media["bloco"] == id_a].dropna(subset=[col])
        sub_b = media[media["bloco"] == id_b].dropna(subset=[col])
        if not sub_a.empty:
            ax.plot(
                sub_a["mes_calendario"],
                sub_a[col],
                "o-",
                color=_CORES_BLOCO_CMP[0],
                label=id_a,
            )
        if not sub_b.empty:
            ax.plot(
                sub_b["mes_calendario"],
                sub_b[col],
                "s-",
                color=_CORES_BLOCO_CMP[1],
                label=id_b,
            )
        ax.axhline(0, color="gray", linewidth=0.8)
        ax.set_ylabel(f"Erro {tit} (p.p.)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(_MESES_CALENDARIO)

    ax_selic.set_xlabel("Mês de publicação")
    fig.suptitle(f"{cmp_label}: erro médio mensal por bloco (exploratório)", fontsize=11)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    return True
