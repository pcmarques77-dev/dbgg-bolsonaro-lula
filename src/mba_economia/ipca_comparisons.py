"""Comparações metodológicas IPCA Focus × IBGE (mensal e ano-calendário)."""

from __future__ import annotations

import calendar
import logging
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from .config import IPCA_ANUAL_OUTPUT_DIR, SeriesConfig
from .focus_extract import (
    fetch_ipca_expectativa_ano_calendario,
    fetch_ipca_expectativa_ano_ref_long,
    fetch_ipca_expectativa_mensal_long,
)
from .ibge_ipca_client import fetch_ipca_ibge_acum_ano_pct, fetch_ipca_ibge_mensal_pct

logger = logging.getLogger(__name__)


def ipca_year_dir(out_dir: Path, ano: int) -> Path:
    """Diretório de saídas IPCA mensal por ano: ``{out_dir}/IPCA/{ano}/``."""
    path = out_dir / "IPCA" / str(ano)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ipca_anual_year_dir(out_dir: Path, ano: int) -> Path:
    """Diretório piloto IPCA ano-calendário: ``{out_dir}/IPCA Anual/{ano}/``."""
    path = out_dir / IPCA_ANUAL_OUTPUT_DIR / str(ano)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _focus_ano_long_para_boletim_mes(
    focus_long: pd.DataFrame,
    ano_ref: int,
) -> pd.DataFrame:
    """Mapeia expectativa anual para chave ``ref_yyyymm`` = mês de publicação (survey)."""
    g = focus_long[focus_long["ipca_year_ref"] == ano_ref].copy()
    if g.empty:
        return g
    g["survey_date"] = _as_ts(g["survey_date"])
    g = g[
        (g["survey_date"].dt.year == ano_ref)
        & (g["survey_date"] >= pd.Timestamp(ano_ref, 1, 1))
        & (g["survey_date"] <= pd.Timestamp(ano_ref, 12, 31))
    ]
    g["ref_yyyymm"] = g["survey_date"].dt.strftime("%Y%m")
    g["ipca_focus_med_mensal_pct"] = g["ipca_focus_ano_pct"]
    return g.sort_values(["ref_yyyymm", "survey_date"]).reset_index(drop=True)


def _as_ts(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.normalize().astype("datetime64[ns]")


def _mondays_no_mes_calendario(ref_period: pd.Period) -> list[pd.Timestamp]:
    y, m = ref_period.year, ref_period.month
    ndays = calendar.monthrange(y, m)[1]
    return [
        pd.Timestamp(y, m, d).normalize()
        for d in range(1, ndays + 1)
        if pd.Timestamp(y, m, d).weekday() == 0
    ]


def data_publicacao_focus_na_semana(
    segunda_feira: pd.Timestamp,
    datas_com_registro: set[pd.Timestamp],
) -> pd.Timestamp | None:
    """Data do boletim Focus na semana: segunda ou 1º dia útil depois (sem antecipação).

    Percorre segunda → sexta da mesma semana; retorna o primeiro dia com registro na API.
    """
    seg = pd.Timestamp(segunda_feira).normalize()
    for offset in range(5):
        cand = (seg + pd.Timedelta(days=offset)).normalize()
        if cand in datas_com_registro:
            return cand
    return None


def edicoes_focus_boletim_no_mes(
    focus_long: pd.DataFrame,
    ref_yyyymm: str,
) -> pd.DataFrame:
    """Uma linha por edição semanal do Focus no mês (mediana IPCA para ``ref_yyyymm``).

    Só entram publicações cuja ``survey_date`` cai no mês de referência.
    """
    ref = str(ref_yyyymm)
    ref_period = pd.Period(ref, freq="M")
    g = focus_long[focus_long["ref_yyyymm"].astype(str) == ref].copy()
    if g.empty:
        return g
    g["survey_date"] = _as_ts(g["survey_date"])
    datas = set(g["survey_date"].tolist())

    rows: list[pd.Series] = []
    for seg in _mondays_no_mes_calendario(ref_period):
        pub = data_publicacao_focus_na_semana(seg, datas)
        if pub is None or pub.to_period("M") != ref_period:
            continue
        no_dia = g[g["survey_date"] == pub]
        if no_dia.empty:
            continue
        rows.append(no_dia.iloc[-1])

    if not rows:
        return g.iloc[:0].copy()
    return pd.DataFrame(rows).sort_values("survey_date").reset_index(drop=True)


def ultima_mediana_focus_no_mes_referencia(
    focus_long: pd.DataFrame,
    ref_yyyymm: str,
) -> pd.Series | None:
    """Última edição semanal do Focus no mês M para prever IPCA de M (``ref_yyyymm``).

    Regra boletim: segunda-feira ou primeiro dia útil posterior com dado na API
    (Focus não é antecipado). Comparação mensal usa a última dessas edições no mês.
    """
    eds = edicoes_focus_boletim_no_mes(focus_long, ref_yyyymm)
    if eds.empty:
        return None
    return eds.iloc[-1]


def primeira_mediana_focus_no_mes_referencia(
    focus_long: pd.DataFrame,
    ref_yyyymm: str,
) -> pd.Series | None:
    """Primeira edição semanal do Focus no mês M (``ref_yyyymm``)."""
    eds = edicoes_focus_boletim_no_mes(focus_long, ref_yyyymm)
    if eds.empty:
        return None
    return eds.iloc[0]


def focus_semanas_no_mes_referencia(
    focus_long: pd.DataFrame,
    ref_yyyymm: str,
) -> pd.DataFrame:
    """Edições semanais do boletim Focus no mês (não snapshots diários intermediários)."""
    return edicoes_focus_boletim_no_mes(focus_long, ref_yyyymm)


def build_comparacao_ipca_mensal(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compara previsão Focus do mês M com IPCA realizado em M (SIDRA var. 63).

    Regra Focus (boletim): para cada segunda do mês M, usa-se a mediana na segunda
    ou no **primeiro dia útil seguinte** com dado na API (sem antecipação).
    Comparação: **última** edição assim definida no mês M × IPCA IBGE realizado em M.

    Returns:
        comparacao: uma linha por ``ref_yyyymm`` (mês de referência).
        focus_long: todas as surveys × meses de referência (para gráficos).
    """
    sess = session or requests.Session()
    filt = pd.Timestamp(start)
    logger.info("Comparação IPCA mensal Focus × IBGE (%s a %s)...", start, end)
    focus_long = fetch_ipca_expectativa_mensal_long(filt_start=filt, session=sess)
    if focus_long.empty:
        empty = pd.DataFrame(
            columns=[
                "ref_yyyymm",
                "survey_date_previsao",
                "ipca_focus_med_mensal_pct",
                "ipca_ibge_mensal_pct",
                "erro_prev_menos_real_pp",
            ],
        )
        return empty, focus_long

    focus_long = focus_long.copy()
    focus_long["survey_date"] = _as_ts(focus_long["survey_date"])
    focus_long = focus_long[
        (focus_long["survey_date"] >= pd.Timestamp(start))
        & (focus_long["survey_date"] <= pd.Timestamp(end))
    ]

    ibge = fetch_ipca_ibge_mensal_pct(
        start,
        end,
        tabela=cfg.sidra_tab_ipca_acum12,
        codigo_variavel=cfg.sidra_codigo_var_ipca_mensal,
        dia_public_approx_mes_seguinte=cfg.sidra_ipca_disponivel_dia_mes_seguinte,
        session=sess,
    )
    real_lut = (
        ibge.set_index("ibge_period_yyyymm")["ipca_ibge_mensal_pct"].to_dict()
        if not ibge.empty
        else {}
    )

    rows: list[dict] = []
    for ref, grp in focus_long.groupby("ref_yyyymm", sort=True):
        last = ultima_mediana_focus_no_mes_referencia(grp, str(ref))
        if last is None:
            continue
        real = real_lut.get(str(ref))
        if real is None or (isinstance(real, float) and pd.isna(real)):
            continue
        prev = float(last["ipca_focus_med_mensal_pct"])
        rows.append(
            {
                "ref_yyyymm": str(ref),
                "survey_date_previsao": last["survey_date"],
                "ipca_focus_med_mensal_pct": prev,
                "ipca_ibge_mensal_pct": float(real),
                "erro_prev_menos_real_pp": prev - float(real),
                "ipca_focus_mensal_nresp": last.get("ipca_focus_mensal_nresp"),
            },
        )

    comparacao = pd.DataFrame(rows).sort_values("ref_yyyymm").reset_index(drop=True)
    return comparacao, focus_long


def _ipca_ibge_dezembro_fechamento(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None,
) -> pd.DataFrame:
    ibge_ano = fetch_ipca_ibge_acum_ano_pct(
        start,
        end,
        tabela=cfg.sidra_tab_ipca_acum12,
        codigo_variavel=cfg.sidra_codigo_var_ipca_acum_ano,
        dia_public_approx_mes_seguinte=cfg.sidra_ipca_disponivel_dia_mes_seguinte,
        session=session,
    )
    if ibge_ano.empty:
        return pd.DataFrame(
            columns=[
                "ano_ref",
                "ibge_period_yyyymm",
                "ipca_ibge_acum_ano_dez_pct",
                "ibge_ano_disponivel_aprox",
            ],
        )
    dez = ibge_ano[ibge_ano["ibge_period_yyyymm"].str.endswith("12")].copy()
    return (
        dez.rename(
            columns={
                "ipca_ibge_acum_ano_pct": "ipca_ibge_acum_ano_dez_pct",
                "disponivel_aprox": "ibge_ano_disponivel_aprox",
            },
        )
        .assign(ibge_ano_disponivel_aprox=lambda d: _as_ts(d["ibge_ano_disponivel_aprox"]))
        .sort_values("ano_ref")
        .reset_index(drop=True)
    )


def _prepare_focus_ano_window(
    focus: pd.DataFrame,
    start: date,
    end: date,
) -> pd.DataFrame:
    out = focus.copy()
    out["survey_date"] = _as_ts(out["survey_date"])
    out["ipca_year_ref"] = out["ipca_year_ref"].astype(int)
    return out[
        (out["survey_date"] >= pd.Timestamp(start))
        & (out["survey_date"] <= pd.Timestamp(end))
    ].sort_values("survey_date")


def build_comparacao_ipca_ano_calendario(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
    focus_ano: pd.DataFrame | None = None,
    dez: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Série semanal Focus (IPCA do ano-calendário corrente na data da survey).

    Coluna ``ipca_ibge_acum_ano_dez_pct``: IPCA jan–dez do mesmo ``ipca_year_ref``,
    preenchida só após a divulgação (~jan do ano seguinte), para sobrepor no gráfico.
    """
    sess = session or requests.Session()
    focus = focus_ano
    if focus is None:
        focus = fetch_ipca_expectativa_ano_calendario(
            filt_start=pd.Timestamp(start),
            session=sess,
        )
    if focus.empty:
        return pd.DataFrame(
            columns=[
                "survey_date",
                "ipca_focus_ano_pct",
                "ipca_year_ref",
                "ipca_ibge_acum_ano_dez_pct",
                "erro_prev_menos_real_pp",
            ],
        )

    merged = _prepare_focus_ano_window(focus, start, end)
    dez_df = dez if dez is not None else _ipca_ibge_dezembro_fechamento(start, end, cfg, session=sess)
    real_lut = (
        dez_df.set_index("ano_ref")[["ipca_ibge_acum_ano_dez_pct", "ibge_ano_disponivel_aprox"]]
        if not dez_df.empty
        else pd.DataFrame()
    )

    realizados: list[float] = []
    erros: list[float] = []
    for _, row in merged.iterrows():
        y = int(row["ipca_year_ref"])
        if y not in real_lut.index:
            realizados.append(float("nan"))
            erros.append(float("nan"))
            continue
        rd = real_lut.loc[y]
        if row["survey_date"] >= rd["ibge_ano_disponivel_aprox"]:
            r = float(rd["ipca_ibge_acum_ano_dez_pct"])
            realizados.append(r)
            erros.append(float(row["ipca_focus_ano_pct"]) - r)
        else:
            realizados.append(float("nan"))
            erros.append(float("nan"))

    merged["ipca_ibge_acum_ano_dez_pct"] = realizados
    merged["erro_prev_menos_real_pp"] = erros
    return merged.reset_index(drop=True)


def build_comparacao_ipca_ano_fechamento(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
    focus_ano: pd.DataFrame | None = None,
    dez: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Uma linha por ano: última mediana Focus do ano Y vs IPCA realizado jan–dez (dez./SIDRA)."""
    sess = session or requests.Session()
    focus = focus_ano
    if focus is None:
        focus = fetch_ipca_expectativa_ano_calendario(
            filt_start=pd.Timestamp(start),
            session=sess,
        )
    dez_df = dez if dez is not None else _ipca_ibge_dezembro_fechamento(start, end, cfg, session=sess)
    if focus.empty or dez_df.empty:
        return pd.DataFrame(
            columns=[
                "ano_ref",
                "survey_date_ultima_previsao",
                "ipca_focus_ano_pct",
                "ipca_ibge_acum_ano_dez_pct",
                "erro_prev_menos_real_pp",
            ],
        )

    focus = _prepare_focus_ano_window(focus, start, end)
    real_lut = dez_df.set_index("ano_ref")["ipca_ibge_acum_ano_dez_pct"].to_dict()

    rows: list[dict] = []
    for y, grp in focus.groupby("ipca_year_ref"):
        no_ano = grp[grp["survey_date"].dt.year == y]
        if no_ano.empty:
            continue
        last = no_ano.sort_values("survey_date").iloc[-1]
        real = real_lut.get(int(y))
        if real is None:
            continue
        prev = float(last["ipca_focus_ano_pct"])
        rows.append(
            {
                "ano_ref": int(y),
                "survey_date_ultima_previsao": last["survey_date"],
                "ipca_focus_ano_pct": prev,
                "ipca_ibge_acum_ano_dez_pct": float(real),
                "erro_prev_menos_real_pp": prev - float(real),
            },
        )
    return pd.DataFrame(rows).sort_values("ano_ref").reset_index(drop=True)


def build_comparacao_ipca_ano_bundle(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Uma única carga Olinda/SIDRA para calendário semanal e fechamento anual."""
    sess = session or requests.Session()
    logger.info("Comparação IPCA ano-calendário Focus × IBGE (bundle, %s a %s)...", start, end)
    focus = fetch_ipca_expectativa_ano_calendario(
        filt_start=pd.Timestamp(start),
        session=sess,
    )
    dez = _ipca_ibge_dezembro_fechamento(start, end, cfg, session=sess)
    cal = build_comparacao_ipca_ano_calendario(
        start,
        end,
        cfg,
        session=sess,
        focus_ano=focus,
        dez=dez,
    )
    fech = build_comparacao_ipca_ano_fechamento(
        start,
        end,
        cfg,
        session=sess,
        focus_ano=focus,
        dez=dez,
    )
    return cal, fech


def _export_ipca_mes_piloto_graficos(
    ref_yyyymm: str,
    comp: pd.DataFrame,
    focus_long: pd.DataFrame,
    out_dir: Path,
) -> tuple[pd.Series, list[Path]]:
    """Gera PNGs e resumo de um mês a partir de ``comp`` / ``focus_long`` já carregados."""
    from .figures import (
        plot_ipca_mes_comparacao_barras,
        plot_ipca_mes_focus_semanas,
        plot_ipca_mes_ibge_ponto,
    )

    ref = str(ref_yyyymm)
    y, m = int(ref[:4]), int(ref[4:6])
    semanas = focus_semanas_no_mes_referencia(focus_long, ref)
    row_df = comp[comp["ref_yyyymm"].astype(str) == ref]
    if row_df.empty:
        raise ValueError(
            f"Sem linha de comparação para ref_yyyymm={ref}. "
            "Verifique janela de download e publicação IBGE.",
        )
    row = row_df.iloc[0]

    out_ano = ipca_year_dir(out_dir, y)
    stem = f"{y:04d}-{m:02d}"
    paths: list[Path] = []

    p_focus = out_ano / f"{stem}-focus.png"
    if plot_ipca_mes_focus_semanas(semanas, row, p_focus):
        paths.append(p_focus)

    p_ibge = out_ano / f"{stem}-ibge.png"
    if plot_ipca_mes_ibge_ponto(row, p_ibge):
        paths.append(p_ibge)

    p_cmp = out_ano / f"{stem}-comparacao-ipca.png"
    if plot_ipca_mes_comparacao_barras(row, p_cmp):
        paths.append(p_cmp)

    resumo = pd.DataFrame(
        [
            {
                "ref_yyyymm": ref,
                "mes_referencia": f"{y:04d}-{m:02d}",
                "survey_date_previsao": row["survey_date_previsao"],
                "ipca_focus_med_mensal_pct": row["ipca_focus_med_mensal_pct"],
                "ipca_ibge_mensal_pct": row["ipca_ibge_mensal_pct"],
                "erro_prev_menos_real_pp": row["erro_prev_menos_real_pp"],
                "n_edicoes_focus_boletim": len(semanas),
            },
        ],
    )
    resumo_path = out_ano / f"{stem}-resumo.csv"
    resumo.to_csv(resumo_path, index=False, decimal=",", sep=";")
    paths.append(resumo_path)

    logger.info(
        "Piloto IPCA %s: Focus=%.2f%% (survey %s) | IBGE=%.2f%% | erro=%.2f p.p.",
        ref,
        float(row["ipca_focus_med_mensal_pct"]),
        pd.Timestamp(row["survey_date_previsao"]).date(),
        float(row["ipca_ibge_mensal_pct"]),
        float(row["erro_prev_menos_real_pp"]),
    )
    return row, paths


def export_ipca_mes_piloto(
    ref_yyyymm: str,
    out_dir: Path,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    """Gera saídas do piloto mensal em ``out_dir/IPCA/{ano}/`` (Focus semanal + comparação).

    Nomes: ``{YYYY-MM}-focus.png``, ``{YYYY-MM}-ibge.png``, ``{YYYY-MM}-comparacao-ipca.png``.
    """
    import calendar

    ref = str(ref_yyyymm)
    y, m = int(ref[:4]), int(ref[4:6])

    start_dl = date(y - 1, 12, 1) if m == 1 else date(y, m, 1)
    fim_mes_ref = date(y, m, calendar.monthrange(y, m)[1])
    end_dl = date(y + 1, 2, 28) if m == 12 else date(y, m + 1, 15)
    if end_dl < fim_mes_ref:
        end_dl = fim_mes_ref

    comp, focus_long = build_comparacao_ipca_mensal(start_dl, end_dl, cfg, session=session)
    _, paths = _export_ipca_mes_piloto_graficos(ref, comp, focus_long, out_dir)
    return comp, focus_long, paths


def export_ipca_mes_piloto_ano(
    ano: int,
    out_dir: Path,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
    gerar_graficos_consolidados: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    """Piloto mensal Focus × IBGE para todos os meses de ``ano`` (uma carga Olinda/SIDRA)."""
    start_dl = date(ano - 1, 12, 1)
    end_dl = date(ano + 1, 2, 28)
    logger.info("Piloto IPCA mensal — ano %s (%s a %s)...", ano, start_dl, end_dl)

    comp, focus_long = build_comparacao_ipca_mensal(start_dl, end_dl, cfg, session=session)
    comp_ano = comp[comp["ref_yyyymm"].astype(str).str.startswith(str(ano))].copy()

    all_paths: list[Path] = []
    resumos: list[pd.DataFrame] = []
    for m in range(1, 13):
        ref = f"{ano}{m:02d}"
        if ref not in comp_ano["ref_yyyymm"].astype(str).values:
            logger.warning("Piloto IPCA: mês %s sem comparação completa — ignorado.", ref)
            continue
        try:
            _, paths = _export_ipca_mes_piloto_graficos(ref, comp, focus_long, out_dir)
            all_paths.extend(paths)
            resumo = pd.read_csv(
                ipca_year_dir(out_dir, ano) / f"{ano}-{m:02d}-resumo.csv",
                sep=";",
                decimal=",",
            )
            resumos.append(resumo)
        except ValueError as exc:
            logger.warning("Piloto IPCA %s: %s", ref, exc)

    out_ano = ipca_year_dir(out_dir, ano)
    if not comp_ano.empty:
        comp_ano.to_csv(out_ano / f"comparacao_ipca_mensal_{ano}.csv", index=False, decimal=",", sep=";")
        all_paths.append(out_ano / f"comparacao_ipca_mensal_{ano}.csv")
    if resumos:
        tab = pd.concat(resumos, ignore_index=True)
        tab.to_csv(out_ano / f"{ano}-resumo-anual.csv", index=False, decimal=",", sep=";")
        all_paths.append(out_ano / f"{ano}-resumo-anual.csv")

    if gerar_graficos_consolidados and resumos:
        pngs = export_ipca_anual_graficos_from_csv(ano, out_dir)
        all_paths.extend(pngs)
        logger.info(
            "Piloto IPCA %s: %s PNGs consolidados (%s-focus, -ibge, -comparacao-ipca).",
            ano,
            len(pngs),
            ano,
        )

    logger.info(
        "Piloto IPCA %s concluído: %s meses, %s arquivos.",
        ano,
        len(resumos),
        len(all_paths),
    )
    return comp, focus_long, all_paths


def _carregar_resumo_anual_ipca(out_dir: Path, ano: int) -> pd.DataFrame:
    candidatos = [
        ipca_year_dir(out_dir, ano) / f"{ano}-resumo-anual.csv",
        ipca_year_dir(out_dir, ano) / f"comparacao_ipca_mensal_{ano}.csv",
        out_dir / "IPCA" / f"{ano}-resumo-anual.csv",
        out_dir / "IPCA" / f"comparacao_ipca_mensal_{ano}.csv",
    ]
    for path in candidatos:
        if path.is_file():
            return pd.read_csv(path, sep=";", decimal=",")
    raise FileNotFoundError(
        f"CSV consolidado de {ano} não encontrado em {out_dir / 'IPCA'}/{ano}/ "
        f"(esperado {ano}-resumo-anual.csv). Rode --figure-extra ipca-mes-piloto-ano antes.",
    )


def export_ipca_anual_graficos_from_csv(
    ano: int,
    out_dir: Path,
) -> list[Path]:
    """Gráficos anuais a partir dos CSVs mensais consolidados (``output/IPCA/{ano}/``).

    Saídas: ``{ano}-focus.png``, ``{ano}-ibge.png``, ``{ano}-comparacao-ipca.png``.
    """
    from .figures import (
        plot_ipca_anual_comparacao_resumo_mensal,
        plot_ipca_anual_focus_resumo_mensal,
        plot_ipca_anual_ibge_resumo_mensal,
    )

    resumo = _carregar_resumo_anual_ipca(out_dir, ano)
    out_ano = ipca_year_dir(out_dir, ano)
    paths: list[Path] = []

    for plot_fn, suffix in (
        (plot_ipca_anual_focus_resumo_mensal, "focus"),
        (plot_ipca_anual_ibge_resumo_mensal, "ibge"),
        (plot_ipca_anual_comparacao_resumo_mensal, "comparacao-ipca"),
    ):
        dest = out_ano / f"{ano}-{suffix}.png"
        if plot_fn(resumo, ano, dest):
            paths.append(dest)
            logger.info("Gráfico anual IPCA: %s", dest.name)

    return paths


def build_comparacao_ipca_ano_trajetoria_mensal(
    ano_ref: int,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Trajetória mensal da expectativa Focus para inflação jan–dez de ``ano_ref``.

    Para cada mês de publicação M em ``ano_ref`` (jan…dez): última edição semanal do
    boletim no mês M com ``DataReferencia`` = ``ano_ref`` (ExpectativasMercadoAnuais).

    Realizado: IPCA acumulado jan–dez do mesmo ano (SIDRA 1737, var. 69, dez.), divulgado
    ~jan do ano seguinte.
    """
    sess = session or requests.Session()
    start_dl = date(ano_ref - 1, 12, 1)
    end_dl = date(ano_ref + 1, 3, 15)
    logger.info(
        "Comparação IPCA ano-calendário %s — trajetória mensal (%s a %s)...",
        ano_ref,
        start_dl,
        end_dl,
    )
    focus_long = fetch_ipca_expectativa_ano_ref_long(
        filt_start=pd.Timestamp(start_dl),
        session=sess,
    )
    focus_boletim = _focus_ano_long_para_boletim_mes(focus_long, ano_ref)

    dez = _ipca_ibge_dezembro_fechamento(start_dl, end_dl, cfg, session=sess)
    real_row = dez[dez["ano_ref"] == ano_ref] if not dez.empty else pd.DataFrame()
    if real_row.empty:
        real_val = float("nan")
        ibge_disp = pd.NaT
    else:
        rd = real_row.iloc[0]
        real_val = float(rd["ipca_ibge_acum_ano_dez_pct"])
        ibge_disp = rd["ibge_ano_disponivel_aprox"]

    rows: list[dict] = []
    for m in range(1, 13):
        ref = f"{ano_ref}{m:02d}"
        last = ultima_mediana_focus_no_mes_referencia(focus_boletim, ref)
        if last is None:
            continue
        prev = float(last["ipca_focus_ano_pct"])
        rows.append(
            {
                "ano_ref": ano_ref,
                "mes_publicacao_yyyymm": ref,
                "mes_publicacao": f"{ano_ref}-{m:02d}",
                "survey_date_previsao": last["survey_date"],
                "ipca_focus_ano_pct": prev,
                "ipca_ibge_acum_ano_dez_pct": real_val,
                "ibge_ano_disponivel_aprox": ibge_disp,
                "erro_prev_menos_real_pp": prev - real_val
                if pd.notna(real_val)
                else float("nan"),
                "ipca_focus_ano_nresp": last.get("ipca_focus_ano_nresp"),
            },
        )

    comparacao = pd.DataFrame(rows).sort_values("mes_publicacao_yyyymm").reset_index(drop=True)
    return comparacao, focus_boletim


def _export_ipca_ano_trajetoria_graficos(
    mes_publicacao_yyyymm: str,
    comp: pd.DataFrame,
    focus_boletim: pd.DataFrame,
    out_dir: Path,
) -> tuple[pd.Series, list[Path]]:
    from .figures import (
        plot_ipca_ano_trajetoria_comparacao_barras,
        plot_ipca_ano_trajetoria_focus_semanas,
        plot_ipca_ano_trajetoria_ibge_ponto,
    )

    ref = str(mes_publicacao_yyyymm)
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = y
    semanas = focus_semanas_no_mes_referencia(focus_boletim, ref)
    row_df = comp[comp["mes_publicacao_yyyymm"].astype(str) == ref]
    if row_df.empty:
        raise ValueError(f"Sem comparação para mês de publicação {ref}.")
    row = row_df.iloc[0]

    out_ano = ipca_anual_year_dir(out_dir, ano_ref)
    stem = f"{y:04d}-{m:02d}"
    paths: list[Path] = []

    p_focus = out_ano / f"{stem}-focus.png"
    if plot_ipca_ano_trajetoria_focus_semanas(semanas, row, p_focus):
        paths.append(p_focus)

    p_ibge = out_ano / f"{stem}-ibge.png"
    if plot_ipca_ano_trajetoria_ibge_ponto(row, p_ibge):
        paths.append(p_ibge)

    p_cmp = out_ano / f"{stem}-comparacao-ipca-ano.png"
    if plot_ipca_ano_trajetoria_comparacao_barras(row, p_cmp):
        paths.append(p_cmp)

    resumo = pd.DataFrame(
        [
            {
                "ano_ref": ano_ref,
                "mes_publicacao_yyyymm": ref,
                "mes_publicacao": f"{y:04d}-{m:02d}",
                "survey_date_previsao": row["survey_date_previsao"],
                "ipca_focus_ano_pct": row["ipca_focus_ano_pct"],
                "ipca_ibge_acum_ano_dez_pct": row["ipca_ibge_acum_ano_dez_pct"],
                "erro_prev_menos_real_pp": row["erro_prev_menos_real_pp"],
                "n_edicoes_focus_boletim": len(semanas),
            },
        ],
    )
    resumo_path = out_ano / f"{stem}-resumo.csv"
    resumo.to_csv(resumo_path, index=False, decimal=",", sep=";")
    paths.append(resumo_path)

    logger.info(
        "Piloto IPCA Anual %s (pub. %s): Focus=%.2f%% (survey %s) | IBGE jan–dez=%.2f%% | erro=%.2f p.p.",
        ano_ref,
        ref,
        float(row["ipca_focus_ano_pct"]),
        pd.Timestamp(row["survey_date_previsao"]).date(),
        float(row["ipca_ibge_acum_ano_dez_pct"]),
        float(row["erro_prev_menos_real_pp"]),
    )
    return row, paths


def export_ipca_ano_trajetoria_piloto_ano(
    ano_ref: int,
    out_dir: Path,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
    gerar_graficos_consolidados: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    """Piloto ano-calendário: 12 meses de publicação × IPCA realizado jan–dez do ano."""
    comp, focus_boletim = build_comparacao_ipca_ano_trajetoria_mensal(
        ano_ref,
        cfg,
        session=session,
    )

    all_paths: list[Path] = []
    resumos: list[pd.DataFrame] = []
    for m in range(1, 13):
        ref = f"{ano_ref}{m:02d}"
        if ref not in comp["mes_publicacao_yyyymm"].astype(str).values:
            logger.warning(
                "Piloto IPCA Anual %s: mês de publicação %s sem comparação — ignorado.",
                ano_ref,
                ref,
            )
            continue
        try:
            _, paths = _export_ipca_ano_trajetoria_graficos(
                ref,
                comp,
                focus_boletim,
                out_dir,
            )
            all_paths.extend(paths)
            resumos.append(
                pd.read_csv(
                    ipca_anual_year_dir(out_dir, ano_ref) / f"{ano_ref}-{m:02d}-resumo.csv",
                    sep=";",
                    decimal=",",
                ),
            )
        except ValueError as exc:
            logger.warning("Piloto IPCA Anual %s/%s: %s", ano_ref, ref, exc)

    out_ano = ipca_anual_year_dir(out_dir, ano_ref)
    if not comp.empty:
        comp.to_csv(
            out_ano / f"comparacao_ipca_ano_trajetoria_{ano_ref}.csv",
            index=False,
            decimal=",",
            sep=";",
        )
        all_paths.append(out_ano / f"comparacao_ipca_ano_trajetoria_{ano_ref}.csv")
    if resumos:
        tab = pd.concat(resumos, ignore_index=True)
        tab.to_csv(out_ano / f"{ano_ref}-resumo-anual.csv", index=False, decimal=",", sep=";")
        all_paths.append(out_ano / f"{ano_ref}-resumo-anual.csv")

    if gerar_graficos_consolidados and resumos:
        pngs = export_ipca_anual_trajetoria_graficos_from_csv(ano_ref, out_dir)
        all_paths.extend(pngs)
        logger.info(
            "Piloto IPCA Anual %s: %s PNGs consolidados de trajetória.",
            ano_ref,
            len(pngs),
        )

    logger.info(
        "Piloto IPCA Anual %s concluído: %s meses de publicação, %s arquivos.",
        ano_ref,
        len(resumos),
        len(all_paths),
    )
    return comp, focus_boletim, all_paths


def _carregar_resumo_trajetoria_ipca_anual(out_dir: Path, ano_ref: int) -> pd.DataFrame:
    out_ano = ipca_anual_year_dir(out_dir, ano_ref)
    for nome in (
        f"{ano_ref}-resumo-anual.csv",
        f"comparacao_ipca_ano_trajetoria_{ano_ref}.csv",
    ):
        path = out_ano / nome
        if path.is_file():
            return pd.read_csv(path, sep=";", decimal=",")
    raise FileNotFoundError(
        f"CSV consolidado de {ano_ref} não encontrado em {out_ano}/. "
        "Rode --figure-extra ipca-anual-trajetoria-ano antes.",
    )


def export_ipca_anual_trajetoria_graficos_from_csv(
    ano_ref: int,
    out_dir: Path,
) -> list[Path]:
    """Gráficos consolidados da trajetória (12 pontos) em ``IPCA Anual/{ano}/``."""
    from .figures import (
        plot_ipca_anual_trajetoria_comparacao,
        plot_ipca_anual_trajetoria_focus,
        plot_ipca_anual_trajetoria_ibge,
    )

    resumo = _carregar_resumo_trajetoria_ipca_anual(out_dir, ano_ref)
    out_ano = ipca_anual_year_dir(out_dir, ano_ref)
    paths: list[Path] = []

    for plot_fn, suffix in (
        (plot_ipca_anual_trajetoria_focus, "focus"),
        (plot_ipca_anual_trajetoria_ibge, "ibge"),
        (plot_ipca_anual_trajetoria_comparacao, "comparacao-ipca-ano"),
    ):
        dest = out_ano / f"{ano_ref}-{suffix}.png"
        if plot_fn(resumo, ano_ref, dest):
            paths.append(dest)
            logger.info("Gráfico trajetória IPCA Anual: %s", dest.name)

    return paths
