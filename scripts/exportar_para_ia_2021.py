"""Exportação especial dos dados de IPCA de 2021 para NotebookLM (.md) e Gemini (.csv).

Uso:
    python v2/scripts/exportar_para_ia_2021.py
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

# Caminhos
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "v2" / "pib-focus-viz" / "public" / "data"
OUT_DIR = ROOT / "output" / "exportacao_ia_2021"
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "gemini").mkdir(exist_ok=True)


def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    return pd.read_csv(path, sep=";", decimal=",")


def to_markdown_table(df: pd.DataFrame) -> str:
    header = "| " + " | ".join(df.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = "\n".join(
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in df.itertuples(index=False)
    )
    return f"{header}\n{sep}\n{rows}"


def main() -> None:
    print("=== Exportando dados de IPCA de 2021 para NotebookLM e Gemini ===")

    # 1. Carrega os datasets do IPCA
    df_mensal_final = load_csv("comparacao_ipca_mensal.csv")
    df_mensal_inicial = load_csv("comparacao_ipca_mensal_inicial.csv")
    df_anual_cal = load_csv("comparacao_ipca_ano_calendario.csv")
    df_anual_fech = load_csv("comparacao_ipca_ano_fechamento.csv")

    # 2. Filtra apenas para o ano de 2021
    # IPCA Mensal Final
    mensal_final_2021 = df_mensal_final[
        df_mensal_final["ref_yyyymm"].astype(str).str.startswith("2021")
    ].copy()
    mensal_final_2021["mes_referencia"] = mensal_final_2021["ref_yyyymm"].astype(str).apply(
        lambda s: f"{s[4:6]}/{s[:4]}"
    )
    mensal_final_2021 = mensal_final_2021[[
        "mes_referencia", "survey_date_previsao", "ipca_focus_med_mensal_pct",
        "ipca_ibge_mensal_pct", "erro_prev_menos_real_pp", "ipca_focus_mensal_nresp"
    ]]
    mensal_final_2021.columns = [
        "Mes de Referencia", "Data Survey Focus", "Focus Mediana (%)",
        "IBGE Realizado (%)", "Erro de Previsao (p.p.)", "Numero Respondentes"
    ]

    # IPCA Mensal Inicial
    mensal_inicial_2021 = df_mensal_inicial[
        df_mensal_inicial["ref_yyyymm"].astype(str).str.startswith("2021")
    ].copy()
    mensal_inicial_2021["mes_referencia"] = mensal_inicial_2021["ref_yyyymm"].astype(str).apply(
        lambda s: f"{s[4:6]}/{s[:4]}"
    )
    mensal_inicial_2021 = mensal_inicial_2021[[
        "mes_referencia", "survey_date_previsao", "ipca_focus_med_mensal_pct",
        "ipca_ibge_mensal_pct", "erro_prev_menos_real_pp", "ipca_focus_mensal_nresp"
    ]]
    mensal_inicial_2021.columns = [
        "Mes de Referencia", "Data Survey Focus", "Focus Expectativa Inicial (%)",
        "IBGE Realizado (%)", "Erro de Previsao (p.p.)", "Numero Respondentes"
    ]

    # IPCA Anual Calendario (Trajetória)
    anual_cal_2021 = df_anual_cal[df_anual_cal["ipca_year_ref"] == 2021].copy()
    # Em 2021, o realizado anual fechado foi de 10,06%
    anual_cal_2021["ipca_ibge_acum_ano_dez_pct"] = 10.06
    anual_cal_2021["erro_prev_menos_real_pp"] = anual_cal_2021["ipca_focus_ano_pct"] - 10.06
    
    anual_cal_2021 = anual_cal_2021[[
        "survey_date", "ipca_focus_ano_pct", "ipca_ibge_acum_ano_dez_pct",
        "erro_prev_menos_real_pp", "ipca_focus_ano_nresp"
    ]]
    anual_cal_2021.columns = [
        "Data do Boletim", "Expectativa Focus Anual YTD (%)",
        "IBGE Realizado Acumulado Ano (%)", "Erro de Previsao (p.p.)", "Numero Respondentes"
    ]

    # IPCA Anual Fechamento
    anual_fech_2021 = df_anual_fech[df_anual_fech["ano_ref"] == 2021].copy()
    anual_fech_2021.columns = [
        "Ano de Referencia", "Data 1a Previsao Focus",
        "Expectativa Focus Inicial (%)", "IBGE Realizado Acumulado Ano (%)", "Erro de Previsao (p.p.)"
    ]

    # 3. Exporta para CSV (Gemini) com UTF-8 BOM
    enc = "utf-8-sig"
    mensal_final_2021.to_csv(OUT_DIR / "gemini" / "ipca_mensal_expectativa_final_2021.csv", index=False, encoding=enc, sep=";", decimal=",")
    mensal_inicial_2021.to_csv(OUT_DIR / "gemini" / "ipca_mensal_expectativa_inicial_2021.csv", index=False, encoding=enc, sep=";", decimal=",")
    anual_cal_2021.to_csv(OUT_DIR / "gemini" / "ipca_anual_trajetoria_2021.csv", index=False, encoding=enc, sep=";", decimal=",")
    anual_fech_2021.to_csv(OUT_DIR / "gemini" / "ipca_anual_fechamento_2021.csv", index=False, encoding=enc, sep=";", decimal=",")

    print("  -> CSVs de 2021 exportados na pasta 'output/exportacao_ia_2021/gemini/'")

    # 4. Constrói o Relatório Markdown para o NotebookLM
    md_content = []
    md_content.append("# Relatório IPCA 2021 — Expectativas Focus vs Realizado IBGE\n")
    md_content.append("## Metodologia e Dados Gerais de 2021\n")
    md_content.append(
        "Este documento apresenta as tabelas consolidadas sobre o IPCA para o ano de **2021**, "
        "confrontando as expectativas do mercado pelo Boletim Focus (API Olinda do Banco Central) "
        "com a inflação real registrada pelo IBGE (tabela SIDRA 1737).\n"
    )
    md_content.append("O realizado oficial do IPCA acumulado de jan-dez de 2021 fechou em **10,06%**.\n")

    md_content.append("## 1. IPCA Mensal — Expectativa Final (Última pré-mês)\n")
    md_content.append(
        "Comparação entre a última expectativa coletada antes do início do mês de referência "
        "e o valor realizado divulgado pelo IBGE.\n"
    )
    md_content.append(to_markdown_table(mensal_final_2021) + "\n")

    md_content.append("## 2. IPCA Mensal — Expectativa Inicial (Começo do ano)\n")
    md_content.append(
        "Comparação entre a expectativa Focus registrada na primeira survey do ano (04/01/2021) "
        "para cada mês e o valor realizado do respectivo mês.\n"
    )
    md_content.append(to_markdown_table(mensal_inicial_2021) + "\n")

    md_content.append("## 3. IPCA Anual — Trajetória Mensal das Projeções para 2021\n")
    md_content.append(
        "Evolução da projeção de mercado Focus para a inflação anual fechada de 2021, "
        "medida no primeiro boletim publicado em cada mês de 2021, contra o fechamento oficial (10,06%).\n"
    )
    md_content.append(to_markdown_table(anual_cal_2021) + "\n")

    md_content.append("## 4. IPCA Anual — Fechamento de Previsão Inicial de 2021\n")
    md_content.append(
        "Comparação direta da expectativa inicial registrada no primeiro dia útil de janeiro de 2021 "
        "para o IPCA acumulado total do ano vs o realizado final.\n"
    )
    md_content.append(to_markdown_table(anual_fech_2021) + "\n")

    # Escreve o arquivo MD
    out_md = OUT_DIR / "relatorio_ipca_2021_notebooklm.md"
    out_md.write_text("\n".join(md_content), encoding="utf-8")
    print(f"  -> Relatório NotebookLM exportado em: '{out_md}'")
    print("\n=== Exportação concluída com sucesso! ===")


if __name__ == "__main__":
    main()
