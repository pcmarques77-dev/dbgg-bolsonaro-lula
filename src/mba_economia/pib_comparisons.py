"""Comparações metodológicas PIB Total Focus × IBGE 4T acumulado (ano-calendário)."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from .config import PIB_OUTPUT_DIR, SeriesConfig
from .focus_extract import fetch_pib_expectativa_ano_ref_long
from .ipca_comparisons import (
    _as_ts,
    focus_semanas_no_mes_referencia,
    primeira_mediana_focus_no_mes_referencia,
)
from .pib_ibge_trim_client import load_pib_ibge_4tri_yoy_lut, pib_ibge_4tri_yoy_ano_ref

logger = logging.getLogger(__name__)


def pib_year_dir(out_dir: Path, ano: int) -> Path:
    """Diretório piloto PIB ano-calendário: ``{out_dir}/PIB/{ano}/``."""
    path = out_dir / PIB_OUTPUT_DIR / str(ano)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _focus_pib_long_para_boletim_mes(
    focus_long: pd.DataFrame,
    ano_ref: int,
) -> pd.DataFrame:
    """Mapeia expectativa PIB anual para chave ``ref_yyyymm`` = mês de publicação (survey)."""
    g = focus_long[focus_long["pib_year_ref"] == ano_ref].copy()
    if g.empty:
        return g
    g["survey_date"] = _as_ts(g["survey_date"])
    g = g[
        (g["survey_date"].dt.year == ano_ref)
        & (g["survey_date"] >= pd.Timestamp(ano_ref, 1, 1))
        & (g["survey_date"] <= pd.Timestamp(ano_ref, 12, 31))
    ]
    g["ref_yyyymm"] = g["survey_date"].dt.strftime("%Y%m")
    g["pib_focus_med_mensal_pct"] = g["pib_focus_ano_pct"]
    return g.sort_values(["ref_yyyymm", "survey_date"]).reset_index(drop=True)


def build_comparacao_pib_ano_trajetoria_mensal(
    ano_ref: int,
    out_dir: Path,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Trajetória mensal da expectativa Focus para PIB Total do ano ``ano_ref``.

    Realizado: taxa acumulada em 4 trimestres do **4º trimestre** de ``ano_ref``,
    lida de ``{out_dir}/PIB/*.json`` (IBGE Contas Nacionais Trimestrais).
    """
    sess = session or requests.Session()
    start_dl = date(ano_ref - 1, 12, 1)
    end_dl = date(ano_ref + 1, 3, 15)
    logger.info(
        "Comparação PIB ano-calendário %s — trajetória mensal (%s a %s)...",
        ano_ref,
        start_dl,
        end_dl,
    )
    focus_long = fetch_pib_expectativa_ano_ref_long(
        filt_start=pd.Timestamp(start_dl),
        session=sess,
    )
    focus_boletim = _focus_pib_long_para_boletim_mes(focus_long, ano_ref)

    lut = load_pib_ibge_4tri_yoy_lut(out_dir, cfg)
    real_val, ibge_disp = pib_ibge_4tri_yoy_ano_ref(out_dir, cfg, ano_ref, lut=lut)

    rows: list[dict] = []
    for m in range(1, 13):
        ref = f"{ano_ref}{m:02d}"
        first = primeira_mediana_focus_no_mes_referencia(focus_boletim, ref)
        if first is None:
            continue
        prev = float(first["pib_focus_ano_pct"])
        rows.append(
            {
                "ano_ref": ano_ref,
                "mes_publicacao_yyyymm": ref,
                "mes_publicacao": f"{ano_ref}-{m:02d}",
                "survey_date_previsao": first["survey_date"],
                "pib_focus_ano_pct": prev,
                "pib_ibge_4tri_yoy_pct": real_val,
                "pib_ibge_4tri_disponivel": ibge_disp,
                "erro_prev_menos_real_pp": prev - real_val
                if pd.notna(real_val)
                else float("nan"),
                "pib_focus_ano_nresp": first.get("pib_focus_ano_nresp"),
            },
        )

    comparacao = pd.DataFrame(rows).sort_values("mes_publicacao_yyyymm").reset_index(drop=True)
    return comparacao, focus_boletim


def _realizado_col(df: pd.DataFrame | pd.Series) -> str:
    cols = df.index if isinstance(df, pd.Series) else df.columns
    for name in ("pib_ibge_4tri_yoy_pct", "pib_sgs_nominal_yoy_pct", "pib_ibge_vol_yoy_pct"):
        if name in cols:
            return name
    return "pib_ibge_4tri_yoy_pct"


def _export_pib_ano_trajetoria_graficos(
    mes_publicacao_yyyymm: str,
    comp: pd.DataFrame,
    focus_boletim: pd.DataFrame,
    out_dir: Path,
) -> tuple[pd.Series, list[Path]]:
    from .figures import (
        plot_pib_ano_trajetoria_comparacao_barras,
        plot_pib_ano_trajetoria_focus_semanas,
        plot_pib_ano_trajetoria_ibge_ponto,
    )

    ref = str(mes_publicacao_yyyymm)
    y, m = int(ref[:4]), int(ref[4:6])
    ano_ref = y
    semanas = focus_semanas_no_mes_referencia(focus_boletim, ref)
    row_df = comp[comp["mes_publicacao_yyyymm"].astype(str) == ref]
    if row_df.empty:
        raise ValueError(f"Sem comparação para mês de publicação {ref}.")
    row = row_df.iloc[0]

    out_ano = pib_year_dir(out_dir, ano_ref)
    stem = f"{y:04d}-{m:02d}"
    paths: list[Path] = []

    p_focus = out_ano / f"{stem}-focus.png"
    if plot_pib_ano_trajetoria_focus_semanas(semanas, row, p_focus):
        paths.append(p_focus)

    p_ibge = out_ano / f"{stem}-ibge.png"
    if plot_pib_ano_trajetoria_ibge_ponto(row, p_ibge):
        paths.append(p_ibge)

    p_cmp = out_ano / f"{stem}-comparacao-pib.png"
    if plot_pib_ano_trajetoria_comparacao_barras(row, p_cmp):
        paths.append(p_cmp)

    real_col = _realizado_col(row)
    resumo = pd.DataFrame(
        [
            {
                "ano_ref": ano_ref,
                "mes_publicacao_yyyymm": ref,
                "mes_publicacao": f"{y:04d}-{m:02d}",
                "survey_date_previsao": row["survey_date_previsao"],
                "pib_focus_ano_pct": row["pib_focus_ano_pct"],
                "pib_ibge_4tri_yoy_pct": row.get("pib_ibge_4tri_yoy_pct", row.get(real_col)),
                "erro_prev_menos_real_pp": row["erro_prev_menos_real_pp"],
                "n_edicoes_focus_boletim": len(semanas),
            },
        ],
    )
    resumo_path = out_ano / f"{stem}-resumo.csv"
    resumo.to_csv(resumo_path, index=False, decimal=",", sep=";")
    paths.append(resumo_path)

    logger.info(
        "Piloto PIB %s (pub. %s): Focus=%.2f%% (survey %s) | IBGE 4T=%.2f%% | erro=%.2f p.p.",
        ano_ref,
        ref,
        float(row["pib_focus_ano_pct"]),
        pd.Timestamp(row["survey_date_previsao"]).date(),
        float(row[real_col]),
        float(row["erro_prev_menos_real_pp"]),
    )
    return row, paths


def export_pib_ano_trajetoria_piloto_ano(
    ano_ref: int,
    out_dir: Path,
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
    gerar_graficos_consolidados: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    """Piloto ano-calendário: 12 meses de publicação × PIB IBGE 4T acumulado do ano."""
    comp, focus_boletim = build_comparacao_pib_ano_trajetoria_mensal(
        ano_ref,
        out_dir,
        cfg,
        session=session,
    )

    all_paths: list[Path] = []
    resumos: list[pd.DataFrame] = []
    for m in range(1, 13):
        ref = f"{ano_ref}{m:02d}"
        if ref not in comp["mes_publicacao_yyyymm"].astype(str).values:
            logger.warning(
                "Piloto PIB %s: mês de publicação %s sem comparação — ignorado.",
                ano_ref,
                ref,
            )
            continue
        try:
            _, paths = _export_pib_ano_trajetoria_graficos(
                ref,
                comp,
                focus_boletim,
                out_dir,
            )
            all_paths.extend(paths)
            resumos.append(
                pd.read_csv(
                    pib_year_dir(out_dir, ano_ref) / f"{ano_ref}-{m:02d}-resumo.csv",
                    sep=";",
                    decimal=",",
                ),
            )
        except ValueError as exc:
            logger.warning("Piloto PIB %s/%s: %s", ano_ref, ref, exc)

    out_ano = pib_year_dir(out_dir, ano_ref)
    if not comp.empty:
        comp.to_csv(
            out_ano / f"comparacao_pib_ano_trajetoria_{ano_ref}.csv",
            index=False,
            decimal=",",
            sep=";",
        )
        all_paths.append(out_ano / f"comparacao_pib_ano_trajetoria_{ano_ref}.csv")
    if resumos:
        tab = pd.concat(resumos, ignore_index=True)
        tab.to_csv(out_ano / f"{ano_ref}-resumo-anual.csv", index=False, decimal=",", sep=";")
        all_paths.append(out_ano / f"{ano_ref}-resumo-anual.csv")

    if gerar_graficos_consolidados and resumos:
        pngs = export_pib_anual_trajetoria_graficos_from_csv(ano_ref, out_dir)
        all_paths.extend(pngs)
        logger.info(
            "Piloto PIB %s: %s PNGs consolidados de trajetória.",
            ano_ref,
            len(pngs),
        )

    logger.info(
        "Piloto PIB %s concluído: %s meses de publicação, %s arquivos.",
        ano_ref,
        len(resumos),
        len(all_paths),
    )
    return comp, focus_boletim, all_paths


def _carregar_resumo_trajetoria_pib(out_dir: Path, ano_ref: int) -> pd.DataFrame:
    out_ano = pib_year_dir(out_dir, ano_ref)
    for nome in (
        f"{ano_ref}-resumo-anual.csv",
        f"comparacao_pib_ano_trajetoria_{ano_ref}.csv",
    ):
        path = out_ano / nome
        if path.is_file():
            return pd.read_csv(path, sep=";", decimal=",")
    raise FileNotFoundError(
        f"CSV consolidado de {ano_ref} não encontrado em {out_ano}/. "
        "Rode --figure-extra pib-ano-trajetoria-ano antes.",
    )


def export_pib_anual_trajetoria_graficos_from_csv(
    ano_ref: int,
    out_dir: Path,
) -> list[Path]:
    """Gráficos consolidados da trajetória (12 pontos) em ``PIB/{ano}/``."""
    from .figures import (
        plot_pib_anual_trajetoria_comparacao,
        plot_pib_anual_trajetoria_focus,
        plot_pib_anual_trajetoria_ibge,
    )

    resumo = _carregar_resumo_trajetoria_pib(out_dir, ano_ref)
    out_ano = pib_year_dir(out_dir, ano_ref)
    paths: list[Path] = []

    for plot_fn, suffix in (
        (plot_pib_anual_trajetoria_focus, "focus"),
        (plot_pib_anual_trajetoria_ibge, "ibge"),
        (plot_pib_anual_trajetoria_comparacao, "comparacao-pib"),
    ):
        dest = out_ano / f"{ano_ref}-{suffix}.png"
        if plot_fn(resumo, ano_ref, dest):
            paths.append(dest)
            logger.info("Gráfico trajetória PIB: %s", dest.name)

    return paths
