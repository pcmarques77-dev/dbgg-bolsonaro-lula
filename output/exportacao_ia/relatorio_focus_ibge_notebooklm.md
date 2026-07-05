# Relatório: Expectativas Focus × Realizado Macroeconômico (Brasil)

**Gerado em:** 05/07/2026  

**Fonte:** Banco Central do Brasil (Boletim Focus — API Olinda), IBGE (SIDRA) e BCB (SGS).  

**Propósito:** Base de conhecimento para análise de acurácia de previsões macroeconômicas brasileiras (2019–2025).  

**Autor:** Projeto MBA Economia FIPE — Análise Focus × BCB × IBGE.


## Metodologia e Fontes

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


## IPCA — Inflação Mensal

O **IPCA (Índice Nacional de Preços ao Consumidor Amplo)** é o índice oficial de inflação do Brasil,
medido mensalmente pelo IBGE. É a meta de inflação do Banco Central.

**Período:** 2019 a 2026  |  **n =** 89 meses  |  **MAE =** 0.084 p.p.  |  **Viés médio =** -0.022 p.p.


### Estatísticas Anuais Agregadas — IPCA Mensal

| Ano | Focus Médio (%) | IBGE Médio (%) | MAE (p.p.) | Viés (p.p.) |
| --- | --- | --- | --- | --- |
| 2019 | 0.335 | 0.353 | 0.079 | -0.017 |
| 2020 | 0.347 | 0.37 | 0.082 | -0.023 |
| 2021 | 0.748 | 0.802 | 0.116 | -0.055 |
| 2022 | 0.43 | 0.472 | 0.12 | -0.042 |
| 2023 | 0.382 | 0.378 | 0.065 | 0.004 |
| 2024 | 0.374 | 0.394 | 0.06 | -0.02 |
| 2025 | 0.38 | 0.349 | 0.048 | 0.03 |
| 2026 | 0.536 | 0.632 | 0.124 | -0.096 |

### Série Completa — IPCA Mensal (Focus vs IBGE)

| Mês (AAAAMM) | Data Survey Focus | Focus Mediana (%) | IBGE Realizado (%) | Erro (p.p.) |
| --- | --- | --- | --- | --- |
| 201901 | 2019-01-28 | 0.4 | 0.32 | 0.08 |
| 201902 | 2019-02-25 | 0.35 | 0.43 | -0.08 |
| 201903 | 2019-03-25 | 0.51 | 0.75 | -0.24 |
| 201904 | 2019-04-29 | 0.6 | 0.57 | 0.03 |
| 201905 | 2019-05-27 | 0.25 | 0.13 | 0.12 |
| 201906 | 2019-06-24 | -0.02 | 0.01 | -0.03 |
| 201907 | 2019-07-29 | 0.23 | 0.19 | 0.04 |
| 201908 | 2019-08-26 | 0.12 | 0.11 | 0.0099999999999999 |
| 201909 | 2019-09-30 | 0.05 | -0.04 | 0.09 |
| 201910 | 2019-10-28 | 0.07 | 0.1 | -0.03 |
| 201911 | 2019-11-25 | 0.43 | 0.51 | -0.08 |
| 201912 | 2019-12-30 | 1.03 | 1.15 | -0.1199999999999998 |
| 202001 | 2020-01-27 | 0.35 | 0.21 | 0.1399999999999999 |
| 202002 | 2020-02-26 | 0.15 | 0.25 | -0.1 |
| 202003 | 2020-03-30 | 0.1 | 0.07 | 0.03 |
| 202004 | 2020-04-27 | -0.14 | -0.31 | 0.1699999999999999 |
| 202005 | 2020-05-25 | -0.4 | -0.38 | -0.02 |
| 202006 | 2020-06-29 | 0.25 | 0.26 | -0.01 |
| 202007 | 2020-07-27 | 0.37 | 0.36 | 0.01 |
| 202008 | 2020-08-31 | 0.22 | 0.24 | -0.0199999999999999 |
| 202009 | 2020-09-28 | 0.5 | 0.64 | -0.14 |
| 202010 | 2020-10-26 | 0.8 | 0.86 | -0.0599999999999999 |
| 202011 | 2020-11-30 | 0.75 | 0.89 | -0.14 |
| 202012 | 2020-12-28 | 1.21 | 1.35 | -0.1400000000000001 |
| 202101 | 2021-01-25 | 0.3 | 0.25 | 0.0499999999999999 |
| 202102 | 2021-02-22 | 0.68 | 0.86 | -0.1799999999999999 |
| 202103 | 2021-03-29 | 1.0 | 0.93 | 0.0699999999999999 |
| 202104 | 2021-04-26 | 0.35 | 0.31 | 0.0399999999999999 |
| 202105 | 2021-05-31 | 0.69 | 0.83 | -0.14 |
| 202106 | 2021-06-28 | 0.58 | 0.53 | 0.0499999999999999 |
| 202107 | 2021-07-26 | 0.93 | 0.96 | -0.0299999999999999 |
| 202108 | 2021-08-30 | 0.685 | 0.87 | -0.1849999999999999 |
| 202109 | 2021-09-27 | 1.2 | 1.16 | 0.04 |
| 202110 | 2021-10-25 | 0.8319 | 1.25 | -0.4181 |
| 202111 | 2021-11-29 | 1.0658 | 0.95 | 0.1158000000000001 |
| 202112 | 2021-12-27 | 0.66 | 0.73 | -0.0699999999999999 |
| 202201 | 2022-01-31 | 0.55 | 0.54 | 0.01 |
| 202202 | 2022-02-21 | 0.86 | 1.01 | -0.15 |
| 202203 | 2022-03-28 | 1.27 | 1.62 | -0.3500000000000001 |
| 202204 | 2022-04-25 | 0.9 | 1.06 | -0.16 |
| 202205 | 2022-05-30 | 0.58 | 0.47 | 0.1099999999999999 |
| 202206 | 2022-06-27 | 0.715 | 0.67 | 0.0449999999999999 |
| 202207 | 2022-07-25 | -0.66 | -0.68 | 0.02 |
| 202208 | 2022-08-29 | -0.35 | -0.36 | 0.01 |
| 202209 | 2022-09-26 | -0.16 | -0.29 | 0.1299999999999999 |
| 202210 | 2022-10-31 | 0.449 | 0.59 | -0.1409999999999999 |
| 202211 | 2022-11-28 | 0.55 | 0.41 | 0.14 |
| 202212 | 2022-12-26 | 0.45 | 0.62 | -0.1699999999999999 |
| 202301 | 2023-01-30 | 0.56 | 0.53 | 0.03 |
| 202302 | 2023-02-27 | 0.77 | 0.84 | -0.0699999999999999 |
| 202303 | 2023-03-27 | 0.78 | 0.71 | 0.07 |
| 202304 | 2023-04-24 | 0.55 | 0.61 | -0.0599999999999999 |
| 202305 | 2023-05-29 | 0.35 | 0.23 | 0.1199999999999999 |
| 202306 | 2023-06-26 | -0.11 | -0.08 | -0.03 |
| 202307 | 2023-07-31 | 0.075 | 0.12 | -0.045 |
| 202308 | 2023-08-28 | 0.27 | 0.23 | 0.04 |
| 202309 | 2023-09-25 | 0.3646 | 0.26 | 0.1045999999999999 |
| 202310 | 2023-10-30 | 0.28 | 0.24 | 0.04 |
| 202311 | 2023-11-27 | 0.29 | 0.28 | 0.0099999999999999 |
| 202312 | 2023-12-26 | 0.4 | 0.56 | -0.16 |
| 202401 | 2024-01-29 | 0.37 | 0.42 | -0.0499999999999999 |
| 202402 | 2024-02-26 | 0.75 | 0.83 | -0.0799999999999999 |
| 202403 | 2024-03-25 | 0.2 | 0.16 | 0.04 |
| 202404 | 2024-04-29 | 0.32 | 0.38 | -0.06 |
| 202405 | 2024-05-27 | 0.4095 | 0.46 | -0.0505 |
| 202406 | 2024-06-24 | 0.34 | 0.21 | 0.13 |
| 202407 | 2024-07-29 | 0.33 | 0.38 | -0.0499999999999999 |
| 202408 | 2024-08-26 | 0.02 | -0.02 | 0.04 |
| 202409 | 2024-09-30 | 0.46 | 0.44 | 0.02 |
| 202410 | 2024-10-28 | 0.52 | 0.56 | -0.04 |
| 202411 | 2024-11-25 | 0.24 | 0.39 | -0.15 |
| 202412 | 2024-12-30 | 0.534 | 0.52 | 0.014 |
| 202501 | 2025-01-27 | 0.1355 | 0.16 | -0.0244999999999999 |
| 202502 | 2025-02-24 | 1.38 | 1.31 | 0.0699999999999998 |
| 202503 | 2025-03-31 | 0.56 | 0.56 | 0.0 |
| 202504 | 2025-04-28 | 0.44 | 0.43 | 0.01 |
| 202505 | 2025-05-26 | 0.4 | 0.26 | 0.14 |
| 202506 | 2025-06-30 | 0.21 | 0.24 | -0.03 |
| 202507 | 2025-07-28 | 0.34 | 0.26 | 0.08 |
| 202508 | 2025-08-25 | -0.16 | -0.11 | -0.05 |
| 202509 | 2025-09-29 | 0.55 | 0.48 | 0.07 |
| 202510 | 2025-10-27 | 0.15 | 0.09 | 0.06 |
| 202511 | 2025-11-24 | 0.2 | 0.18 | 0.02 |
| 202512 | 2025-12-29 | 0.35 | 0.33 | 0.0199999999999999 |
| 202601 | 2026-01-26 | 0.35 | 0.33 | 0.0199999999999999 |
| 202602 | 2026-02-23 | 0.44 | 0.7 | -0.2599999999999999 |
| 202603 | 2026-03-30 | 0.7 | 0.88 | -0.18 |
| 202604 | 2026-04-27 | 0.72 | 0.67 | 0.0499999999999999 |
| 202605 | 2026-05-25 | 0.47 | 0.58 | -0.1099999999999999 |

## IPCA — Comparação Anual (Expectativa Inicial vs Realizado)

Comparação da expectativa do mercado no **início do ano** (primeiro boletim Focus de janeiro)
contra o **IPCA acumulado no ano** (janeiro a dezembro), divulgado pelo IBGE.
Esta análise revela o viés estrutural das previsões de início de ano.

**MAE =** 0.100 p.p.  |  **Viés médio =** -0.090 p.p.  |  **n =** 7 anos

| Ano | Data 1ª Previsão Focus | IPCA Focus Inicial (%) | IPCA IBGE Realizado (%) | Erro (p.p.) |
| --- | --- | --- | --- | --- |
| 2019 | 2019-12-31 | 4.2 | 4.31 | -0.1099999999999994 |
| 2020 | 2020-12-31 | 4.38 | 4.52 | -0.1399999999999996 |
| 2021 | 2021-12-31 | 9.9627 | 10.06 | -0.0973000000000006 |
| 2022 | 2022-12-30 | 5.6379 | 5.79 | -0.1520999999999999 |
| 2023 | 2023-12-29 | 4.4547 | 4.62 | -0.1653000000000002 |
| 2024 | 2024-12-31 | 4.8416 | 4.83 | 0.0115999999999996 |
| 2025 | 2025-12-31 | 4.2851 | 4.26 | 0.0251000000000001 |

**Interpretação:** Viés de -0.090 p.p. indica que, em média, o mercado subestima o IPCA anual na previsão de início de ano.


## Selic — Comparação Anual (Expectativa Inicial vs Realizado)

A **Taxa Selic** é a taxa básica de juros da economia brasileira, definida pelo Copom (Comitê de
Política Monetária do BCB). A comparação avalia a expectativa do início do ano contra a Selic
anualizada efetiva no fechamento de dezembro (série SGS 11 do BCB).

**MAE =** 2.321 p.p.  |  **Viés médio =** -0.786 p.p.  |  **n =** 8 anos

| Ano | Data 1ª Previsão Focus | Selic Focus Inicial (%) | Selic SGS Realizada (%) | Erro (p.p.) |
| --- | --- | --- | --- | --- |
| 2019 | 2019-01-28 | 6.75 | 4.5 | 2.25 |
| 2020 | 2020-01-27 | 4.25 | 2.0 | 2.25 |
| 2021 | 2021-01-25 | 3.5 | 9.25 | -5.75 |
| 2022 | 2022-01-31 | 11.875 | 13.75 | -1.875 |
| 2023 | 2023-01-30 | 12.5 | 11.75 | 0.75 |
| 2024 | 2024-01-29 | 9.0 | 12.25 | -3.25 |
| 2025 | 2025-01-27 | 15.125 | 15.0 | 0.125 |
| 2026 | 2026-01-26 | 12.25 | nan | nan |

**Interpretação:** Viés de -0.786 p.p. indica que o mercado tende a subestimar a Selic ao início do ano. Erros grandes em 2020–2022 refletem choques não antecipados (pandemia, alta da inflação).


## PIB — Comparação Anual (Expectativa Inicial vs Realizado)

O **PIB (Produto Interno Bruto)** é a medida de atividade econômica. Aqui é usado a variação
percentual acumulada em quatro trimestres no 4º trimestre (taxa 4T/4T anterior), divulgada pelo
IBGE nas Contas Nacionais Trimestrais (SIDRA 5932). Essa é a métrica anual padrão do mercado.

**MAE =** 2.187 p.p.  |  **Viés médio =** -0.207 p.p.  |  **n =** 8 anos

| Ano | Data 1ª Previsão Focus | PIB Focus Inicial (%) | PIB IBGE Realizado 4T (%) | Erro (p.p.) |
| --- | --- | --- | --- | --- |
| 2019 | 2019-01-07 | 2.53 | 1.2 | 1.3299999999999998 |
| 2020 | 2020-01-06 | 2.3 | -3.3 | 5.6 |
| 2021 | 2021-01-04 | 3.4 | 4.8 | -1.4 |
| 2022 | 2022-01-03 | 0.287 | 3.0 | -2.713 |
| 2023 | 2023-01-02 | 0.8 | 3.2 | -2.4000000000000004 |
| 2024 | 2024-01-02 | 1.7504 | 3.4 | -1.6496 |
| 2025 | 2025-01-06 | 2.0813 | 2.3 | -0.2186999999999996 |
| 2026 | 2026-01-05 | 1.7679 | nan | nan |

**Interpretação:** Viés de -0.207 p.p. indica que o mercado tende a subestimar o crescimento do PIB. O erro de 2020 (pandemia) é um outlier extremo e deve ser tratado separadamente nas análises.


## Sumário Comparativo de Acurácia

Comparação do MAE entre os três indicadores no período completo disponível:

| Indicador | Período | MAE (p.p.) | Viés Médio (p.p.) |
| --- | --- | --- | --- |
| IPCA Anual | 7 anos | 0.100 | -0.090 |
| Selic Anual | 8 anos | 2.321 | -0.786 |
| PIB Anual | 8 anos | 2.187 | -0.207 |

**Notas:**
- MAE: Erro Médio Absoluto. Quanto menor, mais acurada a previsão.
- Viés positivo: mercado sistematicamente otimista (previu mais do que ocorreu).
- Viés negativo: mercado sistematicamente pessimista.
- Período inclui anos com choques excepcionais (2020: pandemia; 2021–2022: inflação pós-pandemia).



## Glossário de Variáveis

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
