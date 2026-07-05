# Metodologia de Cálculo — Simulador Contra-Fatual da DBGG (Bolsonaro vs Lula 3)

Este documento detalha a formulação matemática, a calibração de parâmetros e as premissas metodológicas utilizadas para modelar a trajetória da **Dívida Bruta do Governo Geral (DBGG)** em termos percentuais do PIB.

---

## 1. Equação de Dinâmica da Dívida Pública

A evolução da relação Dívida/PIB de um ano para o outro é descrita pela equação clássica de sustentabilidade da dívida pública, amplamente empregada pelo Fundo Monetário Internacional (FMI) e pelo Banco Central do Brasil:

$$D_t = D_{t-1} \times \left( \frac{1 + i_t}{1 + g_t} \right) - S_t$$

Onde:
* **$D_t$**: Dívida Bruta ao final do ano $t$ (expressa como % do PIB).
* **$D_{t-1}$**: Dívida Bruta ao final do ano anterior $t-1$ (expressa como % do PIB).
* **$i_t$**: Taxa de juros nominal implícita acumulada que incide sobre o estoque da dívida durante o ano $t$.
* **$g_t$**: Taxa de crescimento nominal do PIB no ano $t$ (que engloba o crescimento real da atividade e o deflator do PIB).
* **$S_t$**: Resultado Primário do Governo Central apurado durante o ano $t$ (expresso como % do PIB). Valores positivos representam superávit primário e valores negativos representam déficit primário.

---

## 2. Dedução Algébrica da Equação

Para entender a origem da fórmula, partimos dos valores nominais (em moeda corrente):

$$\text{Dívida Nominal}_t = \text{Dívida Nominal}_{t-1} \times (1 + i_t) - \text{Resultado Primário Nominal}_t$$

Dividindo ambos os lados da equação pelo **PIB Nominal** do ano $t$ ($\text{PIB}_t$):

$$\frac{\text{Dívida Nominal}_t}{\text{PIB}_t} = \left( \frac{\text{Dívida Nominal}_{t-1}}{\text{PIB}_t} \right) \times (1 + i_t) - \frac{\text{Resultado Primário Nominal}_t}{\text{PIB}_t}$$

Sabendo que o PIB do ano $t$ é o PIB do ano anterior reajustado pela taxa de crescimento nominal $g_t$ (ou seja, $\text{PIB}_t = \text{PIB}_{t-1} \times (1 + g_t)$):

$$D_t = \left( \frac{\text{Dívida Nominal}_{t-1}}{\text{PIB}_{t-1} \times (1 + g_t)} \right) \times (1 + i_t) - S_t$$

Substituindo a definição da dívida do ano anterior ($D_{t-1} = \frac{\text{Dívida Nominal}_{t-1}}{\text{PIB}_{t-1}}$):

$$D_t = D_{t-1} \times \left( \frac{1 + i_t}{1 + g_t} \right) - S_t$$

---

## 3. Calibração do Custo da Dívida (Juros Implícitos)

Em vez de usar uma taxa arbitrária ou apenas a taxa Selic média (que não captura integralmente os prazos de vencimento da dívida, a parcela pré-fixada ou os títulos indexados à inflação), calibramos a **taxa de juro implícita nominal** ($i_t$) a partir dos próprios dados históricos reais apurados.

Isolando $i_t$ na equação dinâmica:

$$1 + i_t = \frac{(D_t + S_t) \times (1 + g_t)}{D_{t-1}}$$

$$i_t = \frac{(D_t + S_t) \times (1 + g_t)}{D_{t-1}} - 1$$

Ao aplicar esta taxa implícita calibrada $i_t$ nas simulações, garantimos que o cenário de controle (onde mantemos o primário real) reproduz com precisão absoluta de $100\%$ a trajetória oficial observada da dívida.

### Exemplo de Calibração Histórica (2025):
* Dívida em 2024 ($D_{t-1}$): $76,27\%$
* Dívida em 2025 ($D_t$): $78,64\%$
* Resultado Primário em 2025 ($S_t$): $-0,45\%$ (déficit)
* Crescimento do PIB Nominal em 2025 ($g_t$): $8,14\%$
* Cálculo do Juro Implícito ($i_{2025}$):
  $$i_{2025} = \frac{(78,64 - 0,45) \times (1 + 0,0814)}{76,27} - 1 = 10,87\%$$

---

## 4. Construção dos Cenários Contra-Fatuais

Os cenários contra-fatuais simulam trajetórias alternativas isolando o efeito da política fiscal (*ceteris paribus*):

### Cenário A: Bolsonaro com Política Fiscal de Lula 3 (2019-2022)
Substitui-se o Resultado Primário anual de Bolsonaro ($S_t$) pela **média de resultado primário observada no governo Lula 3** (média de $-1,08\%$ do PIB).
* O ponto de partida é a dívida real de $2018$ ($75,27\%$).
* Para cada ano de $2019$ a $2022$, aplica-se a fórmula substituindo $S_t$ por $-1,08\%$, mas mantendo os custos de juros ($i_t$) e o crescimento nominal ($g_t$) exatamente iguais aos ocorridos no governo Bolsonaro histórico.
* A partir de $2023$ (Lula 3), a simulação retoma as séries fiscais reais ocorridas, mas acumulando a dívida a partir da nova base herdada de $2022$.

### Cenário B: Lula 3 com Política Fiscal de Bolsonaro (2023-2025)
Substitui-se o Resultado Primário anual de Lula 3 ($S_t$) pela **média de resultado primário observada no governo Bolsonaro** (média de $-2,71\%$ do PIB).
* Até $2022$, a dívida acumulada segue a trajetória histórica real (terminando em $71,68\%$).
* Para cada ano de $2023$ a $2025$, aplica-se a fórmula substituindo $S_t$ por $-2,71\%$, mas mantendo os juros ($i_t$) e o crescimento ($g_t$) reais do governo Lula 3.

---

## 5. Limitações e Notas Metodológicas

* **Hipótese Ceteris Paribus:** O modelo assume que taxas de juros ($i_t$) e crescimento do PIB ($g_t$) são variáveis exógenas que não reagem a alterações no resultado primário. Na realidade, uma melhora fiscal crível pode reduzir prêmios de risco (juros menores) e estimular investimentos (maior crescimento), enquanto desvios fiscais podem acelerar a inflação e forçar o Banco Central a manter juros mais altos.
* **Resultado Primário Usado:** Empregamos o Resultado Primário do Governo Central apurado de acordo com o critério abaixo da linha (Necessidades de Financiamento do Setor Público - NFSP), que é o padrão utilizado pelo Banco Central para compatibilidade com o estoque da dívida líquida e bruta.

---

## 6. Fontes e Códigos de Dados (Banco Central SGS)

| Código SGS | Nome da Série | Unidade | Função no Modelo |
|---|---|---|---|
| **13762** | Dívida bruta do governo geral (% PIB) | % | Estoque da Dívida ($D_t$) |
| **5784** | NFSP - Governo Federal (Resultado Primário) | % PIB | Cálculo do Resultado Primário ($S_t = -1 \times \text{NFSP}$) |
| **1207** | PIB acumulado nos últimos 12 meses | R$ Milhões | Cálculo do Crescimento Nominal ($g_t$) |
