"""PIB trimestral — variação em volume (%), Contas Nacionais via SIDRA (IBGE).

Tabela **5932** — taxa de variação do índice de volume trimestral.
Setor **90707** (classificação ``c11255``) = PIB a preços de mercado.

Portal: https://sidra.ibge.gov.br/tabela/5932
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
import requests

from .config import SIDRA_IBGE_VALUES_BASE, SeriesConfig

logger = logging.getLogger(__name__)

_VAR_YOY_TRIM = 6561
_VAR_QOQ = 6564
_VAR_ACUM4_YOY = 6562
_VAR_YTD_YOY = 6563

_VAR_COLS: dict[int, str] = {
    _VAR_YOY_TRIM: "pib_ibge_vol_yoy_trim_pct",
    _VAR_QOQ: "pib_ibge_vol_qoq_pct",
    _VAR_ACUM4_YOY: "pib_ibge_vol_acum4_yoy_pct",
    _VAR_YTD_YOY: "pib_ibge_vol_ytd_yoy_pct",
}


def _parse_d3c_trimestre(d3: object) -> tuple[int, int] | None:
    d3s = str(d3)
    if len(d3s) != 6 or not d3s.isdigit():
        return None
    return int(d3s[:4]), int(d3s[4:6])


def fetch_pib_sidra_variacao_volume_trimestral(
    *,
    tabela: int,
    classificacao: str,
    cod_setor_pib_mercado: int,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Uma linha por trimestre IBGE (``ano_ref``, ``tri_ref``) com taxas de volume."""
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", "mba-economia-fipe/0.1")
    vars_csv = ",".join(str(v) for v in _VAR_COLS)
    u = (
        f"{SIDRA_IBGE_VALUES_BASE}/t/{tabela}/n1/1/v/{vars_csv}"
        f"/p/all/{classificacao}/{cod_setor_pib_mercado}/h/n/f/c"
    )
    r = sess.get(u, timeout=180)
    r.raise_for_status()
    chunk: list[dict] = []
    for row in r.json():
        d3 = row.get("D3C")
        if not d3 or str(d3).lower() == "valor":
            continue
        try:
            d2i = int(row.get("D2C"))
        except (TypeError, ValueError):
            continue
        if d2i not in _VAR_COLS:
            continue
        v_raw = row.get("V")
        if isinstance(v_raw, str) and v_raw.strip() in ("...", "..", "", "-"):
            continue
        val = pd.to_numeric(v_raw, errors="coerce")
        if pd.isna(val):
            continue
        parsed = _parse_d3c_trimestre(d3)
        if parsed is None:
            continue
        ano, tri = parsed
        chunk.append(
            {
                "ano_ref": ano,
                "tri_ref": tri,
                _VAR_COLS[d2i]: float(val),
            },
        )
    if not chunk:
        return pd.DataFrame(
            columns=["ano_ref", "tri_ref", *_VAR_COLS.values()],
        )
    long = pd.DataFrame(chunk)
    return (
        long.groupby(["ano_ref", "tri_ref"], as_index=False)
        .first()
        .sort_values(["ano_ref", "tri_ref"])
        .reset_index(drop=True)
    )


def load_pib_from_excel(excel_path: str | Path) -> pd.DataFrame:
    roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
    
    xl = pd.ExcelFile(excel_path)
    
    def parse_pib_sheet(sheet_name: str) -> pd.DataFrame:
        df = xl.parse(sheet_name)
        headers = [str(h).strip() for h in df.iloc[1].tolist()]
        
        # Encontra o índice da coluna PIB
        pib_idx = None
        for idx, h in enumerate(headers):
            if h == 'PIB':
                pib_idx = idx
                break
        if pib_idx is None:
            raise ValueError(f"Coluna PIB não encontrada na planilha {sheet_name}")
            
        data = df.iloc[3:].copy()
        data.columns = headers
        period_col = headers[0]
        data = data.rename(columns={period_col: 'Periodo'})
        
        rows = []
        for _, row in data.iterrows():
            p_val = str(row['Periodo']).strip()
            m = re.match(r'^(\d{4})\.(I|II|III|IV)$', p_val)
            if m:
                ano = int(m.group(1))
                tri = roman_map[m.group(2)]
                val = pd.to_numeric(row.iloc[pib_idx], errors='coerce')
                rows.append({'ano_ref': ano, 'tri_ref': tri, 'val': val})
        return pd.DataFrame(rows)

    sheets_map = {
        'Taxa Trimestral': 'pib_ibge_vol_yoy_trim_pct',
        'Trimestre contra Trimestre Ant.': 'pib_ibge_vol_qoq_pct',
        'Acum. em 4 trimestres': 'pib_ibge_vol_acum4_yoy_pct',
        'Tx. Acumulada ao Longo do Ano': 'pib_ibge_vol_ytd_yoy_pct'
    }

    merged = None
    for sname, colname in sheets_map.items():
        df_sheet = parse_pib_sheet(sname).rename(columns={'val': colname})
        if merged is None:
            merged = df_sheet
        else:
            merged = pd.merge(merged, df_sheet, on=['ano_ref', 'tri_ref'], how='outer')
            
    return merged.sort_values(['ano_ref', 'tri_ref']).reset_index(drop=True)


def fetch_pib_ibge_vol_trim_lut(
    cfg: SeriesConfig,
    *,
    session: requests.Session | None = None,
    excel_path: str | Path | None = r"C:\Users\pcmar\Downloads\Tab_Compl_CNT_1T26.xls",
) -> pd.DataFrame:
    if excel_path and Path(excel_path).exists():
        try:
            logger.info("Carregando PIB trimestral a partir da tabela Excel local: %s", excel_path)
            return load_pib_from_excel(excel_path)
        except Exception as e:
            logger.warning("Falha ao ler Excel local PIB, recorrendo a API SIDRA: %s", e)
    
    logger.info("Planilha Excel local não encontrada ou falhou. Buscando da API SIDRA (IBGE)...")
    return fetch_pib_sidra_variacao_volume_trimestral(
        tabela=cfg.sidra_tab_pib_trim_vol,
        classificacao=cfg.sidra_class_pib_setores_trim,
        cod_setor_pib_mercado=cfg.sidra_codigo_pib_mercado_vol_trim,
        session=session,
    )
