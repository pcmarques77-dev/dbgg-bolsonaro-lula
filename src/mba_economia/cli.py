"""Pipeline TCC FIPE: painel Focus (Olinda) x mercado (yfinance) x USD (SGS)."""

from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from .bcb_pib_sgs1207 import colar_yoy_nas_linhas_focus, fetch_pib_sgs1207_e_yoy
from .config import DEFAULT_START, IPCA_ANOS_CALENDARIO_GRAFICOS, SeriesConfig, today_date
from .figures import (
    escrever_figuras_por_indicador,
    plot_cambio_validacao,
    plot_focus_ipca_vs_ibge_sidra,
    plot_focus_pib_vs_bcb_sgs1207_nominal_yoy,
    plot_focus_pib_vs_ibge_volume_anual,
    plot_focus_selic_vs_bcb_sgs11,
    plot_ipca_ano_calendario_focus_vs_ibge,
    plot_ipca_ano_focus,
    plot_ipca_ano_ibge,
    plot_ipca_ano_por_ano_calendario,
    plot_ipca_mensal_focus_vs_ibge,
)
from .econometrics import run_panel_ols, write_econometrics_outputs
from .ipca_comparisons import (
    build_comparacao_ipca_ano_bundle,
    build_comparacao_ipca_mensal,
    export_ipca_ano_trajetoria_piloto_ano,
    export_ipca_anual_trajetoria_graficos_from_csv,
    export_ipca_mes_piloto,
    export_ipca_mes_piloto_ano,
    export_ipca_anual_graficos_from_csv,
)
from .ipca_selic_cross import (
    export_ipca_selic_cross_ano,
    export_ipca_selic_cross_comparativo_blocos,
    export_ipca_selic_cross_periodo,
)
from .pib_comparisons import (
    export_pib_ano_trajetoria_piloto_ano,
    export_pib_anual_trajetoria_graficos_from_csv,
)
from .pib_period import (
    BLOCO_2019_2022,
    BLOCO_2023_2026,
    PERIODO_2019_2026,
    export_pib_periodo,
)
from .selic_comparisons import (
    export_selic_ano_trajetoria_piloto_ano,
    export_selic_anual_graficos_from_csv,
    export_selic_anual_trajetoria_graficos_from_csv,
    export_selic_mes_piloto_ano,
)
from .focus_extract import build_focus_wide
from .ibge_ipca_client import fetch_ipca_sidra_acum12m_pct
from .ibge_pib_volume_anual_client import (
    colar_ibge_vol_nas_linhas_focus,
    fetch_pib_ibge_vol_lut,
)
from .market_client import fetch_market_data
from .panel import (
    add_dbgg_and_desancoragem_columns,
    attach_ibge_ipca_acum12_como_realizado_conhecido,
    attach_selic_daily,
    attach_usd_daily,
    generate_analysis_panel,
    subset_window,
)
from .sgs_client import fetch_sgs_json

logger = logging.getLogger(__name__)


def _parse_date(s: str, default: date) -> date:
    return default if not s else pd.Timestamp(s).date()


def _parse_ipca_anos(s: str | None) -> tuple[int, ...]:
    if not s:
        return IPCA_ANOS_CALENDARIO_GRAFICOS
    return tuple(int(p.strip()) for p in s.split(",") if p.strip())


def _padded_market_start(start: date) -> date:
    return (pd.Timestamp(start) - pd.Timedelta(days=120)).date()


def _market_end_exclusive(end: date) -> str:
    return (pd.Timestamp(end) + pd.Timedelta(days=1)).date().isoformat()


def _write_outputs(df_panel: pd.DataFrame, out_dir: Path) -> tuple[Path, Path]:
    parquet_file = out_dir / "painel_focus_mvp.parquet"
    csv_file = out_dir / "painel_focus_mvp.csv"
    logger.info("Salvando arquivos finais...")
    df_panel.to_parquet(parquet_file, engine="pyarrow", index=False)
    df_panel.to_csv(csv_file, index=False, decimal=",", sep=";")
    return parquet_file, csv_file


def _write_metadata(df_panel: pd.DataFrame, out_dir: Path, cfg: SeriesConfig) -> None:
    linhas_meta: list[dict[str, str]] = [
        {
            "serie": "ipca_med12m",
            "fonte": "Olinda ExpectativasMercadoInflacao12Meses — IPCA, Suavizada N",
        },
        {
            "serie": "selic_mediana_pct",
            "fonte": "Olinda ExpectativasMercadoSelic — último R*/ano da survey",
        },
        {
            "serie": "usdbrl_med_fwd",
            "fonte": "Olinda ExpectativaMercadoMensais — Câmbio",
        },
        {
            "serie": "pib_med_pct",
            "fonte": "Olinda ExpectativasMercadoAnuais — PIB Total",
        },
        {
            "serie": "usd_sgs_med",
            "fonte": f"BCB SGS {cfg.sgs_codigo_usd_diario} — USD diário",
        },
        {
            "serie": "ibov_fech",
            "fonte": f"yfinance {cfg.proxy_ibovespa}",
        },
        {
            "serie": "vix",
            "fonte": f"yfinance {cfg.proxy_vix}",
        },
        {
            "serie": "commodities",
            "fonte": f"yfinance {cfg.proxy_commodities}",
        },
        {
            "serie": "dummy_lula",
            "fonte": "1 se survey_date >= 2023",
        },
        {
            "serie": "dummy_pandemia",
            "fonte": "1 se survey_date entre 2020-03-01 e 2021-12-31",
        },
    ]
    if "ipca_ibge_acum12m_pct" in df_panel.columns:
        linhas_meta.append(
            {
                "serie": "ipca_ibge_acum12m_pct",
                "fonte": f"IBGE SIDRA {cfg.sidra_tab_ipca_acum12}/v.{cfg.sidra_codigo_var_acum12m}",
            },
        )
    if "pib_ibge_vol_yoy_pct" in df_panel.columns:
        linhas_meta.append(
            {
                "serie": "pib_ibge_vol_yoy_pct",
                "fonte": f"IBGE SIDRA {cfg.sidra_tab_pib_anual_vol}/v.{cfg.sidra_codigo_var_pib_vol_anual_pct}",
            },
        )
    if "pib_sgs_nominal_yoy_pct" in df_panel.columns:
        linhas_meta.append(
            {
                "serie": "pib_sgs_nominal_yoy_pct",
                "fonte": f"BCB SGS {cfg.sgs_codigo_pib_rs_correntes} YoY nominal",
            },
        )
    if "selic_sgs_pct_aa_aprox" in df_panel.columns:
        linhas_meta.append(
            {
                "serie": "selic_sgs_pct_aa_aprox",
                "fonte": f"BCB SGS {cfg.sgs_codigo_selic_diaria} Selic diária anualizada",
            },
        )
    pd.DataFrame(linhas_meta).to_csv(out_dir / "metadados_series.csv", index=False)


def _apply_figure_extras(
    df_panel: pd.DataFrame,
    *,
    start: date,
    end: date,
    out_dir: Path,
    cfg: SeriesConfig,
    figure_extras: tuple[str, ...],
    plot_mode: str,
    session: requests.Session,
    ipca_anos: tuple[int, ...] = IPCA_ANOS_CALENDARIO_GRAFICOS,
    ipca_mes_ref: str | None = None,
    ipca_mes_ano: int | None = None,
) -> tuple[pd.DataFrame, list[Path]]:
    extras: list[Path] = []

    if "ipca-vs-ibge" in figure_extras:
        ipca_sidra = fetch_ipca_sidra_acum12m_pct(
            start,
            end,
            tabela=cfg.sidra_tab_ipca_acum12,
            codigo_variavel=cfg.sidra_codigo_var_acum12m,
            dia_public_approx_mes_seguinte=cfg.sidra_ipca_disponivel_dia_mes_seguinte,
            session=session,
        )
        df_panel = attach_ibge_ipca_acum12_como_realizado_conhecido(
            df_panel,
            ipca_sidra,
            market_lag_bdias=cfg.market_lag_bdias,
        )

    if "pib-vs-bcb1207" in figure_extras:
        yoy_lut = fetch_pib_sgs1207_e_yoy(start, end, cfg, session=session)
        df_panel = colar_yoy_nas_linhas_focus(
            df_panel,
            yoy_lut,
            market_lag_bdias=cfg.market_lag_bdias,
        )

    if "pib-vs-ibge" in figure_extras:
        vol_lut = fetch_pib_ibge_vol_lut(start, end, cfg, session=session)
        df_panel = colar_ibge_vol_nas_linhas_focus(
            df_panel,
            vol_lut,
            market_lag_bdias=cfg.market_lag_bdias,
        )

    if "selic-vs-sgs11" in figure_extras:
        selic_daily = fetch_sgs_json(
            cfg.sgs_codigo_selic_diaria,
            _padded_market_start(start),
            end,
            session=session,
        )
        df_panel = attach_selic_daily(df_panel, selic_daily, cfg=cfg)

    if plot_mode in ("cambio", "todas"):
        plot_cambio_validacao(
            df_panel,
            out_dir / "validacao_focus_usd.png",
            cfg.sgs_codigo_usd_diario,
        )
        extras.append(out_dir / "validacao_focus_usd.png")

    if plot_mode == "todas":
        extras.extend(
            escrever_figuras_por_indicador(
                df_panel,
                out_dir,
                market_lag_bdias=cfg.market_lag_bdias,
                simbolo_ibov=cfg.proxy_ibovespa,
            ),
        )

    if "ipca-vs-ibge" in figure_extras:
        ipca_png = out_dir / "comparacao_focus_ibge_ipca_acum12m.png"
        if plot_focus_ipca_vs_ibge_sidra(
            df_panel,
            ipca_png,
            tabela_sidra=cfg.sidra_tab_ipca_acum12,
            codigo_var=cfg.sidra_codigo_var_acum12m,
            dia_public_approx=cfg.sidra_ipca_disponivel_dia_mes_seguinte,
        ):
            extras.append(ipca_png)

    if "ipca-mes-piloto-ano" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        _, _, piloto_paths = export_ipca_mes_piloto_ano(ano, out_dir, cfg, session=session)
        extras.extend(piloto_paths)

    if "ipca-anual-mensal" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        extras.extend(export_ipca_anual_graficos_from_csv(ano, out_dir))

    if "ipca-anual-trajetoria-ano" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        _, _, piloto_paths = export_ipca_ano_trajetoria_piloto_ano(
            ano,
            out_dir,
            cfg,
            session=session,
        )
        extras.extend(piloto_paths)

    if "ipca-anual-trajetoria-graficos" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        extras.extend(export_ipca_anual_trajetoria_graficos_from_csv(ano, out_dir))

    if "pib-ano-trajetoria-ano" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        _, _, piloto_paths = export_pib_ano_trajetoria_piloto_ano(
            ano,
            out_dir,
            cfg,
            session=session,
        )
        extras.extend(piloto_paths)

    if "pib-ano-trajetoria-graficos" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        extras.extend(export_pib_anual_trajetoria_graficos_from_csv(ano, out_dir))

    if "pib-periodo" in figure_extras:
        _, _, periodo_paths = export_pib_periodo(ipca_anos, out_dir)
        extras.extend(periodo_paths)

    if "pib-periodo-blocos" in figure_extras:
        for bloco in (BLOCO_2019_2022, BLOCO_2023_2026, PERIODO_2019_2026):
            _, _, periodo_paths = export_pib_periodo(bloco, out_dir)
            extras.extend(periodo_paths)

    if "selic-mes-piloto-ano" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        _, _, piloto_paths = export_selic_mes_piloto_ano(ano, out_dir, cfg, session=session)
        extras.extend(piloto_paths)

    if "selic-anual-mensal" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        extras.extend(export_selic_anual_graficos_from_csv(ano, out_dir))

    if "selic-anual-trajetoria-ano" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        _, _, piloto_paths = export_selic_ano_trajetoria_piloto_ano(
            ano,
            out_dir,
            cfg,
            session=session,
        )
        extras.extend(piloto_paths)

    if "selic-anual-trajetoria-graficos" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        extras.extend(export_selic_anual_trajetoria_graficos_from_csv(ano, out_dir))

    if "ipca-selic-cross-ano" in figure_extras:
        ano = ipca_mes_ano if ipca_mes_ano is not None else 2019
        _, _, cross_paths = export_ipca_selic_cross_ano(ano, out_dir)
        extras.extend(cross_paths)

    if "ipca-selic-cross-periodo" in figure_extras:
        anos_periodo = (2020, 2021) if ipca_anos == IPCA_ANOS_CALENDARIO_GRAFICOS else ipca_anos
        _, _, cross_paths = export_ipca_selic_cross_periodo(anos_periodo, out_dir)
        extras.extend(cross_paths)

    if "ipca-selic-cross-comparativo" in figure_extras:
        _, _, cross_paths = export_ipca_selic_cross_comparativo_blocos(out_dir)
        extras.extend(cross_paths)

    if "ipca-mes-piloto" in figure_extras:
        ref_mes = ipca_mes_ref or "201901"
        _, _, piloto_paths = export_ipca_mes_piloto(ref_mes, out_dir, cfg, session=session)
        extras.extend(piloto_paths)

    if "ipca-mes-vs-ibge" in figure_extras:
        comp_mes, _ = build_comparacao_ipca_mensal(start, end, cfg, session=session)
        comp_mes.to_parquet(out_dir / "comparacao_ipca_mensal.parquet", index=False)
        comp_mes.to_csv(out_dir / "comparacao_ipca_mensal.csv", index=False, decimal=",", sep=";")
        png_mes = out_dir / "comparacao_focus_ibge_ipca_mensal.png"
        if plot_ipca_mensal_focus_vs_ibge(comp_mes, png_mes):
            extras.append(png_mes)

    ipca_ano_flags = {
        "ipca-ano-vs-ibge",
        "ipca-ano-focus",
        "ipca-ano-ibge",
        "ipca-ano-por-ano",
    }
    if ipca_ano_flags & set(figure_extras):
        comp_ano, fech = build_comparacao_ipca_ano_bundle(start, end, cfg, session=session)
        comp_ano.to_parquet(out_dir / "comparacao_ipca_ano_calendario.parquet", index=False)
        comp_ano.to_csv(
            out_dir / "comparacao_ipca_ano_calendario.csv",
            index=False,
            decimal=",",
            sep=";",
        )
        fech.to_parquet(out_dir / "comparacao_ipca_ano_fechamento.parquet", index=False)
        fech.to_csv(out_dir / "comparacao_ipca_ano_fechamento.csv", index=False, decimal=",", sep=";")

        if "ipca-ano-focus" in figure_extras:
            png_focus = out_dir / "ipca_focus_expectativa_ano_calendario.png"
            if plot_ipca_ano_focus(comp_ano, png_focus):
                extras.append(png_focus)

        if "ipca-ano-ibge" in figure_extras:
            png_ibge = out_dir / "ipca_ibge_realizado_ano_calendario.png"
            if plot_ipca_ano_ibge(comp_ano, png_ibge):
                extras.append(png_ibge)

        if "ipca-ano-vs-ibge" in figure_extras:
            png_ano = out_dir / "comparacao_focus_ibge_ipca_ano_calendario.png"
            if plot_ipca_ano_calendario_focus_vs_ibge(comp_ano, png_ano):
                extras.append(png_ano)

        if "ipca-ano-por-ano" in figure_extras:
            extras.extend(
                plot_ipca_ano_por_ano_calendario(
                    comp_ano,
                    out_dir / "ipca_ano_por_ano",
                    anos=ipca_anos,
                ),
            )

    if "pib-vs-bcb1207" in figure_extras:
        pib_png = out_dir / "comparacao_focus_bcb_pib_sgs1207_nominal_yoy.png"
        if plot_focus_pib_vs_bcb_sgs1207_nominal_yoy(
            df_panel,
            pib_png,
            codigo_sgs=cfg.sgs_codigo_pib_rs_correntes,
            dias_divulgacao_pos_31dez=cfg.sgs_pib1207_dias_apos_31dez_divulgacao,
        ):
            extras.append(pib_png)

    if "pib-vs-ibge" in figure_extras:
        pib_iv = out_dir / "comparacao_focus_ibge_pib_variacao_volume.png"
        if plot_focus_pib_vs_ibge_volume_anual(
            df_panel,
            pib_iv,
            tabela_sidra=cfg.sidra_tab_pib_anual_vol,
            codigo_var=cfg.sidra_codigo_var_pib_vol_anual_pct,
            dias_pos_31dez=cfg.sidra_pib_vol_anual_dias_apos_31dez,
        ):
            extras.append(pib_iv)

    if "selic-vs-sgs11" in figure_extras:
        selic_png = out_dir / "comparacao_focus_selic_vs_bcb_sgs11.png"
        if plot_focus_selic_vs_bcb_sgs11(
            df_panel,
            selic_png,
            codigo_sgs=cfg.sgs_codigo_selic_diaria,
            market_lag_bdias=cfg.market_lag_bdias,
        ):
            extras.append(selic_png)

    return df_panel, extras


def run(
    *,
    start: date,
    end: date,
    out_dir: Path,
    cfg: SeriesConfig,
    plot_mode: str = "none",
    figure_extras: tuple[str, ...] = (),
    run_econometrics: bool = False,
    ipca_anos: tuple[int, ...] = IPCA_ANOS_CALENDARIO_GRAFICOS,
    ipca_mes_ref: str | None = None,
    ipca_mes_ano: int | None = None,
) -> tuple[pd.DataFrame, list[Path]]:
    """Executa o pipeline Focus → mercado → painel → USD → exportação."""
    out_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    logger.info("Iniciando pipeline de dados: %s até %s", start.isoformat(), end.isoformat())

    logger.info("Extraindo expectativas do Boletim Focus (Olinda / build_focus_wide)...")
    df_focus = build_focus_wide(cfg, filt_start=pd.Timestamp(start), session=session)
    df_focus = subset_window(df_focus, start, end)
    if df_focus.empty:
        raise ValueError("Dados do Focus retornaram vazios. Abortando pipeline.")

    padded_start = _padded_market_start(start)
    end_exclusive = _market_end_exclusive(end)

    logger.info("Extraindo dados de mercado e controles globais (yfinance)...")
    df_market = fetch_market_data(
        padded_start.isoformat(),
        end_exclusive,
        tickers_map={
            "ibovespa": cfg.proxy_ibovespa,
            "vix": cfg.proxy_vix,
            "commodities": cfg.proxy_commodities,
        },
    )
    if df_market.empty:
        raise ValueError("Dados de mercado retornaram vazios. Abortando pipeline.")

    logger.info("Gerando painel analítico com alinhamento temporal (merge_asof)...")
    df_panel = generate_analysis_panel(
        df_focus=df_focus,
        df_market=df_market,
        focus_date_col="survey_date",
        market_date_col="market_date",
        market_lag_bdias=cfg.market_lag_bdias,
    )

    logger.info("Anexando USD realizada (SGS %s)...", cfg.sgs_codigo_usd_diario)
    usd = fetch_sgs_json(
        cfg.sgs_codigo_usd_diario,
        padded_start,
        end,
        session=session,
    )
    df_panel = attach_usd_daily(df_panel, usd, cfg=cfg)
    df_panel = subset_window(df_panel, start, end)
    df_panel = add_dbgg_and_desancoragem_columns(df_panel, session=session)

    _write_metadata(df_panel, out_dir, cfg)
    parquet_file, csv_file = _write_outputs(df_panel, out_dir)

    fig_paths: list[Path] = []
    if figure_extras or plot_mode != "none":
        df_panel, fig_paths = _apply_figure_extras(
            df_panel,
            start=start,
            end=end,
            out_dir=out_dir,
            cfg=cfg,
            figure_extras=figure_extras,
            plot_mode=plot_mode,
            session=session,
            ipca_anos=ipca_anos,
            ipca_mes_ref=ipca_mes_ref,
            ipca_mes_ano=ipca_mes_ano,
        )
        _write_outputs(df_panel, out_dir)

    logger.info(
        "Sucesso! Arquivos salvos em: %s (%s, %s)",
        out_dir.resolve(),
        parquet_file.name,
        csv_file.name,
    )
    logger.info(
        "Dimensões do painel final: %s linhas x %s colunas.",
        df_panel.shape[0],
        df_panel.shape[1],
    )

    if run_econometrics:
        logger.info("Rodando econometria (OLS + ADF + diagnósticos)...")
        # 1. Modelo IPCA med12m
        econ_ipca = run_panel_ols(df_panel, dep_var="ipca_med12m", regressors=("dummy_lula", "dummy_pandemia", "vix", "commodities"))
        fig_paths.extend(write_econometrics_outputs(econ_ipca, out_dir))
        
        # 2. Modelo Selic mediana
        econ_selic = run_panel_ols(df_panel, dep_var="selic_mediana_pct", regressors=("dummy_lula", "dummy_pandemia", "vix", "commodities"))
        fig_paths.extend(write_econometrics_outputs(econ_selic, out_dir))
        
        # 3. Modelo PIB mediana
        econ_pib = run_panel_ols(df_panel, dep_var="pib_med_pct", regressors=("dummy_lula", "dummy_pandemia", "vix", "commodities"))
        fig_paths.extend(write_econometrics_outputs(econ_pib, out_dir))
        
        # 4. Modelo Regra de Taylor (Taylor Rule)
        econ_taylor = run_panel_ols(df_panel, dep_var="taylor_rule", regressors=("desancoragem_centro_12m", "dummy_lula"))
        fig_paths.extend(write_econometrics_outputs(econ_taylor, out_dir))
        
        logger.info("Todos os 4 modelos econométricos foram salvos com sucesso.")

    return df_panel, fig_paths


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Pipeline TCC FIPE: Painel Focus x Mercado",
    )
    parser.add_argument(
        "--start-date",
        "--start",
        dest="start_date",
        type=str,
        default=None,
        help=f"Data de início YYYY-MM-DD (default {DEFAULT_START.isoformat()})",
    )
    parser.add_argument(
        "--end-date",
        "--end",
        dest="end_date",
        type=str,
        default=None,
        help="Data de fim YYYY-MM-DD (default hoje)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("output"),
        help="Diretório de saída dos arquivos",
    )
    parser.add_argument(
        "--plot-mode",
        choices=("cambio", "todas", "none"),
        default="none",
        help="Figuras: cambio (validação USD), todas, ou none",
    )
    parser.add_argument("--usd-sgs-code", type=int, default=None)
    parser.add_argument("--months-ahead-cambio", type=int, default=None)
    parser.add_argument("--market-lag-bdias", type=int, default=None)
    parser.add_argument(
        "--figure-extra",
        action="append",
        choices=(
            "ipca-vs-ibge",
            "ipca-mes-vs-ibge",
            "ipca-mes-piloto",
            "ipca-mes-piloto-ano",
            "ipca-anual-mensal",
            "ipca-anual-trajetoria-ano",
            "ipca-anual-trajetoria-graficos",
            "selic-mes-piloto-ano",
            "selic-anual-mensal",
            "selic-anual-trajetoria-ano",
            "selic-anual-trajetoria-graficos",
            "ipca-selic-cross-ano",
            "ipca-selic-cross-periodo",
            "ipca-selic-cross-comparativo",
            "ipca-ano-vs-ibge",
            "ipca-ano-focus",
            "ipca-ano-ibge",
            "ipca-ano-por-ano",
            "pib-vs-bcb1207",
            "pib-vs-ibge",
            "pib-ano-trajetoria-ano",
            "pib-ano-trajetoria-graficos",
            "pib-periodo",
            "pib-periodo-blocos",
            "selic-vs-sgs11",
        ),
        default=None,
        help=(
            "Figuras/dados extras: ipca-mes-vs-ibge; ipca-mes-piloto (1 mês); "
            "ipca-mes-piloto-ano (12 meses + 3 PNGs consolidados em IPCA/{ano}/); "
            "ipca-anual-mensal (só re-plot dos 3 PNGs a partir de CSV existente); "
            "ipca-anual-trajetoria-ano (IPCA jan–dez + 3 PNGs em IPCA Anual/{ano}/); "
            "ipca-anual-trajetoria-graficos (só re-plot trajetória a partir de CSV); "
            "selic-mes-piloto-ano (~reuniões Copom + 3 PNGs em Selic/{ano}/); "
            "selic-anual-mensal (só re-plot dos 3 PNGs Selic/); "
            "selic-anual-trajetoria-ano (Selic fim de ano + 3 PNGs em Selic Anual/{ano}/); "
            "selic-anual-trajetoria-graficos (só re-plot trajetória Selic Anual); "
            "ipca-selic-cross-ano (cruzamento Focus IPCA Anual × Selic Anual em IPCA x Selic/{ano}/); "
            "ipca-selic-cross-periodo (comparação multi-ano em IPCA x Selic/{ano}-{ano}/; default 2020-2021 ou --ipca-anos); "
            "ipca-selic-cross-comparativo (2019-2022 vs 2023-2026 em IPCA x Selic/2019-2022-vs-2023-2026/); "
            "ipca-ano-vs-ibge (combinado legado); "
            "ipca-ano-focus / ipca-ano-ibge (séries anuais separadas); "
            "ipca-ano-por-ano (um PNG por ano-calendário); "
            "ipca-vs-ibge (exploratório 12m); "
            "pib-ano-trajetoria-ano (PIB Total ano Y + 3 PNGs em PIB/{ano}/; realizado IBGE 4T JSON); "
            "pib-ano-trajetoria-graficos (só re-plot trajetória PIB a partir de CSV); "
            "pib-periodo (consolidado multi-ano em PIB/{ini}-{fim}/; use --ipca-anos); "
            "pib-periodo-blocos (2019-2022, 2023-2026 e 2019-2026); "
            "pib-vs-ibge / pib-vs-bcb1207 (legado); selic conforme README"
        ),
    )
    parser.add_argument(
        "--ipca-mes-ref",
        type=str,
        default="201901",
        help="Mês YYYYMM para --figure-extra ipca-mes-piloto (default: 201901 = jan/2019)",
    )
    parser.add_argument(
        "--ipca-mes-ano",
        type=int,
        default=2019,
        help="Ano-calendário para --figure-extra ipca-mes-piloto-ano (default: 2019)",
    )
    parser.add_argument(
        "--ipca-anos",
        type=str,
        default=None,
        help=(
            "Anos para --figure-extra ipca-ano-por-ano (lista separada por vírgula). "
            f"Default: {','.join(str(y) for y in IPCA_ANOS_CALENDARIO_GRAFICOS)}. "
            "Para incluir 2018 use --start-date 2018-01-01."
        ),
    )
    parser.add_argument(
        "--econometrics",
        action="store_true",
        help=(
            "Após o painel: OLS ipca_med12m ~ dummy_lula + dummy_pandemia + vix + commodities "
            "(statsmodels), com ADF e diagnósticos BP/DW/JB em output/"
        ),
    )
    args = parser.parse_args(argv)

    cfg = SeriesConfig()
    if args.usd_sgs_code is not None:
        cfg = replace(cfg, sgs_codigo_usd_diario=args.usd_sgs_code)
    if args.months_ahead_cambio is not None:
        cfg = replace(cfg, months_ahead_cambio=args.months_ahead_cambio)
    if args.market_lag_bdias is not None:
        cfg = replace(cfg, market_lag_bdias=args.market_lag_bdias)

    start = _parse_date(args.start_date, DEFAULT_START)
    end = _parse_date(args.end_date, today_date())
    ipca_anos = _parse_ipca_anos(args.ipca_anos)

    try:
        df, fig_paths = run(
            start=start,
            end=end,
            out_dir=args.out_dir,
            cfg=cfg,
            plot_mode=args.plot_mode,
            figure_extras=tuple(args.figure_extra or ()),
            run_econometrics=args.econometrics,
            ipca_anos=ipca_anos,
            ipca_mes_ref=args.ipca_mes_ref,
            ipca_mes_ano=args.ipca_mes_ano,
        )
        msg = f"Linhas: {len(df)} | Colunas: {list(df.columns)}"
        if fig_paths:
            msg += "\nFiguras: " + "; ".join(str(p) for p in fig_paths)
        print(msg)
    except Exception:
        logger.exception("Ocorreu um erro crítico durante a execução do pipeline.")
        raise


if __name__ == "__main__":
    main()
