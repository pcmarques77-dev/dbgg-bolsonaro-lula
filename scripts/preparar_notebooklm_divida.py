"""Monta pacote de fontes para NotebookLM em output/DIVIDA/NotebookLM/."""
from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path

import pandas as pd


def _tabela_consolidada(base: Path) -> pd.DataFrame:
    dbgg = pd.read_csv(base / "comparacao_focus_dbgg_anual.csv")
    dlsp = pd.read_csv(base / "comparacao_focus_dlsp_anual.csv")
    reais = pd.read_csv(base / "previa_dlsp_reais.csv")

    m = dbgg.merge(dlsp, on="ano", how="outer", suffixes=("_dbgg", "_dlsp"))
    m = m.merge(
        reais[["ano", "dlsp_rs_trilhoes", "dlsp_yoy_pct_nominal"]],
        on="ano",
        how="left",
    )
    return (
        m[
            [
                "ano",
                "focus_ultima_mediana_pct_pib_dbgg",
                "dbgg_realizado_dez_pct_pib",
                "erro_focus_vs_realizado_pp_dbgg",
                "focus_ultima_mediana_pct_pib_dlsp",
                "dlsp_realizado_dez_pct_pib",
                "erro_focus_vs_realizado_pp_dlsp",
                "dlsp_rs_trilhoes",
                "dlsp_yoy_pct_nominal",
            ]
        ]
        .rename(
            columns={
                "focus_ultima_mediana_pct_pib_dbgg": "focus_dbgg_pct_pib",
                "dbgg_realizado_dez_pct_pib": "realizado_dbgg_pct_pib",
                "erro_focus_vs_realizado_pp_dbgg": "erro_dbgg_pp",
                "focus_ultima_mediana_pct_pib_dlsp": "focus_dlsp_pct_pib",
                "dlsp_realizado_dez_pct_pib": "realizado_dlsp_pct_pib",
                "erro_focus_vs_realizado_pp_dlsp": "erro_dlsp_pp",
            },
        )
        .sort_values("ano")
        .reset_index(drop=True)
    )


def _resumo_executivo(dbgg: pd.DataFrame, dlsp: pd.DataFrame, cons: pd.DataFrame) -> str:
    dbgg_c = dbgg.dropna(subset=["erro_focus_vs_realizado_pp"])
    dlsp_c = dlsp.dropna(subset=["erro_focus_vs_realizado_pp"])

    lines = [
        "# Resumo executivo — Dívida pública (Focus vs realizado)",
        "",
        f"Data de geração: {date.today().isoformat()}",
        "",
        "## Escopo",
        "",
        "Comparação entre expectativas do Boletim Focus (BCB) e dados realizados",
        "do Banco Central (SGS), para 2019–2026 (2026 apenas expectativa DBGG).",
        "",
        "## DBGG — Dívida Bruta do Governo Geral (% PIB)",
        "",
        f"- Anos com realizado: {len(dbgg_c)}",
        f"- Erro médio (Focus − realizado): {dbgg_c['erro_focus_vs_realizado_pp'].mean():.2f} p.p.",
        f"- Erro mediano: {dbgg_c['erro_focus_vs_realizado_pp'].median():.2f} p.p.",
        "- Padrão: Focus superestima a DBGG em todos os anos com realizado.",
        "",
        "### Por ano (DBGG)",
        "",
        "| Ano | Focus | Realizado | Erro (p.p.) |",
        "|-----|-------|-----------|-------------|",
    ]
    for _, r in dbgg.iterrows():
        foc = r.get("focus_ultima_mediana_pct_pib")
        real = r.get("dbgg_realizado_dez_pct_pib")
        err = r.get("erro_focus_vs_realizado_pp")
        foc_s = f"{foc:.1f}" if pd.notna(foc) else "—"
        real_s = f"{real:.1f}" if pd.notna(real) else "—"
        err_s = f"{err:+.1f}" if pd.notna(err) else "—"
        lines.append(f"| {int(r['ano'])} | {foc_s} | {real_s} | {err_s} |")

    lines.extend(
        [
            "",
            "## DLSP — Dívida Líquida do Setor Público (% PIB)",
            "",
            f"- Anos com realizado: {len(dlsp_c)}",
            f"- Erro médio: {dlsp_c['erro_focus_vs_realizado_pp'].mean():.2f} p.p.",
            f"- Erro mediano: {dlsp_c['erro_focus_vs_realizado_pp'].median():.2f} p.p.",
            "",
            "### Por ano (DLSP + R$)",
            "",
            "| Ano | Focus | Realizado | Erro (p.p.) | DLSP (R$ tri) |",
            "|-----|-------|-----------|-------------|---------------|",
        ],
    )
    for _, r in cons.iterrows():
        foc = r.get("focus_dlsp_pct_pib")
        real = r.get("realizado_dlsp_pct_pib")
        err = r.get("erro_dlsp_pp")
        tri = r.get("dlsp_rs_trilhoes")
        if pd.isna(foc) and pd.isna(real):
            continue
        foc_s = f"{foc:.1f}" if pd.notna(foc) else "—"
        real_s = f"{real:.1f}" if pd.notna(real) else "—"
        err_s = f"{err:+.1f}" if pd.notna(err) else "—"
        tri_s = f"{tri:.2f}" if pd.notna(tri) else "—"
        lines.append(f"| {int(r['ano'])} | {foc_s} | {real_s} | {err_s} | {tri_s} |")

    lines.extend(
        [
            "",
            "## Períodos analisados",
            "",
            "- **2019–2022**: erros DBGG maiores (~2,8–3,7 p.p.)",
            "- **2023–2026**: erros DBGG menores (~1,0–1,3 p.p.); 2026 sem realizado",
            "- **2019–2026**: visão completa da convergência das expectativas",
            "",
            "## Fontes",
            "",
            "- Focus: https://dadosabertos.bcb.gov.br/dataset/expectativas-mercado",
            "- DBGG realizada: SGS 13762",
            "- DLSP realizada: SGS 4513 (% PIB) e SGS 4478 (R$)",
        ],
    )
    return "\n".join(lines)


def _glossario() -> str:
    return "\n".join(
        [
            "GLOSSÁRIO — Conceitos de dívida pública usados neste pacote",
            "",
            "DBGG (Dívida Bruta do Governo Geral)",
            "  Endividamento bruto dos governos federal, estaduais e municipais.",
            "  Não inclui estatais. Inclui compromissadas do BC.",
            "  Focus: indicador 'Dívida bruta do governo geral'. Realizado: SGS 13762.",
            "",
            "DLSP (Dívida Líquida do Setor Público)",
            "  Saldo líquido (dívidas − créditos) do setor público consolidado + BC.",
            "  Inclui estatais (exc. Petrobras/Eletrobras). Mais amplo que DBGG.",
            "  Focus: 'Dívida líquida do setor público'. Realizado: SGS 4513 (% PIB), 4478 (R$).",
            "",
            "DPF (Dívida Pública Federal)",
            "  Estoque da dívida mobiliária federal (Tesouro Transparente).",
            "  NÃO está neste pacote; conceito diferente de DBGG e DLSP.",
            "",
            "Erro de previsão (p.p.)",
            "  focus_ultima_mediana − realizado_dez_ano, em pontos percentuais do PIB.",
            "  Positivo = Focus superestimou; negativo = subestimou.",
            "",
            "Metodologia comparativa",
            "  Para cada ano Y: última mediana Focus antes de 01/05/(Y+1)",
            "  vs fechamento de dezembro/Y no SGS.",
        ],
    )


def preparar_notebooklm(
    *,
    base_dir: Path = Path("output/DIVIDA"),
    out_dir: Path = Path("output/DIVIDA/NotebookLM"),
) -> Path:
    copias: list[tuple[Path, str]] = [
        (base_dir / "comparacao_focus_dbgg_anual.csv", "01-comparacao-dbgg-anual.csv"),
        (base_dir / "comparacao_focus_dlsp_anual.csv", "02-comparacao-dlsp-anual.csv"),
        (base_dir / "previa_dlsp_reais.csv", "03-dlsp-reais-anual.csv"),
        (base_dir / "periodos" / "2019-2022" / "comparacao_focus_dbgg.csv", "04-dbgg-periodo-2019-2022.csv"),
        (base_dir / "periodos" / "2023-2026" / "comparacao_focus_dbgg.csv", "05-dbgg-periodo-2023-2026.csv"),
        (base_dir / "periodos" / "2019-2026" / "comparacao_focus_dbgg.csv", "06-dbgg-periodo-2019-2026.csv"),
        (base_dir / "metadados_divida_dlsp.txt", "metadados-dlsp.txt"),
        (base_dir / "metadados_dbgg_anual.txt", "metadados-dbgg.txt"),
        (base_dir / "periodos" / "2019-2026" / "metadados_periodo.txt", "metadados-periodos.txt"),
    ]

    graficos: list[tuple[Path, str]] = [
        (base_dir / "periodos" / "2019-2026" / "comparacao_focus_dbgg.png", "comparacao_focus_dbgg_2019-2026.png"),
        (base_dir / "periodos" / "2019-2026" / "erro_previsao_dbgg.png", "erro_previsao_dbgg_2019-2026.png"),
        (base_dir / "periodos" / "2019-2026" / "dispersao_focus_dbgg.png", "dispersao_focus_dbgg_2019-2026.png"),
        (base_dir / "periodos" / "2019-2022" / "comparacao_focus_dbgg.png", "comparacao_focus_dbgg_2019-2022.png"),
        (base_dir / "periodos" / "2023-2026" / "comparacao_focus_dbgg.png", "comparacao_focus_dbgg_2023-2026.png"),
        (base_dir / "comparacao_focus_dlsp_anual.png", "comparacao_focus_dlsp_anual.png"),
        (base_dir / "erro_previsao_dlsp_anual.png", "erro_previsao_dlsp_anual.png"),
    ]

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    graf_dir = out_dir / "graficos"
    graf_dir.mkdir()

    for src, nome in copias:
        if not src.is_file():
            raise FileNotFoundError(f"Arquivo ausente: {src}")
        shutil.copy2(src, out_dir / nome)

    for src, nome in graficos:
        if src.is_file():
            shutil.copy2(src, graf_dir / nome)

    cons = _tabela_consolidada(base_dir)
    cons.to_csv(out_dir / "07-tabela-consolidada-dbgg-dlsp.csv", index=False)

    dbgg = pd.read_csv(base_dir / "comparacao_focus_dbgg_anual.csv")
    dlsp = pd.read_csv(base_dir / "comparacao_focus_dlsp_anual.csv")

    (out_dir / "00-glossario-conceitos.txt").write_text(_glossario(), encoding="utf-8")
    (out_dir / "09-resumo-executivo.md").write_text(
        _resumo_executivo(dbgg, dlsp, cons),
        encoding="utf-8",
    )

    arquivos = sorted(
        [p.name for p in out_dir.iterdir() if p.is_file()]
        + [f"graficos/{p.name}" for p in graf_dir.iterdir() if p.is_file()],
    )
    (out_dir / "08-guia-notebooklm.md").write_text(
        "\n".join(
            [
                "# Guia — Pacote NotebookLM (Dívida pública)",
                "",
                "Upload desta pasta (ou dos arquivos abaixo) no NotebookLM.",
                "",
                "## Arquivos",
                "",
                *[f"- `{a}`" for a in arquivos],
                "",
                "## Ordem sugerida",
                "",
                "1. `00-glossario-conceitos.txt`",
                "2. `09-resumo-executivo.md`",
                "3. `07-tabela-consolidada-dbgg-dlsp.csv`",
                "4. CSVs numerados (01–06)",
                "5. `graficos/` — visualizações",
                "6. `metadados-*.txt`",
            ],
        ),
        encoding="utf-8",
    )
    (out_dir / "INDICE.txt").write_text("\n".join(arquivos), encoding="utf-8")

    return out_dir


def main() -> None:
    p = argparse.ArgumentParser(description="Prepara pacote NotebookLM em output/DIVIDA/NotebookLM/")
    p.add_argument("--base-dir", type=Path, default=Path("output/DIVIDA"))
    p.add_argument("--out-dir", type=Path, default=Path("output/DIVIDA/NotebookLM"))
    args = p.parse_args()

    out = preparar_notebooklm(base_dir=args.base_dir, out_dir=args.out_dir)
    n = sum(1 for _ in out.rglob("*") if _.is_file())
    print(f"Pacote NotebookLM: {out.resolve()} ({n} arquivos)")


if __name__ == "__main__":
    main()
