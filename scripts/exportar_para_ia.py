"""Exportação de dados para uso em ferramentas de IA externas.

Gera dois pacotes:
  1. NotebookLM  → relatorio_focus_ibge_notebooklm.md  (narrativa + tabelas Markdown)
  2. Gemini      → pasta gemini/ com CSVs limpos e legíveis em português

Uso:
    python v2/scripts/exportar_para_ia.py

Saída: output/exportacao_ia/
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parents[1]          # expectativas-macro-2019-2026/
DATA_DIR  = ROOT / "public" / "data"
OUT_DIR   = ROOT / "output" / "exportacao_ia"
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "gemini").mkdir(exist_ok=True)

HOJE = date.today().strftime("%d/%m/%Y")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load(nome: str) -> pd.DataFrame:
    path = DATA_DIR / nome
    if not path.exists():
        print(f"[AVISO] Arquivo nao encontrado: {path}. Execute npm run sync-data primeiro.")
        return pd.DataFrame()
    return pd.read_csv(path, sep=";", decimal=",")


def pct(v: float, casas: int = 2) -> str:
    return f"{v:+.{casas}f}%" if pd.notna(v) else "N/D"


def pp(v: float, casas: int = 2) -> str:
    return f"{v:+.{casas}f} p.p." if pd.notna(v) else "N/D"


def mae(series: pd.Series) -> float:
    return series.dropna().abs().mean()


def tabela_md(df: pd.DataFrame) -> str:
    """Converte DataFrame para tabela Markdown."""
    header = "| " + " | ".join(df.columns) + " |"
    sep    = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows   = "\n".join(
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in df.itertuples(index=False)
    )
    return f"{header}\n{sep}\n{rows}"


# ─────────────────────────────────────────────────────────────────────────────
# Carrega dados
# ─────────────────────────────────────────────────────────────────────────────

ipca_mensal     = load("comparacao_ipca_mensal.csv")
ipca_anual      = load("comparacao_ipca_ano_fechamento.csv")
selic_mensal    = load("comparacao_selic_mensal.csv")
pib_anual       = load("comparacao_pib_ano_fechamento.csv")

# Calcula selic_anual (fechamento) a partir de comparacao_selic_ano_calendario.csv
selic_cal = load("comparacao_selic_ano_calendario.csv")
if not selic_cal.empty:
    selic_cal["ano_ref"] = pd.to_numeric(selic_cal["ano_ref"], errors="coerce")
    selic_cal["selic_focus_pct"] = pd.to_numeric(selic_cal["selic_focus_pct"], errors="coerce")
    selic_cal["selic_sgs_pct_aa_aprox"] = pd.to_numeric(selic_cal["selic_sgs_pct_aa_aprox"], errors="coerce")
    
    rows = []
    for ano, grp in selic_cal.groupby("ano_ref"):
        if pd.isna(ano):
            continue
        grp_sorted = grp.sort_values("survey_date_previsao")
        first = grp_sorted.iloc[0]
        last = grp_sorted.iloc[-1]
        
        realized = last["selic_sgs_pct_aa_aprox"]
        focus_init = first["selic_focus_pct"]
        erro = focus_init - realized if pd.notna(realized) and pd.notna(focus_init) else float("nan")
        
        rows.append({
            "ano_ref": int(ano),
            "survey_date_primeira_previsao": first["survey_date_previsao"],
            "selic_focus_ano_pct": focus_init,
            "selic_sgs_pct_aa_aprox": realized,
            "erro_prev_menos_real_pp": erro
        })
    selic_anual = pd.DataFrame(rows)
else:
    selic_anual = pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# PACOTE 1 — NOTEBOOKLM: Relatório Markdown narrativo
# ─────────────────────────────────────────────────────────────────────────────

def build_notebooklm() -> str:
    """Monta o relatório completo em Markdown para upload no NotebookLM."""

    linhas: list[str] = []

    def h(nivel: int, texto: str) -> None:
        linhas.append(f"\n{'#' * nivel} {texto}\n")

    def p(texto: str) -> None:
        linhas.append(texto + "\n")

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    linhas.append(f"# Relatório: Expectativas Focus × Realizado Macroeconômico (Brasil)\n")
    p(f"**Gerado em:** {HOJE}  ")
    p("**Fonte:** Banco Central do Brasil (Boletim Focus — API Olinda), IBGE (SIDRA) e BCB (SGS).  ")
    p("**Propósito:** Base de conhecimento para análise de acurácia de previsões macroeconômicas brasileiras (2019–2025).  ")
    p("**Autor:** Projeto MBA Economia FIPE — Análise Focus × BCB × IBGE.")

    # ── Metodologia ───────────────────────────────────────────────────────────
    h(2, "Metodologia e Fontes")
    p("""
O **Boletim Focus** é o relatório semanal do Banco Central do Brasil que consolida as expectativas
de mercado para os principais indicadores macroeconômicos brasileiros. É divulgado toda segunda-feira,
com dados coletados até a sexta-feira anterior.

Este conjunto de dados compara duas grandezas para cada indicador:

- **Expectativa Focus:** mediana das projeções dos analistas de mercado coletadas no **primeiro
  boletim Focus publicado no ano de referência** (normalmente a primeira segunda-feira de janeiro).
  Essa é a "aposta inicial" do mercado no início do ano.
- **Realizado (Oficial):** valor efetivamente divulgado pelo órgão competente ao final do período.

### Regras de alinhamento temporal
- **IPCA mensal:** expectativa = último boletim Focus antes do início do mês de referência. Realizado = SIDRA 1737.
- **IPCA anual:** expectativa = primeiro boletim Focus do ano Y. Realizado = acumulado IPCA jan–dez (IBGE).
- **Selic anual:** expectativa = primeiro boletim Focus do ano Y. Realizado = taxa Selic anualizada no fechamento de dezembro (SGS série 11).
- **PIB anual:** expectativa = primeiro boletim Focus do ano Y. Realizado = variação acumulada em 4 trimestres do 4º trimestre do IBGE (SIDRA 5932).

### Métricas de erro
- **Erro (p.p.):** Focus − Realizado. Positivo = mercado superestimou; Negativo = mercado subestimou.
- **MAE:** Erro Médio Absoluto (mean absolute error) — mede a magnitude média dos erros.
""".strip())

    # ── IPCA Mensal ───────────────────────────────────────────────────────────
    h(2, "IPCA — Inflação Mensal")
    p("""
O **IPCA (Índice Nacional de Preços ao Consumidor Amplo)** é o índice oficial de inflação do Brasil,
medido mensalmente pelo IBGE. É a meta de inflação do Banco Central.
""".strip())

    if not ipca_mensal.empty:
        n = len(ipca_mensal)
        mae_val = mae(ipca_mensal["erro_prev_menos_real_pp"])
        vies = ipca_mensal["erro_prev_menos_real_pp"].dropna().mean()
        anos = f"{str(ipca_mensal['ref_yyyymm'].iloc[0])[:4]} a {str(ipca_mensal['ref_yyyymm'].iloc[-1])[:4]}"

        p(f"**Período:** {anos}  |  **n =** {n} meses  |  **MAE =** {mae_val:.3f} p.p.  |  **Viés médio =** {vies:+.3f} p.p.")

        # Tabela anual agregada
        ipca_mensal["ano"] = ipca_mensal["ref_yyyymm"].astype(str).str[:4].astype(int)
        tab_anual = ipca_mensal.groupby("ano").agg(
            IPCA_Focus_Media=("ipca_focus_med_mensal_pct", "mean"),
            IPCA_IBGE_Media=("ipca_ibge_mensal_pct", "mean"),
            MAE_pp=("erro_prev_menos_real_pp", lambda x: x.abs().mean()),
            Vies_pp=("erro_prev_menos_real_pp", "mean"),
        ).round(3).reset_index()
        tab_anual.columns = ["Ano", "Focus Médio (%)", "IBGE Médio (%)", "MAE (p.p.)", "Viés (p.p.)"]

        h(3, "Estatísticas Anuais Agregadas — IPCA Mensal")
        linhas.append(tabela_md(tab_anual))

        h(3, "Série Completa — IPCA Mensal (Focus vs IBGE)")
        tab = ipca_mensal[["ref_yyyymm", "survey_date_previsao",
                            "ipca_focus_med_mensal_pct", "ipca_ibge_mensal_pct",
                            "erro_prev_menos_real_pp"]].copy()
        tab.columns = ["Mês (AAAAMM)", "Data Survey Focus", "Focus Mediana (%)", "IBGE Realizado (%)", "Erro (p.p.)"]
        linhas.append(tabela_md(tab))

    # ── IPCA Anual ────────────────────────────────────────────────────────────
    h(2, "IPCA — Comparação Anual (Expectativa Inicial vs Realizado)")
    p("""
Comparação da expectativa do mercado no **início do ano** (primeiro boletim Focus de janeiro)
contra o **IPCA acumulado no ano** (janeiro a dezembro), divulgado pelo IBGE.
Esta análise revela o viés estrutural das previsões de início de ano.
""".strip())

    if not ipca_anual.empty:
        mae_val = mae(ipca_anual["erro_prev_menos_real_pp"])
        vies    = ipca_anual["erro_prev_menos_real_pp"].dropna().mean()
        p(f"**MAE =** {mae_val:.3f} p.p.  |  **Viés médio =** {vies:+.3f} p.p.  |  **n =** {len(ipca_anual)} anos")

        tab = ipca_anual.copy()
        tab.columns = ["Ano", "Data 1ª Previsão Focus", "IPCA Focus Inicial (%)", "IPCA IBGE Realizado (%)", "Erro (p.p.)"]
        linhas.append(tabela_md(tab))

        p(f"\n**Interpretação:** Viés de {vies:+.3f} p.p. indica que, em média, o mercado "
          f"{'superestima' if vies > 0 else 'subestima'} o IPCA anual na previsão de início de ano.")

    # ── Selic Anual ───────────────────────────────────────────────────────────
    h(2, "Selic — Comparação Anual (Expectativa Inicial vs Realizado)")
    p("""
A **Taxa Selic** é a taxa básica de juros da economia brasileira, definida pelo Copom (Comitê de
Política Monetária do BCB). A comparação avalia a expectativa do início do ano contra a Selic
anualizada efetiva no fechamento de dezembro (série SGS 11 do BCB).
""".strip())

    if not selic_anual.empty:
        mae_val = mae(selic_anual["erro_prev_menos_real_pp"])
        vies    = selic_anual["erro_prev_menos_real_pp"].dropna().mean()
        p(f"**MAE =** {mae_val:.3f} p.p.  |  **Viés médio =** {vies:+.3f} p.p.  |  **n =** {len(selic_anual)} anos")

        tab = selic_anual.copy()
        tab.columns = ["Ano", "Data 1ª Previsão Focus", "Selic Focus Inicial (%)", "Selic SGS Realizada (%)", "Erro (p.p.)"]
        linhas.append(tabela_md(tab))

        p(f"\n**Interpretação:** Viés de {vies:+.3f} p.p. indica que o mercado tende a "
          f"{'superestimar' if vies > 0 else 'subestimar'} a Selic ao início do ano. "
          "Erros grandes em 2020–2022 refletem choques não antecipados (pandemia, alta da inflação).")

    # ── PIB Anual ─────────────────────────────────────────────────────────────
    h(2, "PIB — Comparação Anual (Expectativa Inicial vs Realizado)")
    p("""
O **PIB (Produto Interno Bruto)** é a medida de atividade econômica. Aqui é usado a variação
percentual acumulada em quatro trimestres no 4º trimestre (taxa 4T/4T anterior), divulgada pelo
IBGE nas Contas Nacionais Trimestrais (SIDRA 5932). Essa é a métrica anual padrão do mercado.
""".strip())

    if not pib_anual.empty:
        mae_val = mae(pib_anual["erro_prev_menos_real_pp"])
        vies    = pib_anual["erro_prev_menos_real_pp"].dropna().mean()
        p(f"**MAE =** {mae_val:.3f} p.p.  |  **Viés médio =** {vies:+.3f} p.p.  |  **n =** {len(pib_anual)} anos")

        tab = pib_anual[["ano_ref", "survey_date_previsao", "pib_focus_ano_pct", "pib_ibge_4tri_yoy_pct", "erro_prev_menos_real_pp"]].copy()
        tab.columns = ["Ano", "Data 1ª Previsão Focus", "PIB Focus Inicial (%)", "PIB IBGE Realizado 4T (%)", "Erro (p.p.)"]
        linhas.append(tabela_md(tab))

        p(f"\n**Interpretação:** Viés de {vies:+.3f} p.p. indica que o mercado tende a "
          f"{'superestimar' if vies > 0 else 'subestimar'} o crescimento do PIB. "
          "O erro de 2020 (pandemia) é um outlier extremo e deve ser tratado separadamente nas análises.")

    # ── Sumário comparativo ────────────────────────────────────────────────────
    h(2, "Sumário Comparativo de Acurácia")
    p("Comparação do MAE entre os três indicadores no período completo disponível:")

    resumo_rows = []
    if not ipca_anual.empty:
        resumo_rows.append([
            "IPCA Anual", f"{len(ipca_anual)} anos",
            f"{mae(ipca_anual['erro_prev_menos_real_pp']):.3f}",
            f"{ipca_anual['erro_prev_menos_real_pp'].mean():+.3f}",
        ])
    if not selic_anual.empty:
        resumo_rows.append([
            "Selic Anual", f"{len(selic_anual)} anos",
            f"{mae(selic_anual['erro_prev_menos_real_pp']):.3f}",
            f"{selic_anual['erro_prev_menos_real_pp'].mean():+.3f}",
        ])
    if not pib_anual.empty:
        resumo_rows.append([
            "PIB Anual", f"{len(pib_anual)} anos",
            f"{mae(pib_anual['erro_prev_menos_real_pp']):.3f}",
            f"{pib_anual['erro_prev_menos_real_pp'].mean():+.3f}",
        ])

    resumo_df = pd.DataFrame(resumo_rows, columns=["Indicador", "Período", "MAE (p.p.)", "Viés Médio (p.p.)"])
    linhas.append(tabela_md(resumo_df))

    p("""
**Notas:**
- MAE: Erro Médio Absoluto. Quanto menor, mais acurada a previsão.
- Viés positivo: mercado sistematicamente otimista (previu mais do que ocorreu).
- Viés negativo: mercado sistematicamente pessimista.
- Período inclui anos com choques excepcionais (2020: pandemia; 2021–2022: inflação pós-pandemia).
""")

    # ── Glossário ──────────────────────────────────────────────────────────────
    h(2, "Glossário de Variáveis")
    p("""
| Variável | Descrição | Unidade |
|---|---|---|
| ref_yyyymm | Mês de referência no formato AAAAMM | — |
| survey_date_previsao | Data do boletim Focus utilizado | AAAA-MM-DD |
| survey_date_primeira_previsao | Data do primeiro boletim Focus do ano | AAAA-MM-DD |
| ipca_focus_med_mensal_pct | Mediana Focus para IPCA do mês | % |
| ipca_ibge_mensal_pct | IPCA mensal realizado (IBGE SIDRA 1737) | % |
| ipca_focus_ano_pct | Mediana Focus para IPCA acumulado no ano | % |
| ipca_ibge_acum_ano_dez_pct | IPCA acumulado jan–dez (IBGE) | % |
| selic_focus_pct | Mediana Focus para Selic na reunião Copom | % a.a. |
| selic_focus_ano_pct | Mediana Focus para Selic no fechamento do ano | % a.a. |
| selic_sgs_pct_aa_aprox | Selic efetiva anualizada em dezembro (SGS 11) | % a.a. |
| pib_focus_ano_pct | Mediana Focus para crescimento do PIB no ano | % |
| pib_ibge_4tri_yoy_pct | PIB acumulado em 4T no 4º trimestre (SIDRA 5932) | % |
| erro_prev_menos_real_pp | Erro = Focus − Realizado | p.p. |
| MAE | Erro Médio Absoluto | p.p. |
""".strip())

    return "\n".join(linhas)


# ─────────────────────────────────────────────────────────────────────────────
# PACOTE 2 — GEMINI: CSVs limpos com cabeçalhos em português
# ─────────────────────────────────────────────────────────────────────────────

def build_gemini() -> None:
    """Gera CSVs com nomes de colunas legíveis para uso no Gemini Advanced."""

    enc = "utf-8-sig"  # BOM para compatibilidade com Excel/upload

    # 1. IPCA Mensal
    if not ipca_mensal.empty:
        df = ipca_mensal.copy()
        df["mes_referencia"] = df["ref_yyyymm"].astype(str).apply(
            lambda s: f"{s[4:6]}/{s[:4]}"
        )
        out = df[[
            "mes_referencia", "survey_date_previsao",
            "ipca_focus_med_mensal_pct", "ipca_ibge_mensal_pct",
            "erro_prev_menos_real_pp", "ipca_focus_mensal_nresp",
        ]].copy()
        out.columns = [
            "Mes de Referencia (MM/AAAA)", "Data do Boletim Focus",
            "IPCA Focus - Mediana (%)", "IPCA IBGE Realizado (%)",
            "Erro de Previsao (p.p.)", "Numero de Respondentes Focus",
        ]
        out.to_csv(OUT_DIR / "gemini" / "ipca_mensal_focus_vs_ibge.csv", index=False, encoding=enc)
        print("[OK] ipca_mensal_focus_vs_ibge.csv")

    # 2. IPCA Anual
    if not ipca_anual.empty:
        out = ipca_anual.copy()
        out.columns = [
            "Ano de Referencia", "Data da 1a Previsao Focus (inicio do ano)",
            "IPCA Focus - Expectativa Inicial (%)", "IPCA IBGE Acumulado jan-dez (%)",
            "Erro de Previsao (p.p.)",
        ]
        out.to_csv(OUT_DIR / "gemini" / "ipca_anual_focus_vs_ibge.csv", index=False, encoding=enc)
        print("[OK] ipca_anual_focus_vs_ibge.csv")

    # 3. Selic por Reuniao Copom
    if not selic_mensal.empty:
        df = selic_mensal.copy()
        df["mes_reuniao"] = df["ref_yyyymm"].astype(str).apply(
            lambda s: f"{s[4:6]}/{s[:4]}"
        )
        out = df[[
            "mes_reuniao", "reuniao_focus", "survey_date_previsao",
            "selic_focus_pct", "selic_sgs_pct_aa_aprox",
            "erro_prev_menos_real_pp", "selic_focus_nresp",
        ]].copy()
        out.columns = [
            "Mes da Reuniao Copom (MM/AAAA)", "Codigo da Reuniao", "Data do Boletim Focus",
            "Selic Focus - Mediana (% a.a.)", "Selic SGS Realizada - Dezembro (% a.a.)",
            "Erro de Previsao (p.p.)", "Numero de Respondentes Focus",
        ]
        out.to_csv(OUT_DIR / "gemini" / "selic_copom_focus_vs_realizado.csv", index=False, encoding=enc)
        print("[OK] selic_copom_focus_vs_realizado.csv")

    # 4. Selic Anual
    if not selic_anual.empty:
        out = selic_anual.copy()
        out.columns = [
            "Ano de Referencia", "Data da 1a Previsao Focus (inicio do ano)",
            "Selic Focus - Expectativa Inicial (% a.a.)", "Selic SGS Realizada - Dezembro (% a.a.)",
            "Erro de Previsao (p.p.)",
        ]
        out.to_csv(OUT_DIR / "gemini" / "selic_anual_focus_vs_realizado.csv", index=False, encoding=enc)
        print("[OK] selic_anual_focus_vs_realizado.csv")

    # 5. PIB Anual
    if not pib_anual.empty:
        out = pib_anual[["ano_ref", "survey_date_previsao", "pib_focus_ano_pct", "pib_ibge_4tri_yoy_pct", "erro_prev_menos_real_pp"]].copy()
        out.columns = [
            "Ano de Referencia", "Data da 1a Previsao Focus (inicio do ano)",
            "PIB Focus - Expectativa Inicial (%)", "PIB IBGE Realizado - 4T acumulado em 4 trimestres (%)",
            "Erro de Previsao (p.p.)",
        ]
        out.to_csv(OUT_DIR / "gemini" / "pib_anual_focus_vs_ibge.csv", index=False, encoding=enc)
        print("[OK] pib_anual_focus_vs_ibge.csv")

    # 6. Arquivo consolidado de resumo anual (todos os indicadores)
    rows = []
    anos = sorted(set(
        (ipca_anual["ano_ref"].tolist() if not ipca_anual.empty else []) +
        (selic_anual["ano_ref"].tolist() if not selic_anual.empty else []) +
        (pib_anual["ano_ref"].tolist()   if not pib_anual.empty  else [])
    ))
    ipca_idx  = ipca_anual.set_index("ano_ref")  if not ipca_anual.empty  else pd.DataFrame()
    selic_idx = selic_anual.set_index("ano_ref") if not selic_anual.empty else pd.DataFrame()
    pib_idx   = pib_anual.set_index("ano_ref")   if not pib_anual.empty   else pd.DataFrame()

    for ano in anos:
        row = {"Ano": ano}
        if ano in ipca_idx.index:
            r = ipca_idx.loc[ano]
            row["IPCA Focus Inicial (%)"]    = round(r["ipca_focus_ano_pct"], 2)
            row["IPCA IBGE Realizado (%)"]   = round(r["ipca_ibge_acum_ano_dez_pct"], 2)
            row["IPCA Erro (p.p.)"]          = round(r["erro_prev_menos_real_pp"], 2)
        if ano in selic_idx.index:
            r = selic_idx.loc[ano]
            row["Selic Focus Inicial (%)"]   = round(r["selic_focus_ano_pct"], 2)
            row["Selic SGS Realizada (%)"]   = round(r["selic_sgs_pct_aa_aprox"], 2)
            row["Selic Erro (p.p.)"]         = round(r["erro_prev_menos_real_pp"], 2)
        if ano in pib_idx.index:
            r = pib_idx.loc[ano]
            row["PIB Focus Inicial (%)"]     = round(r["pib_focus_ano_pct"], 2)
            row["PIB IBGE Realizado (%)"]    = round(r["pib_ibge_4tri_yoy_pct"], 2)
            row["PIB Erro (p.p.)"]           = round(r["erro_prev_menos_real_pp"], 2)
        rows.append(row)

    pd.DataFrame(rows).to_csv(
        OUT_DIR / "gemini" / "resumo_anual_todos_indicadores.csv",
        index=False, encoding=enc
    )
    print("[OK] resumo_anual_todos_indicadores.csv")


# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=== Exportando dados para IAs externas ===\n")

    # NotebookLM
    print("[1/2] Gerando relatorio Markdown para NotebookLM...")
    md = build_notebooklm()
    out_md = OUT_DIR / "relatorio_focus_ibge_notebooklm.md"
    out_md.write_text(md, encoding="utf-8")
    print(f"[OK] {out_md}")

    # Gemini
    print("\n[2/2] Gerando CSVs limpos para Gemini Advanced...")
    build_gemini()

    print(f"""
=== Exportacao concluida! ===

NotebookLM:
  Arquivo: output/exportacao_ia/relatorio_focus_ibge_notebooklm.md
  Como usar: Faca upload diretamente no NotebookLM (aceita .md e .txt)
  Dica: converta para PDF via VS Code (Ctrl+Shift+P -> Markdown: Open Preview)
        ou via Pandoc: pandoc relatorio_focus_ibge_notebooklm.md -o relatorio.pdf

Gemini Advanced:
  Pasta: output/exportacao_ia/gemini/
  Arquivos:
    - resumo_anual_todos_indicadores.csv   <- comece por aqui
    - ipca_mensal_focus_vs_ibge.csv
    - ipca_anual_focus_vs_ibge.csv
    - selic_copom_focus_vs_realizado.csv
    - selic_anual_focus_vs_realizado.csv
    - pib_anual_focus_vs_ibge.csv
  Como usar: Anexe o CSV na conversa e pergunte diretamente ao Gemini.
""")


if __name__ == "__main__":
    main()
