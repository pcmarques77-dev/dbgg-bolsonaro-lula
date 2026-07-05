"""Gera dist/port-divida/ para copiar à máquina principal (Git)."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SRC_NOVOS = [
    "src/mba_economia/bcb_dbgg_sgs13762.py",
    "src/mba_economia/bcb_dlsp_sgs4513.py",
    "src/mba_economia/divida_dbgg_compare.py",
    "src/mba_economia/divida_dlsp_compare.py",
    "src/mba_economia/divida_focus.py",
    "src/mba_economia/figures_divida.py",
]

SCRIPTS = [
    "scripts/exportar_dbgg_anual.py",
    "scripts/exportar_divida_dlsp.py",
    "scripts/comparativos_dbgg_periodos.py",
    "scripts/graficos_divida_dlsp.py",
    "scripts/previa_dlsp_reais.py",
    "scripts/previa_dbgg_2025.py",
    "scripts/preparar_notebooklm_divida.py",
]

DOCS = [
    "output/DIVIDA/HANDOFF.md",
    "docs/PORTAR-DIVIDA-MAC-PRINCIPAL.md",
]

INTEGRAR_CONFIG = """
# Colar em src/mba_economia/config.py (SeriesConfig), após sidra_pib_vol_anual_dias_apos_31dez:

    # DLSP (% PIB), setor público consolidado
    sgs_codigo_dlsp_pct_pib: int = 4513
    dlsp_anual_divulgacao_mes_ano_seguinte: int = 5
    dlsp_anual_divulgacao_dia_mes: int = 1

    # DBGG (% PIB), governo geral (metodologia a partir de 2008)
    sgs_codigo_dbgg_pct_pib: int = 13762
"""


def empacotar(out: Path = ROOT / "dist" / "port-divida") -> Path:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for rel in SRC_NOVOS + SCRIPTS:
        src = ROOT / rel
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    for rel in DOCS:
        src = ROOT / rel
        if src.is_file():
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    (out / "integrar").mkdir(parents=True, exist_ok=True)
    (out / "integrar" / "config_divida.txt").write_text(INTEGRAR_CONFIG.strip() + "\n", encoding="utf-8")
    (out / "LEIA-ME.txt").write_text(
        (ROOT / "docs" / "PORTAR-DIVIDA-MAC-PRINCIPAL.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    # NotebookLM opcional (sem output/ pesado)
    nb = ROOT / "output" / "DIVIDA" / "NotebookLM"
    if nb.is_dir():
        shutil.copytree(nb, out / "output" / "DIVIDA" / "NotebookLM")

    manifest = []
    for p in sorted(out.rglob("*")):
        if p.is_file():
            manifest.append(str(p.relative_to(out)))
    (out / "MANIFEST.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=ROOT / "dist" / "port-divida")
    args = p.parse_args()
    out = empacotar(args.out)
    n = sum(1 for _ in out.rglob("*") if _.is_file())
    print(f"Pacote: {out.resolve()} ({n} arquivos)")
    print("Copie a pasta dist/port-divida para a Mac principal e siga LEIA-ME.txt")


if __name__ == "__main__":
    main()
