"""Script de simulação contra-fatual da DBGG (Bolsonaro vs Lula 3) - Versão Avançada.

Calcula o custo implícito da dívida, introduz a série estrutural (sem Covid)
e projeta as trajetórias de base (baseline) de 2026 a 2030.
"""

from pathlib import Path
import pandas as pd
import requests

# Configurações de diretório
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_sgs(codigo: int) -> pd.DataFrame:
    """Busca série temporal do SGS do Banco Central."""
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
    print(f"Buscando SGS {codigo}...")
    res = requests.get(url)
    res.raise_for_status()
    df = pd.DataFrame(res.json())
    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    df["valor"] = pd.to_numeric(df["valor"].str.replace(",", "."))
    return df

def main():
    print("=== INICIANDO SIMULAÇÃO FISCAL AVANÇADA DA DBGG (2018-2030) ===")
    
    # 1. Carregar dados do SGS
    # 13762: DBGG (% PIB)
    # 5784: NFSP Governo Central - Resultado Primário (% PIB acumulado 12m)
    # 1207: PIB nominal acumulado 12m (R$ milhões)
    
    dbgg_raw = fetch_sgs(13762)
    nfsp_raw = fetch_sgs(5784)
    pib_raw = fetch_sgs(1207)
    
    # Filtrar para valores de dezembro
    def filtrar_dezembro(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
        df_copy = df.copy()
        df_copy["ano"] = df_copy["data"].dt.year
        df_copy["mes"] = df_copy["data"].dt.month
        
        dez = df_copy[df_copy["mes"] == 12].copy()
        
        ultimo_ano = df_copy["ano"].max()
        if ultimo_ano not in dez["ano"].values:
            ultimo_obs = df_copy[df_copy["ano"] == ultimo_ano].sort_values("data").iloc[-1:]
            dez = pd.concat([dez, ultimo_obs])
        
        dez = dez.sort_values("ano").drop_duplicates(subset=["ano"], keep="last")
        return dez[["ano", "valor"]].rename(columns={"valor": col_name})
    
    pib_anual = pib_raw.copy()
    pib_anual["ano"] = pib_anual["data"].dt.year
    pib_anual = pib_anual[["ano", "valor"]].rename(columns={"valor": "pib_nominal"})
    
    dbgg_anual = filtrar_dezembro(dbgg_raw, "dbgg_realizado")
    nfsp_anual = filtrar_dezembro(nfsp_raw, "nfsp_realizado")
    
    # Mesclar dados históricos de 2018 a 2025
    df = dbgg_anual.merge(nfsp_anual, on="ano", how="inner")
    df = df.merge(pib_anual, on="ano", how="inner")
    df = df[(df["ano"] >= 2018) & (df["ano"] <= 2025)].sort_values("ano").reset_index(drop=True)
    
    # Converter NFSP (Déficit) para Resultado Primário (Superávit)
    # Resultado Primário = -1 * NFSP
    df["primario_realizado"] = -1.0 * df["nfsp_realizado"]
    df = df.drop(columns=["nfsp_realizado"])
    
    # Injetar o Resultado Primário Estrutural (Frente 2)
    # Exclui os gastos extraordinários com a pandemia de Covid-19 em 2020 (~6,80% do PIB)
    df["primario_estrutural"] = df["primario_realizado"].copy()
    df.loc[df["ano"] == 2020, "primario_estrutural"] = -2.99  # Déficit estrutural real ajustado
    
    # Calcular Crescimento Nominal do PIB histórico
    df["g_nominal"] = df["pib_nominal"].pct_change()
    
    # Calcular custo implícito da dívida histórico
    df["custo_implicito"] = None
    for idx in range(1, len(df)):
        d_t = df.loc[idx, "dbgg_realizado"]
        s_t = df.loc[idx, "primario_realizado"]
        g_t = df.loc[idx, "g_nominal"]
        d_prev = df.loc[idx - 1, "dbgg_realizado"]
        
        i_t = ((d_t + s_t) * (1 + g_t) / d_prev) - 1
        df.loc[idx, "custo_implicito"] = i_t

    # 2. Projetar anos de 2026 a 2030 (Frente 4)
    # Premissas de baseline: crescimento nominal do PIB de 6.50% e juro implícito de 9.50%
    baseline_g = 0.065
    baseline_i = 0.095
    baseline_s = 0.0 # Resultado Primário nulo
    
    records_proj = []
    current_debt = df.loc[df.index[-1], "dbgg_realizado"]
    current_pib = df.loc[df.index[-1], "pib_nominal"]
    
    for ano in range(2026, 2031):
        # PIB nominal projetado
        current_pib = current_pib * (1 + baseline_g)
        # Dívida projetada sob premissa de baseline
        current_debt = current_debt * (1 + baseline_i) / (1 + baseline_g) - baseline_s
        
        records_proj.append({
            "ano": ano,
            "dbgg_realizado": round(current_debt, 2),
            "pib_nominal": round(current_pib, 2),
            "primario_realizado": baseline_s,
            "primario_estrutural": baseline_s,
            "g_nominal": baseline_g,
            "custo_implicito": baseline_i
        })
        
    df_proj = pd.DataFrame(records_proj)
    df_completo = pd.concat([df, df_proj], ignore_index=True)
    
    print("\nDados Consolidados da Simulação (2018-2030):")
    print(df_completo.to_string(index=False))
    
    # Exportar para CSV
    out_path = OUT_DIR / "simulacao_dbgg_contra_fatual.csv"
    df_completo.to_csv(out_path, index=False, sep=";", decimal=",")
    print(f"\n[OK] Nova planilha de simulação avançada salva em: {out_path}")

if __name__ == "__main__":
    main()
