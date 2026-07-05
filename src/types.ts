export interface ComparacaoTrimestre {
  trimestre: string;
  ano_ref: number;
  tri_ref: number;
  divulgacao_ibge_aprox: string;
  focus_ultima_mediana_pct: number;
  focus_ultima_survey_date: string;
  focus_n_respondentes: number;
  n_surveys_focus: number;
  ibge_vol_yoy_trim_pct: number;
  ibge_vol_qoq_pct: number;
  ibge_vol_acum4_yoy_pct: number;
  erro_focus_vs_ibge_yoy_pp: number;
}

export interface FocusJoinedRow {
  survey_date: string;
  tri_ref: number;
  ano_ref: number;
  pib_focus_trim_med_pct: number;
  numeroRespondentes: number;
  ibge_vol_yoy_trim_pct: number | null;
  ibge_vol_qoq_pct: number | null;
  ibge_vol_acum4_yoy_pct: number | null;
  ibge_vol_ytd_yoy_pct: number | null;
}

export interface PibData {
  comparacao: ComparacaoTrimestre[];
  joined: FocusJoinedRow[];
}

export interface IpcaMensalRow {
  ref_yyyymm: string;
  survey_date_previsao: string;
  ipca_focus_med_mensal_pct: number;
  ipca_ibge_mensal_pct: number;
  erro_prev_menos_real_pp: number;
  ipca_focus_mensal_nresp: number;
}

export interface PibAnualRow {
  survey_date: string;
  pib_focus_ano_pct: number;
  pib_year_ref: number;
  pib_ibge_4tri_yoy_pct: number;
  erro_prev_menos_real_pp: number;
}

export interface PibAnualFechamentoRow {
  ano_ref: number;
  survey_date_primeira_previsao: string;
  pib_focus_ano_pct: number;
  pib_ibge_4tri_yoy_pct: number;
  erro_prev_menos_real_pp: number;
}

export interface IpcaAnualRow {
  survey_date: string;
  ipca_focus_ano_pct: number;
  ipca_year_ref: number;
  ipca_ibge_acum_ano_dez_pct: number;
  erro_prev_menos_real_pp: number;
  ipca_focus_ano_nresp: number;
  meta_centro?: number;
  meta_inferior?: number;
  meta_superior?: number;
  desancoragem_centro?: number;
  desancoragem_absoluta?: number;
}

export interface IpcaAnualFechamentoRow {
  ano_ref: number;
  survey_date_primeira_previsao: string;
  ipca_focus_ano_pct: number;
  ipca_ibge_acum_ano_dez_pct: number;
  erro_prev_menos_real_pp: number;
}

export interface SelicMensalRow {
  ref_yyyymm: string;
  survey_date_previsao: string;
  selic_focus_pct: number;
  reuniao_focus: string;
  selic_sgs_pct_aa_aprox: number;
  erro_prev_menos_real_pp: number;
  selic_focus_nresp: number;
}

export interface SelicAnualRow {
  survey_date: string;
  selic_focus_ano_pct: number;
  selic_year_ref: number;
  selic_sgs_pct_aa_aprox: number;
  selic_meta_primeira_survey_pct: number;
  erro_prev_menos_real_pp: number;
}

export interface SelicAnualFechamentoRow {
  ano_ref: number;
  survey_date_primeira_previsao: string;
  selic_focus_ano_pct: number;
  selic_sgs_pct_aa_aprox: number;
  erro_prev_menos_real_pp: number;
}

export interface PainelRow {
  survey_date: string;
  ipca_med12m: number;
  selic_mediana_pct: number;
  usdbrl_med_fwd: number;
  pib_med_pct: number;
  usd_sgs_med: number;
  ibov_fech: number;
  vix: number;
  commodities: number;
  dummy_lula: number;
  dummy_pandemia: number;
  ipca_meta_centro_12m?: number;
  ipca_meta_inferior_12m?: number;
  ipca_meta_superior_12m?: number;
  desancoragem_centro_12m?: number;
  desancoragem_absoluta_12m?: number;
  dbgg_med_pct?: number;
  dbgg_year_ref?: number;
}

export interface EconometriaCoefRow {
  variavel: string;
  coef: number;
  stderr: number;
  t: number;
  pvalue: number;
  conf_low: number;
  conf_high: number;
}

export interface DbggAnualFechamentoRow {
  ano: number;
  divulgacao_aprox: string;
  focus_ultima_mediana_pct_pib: number;
  focus_ultima_survey_date: string;
  focus_n_respondentes: number;
  n_surveys_focus: number;
  dbgg_realizado_dez_pct_pib: number;
  dbgg_realizado_yoy_pp: number;
  erro_focus_vs_realizado_pp: number;
}

export interface DbggMensalRow {
  data_obs: string;
  mes: number;
  dbgg_sgs_pct_pib: number;
  ano_ref: number;
}

export interface DbggTrajetoriaRow {
  survey_date: string;
  ano_ref: number;
  dbgg_focus_med_pct_pib: number;
  dbgg_sgs_pct_pib: number | null;
}

export interface DashboardData {
  pib: PibData;
  pibAnual: PibAnualRow[];
  pibAnualFechamento: PibAnualFechamentoRow[];
  ipcaMensal: IpcaMensalRow[];
  ipcaMensalInicial: IpcaMensalRow[];
  ipcaAnual: IpcaAnualRow[];
  ipcaAnualFechamento: IpcaAnualFechamentoRow[];
  selicMensal: SelicMensalRow[];
  selicAnual: SelicAnualRow[];
  selicAnualFechamento: SelicAnualFechamentoRow[];
  painel: PainelRow[];
  econometriaCoefs: EconometriaCoefRow[];
  econometriaDiagnosticos: string;
  econometriaSummary: string;
  econometriaSelicCoefs: EconometriaCoefRow[];
  econometriaSelicDiagnosticos: string;
  econometriaSelicSummary: string;
  econometriaPibCoefs: EconometriaCoefRow[];
  econometriaPibDiagnosticos: string;
  econometriaPibSummary: string;
  econometriaTaylorCoefs: EconometriaCoefRow[];
  econometriaTaylorDiagnosticos: string;
  econometriaTaylorSummary: string;
  dbggAnualFechamento: DbggAnualFechamentoRow[];
  dbggMensal: DbggMensalRow[];
  dbggTrajetorias: DbggTrajetoriaRow[];
  dbggSimulacao: DbggSimulacaoRow[];
}

export interface DbggSimulacaoRow {
  ano: number;
  dbgg_realizado: number;
  pib_nominal: number;
  primario_realizado: number;
  g_nominal: number | null;
  custo_implicito: number | null;
  sim_bols_com_fiscal_lula: number;
  sim_lula_com_fiscal_bols: number;
}

