# Handoff — Análises de dívida pública (MBA Economia FIPE)

Documento para continuar o trabalho em outra sessão/janela do Cursor.

**Última atualização:** 2026-06-02  
**Repositório:** `app-mba-economia-fipe`  
**Pasta principal de saída:** `output/DIVIDA/`

---

## 1. Objetivo do que já foi feito

Comparar **expectativas de mercado (Focus/BCB)** com **dados realizados (SGS/BCB)** para indicadores de dívida pública, janela principal **2019–2026** (2026 parcial: só Focus na DBGG).

Dois indicadores implementados:

| Indicador | Focus (Olinda) | Realizado (SGS) | Unidade |
|-----------|----------------|-----------------|---------|
| **DLSP** — Dívida Líquida do Setor Público | `Dívida líquida do setor público` | **4513** (% PIB), **4478** (R$ mi) | % PIB e R$ |
| **DBGG** — Dívida Bruta do Governo Geral | `Dívida bruta do governo geral` | **13762** (% PIB, metodologia ≥2008) | % PIB |

**Não confundir com DPF:** estoque da Dívida Pública Federal (Tesouro CKAN `estoque-da-divida-publica-federal`) é dívida mobiliária **federal**; carteira **Mercado** (~R$ 8,6 tri mar/2026) ≠ DLSP ≠ DBGG.

---

## 2. Metodologia comparativa (padrão do projeto)

Para cada **ano-calendário Y**:

1. **Focus:** mediana anual (`ExpectativasMercadoAnuais`, `DataReferencia = Y`)
2. **Última survey antes da divulgação:** proxy **01/05/(Y+1)** (`SeriesConfig.dlsp_anual_divulgacao_*`)
3. **Realizado:** fechamento **dezembro/Y** na série SGS mensal
4. **Erro:** `focus_ultima_mediana − realizado` em **pontos percentuais** (% PIB)

Prioriza `baseCalculo` 1 em duplicatas Olinda (`focus_extract._prefer_base_calculo`).

---

## 3. Estrutura de arquivos gerados

```
output/DIVIDA/
├── comparacao_focus_dlsp_anual.csv      # DLSP 2019–2025
├── comparacao_focus_dbgg_anual.csv      # DBGG 2019–2026 (2026 só Focus)
├── previa_dlsp_reais.csv                # DLSP em R$ (SGS 4478)
├── focus_dlsp_*.csv, dlsp_sgs4513_anual.csv, gráficos DLSP na raiz
├── {2019..2026}/                        # DBGG por ano (6 CSV + metadados)
├── periodos/
│   ├── 2019-2022/   # CSVs + 5 PNGs DBGG
│   ├── 2023-2026/
│   └── 2019-2026/
└── NotebookLM/                          # Pacote pronto p/ upload (21 arquivos)
    ├── 00-glossario-conceitos.txt
    ├── 09-resumo-executivo.md
    ├── 07-tabela-consolidada-dbgg-dlsp.csv
    ├── 01–06 CSVs, metadados, graficos/
    └── 08-guia-notebooklm.md
```

---

## 4. Código Python (pacote `mba_economia`)

| Módulo | Função |
|--------|--------|
| `focus_extract.py` | `fetch_dlsp_expectativa_anual`, `fetch_dbgg_expectativa_anual` |
| `bcb_dlsp_sgs4513.py` | DLSP anual/mensal SGS 4513 |
| `bcb_dbgg_sgs13762.py` | DBGG anual/mensal SGS 13762 |
| `divida_dlsp_compare.py` | Comparação DLSP por ano |
| `divida_dbgg_compare.py` | Comparação DBGG + `complementar_anos_apenas_focus` (ex. 2026) |
| `figures.py` | `gerar_figuras_divida_dlsp`, `gerar_figuras_divida_dbgg` |
| `config.py` | SGS 4513, 4478, 13762; proxy divulgação 01/05 |

### Scripts CLI

```powershell
# DLSP (export raiz output/DIVIDA)
python scripts/exportar_divida_dlsp.py --ano-ini 2019 --ano-fim 2025
python scripts/graficos_divida_dlsp.py

# DBGG (pastas por ano)
python scripts/exportar_dbgg_anual.py --ano-ini 2019 --ano-fim 2026

# DBGG comparativos por período + gráficos
python scripts/comparativos_dbgg_periodos.py

# DLSP em R$ (prévia)
python scripts/previa_dlsp_reais.py --ano-ini 2019 --ano-fim 2025

# Pacote NotebookLM
python scripts/preparar_notebooklm_divida.py
```

Instalar: `pip install -e .` na raiz do repo.

---

## 5. Principais achados (até aqui)

### DLSP (% PIB) — Focus superestima todos os anos

| Ano | Focus | Realizado | Erro (p.p.) |
|-----|-------|-----------|-------------|
| 2019 | 56,0 | 54,7 | +1,3 |
| 2025 | 66,0 | 65,2 | +0,7 |

DLSP nominal (dez): **R$ 4,0 tri (2019) → R$ 8,3 tri (2025)** (SGS 4478).

### DBGG (% PIB) — Focus superestima; erro caiu no tempo

| Período | Erro médio (p.p.) |
|---------|-------------------|
| 2019–2022 | ~3,1 |
| 2023–2025 | ~1,2 |
| 2026 | Focus ~83,3%; **sem realizado** |

---

## 6. Fontes oficiais

- **Focus:** https://dadosabertos.bcb.gov.br/dataset/expectativas-mercado  
  API: `https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata`
- **DLSP % PIB:** SGS 4513 — https://dadosabertos.bcb.gov.br/dataset/4513-divida-liquida-do-setor-publico--pib---total---setor-publico-consolidado
- **DLSP R$:** SGS 4478 — setor público consolidado, milhões de reais
- **DBGG % PIB:** SGS 13762 — https://dadosabertos.bcb.gov.br/dataset/13762-divida-bruta-do-governo-geral--pib---metodologia-utilizada-a-partir-de-2008
- **DPF estoque (não integrado):** https://www.tesourotransparente.gov.br/ckan/dataset/estoque-da-divida-publica-federal  
  CSV `estoquedpf.csv`; total headline **Mercado** = soma `Valor do Estoque` onde `Classe da Carteira = Mercado`

---

## 7. O que NÃO foi feito (candidatos à próxima análise)

- [ ] **DPF Tesouro** vs expectativas (Focus não tem DPF; comparar só realizado ou outra proxy)
- [ ] **DBGG em R$** (buscar série SGS nominal consolidada, análoga à 4478 para DLSP)
- [ ] **Resultado primário** Focus vs realizado (indicador existe no Focus)
- [ ] **DLSP comparativos por período** (espelhar `comparativos_dbgg_periodos.py`)
- [ ] **Visualização web** (padrão `pib-focus-viz/` para dívida)
- [ ] **Integrar DPF** (CKAN): estoque Mercado mensal, LFT/Selic, mar→abr 2026
- [ ] Revisar proxy de divulgação (01/05) vs calendário STN real
- [ ] Erro em **variação YoY** (p.p.) além do nível % PIB

---

## 8. Portar para a Mac principal (Git)

```powershell
python scripts/empacotar_port_divida.py
```

Pacote em `dist/port-divida/`. Guia completo: `docs/PORTAR-DIVIDA-MAC-PRINCIPAL.md`.

Fluxo: copiar pacote → Mac → integrar só `config.py` → push → `git pull` nesta máquina.

---

## 9. Prompt sugerido para a nova janela

Copie e adapte:

> Continuo o projeto `app-mba-economia-fipe`. Leia `output/DIVIDA/HANDOFF.md` e o pacote `output/DIVIDA/NotebookLM/`.  
> Já temos comparação Focus × realizado para **DLSP** (SGS 4513/4478) e **DBGG** (SGS 13762), 2019–2026, em `output/DIVIDA/`.  
> Quero agora: **[descreva a próxima análise, ex.: DPF Tesouro mensal, resultado primário, DBGG em R$, etc.]**.

---

## 9. Armadilhas conhecidas

1. **PowerShell:** evitar `&&`; usar `;` ou scripts `.py`
2. **Olinda OData:** filtros com acento — usar `contains(Indicador,'bruta')` e filtrar no pandas
3. **2026 DBGG:** `complementar_anos_apenas_focus` usa última survey antes de 01/05/2027
4. **DPF CKAN:** CSV pode ir até 03/2026 enquanto matéria de imprensa cita 04/2026
5. **Conceitos:** DLSP ⊃ escopo diferente de DBGG ⊃ escopo diferente de DPF federal

---

## 10. Git

Arquivos em `output/` e scripts novos podem estar **untracked** (ver git status inicial da sessão). Nenhum commit automático foi feito neste fluxo.
