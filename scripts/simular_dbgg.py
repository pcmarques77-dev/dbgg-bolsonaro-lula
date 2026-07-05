"""Script de simulação contra-fatual da DBGG (Bolsonaro vs Lula 3).

Calcula o custo implícito da dívida e simula as trajetórias se os padrões
de resultado primário fossem trocados entre os governos.
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
    print("=== INICIANDO SIMULAÇÃO CONTRA-FATUAL DA DBGG ===")
    
    # 1. Carregar dados do SGS
    # 13762: DBGG (% PIB)
    # 5784: NFSP Governo Central - Resultado Primário (% PIB acumulado 12m) - Nota: NFSP é o Déficit, então multiplicamos por -1 para obter o Superávit.
    # 1207: PIB nominal acumulado 12m (R$ milhões)
    
    dbgg_raw = fetch_sgs(13762)
    nfsp_raw = fetch_sgs(5784)
    pib_raw = fetch_sgs(1207)
    
    # Filtrar para valores de dezembro (fechamento do ano) para DBGG e NFSP
    def filtrar_dezembro(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
        df_copy = df.copy()
        df_copy["ano"] = df_copy["data"].dt.year
        df_copy["mes"] = df_copy["data"].dt.month
        # Pegar dezembro
        dez = df_copy[df_copy["mes"] == 12].copy()
        # Se algum ano não tiver dezembro (ex: ano corrente), pega o último disponível
        ultimo_ano = df_copy["ano"].max()
        if ultimo_ano not in dez["ano"].values:
            ultimo_obs = df_copy[df_copy["ano"] == ultimo_ano].sort_values("data").iloc[-1:]
            dez = pd.concat([dez, ultimo_obs])
        
        dez = dez.sort_values("ano").drop_duplicates(subset=["ano"], keep="last")
        return dez[["ano", "valor"]].rename(columns={"valor": col_name})
    
    # Filtrar PIB nominal (que vem como 01/01/ano no SGS)
    pib_anual = pib_raw.copy()
    pib_anual["ano"] = pib_anual["data"].dt.year
    pib_anual = pib_anual[["ano", "valor"]].rename(columns={"valor": "pib_nominal"})
    
    dbgg_anual = filtrar_dezembro(dbgg_raw, "dbgg_realizado")
    nfsp_anual = filtrar_dezembro(nfsp_raw, "nfsp_realizado")
    
    # Mesclar dados anuais de 2018 a 2025
    df = dbgg_anual.merge(nfsp_anual, on="ano", how="inner")
    df = df.merge(pib_anual, on="ano", how="inner")
    df = df[(df["ano"] >= 2018) & (df["ano"] <= 2025)].sort_values("ano").reset_index(drop=True)
    
    # Converter NFSP (Déficit) para Resultado Primário (Superávit)
    # Resultado Primário = -1 * NFSP
    df["primario_realizado"] = -1.0 * df["nfsp_realizado"]
    df = df.drop(columns=["nfsp_realizado"])
    
    # Calcular Crescimento Nominal do PIB (g_t)
    df["g_nominal"] = df["pib_nominal"].pct_change()
    
    # Calcular custo implícito da dívida (i_t)
    # 1 + i_t = (D_t + S_t) * (1 + g_t) / D_{t-1}
    df["custo_implicito"] = None
    for idx in range(1, len(df)):
        d_t = df.loc[idx, "dbgg_realizado"]
        s_t = df.loc[idx, "primario_realizado"]
        g_t = df.loc[idx, "g_nominal"]
        d_prev = df.loc[idx - 1, "dbgg_realizado"]
        
        i_t = ((d_t + s_t) * (1 + g_t) / d_prev) - 1
        df.loc[idx, "custo_implicito"] = i_t
    
    print("\nDados Históricos Consolidados:")
    print(df.to_string(index=False))
    
    # 2. Definir Padrões de Gastos/Resultado Primário
    # Bolsonaro (2019-2022)
    # Lula 3 (2023-2025)
    
    prim_bols_avg = df[(df["ano"] >= 2019) & (df["ano"] <= 2022)]["primario_realizado"].mean()
    prim_lula_avg = df[(df["ano"] >= 2023) & (df["ano"] <= 2025)]["primario_realizado"].mean()
    
    print(f"\nMédia Resultado Primário Bolsonaro (2019-2022): {prim_bols_avg:.3f}% do PIB")
    print(f"Média Resultado Primário Lula 3 (2023-2025): {prim_lula_avg:.3f}% do PIB")
    
    # 3. Rodar Simulações
    
    # Simulação 1: Bolsonaro se tivesse mantido a política fiscal média de Lula 3 (2019-2022)
    df["sim_bols_com_fiscal_lula"] = df["dbgg_realizado"].copy()
    for idx in range(1, len(df)):
        ano = df.loc[idx, "ano"]
        if 2019 <= ano <= 2022:
            d_prev = df.loc[idx - 1, "sim_bols_com_fiscal_lula"]
            g_t = df.loc[idx, "g_nominal"]
            i_t = df.loc[idx, "custo_implicito"]
            # Resultado primário contra-fatual (média do Lula 3)
            s_t = prim_lula_avg
            
            df.loc[idx, "sim_bols_com_fiscal_lula"] = d_prev * (1 + i_t) / (1 + g_t) - s_t
        elif ano > 2022:
            # Propaga a partir da nova base acumulada
            d_prev = df.loc[idx - 1, "sim_bols_com_fiscal_lula"]
            g_t = df.loc[idx, "g_nominal"]
            i_t = df.loc[idx, "custo_implicito"]
            s_t = df.loc[idx, "primario_realizado"]
            df.loc[idx, "sim_bols_com_fiscal_lula"] = d_prev * (1 + i_t) / (1 + g_t) - s_t

    # Simulação 2: Lula 3 se tivesse adotado a política fiscal média de Bolsonaro (2023-2025)
    df["sim_lula_com_fiscal_bols"] = df["dbgg_realizado"].copy()
    for idx in range(1, len(df)):
        ano = df.loc[idx, "ano"]
        if 2023 <= ano <= 2025:
            d_prev = df.loc[idx - 1, "sim_lula_com_fiscal_bols"]
            g_t = df.loc[idx, "g_nominal"]
            i_t = df.loc[idx, "custo_implicito"]
            # Resultado primário contra-fatual (média do Bolsonaro)
            s_t = prim_bols_avg
            
            df.loc[idx, "sim_lula_com_fiscal_bols"] = d_prev * (1 + i_t) / (1 + g_t) - s_t
            
    print("\nResultados das Simulações:")
    print(df[["ano", "dbgg_realizado", "primario_realizado", "sim_bols_com_fiscal_lula", "sim_lula_com_fiscal_bols"]].to_string(index=False))
    
    # Exportar para CSV
    out_path = OUT_DIR / "simulacao_dbgg_contra_fatual.csv"
    df.to_csv(out_path, index=False, sep=";", decimal=",")
    print(f"\n[OK] Simulação salva em: {out_path}")

if __name__ == "__main__":
    main()
