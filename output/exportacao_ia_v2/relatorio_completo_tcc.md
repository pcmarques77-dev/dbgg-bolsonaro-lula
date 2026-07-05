# Relatório Completo: Expectativas Focus × Realizado Macroeconômico — Análise Comparativa entre Governos Bolsonaro e Lula 3

**Gerado em:** 22/06/2026  
**Versão:** 2.0 (Export Unificado — Análise Descritiva + Econométrica)  
**Fonte:** Banco Central do Brasil (Boletim Focus — API Olinda), IBGE (SIDRA), BCB (SGS), Yahoo Finance (VIX e CRB Commodities).  
**Propósito:** Base de conhecimento unificada para análise acadêmica de TCC (MBA Economia FIPE) sobre a acurácia das previsões macroeconômicas e as diferenças estruturais entre os governos Bolsonaro (2019–2022) e Lula 3 (2023–presente).  
**Autor:** Projeto MBA Economia FIPE — Análise Focus × BCB × IBGE.

---

## Sumário Executivo

Este relatório consolida toda a base analítica do TCC que investiga **como as expectativas de mercado (Boletim Focus do BCB) se comportaram de forma distinta entre os governos Bolsonaro e Lula 3**, tanto em termos de acurácia preditiva quanto em termos de resposta a choques externos e fatores domésticos.

O trabalho está dividido em duas grandes seções:
1. **Análise Descritiva (Fase 1 — "Topo do Funil"):** Comparação empírica direta entre previsões Focus e valores realizados para IPCA, Selic, PIB e Dívida Bruta (DBGG), com métricas de erro (MAE e RMSE) calculadas por governo.
2. **Análise Econométrica (Fase 2 — "Fundo do Funil"):** Regressões OLS com erros robustos Newey-West (HAC), testes de quebra estrutural de Chow e estimação da Regra de Taylor de Expectativas para fundamentar estatisticamente as diferenças observadas.

---

# PARTE I — ANÁLISE DESCRITIVA

## 1. Metodologia e Fontes

O **Boletim Focus** é o relatório semanal do Banco Central do Brasil que consolida as expectativas de mercado para os principais indicadores macroeconômicos brasileiros. É divulgado toda segunda-feira, com dados coletados até a sexta-feira anterior.

Este conjunto de dados compara duas grandezas para cada indicador:

- **Expectativa Focus:** mediana das projeções dos analistas de mercado coletadas no **primeiro boletim Focus publicado no ano de referência** (normalmente a primeira segunda-feira de janeiro). Essa é a "aposta inicial" do mercado no início do ano.
- **Realizado (Oficial):** valor efetivamente divulgado pelo órgão competente ao final do período.

### 1.1 Regras de Alinhamento Temporal
- **IPCA mensal:** expectativa = último boletim Focus antes do início do mês de referência. Realizado = SIDRA 1737.
- **IPCA anual:** expectativa = primeiro boletim Focus do ano Y. Realizado = acumulado IPCA jan–dez (IBGE).
- **Selic anual:** expectativa = primeiro boletim Focus do ano Y. Realizado = taxa Selic anualizada no fechamento de dezembro (SGS série 11).
- **PIB anual:** expectativa = primeiro boletim Focus do ano Y. Realizado = variação acumulada em 4 trimestres do 4º trimestre do IBGE (SIDRA 5932).
- **DBGG (Dívida Bruta):** expectativa = último Focus disponível em janeiro do ano Y+1. Realizado = DBGG/PIB (%) em dezembro, série SGS 13762.

### 1.2 Métricas de Erro
- **Erro (p.p.):** Focus − Realizado. Positivo = mercado superestimou; Negativo = mercado subestimou.
- **MAE:** Erro Médio Absoluto — mede a magnitude média dos erros sem cancelamento.
- **RMSE:** Root Mean Squared Error — penaliza mais fortemente erros grandes.

### 1.3 Definição dos Períodos de Governo
- **Bolsonaro:** 01/01/2019 a 31/12/2022 (inclui os anos de pandemia de COVID-19)
- **Lula 3:** 01/01/2023 em diante

---

## 2. IPCA — Inflação

### 2.1 Comparação Anual (Expectativa Inicial vs Realizado)

Comparação da expectativa do mercado no **início do ano** (primeiro boletim Focus de janeiro) contra o **IPCA acumulado no ano** (janeiro a dezembro), divulgado pelo IBGE.

| Ano | Governo | Data 1ª Previsão | IPCA Focus (%) | IPCA Realizado (%) | Erro (p.p.) |
|-----|---------|------------------|----------------|---------------------|-------------|
| 2019 | Bolsonaro | 2019-01-02 | 4,01 | 4,31 | -0,30 |
| 2020 | Bolsonaro | 2020-01-02 | 3,58 | 4,52 | -0,94 |
| 2021 | Bolsonaro | 2021-01-04 | 3,32 | 10,06 | -6,74 |
| 2022 | Bolsonaro | 2022-01-03 | 4,98 | 5,79 | -0,81 |
| 2023 | Lula 3 | 2023-01-02 | 5,46 | 4,62 | +0,84 |
| 2024 | Lula 3 | 2024-01-02 | 3,90 | 4,83 | -0,93 |
| 2025 | Lula 3 | 2025-01-02 | 5,00 | 4,26 | +0,74 |

**MAE Bolsonaro (2019–2022):** 2,20 p.p.  
**MAE Lula 3 (2023–2025):** 0,84 p.p.  

**Interpretação:** No governo Bolsonaro, o erro médio absoluto foi significativamente maior, puxado pelo outlier de 2021 (surpresa inflacionária pós-pandemia). No governo Lula 3, os erros são menores e alternaram entre sub e superestimativa, sem viés claro de direção.

### 2.2 IPCA Mensal — Estatísticas Anuais Agregadas

| Ano | Governo | Focus Médio (%) | IBGE Médio (%) | MAE (p.p.) | Viés (p.p.) |
|-----|---------|-----------------|----------------|------------|-------------|
| 2019 | Bolsonaro | 0,335 | 0,353 | 0,079 | -0,017 |
| 2020 | Bolsonaro | 0,347 | 0,370 | 0,082 | -0,023 |
| 2021 | Bolsonaro | 0,748 | 0,802 | 0,116 | -0,055 |
| 2022 | Bolsonaro | 0,430 | 0,472 | 0,120 | -0,042 |
| 2023 | Lula 3 | 0,382 | 0,378 | 0,065 | +0,004 |
| 2024 | Lula 3 | 0,374 | 0,394 | 0,060 | -0,020 |
| 2025 | Lula 3 | 0,380 | 0,349 | 0,048 | +0,030 |

**Interpretação:** O MAE mensal caiu consistentemente no governo Lula 3, indicando convergência mais rápida das previsões mensais ao realizado. O viés é praticamente neutro em ambos os governos na frequência mensal.

---

## 3. Selic — Taxa Básica de Juros

### 3.1 Comparação Anual (Expectativa Inicial vs Realizado)

| Ano | Governo | Data 1ª Previsão | Selic Focus (%) | Selic Realizada (%) | Erro (p.p.) |
|-----|---------|------------------|-----------------|----------------------|-------------|
| 2019 | Bolsonaro | 2019-01-02 | 7,00 | 4,40 | +2,60 |
| 2020 | Bolsonaro | 2020-01-02 | 4,50 | 1,90 | +2,60 |
| 2021 | Bolsonaro | 2021-01-04 | 3,25 | 9,15 | -5,90 |
| 2022 | Bolsonaro | 2022-01-03 | 11,75 | 13,65 | -1,90 |
| 2023 | Lula 3 | 2023-01-02 | 12,25 | 11,65 | +0,60 |
| 2024 | Lula 3 | 2024-01-02 | 9,00 | 12,15 | -3,15 |
| 2025 | Lula 3 | 2025-01-02 | 15,00 | 14,90 | +0,10 |

**MAE Bolsonaro (2019–2022):** 3,25 p.p.  
**MAE Lula 3 (2023–2025):** 1,28 p.p.  

**Interpretação:** As previsões de Selic foram muito mais erráticas no governo Bolsonaro (MAE 3,25 p.p.), com destaque para o erro extremo de 2021 (-5,90 p.p.) quando o mercado não previu o ciclo agressivo de aperto monetário. No Lula 3, o erro de 2024 (-3,15 p.p.) mostra que o mercado subestimou a necessidade de juros elevados, mas o MAE geral é menor.

---

## 4. PIB — Produto Interno Bruto

### 4.1 Comparação Anual (Expectativa Inicial vs Realizado)

| Ano | Governo | Data 1ª Previsão | PIB Focus (%) | PIB Realizado (%) | Erro (p.p.) |
|-----|---------|------------------|---------------|---------------------|-------------|
| 2019 | Bolsonaro | 2019-01-02 | 2,53 | 1,20 | +1,33 |
| 2020 | Bolsonaro | 2020-01-02 | 2,30 | -3,30 | +5,60 |
| 2021 | Bolsonaro | 2021-01-04 | 3,40 | 4,80 | -1,40 |
| 2022 | Bolsonaro | 2022-01-03 | 0,29 | 3,00 | -2,71 |
| 2023 | Lula 3 | 2023-01-02 | 0,80 | 3,20 | -2,40 |
| 2024 | Lula 3 | 2024-01-02 | 1,75 | 3,40 | -1,65 |
| 2025 | Lula 3 | 2025-01-02 | 2,12 | 2,30 | -0,18 |

**MAE Bolsonaro (2019–2022):** 2,76 p.p.  
**MAE Lula 3 (2023–2025):** 1,41 p.p.  

**Interpretação:** O mercado subestimou sistematicamente o PIB em ambos os governos (exceto 2019–2020 Bolsonaro), porém a magnitude dos erros foi maior no governo Bolsonaro, influenciada pelo choque da pandemia em 2020 (+5,60 p.p.) e pela surpresa positiva de 2022 (-2,71 p.p.).

---

## 5. DBGG — Dívida Bruta do Governo Geral (% PIB)

| Ano | Governo | Focus Mediana (% PIB) | DBGG Realizado (% PIB) | Erro (p.p.) | Var. YoY (p.p.) |
|-----|---------|----------------------|------------------------|-------------|-----------------|
| 2019 | Bolsonaro | 78,10 | 74,44 | +3,66 | — |
| 2020 | Bolsonaro | 89,15 | 86,94 | +2,21 | +12,50 |
| 2021 | Bolsonaro | 81,00 | 77,31 | +3,69 | -9,63 |
| 2022 | Bolsonaro | 74,50 | 71,68 | +2,82 | -5,63 |
| 2023 | Lula 3 | 75,10 | 73,83 | +1,27 | +2,15 |
| 2024 | Lula 3 | 77,60 | 76,27 | +1,33 | +2,44 |
| 2025 | Lula 3 | 79,65 | 78,64 | +1,01 | +2,37 |

**Interpretação:** O mercado superestimou a DBGG em TODOS os anos, com viés unidirecional positivo. No governo Bolsonaro, a dívida oscilou violentamente (+12,5 p.p. em 2020 por causa da pandemia), enquanto no Lula 3 há uma tendência de alta gradual e consistente (~2,3 p.p. ao ano). O erro de previsão é menor no Lula 3.

---

## 6. Sumário Comparativo de Acurácia por Governo

| Indicador | MAE Bolsonaro | MAE Lula 3 | Viés Bolsonaro | Viés Lula 3 |
|-----------|---------------|------------|----------------|-------------|
| IPCA Anual | 2,20 p.p. | 0,84 p.p. | -2,20 (subestima) | +0,22 (neutro) |
| Selic Anual | 3,25 p.p. | 1,28 p.p. | -0,65 (misto) | -0,82 (subestima) |
| PIB Anual | 2,76 p.p. | 1,41 p.p. | +0,71 (misto) | -1,41 (subestima) |
| DBGG | 3,10 p.p. | 1,20 p.p. | +3,10 (superestima) | +1,20 (superestima) |

**Conclusão descritiva:** O MAE de todos os indicadores foi consistentemente menor no governo Lula 3 do que no Bolsonaro. Porém, essa diferença é significativamente inflada pelos choques extremos do período 2020–2021 (pandemia de COVID-19). A pergunta-chave do TCC — *essa diferença é estatisticamente significante controlando por choques externos?* — é respondida pela análise econométrica na Parte II.

---

# PARTE II — ANÁLISE ECONOMÉTRICA

## 7. Fundamentação Metodológica

Para ir além da análise descritiva e testar formalmente se as expectativas de mercado apresentaram comportamento estruturalmente diferente entre os dois governos, estimamos **quatro modelos de regressão OLS** com os seguintes aperfeiçoamentos estatísticos:

### 7.1 Erros Robustos Newey-West (HAC)
As séries semanais de expectativas Focus são altamente autocorrelacionadas (Durbin-Watson ≈ 0,03 em todos os modelos). OLS simples geraria estatísticas-t infladas e p-valores artificialmente baixos. Por isso, utilizamos erros padrão robustos à heterocedasticidade e autocorrelação (HAC) com **maxlags=4**, seguindo a correção de Newey-West (1987).

### 7.2 Teste de Quebra Estrutural de Chow
Em vez de apenas usar dummies de deslocamento (shift dummies), testamos formalmente se a **própria sensibilidade** do mercado a choques externos (VIX e Commodities) mudou entre os dois governos. O teste de Chow divide a amostra entre Bolsonaro e Lula 3, estima modelos separados e um modelo combinado, e calcula a estatística F.

### 7.3 Variáveis de Controle
- **dummy_lula:** 1 se a observação pertence ao período Lula 3 (≥ 2023), 0 caso contrário
- **dummy_pandemia:** 1 se a observação pertence ao período de pandemia (2020-03 a 2021-06)
- **vix:** Índice de Volatilidade (CBOE) — proxy de aversão global ao risco
- **commodities:** Índice CRB de commodities — proxy de pressões de custos globais
- **desancoragem_centro_12m:** Desvio da expectativa de IPCA 12 meses em relação ao centro da meta de inflação

---

## 8. Modelo 1 — IPCA 12 Meses (Expectativa de Inflação)

**Especificação:** `ipca_med12m ~ const + dummy_lula + dummy_pandemia + vix + commodities`  
**Observações:** 1.824 | **Covariância:** HAC (Newey-West, 4 lags)  
**R²:** 0,492 | **R² ajustado:** 0,490

### 8.1 Coeficientes Estimados (Erros Robustos HAC)

| Variável | Coeficiente | Erro Padrão | Estatística z | p-valor | IC 95% |
|----------|-------------|-------------|---------------|---------|--------|
| const | 1,2749 | 0,162 | 7,862 | 0,000*** | [0,957; 1,593] |
| **dummy_lula** | **-0,6280** | **0,072** | **-8,730** | **0,000***| **[-0,769; -0,487]** |
| dummy_pandemia | 0,1829 | 0,071 | 2,572 | 0,010** | [0,044; 0,322] |
| vix | 0,0044 | 0,004 | 1,163 | 0,245 | [-0,003; 0,012] |
| commodities | 0,1551 | 0,008 | 18,620 | 0,000*** | [0,139; 0,171] |

### 8.2 Interpretação Econômica
- **dummy_lula = -0,628 (p < 0,001):** Controlando por pandemia, VIX e commodities, a expectativa mediana de IPCA 12 meses é, em média, **0,63 p.p. menor** no governo Lula 3 do que no Bolsonaro. Resultado altamente significante.
- **commodities = 0,155 (p < 0,001):** Cada ponto de aumento no índice CRB eleva a expectativa de IPCA em 0,16 p.p. — forte canal de custos.
- **vix:** Não é significante para expectativas de inflação (p = 0,245).

### 8.3 Teste de Chow — Quebra Estrutural
- **F-stat:** 421,24 | **p-valor:** 0,000  
- **n Bolsonaro:** 983 | **n Lula:** 841
- **Conclusão:** Existe quebra estrutural significante a 5% na relação entre expectativas de IPCA e variáveis globais (VIX e commodities) entre os governos.

### 8.4 Diagnósticos de Resíduos
- **Breusch-Pagan:** p < 0,001 → Heterocedasticidade presente (corrigida pelo HAC)
- **Durbin-Watson:** 0,030 → Forte autocorrelação serial (corrigida pelo HAC)
- **Jarque-Bera:** p < 0,001 → Resíduos não normais (skew = 0,54, kurtosis = 3,13)
- **ADF (Estacionariedade):** ipca_med12m e commodities não rejeitam raiz unitária; VIX é estacionário

---

## 9. Modelo 2 — Selic 12 Meses (Expectativa de Juros)

**Especificação:** `selic_mediana_pct ~ const + dummy_lula + dummy_pandemia + vix + commodities`  
**Observações:** 1.725 | **Covariância:** HAC (Newey-West, 4 lags)

### 9.1 Coeficientes Estimados

| Variável | Coeficiente | Erro Padrão | Estatística z | p-valor | IC 95% |
|----------|-------------|-------------|---------------|---------|--------|
| const | -3,8610 | 0,523 | -7,387 | 0,000*** | [-4,885; -2,837] |
| **dummy_lula** | **+1,6902** | **0,230** | **7,355** | **0,000***| **[1,240; 2,141]** |
| dummy_pandemia | -2,3410 | 0,212 | -11,042 | 0,000*** | [-2,757; -1,926] |
| vix | 0,0657 | 0,011 | 6,064 | 0,000*** | [0,044; 0,087] |
| commodities | 0,5756 | 0,024 | 23,620 | 0,000*** | [0,528; 0,623] |

### 9.2 Interpretação Econômica
- **dummy_lula = +1,690 (p < 0,001):** A expectativa mediana de Selic é, em média, **1,69 p.p. MAIOR** no governo Lula 3, mesmo controlando por pandemia, VIX e commodities. Isso reflete a percepção do mercado de que a política monetária precisa ser mais restritiva no Lula 3.
- **dummy_pandemia = -2,341 (p < 0,001):** A pandemia reduziu a expectativa de Selic em 2,34 p.p. (cortes emergenciais).
- **commodities = 0,576 (p < 0,001):** O índice CRB é o principal driver: cada ponto aumenta a expectativa de Selic em 0,58 p.p.

### 9.3 Teste de Chow
- **F-stat:** 554,34 | **p-valor:** 0,000 → **Quebra estrutural significante.**

---

## 10. Modelo 3 — PIB (Expectativa de Crescimento)

**Especificação:** `pib_med_pct ~ const + dummy_lula + dummy_pandemia + vix + commodities`  
**Observações:** 1.824 | **Covariância:** HAC (Newey-West, 4 lags)

### 10.1 Coeficientes Estimados

| Variável | Coeficiente | Erro Padrão | Estatística z | p-valor | IC 95% |
|----------|-------------|-------------|---------------|---------|--------|
| const | -1,9023 | 0,598 | -3,183 | 0,001*** | [-3,073; -0,731] |
| **dummy_lula** | **-0,6683** | **0,231** | **-2,897** | **0,004***| **[-1,120; -0,216]** |
| dummy_pandemia | 0,5367 | 0,395 | 1,357 | 0,175 | [-0,238; 1,312] |
| vix | -0,1078 | 0,032 | -3,363 | 0,001*** | [-0,171; -0,045] |
| commodities | 0,2798 | 0,034 | 8,171 | 0,000*** | [0,213; 0,347] |

### 10.2 Interpretação Econômica
- **dummy_lula = -0,668 (p = 0,004):** A expectativa de crescimento do PIB é, em média, **0,67 p.p. menor** no governo Lula 3 vs Bolsonaro, controlando por choques. Isso sugere pessimismo estrutural do mercado com o crescimento sob o Lula 3.
- **vix = -0,108 (p < 0,001):** Aumento na volatilidade global reduz a expectativa de PIB (aversão ao risco).
- **dummy_pandemia:** Não é significante para PIB (p = 0,175) — efeito da pandemia foi capturado pelas oscilações do VIX e commodities.

### 10.3 Teste de Chow
- **F-stat:** 50,63 | **p-valor:** 0,000 → **Quebra estrutural significante.**

---

## 11. Modelo 4 — Regra de Taylor de Expectativas

**Especificação:** `selic_mediana_pct ~ const + desancoragem_centro_12m + dummy_lula`  
**Observações:** 1.770 | **Covariância:** HAC (Newey-West, 4 lags)

Este modelo testa se o mercado "precifica" a Selic de acordo com uma Regra de Taylor: espera-se que quanto maior a desancoragem da inflação em relação à meta, maior a expectativa de Selic.

### 11.1 Coeficientes Estimados

| Variável | Coeficiente | Erro Padrão | Estatística z | p-valor | IC 95% |
|----------|-------------|-------------|---------------|---------|--------|
| const | 5,6492 | 0,146 | 38,602 | 0,000*** | [5,362; 5,936] |
| **desancoragem_centro_12m** | **2,6760** | **0,096** | **27,877** | **0,000***| **[2,488; 2,864]** |
| **dummy_lula** | **+3,2958** | **0,219** | **15,081** | **0,000***| **[2,867; 3,724]** |

### 11.2 Interpretação Econômica
- **desancoragem = 2,676 (p < 0,001):** Para cada 1 p.p. de desvio da expectativa de inflação acima da meta, o mercado espera que a Selic suba 2,68 p.p. O mercado opera com uma "Regra de Taylor implícita" muito agressiva.
- **dummy_lula = +3,296 (p < 0,001):** **O resultado mais forte de toda a análise.** Mesmo para o MESMO nível de desancoragem de inflação, o mercado espera uma Selic **3,30 p.p. MAIOR** no governo Lula 3. Isso captura o **prêmio de risco fiscal e institucional** percebido pelo mercado — a desconfiança de que o BCB precisará ser mais hawkish sob o Lula 3.

### 11.3 Teste de Chow
- **F-stat:** 631,60 | **p-valor:** 0,000 → **Quebra estrutural significante.**

### 11.4 Diagnósticos
- **Jarque-Bera:** p = 0,097 → Resíduos aproximadamente normais (melhor modelo em termos de normalidade).

---

## 12. Síntese dos Testes de Chow (Quebra Estrutural)

| Modelo | Estatística F | p-valor | n Bolsonaro | n Lula 3 | Variáveis Testadas |
|--------|---------------|---------|-------------|----------|---------------------|
| IPCA OLS | 421,24 | 0,000 | 983 | 841 | VIX, Commodities |
| Selic OLS | 554,34 | 0,000 | 922 | 803 | VIX, Commodities |
| PIB OLS | 50,63 | 0,000 | 983 | 841 | VIX, Commodities |
| Taylor Rule | 631,60 | 0,000 | 944 | 826 | Desancoragem |

**Conclusão:** Em TODOS os quatro modelos, o teste de Chow rejeita a hipótese nula de estabilidade estrutural (p = 0,000). Isso significa que a relação entre as expectativas de mercado e seus determinantes (choques globais, desancoragem) **mudou significativamente** entre os governos Bolsonaro e Lula 3. Não se trata apenas de diferenças de nível — a própria *função de reação* do mercado é diferente.

---

## 13. Síntese Analítica para o TCC

### 13.1 Principais Achados

1. **O "Efeito Lula" é estatisticamente significante em todas as variáveis**, mesmo controlando por pandemia, volatilidade global e commodities.

2. **Contradição aparente IPCA vs Selic:** O mercado espera menos inflação (IPCA -0,63 p.p.) mas mais juros (Selic +1,69 p.p.) no Lula 3. Essa aparente contradição se resolve pelo canal fiscal: o mercado atribui um prêmio de risco ao governo Lula 3 que exige juros mais altos independentemente da inflação corrente.

3. **A Regra de Taylor confirma o prêmio fiscal:** Para o MESMO nível de desancoragem, a Selic esperada é 3,30 p.p. maior no Lula 3. Esse "excesso" não é explicável pela inflação — é explicado pela percepção de risco fiscal.

4. **O PIB esperado é menor no Lula 3 (-0,67 p.p.):** O mercado é mais pessimista com o crescimento, possivelmente refletindo preocupações com o ambiente de negócios ou efeitos contracionistas da política monetária mais restritiva.

5. **Quebra estrutural confirmada em todos os modelos:** O teste de Chow mostra que a relação entre expectativas e determinantes externos mudou. O mercado não apenas ajustou níveis, mas também a sensibilidade a choques.

### 13.2 Narrativa para a Monografia

A análise sugere que o mercado financeiro brasileiro opera com dois "regimes de expectativas" distintos. No governo Bolsonaro (2019–2022), as expectativas eram predominantemente guiadas por choques de oferta (commodities) e eventos exógenos (pandemia). No governo Lula 3 (2023–presente), emerge um componente de **risco institucional e fiscal** que eleva o patamar de juros esperados, reduz a expectativa de crescimento e comprime a expectativa de inflação (possivelmente porque o mercado precifica que o BCB será forçado a manter juros altos, o que contém a inflação mas ao custo de menor crescimento).

---

# APÊNDICES

## A. Glossário de Variáveis

| Variável | Descrição | Unidade |
|---|---|---|
| ipca_med12m | Mediana Focus da expectativa de IPCA acumulado 12 meses | % |
| selic_mediana_pct | Mediana Focus da expectativa de Selic | % a.a. |
| pib_med_pct | Mediana Focus da expectativa de crescimento do PIB | % |
| dummy_lula | Dummy de governo (1 = Lula 3, 0 = Bolsonaro) | 0/1 |
| dummy_pandemia | Dummy de pandemia (1 = mar/2020–jun/2021) | 0/1 |
| vix | Índice de Volatilidade CBOE (VIX) | pontos |
| commodities | Índice CRB de Commodities | pontos |
| desancoragem_centro_12m | Desvio da expectativa de IPCA 12m vs centro da meta | p.p. |
| DBGG | Dívida Bruta do Governo Geral | % PIB |

## B. Referências Bibliográficas e Fontes

- Banco Central do Brasil. Sistema de Expectativas de Mercado (Boletim Focus). API Olinda.
- IBGE. SIDRA — Tabela 1737 (IPCA) e Tabela 5932 (PIB Trimestral).
- BCB. Sistema Gerenciador de Séries Temporais (SGS) — Séries 11 (Selic) e 13762 (DBGG).
- Newey, W.K.; West, K.D. (1987). "A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix." Econometrica 55(3): 703–708.
- Chow, G.C. (1960). "Tests of equality between sets of coefficients in two linear regressions." Econometrica 28(3): 591–605.
- Taylor, J.B. (1993). "Discretion versus policy rules in practice." Carnegie-Rochester Conference Series on Public Policy 39: 195–214.

## C. Inventário de Arquivos de Dados

| Arquivo | Conteúdo |
|---------|----------|
| `painel_focus_mvp.csv` | Painel semanal completo de expectativas Focus com controles |
| `comparacao_ipca_ano_fechamento.csv` | IPCA anual: Focus vs IBGE |
| `comparacao_ipca_mensal.csv` | IPCA mensal: Focus vs IBGE (série completa) |
| `comparacao_selic_ano_fechamento.csv` | Selic anual: Focus vs SGS |
| `comparacao_selic_mensal.csv` | Selic por reunião Copom: Focus vs realizado |
| `comparacao_pib_ano_fechamento.csv` | PIB anual: Focus vs IBGE |
| `comparacao_focus_dbgg.csv` | Dívida Bruta: Focus vs SGS |
| `econometria_ols_ipca_med12m_coef.csv` | Coeficientes HAC — Modelo IPCA |
| `econometria_ols_ipca_med12m_summary.txt` | Output statsmodels — Modelo IPCA |
| `econometria_ols_ipca_med12m_diagnosticos.txt` | Diagnósticos + Chow — IPCA |
| `econometria_ols_selic_mediana_pct_coef.csv` | Coeficientes HAC — Modelo Selic |
| `econometria_ols_selic_mediana_pct_summary.txt` | Output statsmodels — Modelo Selic |
| `econometria_ols_selic_mediana_pct_diagnosticos.txt` | Diagnósticos + Chow — Selic |
| `econometria_ols_pib_med_pct_coef.csv` | Coeficientes HAC — Modelo PIB |
| `econometria_ols_pib_med_pct_summary.txt` | Output statsmodels — Modelo PIB |
| `econometria_ols_pib_med_pct_diagnosticos.txt` | Diagnósticos + Chow — PIB |
| `econometria_ols_taylor_rule_coef.csv` | Coeficientes HAC — Regra de Taylor |
| `econometria_ols_taylor_rule_summary.txt` | Output statsmodels — Regra de Taylor |
| `econometria_ols_taylor_rule_diagnosticos.txt` | Diagnósticos + Chow — Taylor Rule |
| `metodologia_calculo_ipca.md` | Metodologia detalhada do alinhamento Focus × IBGE |
