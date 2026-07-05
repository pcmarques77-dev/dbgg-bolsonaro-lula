"""Valida um trimestre: expectativa Focus (PIB Total trimestral) x IBGE SIDRA 5932.

Exemplo (1T/2023, divulgacao IBGE em 01/jun/2023):
    python scripts/validar_pib_trimestre.py --ano 2023 --tri 1 --divulgacao 2023-06-01
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import requests

from mba_economia.config import SeriesConfig
from mba_economia.focus_extract import fetch_pib_total_expectativa_trimestral
from mba_economia.ibge_pib_volume_trimestral_client import fetch_pib_ibge_vol_trim_lut


def validar_trimestre(
    ano: int,
    tri: int,
    *,
    divulgacao: pd.Timestamp,
    cfg: SeriesConfig | None = None,
    session: requests.Session | None = None,
) -> dict:
    cfg = cfg or SeriesConfig()
    sess = session or requests.Session()

    focus = fetch_pib_total_expectativa_trimestral(session=sess)
    ibge = fetch_pib_ibge_vol_trim_lut(cfg, session=sess)

    f = focus[(focus["ano_ref"] == ano) & (focus["tri_ref"] == tri)].copy()
    i = ibge[(ibge["ano_ref"] == ano) & (ibge["tri_ref"] == tri)]
    ibge_row = {} if i.empty else i.iloc[0].to_dict()

    pre = f[f["survey_date"] < divulgacao.normalize()]
    ultima = pre.iloc[-1] if not pre.empty else None

    foc_med = float(ultima["pib_focus_trim_med_pct"]) if ultima is not None else None
    ibge_yoy = ibge_row.get("pib_ibge_vol_yoy_trim_pct")
    ibge_qoq = ibge_row.get("pib_ibge_vol_qoq_pct")

    return {
        "trimestre": f"{tri}T/{ano}",
        "divulgacao_ibge": divulgacao.date().isoformat(),
        "n_surveys_focus": len(f),
        "ultima_focus": None if ultima is None else ultima.to_dict(),
        "ibge": ibge_row,
        "erro_yoy_pp": None if foc_med is None or ibge_yoy is None else foc_med - ibge_yoy,
        "erro_qoq_pp": None if foc_med is None or ibge_qoq is None else foc_med - ibge_qoq,
        "focus_series": f,
    }


def _print_relatorio(res: dict) -> None:
    print(f"\n=== {res['trimestre']} — validacao Focus x IBGE ===")
    ibge = res["ibge"]
    if ibge:
        print("IBGE realizado (SIDRA t5932, PIB mercado, volume):")
        print(f"  YoY mesmo trimestre (var. 6561): {ibge.get('pib_ibge_vol_yoy_trim_pct')}%")
        print(f"  QoQ t/t-1 (var. 6564):           {ibge.get('pib_ibge_vol_qoq_pct')}%")
        print(f"  Acum. 4 trim. YoY:               {ibge.get('pib_ibge_vol_acum4_yoy_pct')}%")
    else:
        print("IBGE: sem dado para o trimestre (revisar SIDRA).")

    ult = res["ultima_focus"]
    if ult:
        print(f"\nFocus — ultima mediana antes de {res['divulgacao_ibge']}:")
        print(f"  survey_date  = {pd.Timestamp(ult['survey_date']).date()}")
        print(f"  mediana      = {ult['pib_focus_trim_med_pct']}%")
        print(f"  respondentes = {ult['numeroRespondentes']}")
    else:
        print("\nFocus: nenhuma survey antes da data de divulgacao informada.")

    if res["erro_yoy_pp"] is not None:
        print("\nConfronto (Focus vs IBGE):")
        print(f"  Erro vs YoY (comparacao recomendada): {res['erro_yoy_pp']:+.2f} p.p.")
        if res["erro_qoq_pp"] is not None:
            print(f"  Erro vs QoQ (nao e a definicao Focus): {res['erro_qoq_pp']:+.2f} p.p.")
        print(
            "\nNota: a mediana Focus trimestral alinha com YoY (ex. 1T/23: Focus 3,1% vs "
            "IBGE 4,0% na divulgacao de jun/2023; SIDRA hoje pode refletir revisoes).",
        )


def main() -> None:
    p = argparse.ArgumentParser(description="Valida PIB Focus trimestral x IBGE por trimestre.")
    p.add_argument("--ano", type=int, required=True, help="Ano de referencia (ex. 2023)")
    p.add_argument("--tri", type=int, choices=(1, 2, 3, 4), required=True, help="Trimestre 1-4")
    p.add_argument(
        "--divulgacao",
        required=True,
        help="Data ISO da divulgacao IBGE (ex. 2023-06-01 para 1T/2023)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("output"),
        help="Pasta para CSV da serie Focus do trimestre",
    )
    args = p.parse_args()

    div = pd.Timestamp(args.divulgacao).normalize()
    res = validar_trimestre(args.ano, args.tri, divulgacao=div)
    _print_relatorio(res)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    slug = f"pib_focus_trim_{args.tri}t{args.ano}.csv"
    path = args.out_dir / slug
    res["focus_series"].to_csv(path, index=False)
    print(f"\nSerie Focus exportada: {path}")


if __name__ == "__main__":
    main()
