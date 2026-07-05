# Metodologia de Comparação: IPCA Focus vs. IBGE

Este documento descreve detalhadamente as regras de negócio, o alinhamento temporal, as fontes de dados e os cálculos matemáticos utilizados no cruzamento das expectativas do mercado (Boletim Focus / Banco Central do Brasil) com os dados oficiais de inflação realizada (IPCA / IBGE). 

O objetivo principal desta modelagem é calcular o erro de previsão de curto e médio prazo do mercado para identificar vieses sistemáticos (subestimativas ou superestimativas) e entender a velocidade de reação e convergência das expectativas diante de choques inflacionários.

---

## 1. Fontes de Dados

### 1.1. Expectativas de Mercado (Focus/BCB)
As expectativas são extraídas do **Sistema de Expectativas de Mercado (API OData do Portal Olinda do Banco Central do Brasil)**. 
* **Série Mensal**: `ExpectativasMercadoMensais` — Coleta a variação percentual mensal esperada para o IPCA.
* **Série Anual**: `ExpectativasMercadoAnuais` — Coleta a variação acumulada anual esperada para o IPCA no ano de referência (ano-calendário).
* **Métrica utilizada**: **Mediana** das expectativas fornecidas pelas instituições cadastradas na pesquisa (Bancos, Assets, Consultorias, etc.).

### 1.2. Inflação Realizada (IBGE)
Os dados de inflação final realizada são extraídos da **API SIDRA do IBGE**, utilizando a **Tabela 1737** (Índice Nacional de Preços ao Consumidor Amplo):
* **IPCA Mensal**: Variável `63` (Variação mensal do IPCA em %).
* **IPCA Anual**: Variável `69` (Variação acumulada no ano em %, especificamente a leitura de dezembro de cada ano, que consolida o fechamento anual).

---

## 2. Alinhamento Temporal e Regras de Negócio

Para que a comparação entre previsão e realizado seja justa e estatisticamente válida, é necessário aplicar regras rígidas de alinhamento de datas, dado que as previsões variam diariamente enquanto o realizado é uma variável mensal de divulgação defasada.

### 2.1. IPCA Mensal — Expectativa Final do Mês vs. Realizado
Esta metodologia compara a previsão de curtíssimo prazo ajustada pelo mercado no final do próprio mês de referência com o valor final divulgado semanas depois.
* **Regra Focus (Previsão)**: Para cada mês de referência $M$, busca-se a última expectativa divulgada dentro do próprio mês $M$. A regra seleciona a mediana reportada na **última segunda-feira do mês de referência** (ou primeiro dia útil seguinte em caso de feriados e atrasos oficiais da API do BCB).
* **Comparação**: Essa última expectativa do mês $M$ é confrontada com o IPCA realizado do mês $M$ (divulgado pelo IBGE aproximadamente no 10º dia do mês $M+1$).

### 2.2. IPCA Mensal — Expectativa Inicial do Ano vs. Realizado
Esta metodologia avalia a acurácia preditiva de médio prazo, verificando o que o mercado projetava no início do ano para cada um dos 12 meses seguintes.
* **Regra Focus (Previsão)**: Para o ano de referência $Y$ e um mês $M$ pertencente a esse ano, filtra-se a **primeira expectativa divulgada no primeiro boletim Focus de janeiro do ano $Y$**.
* **Comparação**: Essa primeira expectativa (coletada em janeiro de $Y$) é congelada e comparada individualmente com os IPCA realizados de janeiro a dezembro de $Y$. Ela demonstra o cenário de base traçado pelo mercado na partida do ano.

### 2.3. IPCA Anual — Expectativa Inicial vs. Fechamento
Esta metodologia afere a acurácia da projeção anual completa no início do ciclo.
* **Regra Focus (Previsão)**: Seleciona-se a mediana projetada para o IPCA acumulado do ano de referência $Y$ divulgada no **primeiro boletim Focus do próprio ano $Y$** (primeira segunda-feira útil de janeiro).
* **Comparação**: Essa estimativa inicial é comparada com o IPCA acumulado de janeiro a dezembro divulgado pelo IBGE (leitura de fechamento de dezembro, disponibilizada em janeiro do ano $Y+1$).

### 2.4. IPCA Anual — Trajetória Mensal das Expectativas
Esta metodologia monitora como a projeção para o fechamento do ano corrente é recalculada pelos analistas conforme os meses passam.
* **Regra Focus (Previsão)**: Para o ano de referência $Y$, extrai-se a expectativa para o IPCA acumulado anual divulgada na **primeira segunda-feira de cada um dos meses do ano** (de janeiro a dezembro). 
* **Comparação**: As 12 previsões mensais são plotadas sequencialmente contra o mesmo valor de fechamento anual (IPCA acumulado divulgado em dezembro), permitindo observar visualmente em qual mês do ano a expectativa do mercado finalmente convergiu para o resultado real da economia.

---

## 3. Fórmulas de Cálculo e Métricas de Erro

Para quantificar a dispersão e a direção do erro preditivo, aplicamos as seguintes fórmulas sobre as séries alinhadas:

### 3.1. Erro de Previsão Absoluto
Calcula a diferença direta entre o valor previsto e o realizado, expressa em pontos percentuais (p.p.):

$$\text{Erro de Previsão (p.p.)} = \text{IPCA}_{\text{Focus}} - \text{IPCA}_{\text{IBGE}}$$

**Interpretação Econômica:**
* **Erro Positivo ($> 0$ p.p.)**: Indica **Superestimativa**. O mercado projetou uma inflação mais alta do que a que de fato ocorreu.
* **Erro Negativo ($< 0$ p.p.)**: Indica **Subestimativa**. O mercado projetou uma inflação mais baixa do que a real. Representa cenários de aceleração inflacionária surpresa ou desancoragem tardia.

### 3.2. Erro Absoluto Médio (MAE)
Usado para consolidar o erro geral de previsões de um determinado período sem que erros positivos e negativos se anulem:

$$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} \left| \text{IPCA}_{\text{Focus}, i} - \text{IPCA}_{\text{IBGE}, i} \right|$$

---

## 4. Estrutura de Saída dos Arquivos de Dados

Os dados gerados por essa metodologia são exportados em tabelas estruturadas contendo:
* `ref_yyyymm` / `mes_publicacao`: Períodos de referência temporais padronizados.
* `survey_date_previsao`: Data exata do Boletim Focus em que a mediana foi extraída.
* `ipca_focus_med_mensal_pct` / `ipca_focus_ano_pct`: A mediana da expectativa da taxa de variação percentual.
* `ipca_ibge_mensal_pct` / `ipca_ibge_acum_ano_dez_pct`: O valor oficial apurado pelo IBGE.
* `erro_prev_menos_real_pp`: O resultado algébrico da fórmula de erro em pontos percentuais.
