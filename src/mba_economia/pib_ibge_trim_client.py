"""PIB IBGE Contas Nacionais Trimestrais — taxa acumulada em 4 trimestres (%).

Arquivo manual em ``{out_dir}/PIB/*.json`` (export do portal IBGE / painel).
Título típico: *PIB a preços de mercado - Taxa acumulada em 4 trimestres*.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pandas as pd

from .config import PIB_OUTPUT_DIR, SeriesConfig

logger = logging.getLogger(__name__)

_TRIM_RE = re.compile(
    r"^(?P<tri>[1-4])º\s+trimestre\s+(?P<ano>\d{4})$",
    re.IGNORECASE,
)


_SIDRA_CSV_NAME = "ibge_pib_mercado_volume_trimestral.csv"


def resolve_pib_trimestral_sidra_csv(out_dir: Path) -> Path | None:
    """CSV SIDRA t5932 (var. acumulada 4 trimestres) em ``{out_dir}/PIB/``."""
    root = out_dir / PIB_OUTPUT_DIR
    path = root / _SIDRA_CSV_NAME
    return path if path.is_file() else None


def resolve_pib_trimestral_json(out_dir: Path) -> Path | None:
    """Primeiro ``*.json`` na raiz de ``{out_dir}/PIB/``."""
    root = out_dir / PIB_OUTPUT_DIR
    if not root.is_dir():
        return None
    matches = sorted(p for p in root.glob("*.json") if p.is_file())
    return matches[0] if matches else None


def _parse_br_pct(raw: str) -> float:
    s = str(raw).strip().replace(".", "").replace(",", ".")
    return float(s)


def _disponivel_4tri_ano_ref(ano_ref: int, cfg: SeriesConfig) -> pd.Timestamp:
    return pd.Timestamp(
        ano_ref + 1,
        cfg.pib_ibge_4tri_disponivel_mes_ano_seguinte,
        cfg.pib_ibge_4tri_disponivel_dia,
    ).normalize()


def load_pib_ibge_trimestral_long(
    json_path: Path,
    *,
    cfg: SeriesConfig | None = None,
) -> pd.DataFrame:
    """Uma linha por trimestre: ``ano_ref``, ``trimestre``, ``pib_ibge_4tri_yoy_pct``."""
    cfg = cfg or SeriesConfig()
    with json_path.open(encoding="utf-8") as fh:
        payload = json.load(fh)

    values_map = payload.get("valuesMap") or {}
    brasil = values_map.get("Brasil") or {}
    if not brasil:
        return pd.DataFrame(
            columns=["ano_ref", "trimestre", "periodo_label", "pib_ibge_4tri_yoy_pct"],
        )

    rows: list[dict] = []
    for label, val_raw in brasil.items():
        m = _TRIM_RE.match(str(label).strip())
        if not m:
            continue
        ano = int(m.group("ano"))
        tri = int(m.group("tri"))
        try:
            pct = _parse_br_pct(val_raw)
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                "ano_ref": ano,
                "trimestre": tri,
                "periodo_label": str(label),
                "pib_ibge_4tri_yoy_pct": pct,
                "disponivel_aprox": _disponivel_4tri_ano_ref(ano, cfg)
                if tri == 4
                else pd.NaT,
            },
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["ano_ref", "trimestre"])
        .reset_index(drop=True)
    )


def load_pib_ibge_4tri_yoy_from_sidra_csv(
    csv_path: Path,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    """Ano Y: taxa acumulada em 4 trimestres do 4T (coluna SIDRA t5932 v6562)."""
    df = pd.read_csv(csv_path)
    if df.empty or "tri_ref" not in df.columns:
        return pd.DataFrame(
            columns=["ano_ref", "pib_ibge_4tri_yoy_pct", "pib_ibge_4tri_disponivel"],
        )
    col = "pib_ibge_vol_acum4_yoy_pct"
    if col not in df.columns:
        logger.warning("CSV %s sem coluna %s", csv_path.name, col)
        return pd.DataFrame(
            columns=["ano_ref", "pib_ibge_4tri_yoy_pct", "pib_ibge_4tri_disponivel"],
        )
    q4 = df[df["tri_ref"] == 4].copy()
    q4["pib_ibge_4tri_yoy_pct"] = pd.to_numeric(q4[col], errors="coerce")
    q4["pib_ibge_4tri_disponivel"] = q4["ano_ref"].map(
        lambda y: _disponivel_4tri_ano_ref(int(y), cfg),
    )
    return (
        q4[["ano_ref", "pib_ibge_4tri_yoy_pct", "pib_ibge_4tri_disponivel"]]
        .dropna(subset=["pib_ibge_4tri_yoy_pct"])
        .astype({"ano_ref": int})
        .sort_values("ano_ref")
        .reset_index(drop=True)
    )


def load_pib_ibge_4tri_yoy_lut(
    out_dir: Path,
    cfg: SeriesConfig,
) -> pd.DataFrame:
    """Ano-calendário Y: taxa acumulada 4 trimestres do **4º trimestre de Y**."""
    json_path = resolve_pib_trimestral_json(out_dir)
    if json_path is not None:
        logger.info("Carregando PIB IBGE trimestral: %s", json_path.name)
        long = load_pib_ibge_trimestral_long(json_path, cfg=cfg)
        q4 = long[long["trimestre"] == 4].copy()
        return (
            q4[["ano_ref", "pib_ibge_4tri_yoy_pct", "disponivel_aprox"]]
            .rename(columns={"disponivel_aprox": "pib_ibge_4tri_disponivel"})
            .sort_values("ano_ref")
            .reset_index(drop=True)
        )

    csv_path = resolve_pib_trimestral_sidra_csv(out_dir)
    if csv_path is not None:
        logger.info(
            "JSON IBGE ausente; usando SIDRA CSV %s (4T acumulado em 4 trimestres)",
            csv_path.name,
        )
        return load_pib_ibge_4tri_yoy_from_sidra_csv(csv_path, cfg)

    logger.warning(
        "PIB IBGE realizado não encontrado em %s/*.json nem %s",
        out_dir / PIB_OUTPUT_DIR,
        _SIDRA_CSV_NAME,
    )
    return pd.DataFrame(
        columns=["ano_ref", "pib_ibge_4tri_yoy_pct", "pib_ibge_4tri_disponivel"],
    )


def pib_ibge_4tri_yoy_ano_ref(
    out_dir: Path,
    cfg: SeriesConfig,
    ano_ref: int,
    *,
    lut: pd.DataFrame | None = None,
) -> tuple[float, pd.Timestamp]:
    """Realizado ano Y = 4T acumulado em 4 trimestres (%)."""
    table = lut if lut is not None else load_pib_ibge_4tri_yoy_lut(out_dir, cfg)
    row = table[table["ano_ref"] == ano_ref] if not table.empty else pd.DataFrame()
    if row.empty:
        return float("nan"), pd.NaT
    rd = row.iloc[0]
    disp = rd.get("pib_ibge_4tri_disponivel", pd.NaT)
    return float(rd["pib_ibge_4tri_yoy_pct"]), disp
