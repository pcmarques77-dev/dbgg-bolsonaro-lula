"""Script de exportação unificado para o dashboard web React (V2).

Extrai dados do PIB trimestral, IPCA, Selic, Câmbio e Econometria, salvando-os
diretamente na pasta pública do frontend para consumo dinâmico.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

# Garante que possamos importar a biblioteca do diretório v2/src/
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir / "src"))

from mba_economia.config import SeriesConfig
from mba_economia.focus_extract import fetch_pib_total_expectativa_trimestral
from mba_economia.ibge_pib_volume_trimestral_client import fetch_pib_ibge_vol_trim_lut
from mba_economia.pib_trimestral_compare import (
    filtrar_janela_trimestres,
    juntar_focus_com_realizado,
    montar_comparacao_por_trimestre,
    trimestre_fim_por_data,
)
from mba_economia.ipca_comparisons import (
    build_comparacao_ipca_ano_bundle,
    build_comparacao_ipca_mensal,
    # build_comparacao_ipca_mensal_inicial,
)
from mba_economia.bcb_meta_inflacao import fetch_metas_inflacao_sgs, metas_como_dict
from mba_economia.selic_comparisons import (
    build_comparacao_selic_mensal,
    build_comparacao_selic_ano_trajetoria_mensal,
)
from mba_economia.copom_meta_selic import (
    fetch_meta_selic_sgs,
    meta_selic_em_datas,
    meta_selic_fim_ano,
)
from mba_economia.pib_comparisons import (
    build_comparacao_pib_ano_trajetoria_mensal,
)
from mba_economia.cli import run as run_pipeline


def main() -> None:
    dest_dir = root_dir / "public" / "data"
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_dir = root_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    start_date = date(2019, 1, 1)
    end_date = date.today()
    cfg = SeriesConfig()
    session = requests.Session()

    print("==============================================================")
    print("INICIANDO EXPORTAÇÃO UNIFICADA DE DADOS PARA O DASHBOARD (V2)")
    print("==============================================================")

    # 1. PIB trimestral
    print("\n[1/4] Processando dados do PIB trimestral...")
    ano_ini, tri_ini = 2019, 1
    ano_fim, tri_fim = trimestre_fim_por_data(end_date)
    
    ibge_all = fetch_pib_ibge_vol_trim_lut(cfg, session=session)
    ibge = filtrar_janela_trimestres(
        ibge_all,
        ano_ini=ano_ini,
        tri_ini=tri_ini,
        ano_fim=ano_fim,
        tri_fim=tri_fim,
    )
    
    focus_all = fetch_pib_total_expectativa_trimestral(
        filt_start=pd.Timestamp(2018, 6, 1),
        session=session,
    )
    focus = filtrar_janela_trimestres(
        focus_all,
        ano_ini=ano_ini,
        tri_ini=tri_ini,
        ano_fim=ano_fim,
        tri_fim=tri_fim,
    )
    
    comp_pib = montar_comparacao_por_trimestre(focus, ibge)
    joined_pib = juntar_focus_com_realizado(focus, ibge)
    
    comp_pib.to_csv(dest_dir / "comparacao_focus_ibge_pib_trimestral.csv", index=False)
    joined_pib.to_csv(dest_dir / "focus_pib_total_com_ibge_realizado.csv", index=False)
    
    # PIB Anual
    dfs_pib_cal = []
    dfs_pib_fech = []
    for y in range(start_date.year, end_date.year + 1):
        try:
            c_cal, c_fech = build_comparacao_pib_ano_trajetoria_mensal(y, out_dir, cfg, session=session)
            if not c_cal.empty:
                dfs_pib_cal.append(c_cal)
                dfs_pib_fech.append(c_cal.iloc[[0]])
        except Exception:
            pass
            
    if dfs_pib_cal:
        comp_pib_ano_cal = pd.concat(dfs_pib_cal, ignore_index=True)
        comp_pib_ano_cal.to_csv(dest_dir / "comparacao_pib_ano_calendario.csv", index=False, decimal=",", sep=";")
        
    if dfs_pib_fech:
        comp_pib_ano_fech = pd.concat(dfs_pib_fech, ignore_index=True)
        comp_pib_ano_fech.to_csv(dest_dir / "comparacao_pib_ano_fechamento.csv", index=False, decimal=",", sep=";")
        
    print("  -> PIB trimestral e anual salvos com sucesso!")

    # 2. IPCA
    print("\n[2/4] Processando dados do IPCA (mensal e anual)...")
    comp_ipca, focus_long_ipca = build_comparacao_ipca_mensal(start_date, end_date, cfg, session=session)
    comp_ipca.to_csv(dest_dir / "comparacao_ipca_mensal.csv", index=False, decimal=",", sep=";")
    
    # comp_ipca_inicial = build_comparacao_ipca_mensal_inicial(
        # start_date, end_date, cfg, session=session, focus_long=focus_long_ipca
    # )
    # comp_ipca_inicial.to_csv(dest_dir / "comparacao_ipca_mensal_inicial.csv", index=False, decimal=",", sep=";")
    
    comp_ipca_ano, fech_ipca_ano = build_comparacao_ipca_ano_bundle(start_date, end_date, cfg, session=session)

    # Enriquecer com metas CMN (SGS 13521) para uso no gráfico de desancoragem anual
    try:
        _metas_df = fetch_metas_inflacao_sgs(start_date, end_date, session=session)
        _metas_dict = metas_como_dict(_metas_df)
        _tolerancia = 1.50
        if not comp_ipca_ano.empty and _metas_dict:
            comp_ipca_ano["meta_centro"] = comp_ipca_ano["ipca_year_ref"].map(
                lambda y: _metas_dict.get(int(y), {}).get("centro", float("nan"))
            )
            comp_ipca_ano["meta_inferior"] = comp_ipca_ano["meta_centro"] - _tolerancia
            comp_ipca_ano["meta_superior"] = comp_ipca_ano["meta_centro"] + _tolerancia
            comp_ipca_ano["desancoragem_centro"] = comp_ipca_ano["ipca_focus_ano_pct"] - comp_ipca_ano["meta_centro"]
            comp_ipca_ano["desancoragem_absoluta"] = comp_ipca_ano["desancoragem_centro"].abs()
            print("  -> Metas CMN incorporadas ao IPCA anual (SGS 13521).")
    except Exception as _e:
        print(f"  [AVISO] Falha ao enriquecer IPCA anual com metas CMN: {_e}")

    comp_ipca_ano.to_csv(dest_dir / "comparacao_ipca_ano_calendario.csv", index=False, decimal=",", sep=";")
    fech_ipca_ano.to_csv(dest_dir / "comparacao_ipca_ano_fechamento.csv", index=False, decimal=",", sep=";")
    print("  -> IPCA salvo com sucesso!")

    # 3. Selic
    print("\n[3/4] Processando dados da Selic (mensal e anual)...")
    try:
        comp_selic, focus_long = build_comparacao_selic_mensal(start_date, end_date, cfg, session=session)
        comp_selic.to_csv(dest_dir / "comparacao_selic_mensal.csv", index=False, decimal=",", sep=";")
        
        # Meta Selic exata (SGS 432) — substitui a aproximação pelo SGS 11 anualisado
        print("  Buscando Meta Selic oficial (SGS 432)...")
        meta_df = fetch_meta_selic_sgs(start_date, end_date, session=session)
        meta_fim_ano = meta_selic_fim_ano(
            start_date, end_date, session=session, meta_df=meta_df
        )
        print(f"  Meta Selic por ano: {meta_fim_ano}")
        
        dfs_cal = []
        dfs_fech = []
        for y in range(start_date.year, end_date.year + 1):
            try:
                c_cal, c_fech = build_comparacao_selic_ano_trajetoria_mensal(y, cfg, session=session)
                if not c_cal.empty:
                    dfs_cal.append(c_cal)
                if not c_fech.empty:
                    dfs_fech.append(c_fech)
            except Exception:
                pass
                
        if dfs_cal:
            comp_selic_ano_cal = pd.concat(dfs_cal, ignore_index=True)
            # Substitui o SGS 11 anualisado pela Meta Selic oficial (SGS 432)
            comp_selic_ano_cal["selic_sgs_pct_aa_aprox"] = (
                comp_selic_ano_cal["ano_ref"]
                .apply(lambda y: meta_fim_ano.get(int(y), float("nan")))
            )
            # Meta na data da 1ª survey Focus do ano (ex.: 2019-01-28), não 1/jan
            primeira_survey_por_ano: dict[int, date] = {}
            for ano, grp in comp_selic_ano_cal.groupby("ano_ref"):
                dt = pd.to_datetime(grp["survey_date_previsao"].min()).date()
                primeira_survey_por_ano[int(ano)] = dt
            meta_primeira_por_data = meta_selic_em_datas(
                list(primeira_survey_por_ano.values()),
                meta_df,
            )
            meta_primeira_por_ano = {
                ano: meta_primeira_por_data.get(dt, float("nan"))
                for ano, dt in primeira_survey_por_ano.items()
            }
            comp_selic_ano_cal["selic_meta_primeira_survey_pct"] = (
                comp_selic_ano_cal["ano_ref"]
                .apply(lambda y: meta_primeira_por_ano.get(int(y), float("nan")))
            )
            comp_selic_ano_cal["erro_prev_menos_real_pp"] = (
                pd.to_numeric(comp_selic_ano_cal["selic_focus_pct"], errors="coerce")
                - comp_selic_ano_cal["selic_sgs_pct_aa_aprox"]
            ).round(4)
            comp_selic_ano_cal.to_csv(
                dest_dir / "comparacao_selic_ano_calendario.csv",
                index=False, decimal=",", sep=";"
            )
            
        if dfs_fech:
            comp_selic_ano_fech = pd.concat(dfs_fech, ignore_index=True)
            comp_selic_ano_fech.to_csv(
                dest_dir / "comparacao_selic_ano_fechamento.csv",
                index=False, decimal=",", sep=";"
            )
            
        print("  -> Selic salva com sucesso!")
    except Exception as e:
        import traceback
        print(f"  [AVISO] Falha ao processar dados da Selic: {e}")
        traceback.print_exc()

    # 4. Painel completo e Regressões econométricas
    print("\n[4/4] Processando painel semanal e rodando regressões OLS...")
    try:
        # Executa o pipeline padrão gerando o painel unificado e as saídas econométricas em dest_dir
        run_pipeline(
            start=start_date,
            end=end_date,
            out_dir=dest_dir,
            cfg=cfg,
            plot_mode="none",
            figure_extras=(),
            run_econometrics=True,
        )
        print("  -> Painel completo e sumários econométricos salvos com sucesso!")
        
        # Copia dados de DBGG se disponíveis em output
        import shutil
        dbgg_src = out_dir / "DIVIDA" / "periodos" / "2019-2026" / "comparacao_focus_dbgg.csv"
        if dbgg_src.exists():
            shutil.copy(dbgg_src, dest_dir / "comparacao_focus_dbgg.csv")
            print("  -> comparacao_focus_dbgg.csv copiado com sucesso!")
        else:
            dbgg_src_alt = out_dir / "DIVIDA" / "comparacao_focus_dbgg_anual.csv"
            if dbgg_src_alt.exists():
                shutil.copy(dbgg_src_alt, dest_dir / "comparacao_focus_dbgg.csv")
                print("  -> comparacao_focus_dbgg.csv copiado como fallback!")

        # Exporta DBGG mensal realizado (SGS 13762)
        print("  Buscando DBGG mensal oficial (SGS 13762)...")
        from mba_economia.bcb_dbgg_sgs13762 import fetch_dbgg_mensal_sgs
        dbgg_mensal = fetch_dbgg_mensal_sgs(2019, 2026, cfg, session=session)
        dbgg_mensal.to_csv(dest_dir / "dbgg_sgs13762_mensal.csv", index=False)
        print("  -> dbgg_sgs13762_mensal.csv salvo com sucesso!")

        # Gera e exporta os dados anuais detalhados da DBGG (Focus x SGS) de 2019 a 2026
        print("  Gerando dados anuais detalhados da DBGG (Focus x SGS)...")
        from exportar_dbgg_anual import exportar_dbgg_por_ano
        exportar_dbgg_por_ano(ano_ini=2019, ano_fim=2026, base_dir=out_dir / "DIVIDA", session=session)
        
        # Consolidando trajetórias de expectativas da DBGG
        print("  Consolidando trajetórias de expectativas da DBGG...")
        dfs_trajetoria = []
        for y in range(2019, 2027):
            path_ano = out_dir / "DIVIDA" / str(y) / "focus_dbgg_com_realizado.csv"
            if path_ano.exists():
                df_y = pd.read_csv(path_ano)
                # Seleciona apenas as colunas essenciais
                df_y = df_y[["survey_date", "ano_ref", "dbgg_focus_med_pct_pib", "dbgg_sgs_pct_pib"]].copy()
                dfs_trajetoria.append(df_y)
        if dfs_trajetoria:
            dbgg_trajetorias = pd.concat(dfs_trajetoria, ignore_index=True)
            dbgg_trajetorias.to_csv(dest_dir / "dbgg_trajetorias.csv", index=False)
            dbgg_trajetorias.to_csv(out_dir / "DIVIDA" / "dbgg_trajetorias.csv", index=False)
            print("  -> dbgg_trajetorias.csv salvo com sucesso no dest_dir e out_dir!")
    except Exception as e:
        print(f"  [AVISO] Falha ao processar painel e econometria (BCB SGS offline?): {e}")

    print("\n==============================================================")
    print(f"EXPORTAÇÃO CONCLUÍDA! Arquivos salvos em: {dest_dir.resolve()}")
    print("==============================================================")


if __name__ == "__main__":
    main()
