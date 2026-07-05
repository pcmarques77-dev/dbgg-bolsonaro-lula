from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SeriesConfig:
    """Séries e convenções citáveis na monografia."""

    # USD nominal diário (tipo Livre/A). NB: código 3698 no SGS só traz marcação mensal (01/mm).
    sgs_codigo_usd_diario: int = 1

    proxy_ibovespa: str = "^BVSP"
    proxy_vix: str = "^VIX"
    proxy_commodities: str = "DBC"  # Invesco DB Commodity Index (proxy CRB)

    months_ahead_cambio: int = 12

    # Último pregão até N dias úteis **antes** da data Focus (padrão: 1)
    market_lag_bdias: int = 1

    # SIDRA IPCA tabela 1737 — https://sidra.ibge.gov.br/tabela/1737
    sidra_tab_ipca_acum12: int = 1737
    sidra_codigo_var_ipca_mensal: int = 63  # variação mensal (%)
    sidra_codigo_var_ipca_acum_ano: int = 69  # variação acumulada no ano-calendário (%)
    sidra_codigo_var_acum12m: int = 2265  # variação acumulada em 12 meses (%)
    # Proxies de calendário: divulgação ~ início do mês seguinte ao de referência
    sidra_ipca_disponivel_dia_mes_seguinte: int = 10

    # Taxa Selic diária (% a.d.), SGS código 11 — https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic
    sgs_codigo_selic_diaria: int = 11

    # PIB nominal em R$ correntes (SGS, codigo 1207; portal dadosabertos.bcb dataset 1207-sgs)
    sgs_codigo_pib_rs_correntes: int = 1207
    # ~60 dias após 31/12 do ano de referência para proxy de primeira divulgação (versão preliminar)
    sgs_pib1207_dias_apos_31dez_divulgacao: int = 67

    # Contas Nacionais anuais IBGE SIDRA — "PIB - variação em volume" (% ano/ano por referência IBGE)
    sidra_tab_pib_anual_vol: int = 6784
    sidra_codigo_var_pib_vol_anual_pct: int = 9810
    # Proxy da primeira divulgação do resultado do ano Y (após fechamento 31/12)
    # Proxy da primeira divulgação do resultado do ano Y (após fechamento 31/12)
    sidra_pib_vol_anual_dias_apos_31dez: int = 100

    # Contas Nacionais trimestrais IBGE SIDRA — taxa de variação do índice de volume (t5932)
    sidra_tab_pib_trim_vol: int = 5932
    sidra_class_pib_setores_trim: str = "c11255"
    sidra_codigo_pib_mercado_vol_trim: int = 90707

    # DLSP (% PIB), setor público consolidado
    sgs_codigo_dlsp_pct_pib: int = 4513
    dlsp_anual_divulgacao_mes_ano_seguinte: int = 5
    dlsp_anual_divulgacao_dia_mes: int = 1

    # DBGG (% PIB), governo geral (metodologia a partir de 2008)
    sgs_codigo_dbgg_pct_pib: int = 13762


    # Proxy divulgação 4T do ano Y (Contas Nacionais trimestrais ~ março Y+1)
    pib_ibge_4tri_disponivel_mes_ano_seguinte: int = 3
    pib_ibge_4tri_disponivel_dia: int = 1


DEFAULT_START = date(2019, 1, 1)

# Gráficos ``ipca-ano-por-ano``: um PNG por ano-calendário de referência Focus
IPCA_ANOS_CALENDARIO_GRAFICOS: tuple[int, ...] = tuple(range(2018, 2027))

# Piloto IPCA ano-calendário (trajetória mensal da expectativa × realizado jan–dez)
IPCA_ANUAL_OUTPUT_DIR = "IPCA Anual"

# Piloto Selic fim de ano-calendário (trajetória mensal × SGS 11 fechamento dez.)
SELIC_ANUAL_OUTPUT_DIR = "Selic Anual"

# Piloto Selic mensal por reunião (mês de referência × SGS fechamento do mês)
SELIC_OUTPUT_DIR = "Selic"

# Cruzamento exploratório IPCA ano-calendário × Selic fim de ano (trajetórias Focus)
IPCA_SELIC_CROSS_OUTPUT_DIR = "IPCA x Selic"

# Piloto PIB ano-calendário (trajetória mensal Focus × IBGE 4T acumulado, JSON manual)
PIB_OUTPUT_DIR = "PIB"

# Piloto Câmbio forward (trajetória mensal Focus × SGS 1 no mês DataReferencia)
CAMBIO_OUTPUT_DIR = "Cambio"

OLINDA_BASE = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata"
)

# API de valores SIDRA (IBGE): https://apisidra.ibge.gov.br/home/ajuda
SIDRA_IBGE_VALUES_BASE = "https://apisidra.ibge.gov.br/values"


def today_date() -> date:
    return date.today()


def as_ddmmyyyy(d: date) -> str:
    return d.strftime("%d/%m/%Y")
