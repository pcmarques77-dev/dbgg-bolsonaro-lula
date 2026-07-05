# Guia de Prompts para Insights — TCC MBA Economia FIPE

**Objetivo:** Extrair insights acadêmicos dos dados exportados usando Gemini e NotebookLM.
**Dica geral:** No NotebookLM, as respostas são ancoradas nos documentos carregados (citações diretas). No Gemini, você pode pedir análises mais criativas e cruzamentos com conhecimento externo.

---

## 🏛️ BLOCO 1 — Estrutura e Narrativa do TCC

Perguntas para ajudar a organizar a monografia.

### NotebookLM
> "Com base nos dados e resultados econométricos fornecidos, elabore um esboço de sumário (índice) para uma monografia de TCC de MBA que investiga as diferenças nas expectativas de mercado entre os governos Bolsonaro e Lula 3."

> "Quais são os 5 principais achados empíricos deste estudo? Para cada um, indique a evidência quantitativa (número, p-valor ou teste) que o sustenta."

> "Redija um parágrafo de introdução acadêmica para este TCC, contextualizando o Boletim Focus como ferramenta de política monetária e justificando a relevância de comparar dois governos."

> "Com base nos resultados dos 4 modelos econométricos, redija a seção de 'Conclusão' da monografia, organizando os achados em ordem de relevância estatística."

### Gemini
> "Sou aluno de MBA em Economia pela FIPE e estou escrevendo um TCC sobre expectativas de mercado (Boletim Focus) comparando Bolsonaro e Lula 3. Com base nos resultados que forneci, sugira uma estrutura de capítulos que equilibre rigor acadêmico com narrativa acessível para uma banca de MBA."

> "Quais são as possíveis críticas que uma banca de MBA poderia fazer a este estudo? Como posso antecipá-las e mitigá-las na seção de limitações?"

---

## 📊 BLOCO 2 — Análise Descritiva (Fase 1 / Topo do Funil)

Perguntas sobre os dados comparativos Focus vs Realizado.

### NotebookLM
> "Comparando os MAEs de todos os indicadores, em qual variável o mercado foi MAIS preciso e em qual foi MENOS preciso? Essa diferença se mantém entre os dois governos?"

> "O mercado sistematicamente superestimou ou subestimou algum indicador? Identifique os vieses direcionais para IPCA, Selic, PIB e DBGG e discuta se eles mudaram entre Bolsonaro e Lula 3."

> "No IPCA mensal, os erros de previsão se concentram em quais meses do ano? Existe sazonalidade no erro do mercado?"

> "A DBGG foi superestimada em TODOS os anos analisados. Isso configura um viés pessimista fiscal do mercado? Elabore uma hipótese explicativa."

> "Analise a trajetória de convergência da DBGG para os anos-alvo de 2019 a 2026. Como a expectativa do Focus evolui ao longo dos meses para cada ano? Destaque a disparidade entre o pico de estresse projetado para 2023 no auge de 2020 (~93%) e o valor oficial final divulgado (73,83%)."

> "Compare o erro de previsão e a volatilidade da trajetória da Dívida Bruta (DBGG) com a Dívida Líquida (DLSP). O mercado é mais preciso em estimar o conceito bruto ou o conceito líquido da dívida?"

> "Se excluirmos 2020 (pandemia) da amostra de Bolsonaro, os MAEs dos dois governos ficam mais próximos? O que isso implica para a comparação?"

### Gemini
> "Tenho dados de MAE do Focus para IPCA, Selic, PIB e DBGG em dois governos. O MAE de Bolsonaro é consistentemente maior. Ajude-me a construir um argumento acadêmico que separe o 'efeito pandemia' do 'efeito governo' na análise descritiva, ANTES de usar econometria."

> "Com base na literatura de expectativas racionais e adaptive expectations, como posso interpretar o fato de o mercado subestimar sistematicamente o PIB no governo Lula 3 (-2,40, -1,65, -0,18 p.p.)? Isso é consistente com pessimismo estrutural ou com surpresas de política econômica?"

---

## 🧮 BLOCO 3 — Análise Econométrica (Fase 2 / Fundo do Funil)

Perguntas sobre os resultados dos modelos OLS com HAC.

### NotebookLM
> "No modelo de IPCA, a dummy_lula tem coeficiente -0,628 (p<0,001). No modelo de Selic, a dummy_lula tem coeficiente +1,690 (p<0,001). Explique essa aparente contradição: o mercado espera MENOS inflação mas MAIS juros no Lula 3. O que isso revela sobre a percepção de risco?"

> "Compare os R² dos quatro modelos. Qual modelo tem maior poder explicativo? O que isso diz sobre quais expectativas são mais influenciadas por fatores globais vs domésticos?"

> "O Teste de Chow rejeita estabilidade em todos os 4 modelos. O que isso significa em termos econômicos? A sensibilidade do mercado a choques externos realmente mudou ou é apenas um efeito de nível?"

> "Na Regra de Taylor, o coeficiente de desancoragem é 2,676. Isso é maior ou menor do que o coeficiente teórico de Taylor (1,5)? O que essa diferença implica sobre a agressividade esperada do BCB?"

> "O VIX não é significante no modelo de IPCA (p=0,245) mas é significante no modelo de PIB (p<0,001) e de Selic (p<0,001). Explique por que a volatilidade global afeta expectativas de crescimento e juros, mas não de inflação no Brasil."

> "Os testes ADF mostram que ipca_med12m, selic_mediana_pct, pib_med_pct e commodities NÃO são estacionários. Isso é um problema para a validade dos modelos OLS? Como os erros robustos HAC mitigam parcialmente essa questão? Quais limitações permanecem?"

### Gemini
> "Estou usando OLS com erros HAC (Newey-West) em séries temporais de expectativas Focus. O Durbin-Watson é ~0,03, os testes ADF não rejeitam raiz unitária para a maioria das variáveis. Uma banca rigorosa poderia questionar a validade dos resultados. Que argumentos posso usar para defender a abordagem, e quais alternativas (VECM, cointegração, primeiras diferenças) eu deveria mencionar como extensões futuras?"

> "O coeficiente da dummy_lula na Regra de Taylor é +3,296 (p<0,001). Isso significa que, para o MESMO nível de desancoragem inflacionária, o mercado espera Selic 3,3 p.p. maior no Lula 3. Como posso interpretar esse 'prêmio' à luz da literatura sobre dominância fiscal, risco político e credibilidade do Banco Central? Sugira referências acadêmicas."

> "O Teste de Chow deu F = 631,6 na Regra de Taylor e F = 50,6 no PIB. Por que a quebra estrutural é tão mais forte na relação Selic-desancoragem do que na relação PIB-choques? Construa uma narrativa econômica para essa diferença."

---

## 🔍 BLOCO 4 — Cruzamentos e Insights Originais

Perguntas para descobrir padrões não óbvios nos dados.

### NotebookLM
> "Existe alguma relação entre os erros de previsão da Selic e os erros de previsão do IPCA? Quando o mercado erra mais a inflação, ele também erra mais os juros? Analise a correlação entre os erros nos dois governos."

> "A DBGG subiu ~2,3 p.p. ao ano no Lula 3, enquanto oscilou violentamente no Bolsonaro. Ao mesmo tempo, o coeficiente de Selic da dummy_lula é +1,69. Isso é consistente com a hipótese de dominância fiscal — o mercado espera juros mais altos PORQUE a dívida está em trajetória ascendente?"

> "Compare o comportamento da dummy_pandemia nos modelos de IPCA (+0,183, p=0,01), Selic (-2,341, p<0,001) e PIB (+0,537, p=0,175). A pandemia afetou as expectativas de qual variável de forma mais intensa? Por que o efeito no PIB não foi significante?"

> "A desancoragem da inflação (desvio em relação à meta) é o regressor mais forte da Regra de Taylor (coef = 2,676). Isso significa que o mercado confia que o BCB vai reagir à desancoragem? Ou é simplesmente uma correlação mecânica?"

### Gemini
> "Com meus dados, identifiquei que o mercado espera menos inflação mas mais juros no Lula 3. No governo Bolsonaro, a pandemia causou os maiores erros de previsão. Sintetize esses achados em uma 'tese central' de 2-3 frases que eu possa usar como argumento principal do TCC."

> "Imagine que estou apresentando esses resultados para uma banca que inclui um economista do mercado financeiro e um professor acadêmico. Quais perguntas cada um faria? Como devo me preparar para respondê-las?"

> "Se eu pudesse adicionar UMA variável a mais nos modelos, qual seria a mais relevante do ponto de vista econômico? (ex: câmbio, risco-país EMBI+, resultado primário, credibilidade do BCB). Justifique."

---

## 📝 BLOCO 5 — Redação e Revisão Acadêmica

Perguntas para ajudar na escrita da monografia.

### NotebookLM
> "Reescreva a tabela de coeficientes do modelo de IPCA em formato de texto acadêmico, como seria apresentada em uma seção de 'Resultados' de um paper. Use notação padrão (asteriscos para significância, parênteses para erro padrão)."

> "Redija um parágrafo acadêmico interpretando o resultado do Teste de Chow do modelo de Selic (F=554,34, p=0,000) no contexto de mudança de regime de expectativas."

> "Crie uma nota de rodapé técnica explicando por que usamos erros padrão HAC (Newey-West) em vez de OLS convencional, adequada para um leitor de nível MBA."

### Gemini
> "Revise este parágrafo da minha monografia para melhorar a clareza e o tom acadêmico: [cole seu parágrafo aqui]. Mantenha os dados e conclusões, mas refine a linguagem."

> "Sugira 10 referências bibliográficas (artigos, livros e working papers) que fundamentem: (1) o uso do Boletim Focus como proxy de expectativas, (2) a metodologia de Newey-West em séries temporais, (3) a hipótese de dominância fiscal no Brasil, (4) a Regra de Taylor aplicada a expectativas."

> "Crie um abstract (resumo) em português e em inglês para este TCC, com no máximo 250 palavras cada, incluindo objetivo, metodologia, principais resultados e conclusão."

---

## 🎯 BLOCO 6 — Perguntas de Alto Impacto (Top 10)

As perguntas mais poderosas para gerar insights diferenciados.

| # | Pergunta | Melhor em | Finalidade |
|---|----------|-----------|------------|
| 1 | "Por que o mercado espera MENOS inflação mas MAIS juros no Lula 3? Construa o argumento econômico completo." | Gemini | Tese central |
| 2 | "O prêmio de +3,3 p.p. na Regra de Taylor é de risco fiscal, político ou institucional? Diferencie." | Gemini | Profundidade |
| 3 | "Se eu removesse os anos 2020–2021 da amostra, os resultados mudariam qualitativamente?" | NotebookLM | Robustez |
| 4 | "O teste de Chow mostra quebra estrutural. Mas é quebra de NÍVEL ou de SENSIBILIDADE? Analise." | NotebookLM | Precisão técnica |
| 5 | "Quais limitações metodológicas devo reconhecer? Liste pelo menos 5 com suas mitigações." | Gemini | Defesa de banca |
| 6 | "A dummy_pandemia é significante em 2 de 4 modelos. Isso enfraquece ou fortalece a análise?" | NotebookLM | Interpretação |
| 7 | "Elabore a seção de Revisão da Literatura com subtópicos e referências sugeridas." | Gemini | Redação |
| 8 | "Os resíduos não são normais (Jarque-Bera rejeita). Isso invalida as inferências com HAC?" | NotebookLM | Rigor técnico |
| 9 | "Compare meus achados com a literatura sobre expectativas do Focus (ex: Marques 2013, Carvalho & Minella 2012)." | Gemini | Contextualização |
| 10 | "Crie 3 slides-resumo para apresentação de defesa do TCC com os dados mais impactantes." | Gemini | Apresentação |

---

## 💡 Dica Final: Encadeamento de Prompts

Para obter resultados mais profundos, use prompts em sequência:

1. **Primeiro:** "Resuma os principais resultados dos 4 modelos econométricos."
2. **Depois:** "Agora, identifique contradições ou paradoxos entre esses resultados."
3. **Depois:** "Para cada contradição, proponha uma explicação econômica fundamentada."
4. **Por fim:** "Redija um parágrafo acadêmico que sintetize essas explicações em uma narrativa coerente."

Esse encadeamento funciona especialmente bem no Gemini, que mantém o contexto da conversa.
