"""Comparações metodológicas Selic Focus × SGS 11 (trajetória ano-calendário)."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from .config import SELIC_ANUAL_OUTPUT_DIR, SELIC_OUTPUT_DIR, SeriesConfig
from .focus_extract import fetch_selic_expectativa_ano_ref_long
from .ipca_comparisons import (
    _as_ts,
    focus_semanas_no_mes_referencia,
    ultima_mediana_focus_no_mes_referencia,
)
from .sgs_client import fetch_sgs_json, preparar_selic_sgs11_diaria_para_painel

logger = logging.getLogger(__name__)

# Mês-calendário típico da n-ésima reunião Copom do ano (1=fev … 8=dez).
_REUNIAO_MES_COPOM: tuple[int, ...] = (2, 4, 5, 6, 7, 9, 10, 12)


def _ref_yyyymm_reuniao_copom(n_reuniao: int, ano: int) -> str | None:
    if n_reuniao < 1 or n_reuniao > len(_REUNIAO_MES_COPOM):
        return None
    return f"{ano}{_REUNIAO_MES_COPOM[n_reuniao - 1]:02d}"


def selic_year_dir(out_dir: Path, ano: int) -> Path:
    """Diretório piloto Selic mensal: ``{out_dir}/Selic/{ano}/``."""
    path = out_dir / SELIC_OUTPUT_DIR / str(ano)
    path.mkdir(parents=True, exist_ok=True)
    return path


def selic_anual_year_dir(out_dir: Path, ano: int) -> Path:
    """Diretório piloto Selic ano-calendário: ``{out_dir}/Selic Anual/{ano}/``."""
    path = out_dir / SELIC_ANUAL_OUTPUT_DIR / str(ano)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _focus_long_selic_mensal_reuniao(focus_raw: pd.DataFrame) -> pd.DataFrame:
    """``ref_yyyymm`` = mês de referência da reunião ``Rn/ano`` (calendário Copom típico)."""
    g = focus_raw.copy()
    if g.empty:
        return g
    g["survey_date"] = _as_ts(g["survey_date"])
    g["ref_yyyymm"] = [
        _ref_yyyymm_reuniao_copom(int(r["n_reuniao"]), int(r["selic_year_ref"]))
        for _, r in g.iterrows()
    ]
    g = g.dropna(subset=["ref_yyyymm"])
    g["ipca_focus_med_mensal_pct"] = g["selic_focus_pct"]
    return g.sort_values(["ref_yyyymm", "survey_date"]).reset_index(drop=True)


def _selic_sgs_fechamento_mensal(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None,
) -> pd.DataFrame:
    """Última observação SGS 11 em cada mês-calendário + taxa anualizada."""
    raw = fetch_sgs_json(
        cfg.sgs_codigo_selic_diaria,
        start,
        end,
        session=session,
    )
    prep = preparar_selic_sgs11_diaria_para_painel(raw)
    if prep.empty:
        return pd.DataFrame(
            columns=[
                "ref_yyyymm",
                "selic_sgs_data_obs",
                "selic_sgs_pct_aa_aprox",
            ],
        )

    prep = prep.copy()
    prep["ref_yyyymm"] = prep["data_obs"].dt.strftime("%Y%m")
    rows: list[dict] = []
    for ref, grp in prep.groupby("ref_yyyymm", sort=True):
        last = grp.sort_values("data_obs").iloc[-1]
        rows.append(
            {
                "ref_yyyymm": str(ref),
                "selic_sgs_data_obs": last["data_obs"],
                "selic_sgs_pct_aa_aprox": float(last["selic_sgs_pct_aa_aprox"]),
            },
        )
    return pd.DataFrame(rows)


def _collapse_selic_ultima_reuniao_por_survey(
    focus_raw: pd.DataFrame,
    ano_ref: int,
) -> pd.DataFrame:
    """Uma linha por ``survey_date``: última reunião R*/``ano_ref`` naquela survey."""
    g = focus_raw[focus_raw["selic_year_ref"] == ano_ref].copy()
    if g.empty:
        return pd.DataFrame(
            columns=[
                "survey_date",
                "selic_year_ref",
                "selic_focus_pct",
                "reuniao",
                "selic_focus_nresp",
            ],
        )
    g["survey_date"] = _as_ts(g["survey_date"])
    rows: list[dict] = []
    for survey, grp in g.groupby("survey_date", sort=True):
        last = grp.sort_values("n_reuniao").iloc[-1]
        rows.append(
            {
                "survey_date": survey,
                "selic_year_ref": ano_ref,
                "selic_focus_pct": float(last["selic_focus_pct"]),
                "reuniao": str(last["reuniao"]),
                "selic_focus_nresp": last.get("selic_focus_nresp"),
            },
        )
    return pd.DataFrame(rows).sort_values("survey_date").reset_index(drop=True)


def _focus_selic_para_boletim_mes(
    focus_survey: pd.DataFrame,
    ano_ref: int,
) -> pd.DataFrame:
    """Chave ``ref_yyyymm`` = mês de publicação (survey) para regra semanal do boletim."""
    g = focus_survey.copy()
    if g.empty:
        return g
    g["survey_date"] = _as_ts(g["survey_date"])
    g = g[
        (g["survey_date"].dt.year == ano_ref)
        & (g["survey_date"] >= pd.Timestamp(ano_ref, 1, 1))
        & (g["survey_date"] <= pd.Timestamp(ano_ref, 12, 31))
    ]
    g["ref_yyyymm"] = g["survey_date"].dt.strftime("%Y%m")
    g["ipca_focus_med_mensal_pct"] = g["selic_focus_pct"]
    return g.sort_values(["ref_yyyymm", "survey_date"]).reset_index(drop=True)


def _selic_sgs_fechamento_dezembro(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None,
) -> pd.DataFrame:
    """Última observação SGS 11 em dezembro de cada ano + taxa anualizada (252 d.u.)."""
    raw = fetch_sgs_json(
        cfg.sgs_codigo_selic_diaria,
        start,
        end,
        session=session,
    )
    prep = preparar_selic_sgs11_diaria_para_painel(raw)
    if prep.empty:
        return pd.DataFrame(
            columns=[
                "ano_ref",
                "selic_sgs_data_obs",
                "selic_sgs_pct_aa_aprox",
            ],
        )

    prep = prep.copy()
    prep["ano_ref"] = prep["data_obs"].dt.year
    prep["mes"] = prep["data_obs"].dt.month
    dez = prep[prep["mes"] == 12]
    if dez.empty:
        return pd.DataFrame(
            columns=[
                "ano_ref",
                "selic_sgs_data_obs",
                "selic_sgs_pct_aa_aprox",
            ],
        )

    rows: list[dict] = []
    for ano, grp in dez.groupby("ano_ref"):
        last = grp.sort_values("data_obs").iloc[-1]
        rows.append(
            {
                "ano_ref": int(ano),
                "selic_sgs_data_obs": last["data_obs"],
                "selic_sgs_pct_aa_aprox": float(last["selic_sgs_pct_aa_aprox"]),
            },
        )
    return pd.DataFrame(rows).sort_values("ano_ref").reset_index(drop=True)


def build_comparacao_selic_mensal(
    start: date,
    end: date,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compara mediana Focus da reunião do mês M × Selic SGS no fechamento de M.

    Focus: ``ExpectativasMercadoSelic``, ``Reuniao`` = ``Rn/ano``; ``ref_yyyymm`` é o mês
    de referência da reunião (calendário Copom típico). Última edição semanal do boletim
    **no mês M**.

    Realizado: SGS 11 — última observação do mês M, % a.a. anualizada (252 d.u.).
    """
    sess = session or requests.Session()
    filt = pd.Timestamp(start)
    logger.info("Comparação Selic mensal Focus × SGS (%s a %s)...", start, end)
    focus_raw = fetch_selic_expectativa_ano_ref_long(filt_start=filt, session=sess)
    focus_long = _focus_long_selic_mensal_reuniao(focus_raw)
    if focus_long.empty:
        empty = pd.DataFrame(
            columns=[
                "ref_yyyymm",
                "survey_date_previsao",
                "selic_focus_pct",
                "reuniao_focus",
                "selic_sgs_pct_aa_aprox",
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

    sgs = _selic_sgs_fechamento_mensal(start, end, cfg, session=sess)
    real_lut = (
        sgs.set_index("ref_yyyymm")["selic_sgs_pct_aa_aprox"].to_dict()
        if not sgs.empty
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
        prev = float(last["selic_focus_pct"])
        rows.append(
            {
                "ref_yyyymm": str(ref),
                "survey_date_previsao": last["survey_date"],
                "selic_focus_pct": prev,
                "reuniao_focus": str(last.get("reuniao", "")),
                "selic_sgs_pct_aa_aprox": float(real),
                "erro_prev_menos_real_pp": prev - float(real),
                "selic_focus_nresp": last.get("selic_focus_nresp"),
            },
        )

    comparacao = pd.DataFrame(rows).sort_values("ref_yyyymm").reset_index(drop=True)
    return comparacao, focus_long


def _export_selic_mes_piloto_graficos(
    ref_yyyymm: str,
    comp: pd.DataFrame,
    focus_long: pd.DataFrame,
    out_dir: Path,
) -> tuple[pd.Series, list[Path]]:
    from .figures import (
        plot_selic_mes_comparacao_barras,
        plot_selic_mes_focus_semanas,
        plot_selic_mes_sgs_ponto,
    )

    ref = str(ref_yyyymm)
    y, m = int(ref[:4]), int(ref[4:6])
    semanas = focus_semanas_no_mes_referencia(focus_long, ref)
    row_df = comp[comp["ref_yyyymm"].astype(str) == ref]
    if row_df.empty:
        raise ValueError(
            f"Sem linha de comparação para ref_yyyymm={ref}. "
            "Verifique janela de download e reunião Focus no mês.",
        )
    row = row_df.iloc[0]

    out_ano = selic_year_dir(out_dir, y)
    stem = f"{y:04d}-{m:02d}"
    paths: list[Path] = []

    p_focus = out_ano / f"{stem}-focus.png"
    if plot_selic_mes_focus_semanas(semanas, row, p_focus):
        paths.append(p_focus)

    p_sgs = out_ano / f"{stem}-sgs.png"
    if plot_selic_mes_sgs_ponto(row, p_sgs):
        paths.append(p_sgs)

    p_cmp = out_ano / f"{stem}-comparacao-selic.png"
    if plot_selic_mes_comparacao_barras(row, p_cmp):
        paths.append(p_cmp)

    resumo = pd.DataFrame(
        [
            {
                "ref_yyyymm": ref,
                "mes_referencia": f"{y:04d}-{m:02d}",
                "survey_date_previsao": row["survey_date_previsao"],
                "selic_focus_pct": row["selic_focus_pct"],
                "reuniao_focus": row.get("reuniao_focus"),
                "selic_sgs_pct_aa_aprox": row["selic_sgs_pct_aa_aprox"],
                "erro_prev_menos_real_pp": row["erro_prev_menos_real_pp"],
                "n_edicoes_focus_boletim": len(semanas),
            },
        ],
    )
    resumo_path = out_ano / f"{stem}-resumo.csv"
    resumo.to_csv(resumo_path, index=False, decimal=",", sep=";")
    paths.append(resumo_path)

    logger.info(
        "Piloto Selic %s: Focus=%.2f%% (%s) | SGS=%.2f%% | erro=%.2f p.p.",
        ref,
        float(row["selic_focus_pct"]),
        row.get("reuniao_focus", ""),
        float(row["selic_sgs_pct_aa_aprox"]),
        float(row["erro_prev_menos_real_pp"]),
    )
    return row, paths


def export_selic_mes_piloto_ano(
    ano: int,
    out_dir: Path,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
    gerar_graficos_consolidados: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    """Piloto mensal Selic em ``out_dir/Selic/{ano}/`` (mesma estrutura que ``IPCA/``)."""
    start_dl = date(ano - 1, 12, 1)
    end_dl = date(ano + 1, 2, 28)
    logger.info("Piloto Selic mensal — ano %s (%s a %s)...", ano, start_dl, end_dl)

    comp, focus_long = build_comparacao_selic_mensal(start_dl, end_dl, cfg, session=session)
    comp_ano = comp[comp["ref_yyyymm"].astype(str).str.startswith(str(ano))].copy()

    all_paths: list[Path] = []
    resumos: list[pd.DataFrame] = []
    for m in range(1, 13):
        ref = f"{ano}{m:02d}"
        if ref not in comp_ano["ref_yyyymm"].astype(str).values:
            logger.warning("Piloto Selic: mês %s sem comparação completa — ignorado.", ref)
            continue
        try:
            _, paths = _export_selic_mes_piloto_graficos(ref, comp, focus_long, out_dir)
            all_paths.extend(paths)
            resumos.append(
                pd.read_csv(
                    selic_year_dir(out_dir, ano) / f"{ano}-{m:02d}-resumo.csv",
                    sep=";",
                    decimal=",",
                ),
            )
        except ValueError as exc:
            logger.warning("Piloto Selic %s: %s", ref, exc)

    out_ano = selic_year_dir(out_dir, ano)
    if not comp_ano.empty:
        comp_ano.to_csv(
            out_ano / f"comparacao_selic_mensal_{ano}.csv",
            index=False,
            decimal=",",
            sep=";",
        )
        all_paths.append(out_ano / f"comparacao_selic_mensal_{ano}.csv")
    if resumos:
        tab = pd.concat(resumos, ignore_index=True)
        tab.to_csv(out_ano / f"{ano}-resumo-anual.csv", index=False, decimal=",", sep=";")
        all_paths.append(out_ano / f"{ano}-resumo-anual.csv")

    if gerar_graficos_consolidados and resumos:
        pngs = export_selic_anual_graficos_from_csv(ano, out_dir)
        all_paths.extend(pngs)
        logger.info(
            "Piloto Selic mensal %s: %s PNGs consolidados (%s-focus, -sgs, -comparacao-selic).",
            ano,
            len(pngs),
            ano,
        )

    logger.info(
        "Piloto Selic mensal %s concluído: %s meses, %s arquivos.",
        ano,
        len(resumos),
        len(all_paths),
    )
    return comp, focus_long, all_paths


def _carregar_resumo_anual_selic(out_dir: Path, ano: int) -> pd.DataFrame:
    out_ano = selic_year_dir(out_dir, ano)
    for nome in (f"{ano}-resumo-anual.csv", f"comparacao_selic_mensal_{ano}.csv"):
        path = out_ano / nome
        if path.is_file():
            return pd.read_csv(path, sep=";", decimal=",")
    raise FileNotFoundError(
        f"CSV consolidado de {ano} não encontrado em {out_ano}/. "
        "Rode --figure-extra selic-mes-piloto-ano antes.",
    )


def export_selic_anual_graficos_from_csv(
    ano: int,
    out_dir: Path,
) -> list[Path]:
    """Gráficos anuais (12 meses) a partir dos CSVs em ``Selic/{ano}/``."""
    from .figures import (
        plot_selic_anual_comparacao_resumo_mensal,
        plot_selic_anual_focus_resumo_mensal,
        plot_selic_anual_sgs_resumo_mensal,
    )

    resumo = _carregar_resumo_anual_selic(out_dir, ano)
    out_ano = selic_year_dir(out_dir, ano)
    paths: list[Path] = []

    for plot_fn, suffix in (
        (plot_selic_anual_focus_resumo_mensal, "focus"),
        (plot_selic_anual_sgs_resumo_mensal, "sgs"),
        (plot_selic_anual_comparacao_resumo_mensal, "comparacao-selic"),
    ):
        dest = out_ano / f"{ano}-{suffix}.png"
        if plot_fn(resumo, ano, dest):
            paths.append(dest)
            logger.info("Gráfico anual Selic: %s", dest.name)

    return paths


def build_comparacao_selic_ano_trajetoria_mensal(
    ano_ref: int,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Trajetória mensal da expectativa Focus para Selic fim de ``ano_ref``.

    Para cada mês de publicação M em ``ano_ref``: última edição semanal do boletim no mês M
    com mediana na **última reunião** ``R*/ano_ref`` (ExpectativasMercadoSelic).

    Realizado: Selic SGS 11 na **última observação de dezembro** do ano, anualizada
    ``(1+r_d)^{252}-1`` (exploratório vs nível Focus fim de ano).
    """
    sess = session or requests.Session()
    start_dl = date(ano_ref - 1, 12, 1)
    end_dl = date(ano_ref + 1, 3, 15)
    logger.info(
        "Comparação Selic %s — trajetória mensal (%s a %s)...",
        ano_ref,
        start_dl,
        end_dl,
    )

    focus_raw = fetch_selic_expectativa_ano_ref_long(
        filt_start=pd.Timestamp(start_dl),
        session=sess,
    )
    focus_survey = _collapse_selic_ultima_reuniao_por_survey(focus_raw, ano_ref)
    focus_boletim = _focus_selic_para_boletim_mes(focus_survey, ano_ref)

    sgs_dez = _selic_sgs_fechamento_dezembro(start_dl, end_dl, cfg, session=sess)
    real_row = sgs_dez[sgs_dez["ano_ref"] == ano_ref] if not sgs_dez.empty else pd.DataFrame()
    if real_row.empty:
        real_val = float("nan")
        sgs_data = pd.NaT
    else:
        rd = real_row.iloc[0]
        real_val = float(rd["selic_sgs_pct_aa_aprox"])
        sgs_data = rd["selic_sgs_data_obs"]

    rows: list[dict] = []
    for m in range(1, 13):
        ref = f"{ano_ref}{m:02d}"
        last = ultima_mediana_focus_no_mes_referencia(focus_boletim, ref)
        if last is None:
            continue
        prev = float(
            last["selic_focus_pct"]
            if "selic_focus_pct" in last.index
            else last["ipca_focus_med_mensal_pct"],
        )
        rows.append(
            {
                "ano_ref": ano_ref,
                "mes_publicacao_yyyymm": ref,
                "mes_publicacao": f"{ano_ref}-{m:02d}",
                "survey_date_previsao": last["survey_date"],
                "selic_focus_pct": prev,
                "reuniao_focus": last.get("reuniao", ""),
                "selic_sgs_pct_aa_aprox": real_val,
                "selic_sgs_data_obs": sgs_data,
                "erro_prev_menos_real_pp": prev - real_val if pd.notna(real_val) else float("nan"),
                "selic_focus_nresp": last.get("selic_focus_nresp"),
            },
        )

    comparacao = pd.DataFrame(rows).sort_values("mes_publicacao_yyyymm").reset_index(drop=True)
    return comparacao, focus_boletim


def _export_selic_ano_trajetoria_graficos(
    mes_publicacao_yyyymm: str,
    comp: pd.DataFrame,
    focus_boletim: pd.DataFrame,
    out_dir: Path,
) -> tuple[pd.Series, list[Path]]:
    from .figures import (
        plot_selic_ano_trajetoria_comparacao_barras,
        plot_selic_ano_trajetoria_focus_semanas,
        plot_selic_ano_trajetoria_sgs_ponto,
    )

    ref = str(mes_publicacao_yyyymm)
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = y
    semanas = focus_semanas_no_mes_referencia(focus_boletim, ref)
    row_df = comp[comp["mes_publicacao_yyyymm"].astype(str) == ref]
    if row_df.empty:
        raise ValueError(f"Sem comparação para mês de publicação {ref}.")
    row = row_df.iloc[0]

    out_ano = selic_anual_year_dir(out_dir, ano_ref)
    stem = f"{y:04d}-{m:02d}"
    paths: list[Path] = []

    p_focus = out_ano / f"{stem}-focus.png"
    if plot_selic_ano_trajetoria_focus_semanas(semanas, row, p_focus):
        paths.append(p_focus)

    p_sgs = out_ano / f"{stem}-sgs.png"
    if plot_selic_ano_trajetoria_sgs_ponto(row, p_sgs):
        paths.append(p_sgs)

    p_cmp = out_ano / f"{stem}-comparacao-selic.png"
    if plot_selic_ano_trajetoria_comparacao_barras(row, p_cmp):
        paths.append(p_cmp)

    resumo = pd.DataFrame(
        [
            {
                "ano_ref": ano_ref,
                "mes_publicacao_yyyymm": ref,
                "mes_publicacao": f"{y:04d}-{m:02d}",
                "survey_date_previsao": row["survey_date_previsao"],
                "selic_focus_pct": row["selic_focus_pct"],
                "reuniao_focus": row.get("reuniao_focus"),
                "selic_sgs_pct_aa_aprox": row["selic_sgs_pct_aa_aprox"],
                "erro_prev_menos_real_pp": row["erro_prev_menos_real_pp"],
                "n_edicoes_focus_boletim": len(semanas),
            },
        ],
    )
    resumo_path = out_ano / f"{stem}-resumo.csv"
    resumo.to_csv(resumo_path, index=False, decimal=",", sep=";")
    paths.append(resumo_path)

    logger.info(
        "Piloto Selic %s (pub. %s): Focus=%.2f%% (%s) | SGS dez=%.2f%% | erro=%.2f p.p.",
        ano_ref,
        ref,
        float(row["selic_focus_pct"]),
        row.get("reuniao_focus", ""),
        float(row["selic_sgs_pct_aa_aprox"])
        if pd.notna(row["selic_sgs_pct_aa_aprox"])
        else float("nan"),
        float(row["erro_prev_menos_real_pp"])
        if pd.notna(row["erro_prev_menos_real_pp"])
        else float("nan"),
    )
    return row, paths


def export_selic_ano_trajetoria_piloto_ano(
    ano_ref: int,
    out_dir: Path,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
    gerar_graficos_consolidados: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    """Piloto Selic ano-calendário: 12 meses de publicação × fechamento SGS em dezembro."""
    comp, focus_boletim = build_comparacao_selic_ano_trajetoria_mensal(
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
                "Piloto Selic %s: mês de publicação %s sem comparação — ignorado.",
                ano_ref,
                ref,
            )
            continue
        try:
            _, paths = _export_selic_ano_trajetoria_graficos(
                ref,
                comp,
                focus_boletim,
                out_dir,
            )
            all_paths.extend(paths)
            resumos.append(
                pd.read_csv(
                    selic_anual_year_dir(out_dir, ano_ref) / f"{ano_ref}-{m:02d}-resumo.csv",
                    sep=";",
                    decimal=",",
                ),
            )
        except ValueError as exc:
            logger.warning("Piloto Selic %s/%s: %s", ano_ref, ref, exc)

    out_ano = selic_anual_year_dir(out_dir, ano_ref)
    if not comp.empty:
        comp.to_csv(
            out_ano / f"comparacao_selic_ano_trajetoria_{ano_ref}.csv",
            index=False,
            decimal=",",
            sep=";",
        )
        all_paths.append(out_ano / f"comparacao_selic_ano_trajetoria_{ano_ref}.csv")
    if resumos:
        tab = pd.concat(resumos, ignore_index=True)
        tab.to_csv(out_ano / f"{ano_ref}-resumo-anual.csv", index=False, decimal=",", sep=";")
        all_paths.append(out_ano / f"{ano_ref}-resumo-anual.csv")

    if gerar_graficos_consolidados and resumos:
        pngs = export_selic_anual_trajetoria_graficos_from_csv(ano_ref, out_dir)
        all_paths.extend(pngs)
        logger.info(
            "Piloto Selic Anual %s: %s PNGs consolidados de trajetória.",
            ano_ref,
            len(pngs),
        )

    logger.info(
        "Piloto Selic %s concluído: %s meses de publicação, %s arquivos.",
        ano_ref,
        len(resumos),
        len(all_paths),
    )
    return comp, focus_boletim, all_paths


def _carregar_resumo_trajetoria_selic_anual(out_dir: Path, ano_ref: int) -> pd.DataFrame:
    out_ano = selic_anual_year_dir(out_dir, ano_ref)
    for nome in (
        f"{ano_ref}-resumo-anual.csv",
        f"comparacao_selic_ano_trajetoria_{ano_ref}.csv",
    ):
        path = out_ano / nome
        if path.is_file():
            return pd.read_csv(path, sep=";", decimal=",")
    raise FileNotFoundError(
        f"CSV consolidado de {ano_ref} não encontrado em {out_ano}/. "
        "Rode --figure-extra selic-anual-trajetoria-ano antes.",
    )


def export_selic_anual_trajetoria_graficos_from_csv(
    ano_ref: int,
    out_dir: Path,
) -> list[Path]:
    """Gráficos consolidados (12 pontos) em ``Selic Anual/{ano}/``."""
    from .figures import (
        plot_selic_anual_trajetoria_comparacao,
        plot_selic_anual_trajetoria_focus,
        plot_selic_anual_trajetoria_sgs,
    )

    resumo = _carregar_resumo_trajetoria_selic_anual(out_dir, ano_ref)
    out_ano = selic_anual_year_dir(out_dir, ano_ref)
    paths: list[Path] = []

    for plot_fn, suffix in (
        (plot_selic_anual_trajetoria_focus, "focus"),
        (plot_selic_anual_trajetoria_sgs, "sgs"),
        (plot_selic_anual_trajetoria_comparacao, "comparacao-selic"),
    ):
        dest = out_ano / f"{ano_ref}-{suffix}.png"
        if plot_fn(resumo, ano_ref, dest):
            paths.append(dest)
            logger.info("Gráfico trajetória Selic: %s", dest.name)

    return paths
