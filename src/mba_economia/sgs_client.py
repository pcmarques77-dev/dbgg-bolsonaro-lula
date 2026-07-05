from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .config import as_ddmmyyyy

logger = logging.getLogger(__name__)

# A partir de mar/2025 o BC limita janelas (~10 anos); fatiamos para ficar abaixo.
_SGS_INTERVALO_MAX_DIAS = 3600


def _get_sgs_cache_path(codigo: int, start: date, end_inclusive: date) -> Path:
    key_str = f"sgs|{codigo}|{start}|{end_inclusive}"
    h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
    root_dir = Path(__file__).resolve().parents[2]
    cache_dir = root_dir / "v2" / ".cache"
    if not cache_dir.exists():
        cache_dir = root_dir / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"sgs_{h}.json"


def _load_sgs_from_disk_cache(codigo: int, start: date, end_inclusive: date) -> list[dict] | None:
    path = _get_sgs_cache_path(codigo, start, end_inclusive)
    if not path.exists():
        return None
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        # Se o cache tiver menos de 1 dia, considera válido
        if datetime.now() - mtime > timedelta(days=1):
            logger.info("SGS cache em disco expirado para código %d (%s a %s)", codigo, start, end_inclusive)
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Falha ao ler cache em disco do SGS: %s", e)
        return None


def _save_sgs_to_disk_cache(codigo: int, start: date, end_inclusive: date, data: list[dict]) -> None:
    path = _get_sgs_cache_path(codigo, start, end_inclusive)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Falha ao salvar cache em disco do SGS: %s", e)


def _fetch_sgs_json_um_trecho(
    codigo: int,
    start: date,
    end_inclusive: date,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    cached = _load_sgs_from_disk_cache(codigo, start, end_inclusive)
    if cached is not None:
        logger.info("SGS cache em DISCO hit: %d (%s a %s)", codigo, start, end_inclusive)
        rows = cached
    else:
        try:
            logger.info("SGS download: %d (%s a %s)", codigo, start, end_inclusive)
            sess = session or requests.Session()
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
            params = {
                "formato": "json",
                "dataInicial": as_ddmmyyyy(start),
                "dataFinal": as_ddmmyyyy(end_inclusive),
            }
            r = sess.get(url, params=params, timeout=120)
            r.raise_for_status()
            rows = r.json()
            _save_sgs_to_disk_cache(codigo, start, end_inclusive, rows)
        except Exception as e:
            # Fallback para o cache mesmo se expirado
            path = _get_sgs_cache_path(codigo, start, end_inclusive)
            if path.exists():
                logger.warning("Falha ao baixar da API SGS (%s). Usando cache expirado de fallback.", e)
                with open(path, "r", encoding="utf-8") as f:
                    rows = json.load(f)
            else:
                raise e

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["data_obs", "valor"]).astype({"valor": float})
    df["data_obs"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(
        df["valor"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    return df[["data_obs", "valor"]].sort_values("data_obs").reset_index(drop=True)


def fetch_sgs_json(
    codigo: int,
    start: date,
    end_inclusive: date,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Série temporal SGS (`api.bcb.gov.br`). Retorna duas colunas: data_obs, valor."""
    if start > end_inclusive:
        return pd.DataFrame(columns=["data_obs", "valor"]).astype({"valor": float})
    if (end_inclusive - start).days <= _SGS_INTERVALO_MAX_DIAS:
        return _fetch_sgs_json_um_trecho(
            codigo,
            start,
            end_inclusive,
            session=session,
        )

    partes: list[pd.DataFrame] = []
    trecho_ini = start
    delta = timedelta(days=_SGS_INTERVALO_MAX_DIAS)
    while trecho_ini <= end_inclusive:
        trecho_fim = min(end_inclusive, trecho_ini + delta)
        partes.append(
            _fetch_sgs_json_um_trecho(codigo, trecho_ini, trecho_fim, session=session),
        )
        trecho_ini = trecho_fim + timedelta(days=1)

    out = pd.concat(partes, ignore_index=True).drop_duplicates(subset=["data_obs"], keep="last")
    return out.sort_values("data_obs").reset_index(drop=True)


def preparar_selic_sgs11_diaria_para_painel(selic_diaria: pd.DataFrame) -> pd.DataFrame:
    """SGS série 11 (% a.d.) + aproximação % a.a. por composto em 252 dias úteis.

    ``valor`` do BC = taxa em % ao dia; usa-se
    ``((1 + valor/100)^252 - 1) * 100`` para comparar com mediana Focus (% a.a.).
    Conjunto oficial: https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic
    """
    if selic_diaria.empty:
        return pd.DataFrame(
            columns=["data_obs", "selic_sgs_pct_ad", "selic_sgs_pct_aa_aprox"],
        )
    d = selic_diaria.dropna(subset=["data_obs", "valor"]).copy()
    rd = d["valor"].to_numpy(dtype=float) / 100.0
    aa = (np.power(1.0 + rd, 252.0) - 1.0) * 100.0
    return (
        pd.DataFrame(
            {
                "data_obs": d["data_obs"],
                "selic_sgs_pct_ad": d["valor"],
                "selic_sgs_pct_aa_aprox": aa,
            },
        )
        .sort_values("data_obs")
        .reset_index(drop=True)
    )
