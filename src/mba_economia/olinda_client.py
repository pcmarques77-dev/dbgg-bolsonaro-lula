from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Erros típicamente transitórios do gateway Olinda/BC ou rate limit superficial
_OLINDA_RETRY_STATUS = frozenset({429, 502, 503, 504})
_OLINDA_MAX_ATTEMPT = 7


def _get_odata_page(
    sess: requests.Session,
    url: str,
    *,
    params: dict[str, str],
    timeout: int,
) -> requests.Response:
    """GET com backoff exponencial ante 429/502/503/504 e falhas de rede."""
    backoff_s = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
    last_exc: BaseException | None = None

    for i in range(min(_OLINDA_MAX_ATTEMPT, len(backoff_s))):
        try:
            if i > 0:
                time.sleep(backoff_s[i])
            r = sess.get(url, params=params, timeout=timeout)
            if r.status_code in _OLINDA_RETRY_STATUS:
                last_exc = requests.HTTPError(
                    f"{r.status_code} {r.reason}",
                    response=r,
                )
                continue
            r.raise_for_status()
            return r
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.exceptions.ChunkedEncodingError,
        ) as e:
            last_exc = e
            continue

    if isinstance(last_exc, requests.HTTPError) and last_exc.response is not None:
        last_exc.response.raise_for_status()
    if isinstance(last_exc, BaseException):
        raise last_exc
    raise RuntimeError("_get_odata_page: unreachable")


def _get_disk_cache_path(cache_key: tuple[str, str, str, str]) -> Path:
    key_str = "|".join(cache_key)
    h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
    root_dir = Path(__file__).resolve().parents[2]
    cache_dir = root_dir / "v2" / ".cache"
    if not cache_dir.exists():
        cache_dir = root_dir / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"olinda_{h}.json"


def _load_from_disk_cache(cache_key: tuple[str, str, str, str]) -> list[dict[str, Any]] | None:
    path = _get_disk_cache_path(cache_key)
    if not path.exists():
        return None
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if datetime.now() - mtime > timedelta(days=365):
            logger.info("Olinda cache em disco expirado para chave: %s", cache_key[1])
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Falha ao ler cache em disco: %s", e)
        return None


def _save_to_disk_cache(cache_key: tuple[str, str, str, str], data: list[dict[str, Any]]) -> None:
    path = _get_disk_cache_path(cache_key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Falha ao salvar cache em disco: %s", e)


def _session_cache(sess: requests.Session) -> dict[tuple[str, str, str, str], list[dict[str, Any]]]:
    cache = getattr(sess, "_mba_olinda_cache", None)
    if cache is None:
        cache = {}
        setattr(sess, "_mba_olinda_cache", cache)
    return cache


def fetch_odata_resource(
    base_url: str,
    entity: str,
    *,
    filt: str | None = None,
    orderby: str | None = None,
    top: int = 10_000,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Percorre paginação $skip até esgotar `value`.

    Parameters
    ----------
    base_url
        Ex.: https://.../odata (sem barra final)
    filt
        Filtro OData ($filter); codifique caracteres especiais se necessário.
    """
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", "mba-economia-fipe/0.1")
    cache_key = (base_url.rstrip("/"), entity, filt or "", orderby or "")
    
    # 1. Verifica cache em memória da sessão
    cached_mem = _session_cache(sess).get(cache_key)
    if cached_mem is not None:
        logger.info("Olinda cache em memória hit: %s ($filter=%s)", entity, filt or "(none)")
        return cached_mem

    # 2. Verifica cache em disco
    cached_disk = _load_from_disk_cache(cache_key)
    if cached_disk is not None:
        logger.info("Olinda cache em DISCO hit: %s ($filter=%s)", entity, filt or "(none)")
        # Alimenta o cache de memória da sessão
        _session_cache(sess)[cache_key] = cached_disk
        return cached_disk

    logger.info("Olinda download: %s ($filter=%s)", entity, filt or "(none)")
    out: list[dict[str, Any]] = []
    skip = 0
    while True:
        params = {
            "$format": "json",
            "$top": str(top),
            "$skip": str(skip),
        }
        if filt:
            params["$filter"] = filt
        if orderby:
            params["$orderby"] = orderby
        url = f"{base_url.rstrip('/')}/{entity}"
        r = _get_odata_page(sess, url, params=params, timeout=120)
        js = r.json()
        chunk = js.get("value") or []
        out.extend(chunk)
        if len(chunk) < top:
            break
        skip += top
        if skip % 50_000 == 0:
            logger.info("Olinda %s: %s linhas acumuladas...", entity, len(out))

    logger.info("Olinda %s: download concluído (%s linhas).", entity, len(out))
    
    # Salva nos dois caches
    _session_cache(sess)[cache_key] = out
    _save_to_disk_cache(cache_key, out)
    return out
