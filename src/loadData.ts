import Papa from "papaparse";
import type {
  DashboardData,
  ComparacaoTrimestre,
  FocusJoinedRow,
  IpcaMensalRow,
  IpcaAnualRow,
  IpcaAnualFechamentoRow,
  SelicMensalRow,
  SelicAnualRow,
  SelicAnualFechamentoRow,
  PainelRow,
  EconometriaCoefRow,
  PibData,
  PibAnualRow,
  PibAnualFechamentoRow,
  DbggAnualFechamentoRow,
  DbggMensalRow,
  DbggTrajetoriaRow,
  DbggSimulacaoRow,
} from "./types";

function parseNumber(v: unknown): number {
  if (v === undefined || v === null || v === "") return NaN;
  // Trata decimais com vírgula comuns nos CSVs formatados em Português
  const s = String(v).trim().replace(",", ".");
  const n = Number(s);
  return Number.isFinite(n) ? n : NaN;
}

async function fetchCsv<T>(path: string, sep: string = ","): Promise<T[]> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Falha ao carregar ${path}: ${res.status}`);
  const text = await res.text();
  const parsed = Papa.parse<Record<string, string>>(text, {
    header: true,
    skipEmptyLines: true,
    delimiter: sep,
  });
  if (parsed.errors.length) {
    console.warn(`Avisos PapaParse em ${path}:`, parsed.errors);
  }
  return parsed.data as unknown as T[];
}

async function fetchText(path: string): Promise<string> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Falha ao carregar ${path}: ${res.status}`);
  return await res.text();
}

export async function loadDashboardData(): Promise<DashboardData> {
  const [
    compRaw,
    joinedRaw,
    pibAnualRaw,
    pibAnualFechamentoRaw,
    ipcaMensalRaw,
    ipcaMensalInicialRaw,
    ipcaAnualRaw,
    ipcaAnualFechamentoRaw,
    selicMensalRaw,
    selicAnualRaw,
    _selicAnualFechamentoRaw,
    painelRaw,
    econCoefRaw,
    econDiag,
    econSumm,
    dbggRaw,
    econSelicCoefRaw,
    econSelicDiag,
    econSelicSumm,
    econPibCoefRaw,
    econPibDiag,
    econPibSumm,
    econTaylorCoefRaw,
    econTaylorDiag,
    econTaylorSumm,
    dbggMensalRaw,
    dbggTrajetoriasRaw,
    dbggSimulacaoRaw,
  ] = await Promise.all([
    fetchCsv<Record<string, string>>("/data/comparacao_focus_ibge_pib_trimestral.csv").catch(() => []),
    fetchCsv<Record<string, string>>("/data/focus_pib_total_com_ibge_realizado.csv").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_pib_ano_calendario.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_pib_ano_fechamento.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_ipca_mensal.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_ipca_mensal_inicial.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_ipca_ano_calendario.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_ipca_ano_fechamento.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_selic_mensal.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_selic_ano_calendario.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/comparacao_selic_ano_fechamento.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/painel_focus_mvp.csv", ";").catch(() => []),
    fetchCsv<Record<string, string>>("/data/econometria_ols_ipca_med12m_coef.csv", ";").catch(() => []),
    fetchText("/data/econometria_ols_ipca_med12m_diagnosticos.txt").catch(() => "Nenhum teste de diagnóstico gerado."),
    fetchText("/data/econometria_ols_ipca_med12m_summary.txt").catch(() => "Nenhum sumário OLS gerado."),
    fetchCsv<Record<string, string>>("/data/comparacao_focus_dbgg.csv").catch(() => []),
    fetchCsv<Record<string, string>>("/data/econometria_ols_selic_mediana_pct_coef.csv", ";").catch(() => []),
    fetchText("/data/econometria_ols_selic_mediana_pct_diagnosticos.txt").catch(() => "Diagnósticos Selic indisponíveis."),
    fetchText("/data/econometria_ols_selic_mediana_pct_summary.txt").catch(() => "Sumário Selic indisponível."),
    fetchCsv<Record<string, string>>("/data/econometria_ols_pib_med_pct_coef.csv", ";").catch(() => []),
    fetchText("/data/econometria_ols_pib_med_pct_diagnosticos.txt").catch(() => "Diagnósticos PIB indisponíveis."),
    fetchText("/data/econometria_ols_pib_med_pct_summary.txt").catch(() => "Sumário PIB indisponível."),
    fetchCsv<Record<string, string>>("/data/econometria_ols_taylor_rule_coef.csv", ";").catch(() => []),
    fetchText("/data/econometria_ols_taylor_rule_diagnosticos.txt").catch(() => "Diagnósticos Taylor Rule indisponíveis."),
    fetchText("/data/econometria_ols_taylor_rule_summary.txt").catch(() => "Sumário Taylor Rule indisponível."),
    fetchCsv<Record<string, string>>("/data/dbgg_sgs13762_mensal.csv").catch(() => []),
    fetchCsv<Record<string, string>>("/data/dbgg_trajetorias.csv").catch(() => []),
    fetchCsv<Record<string, string>>("/data/simulacao_dbgg_contra_fatual.csv", ";").catch(() => []),
  ]);

  const comparacao: ComparacaoTrimestre[] = compRaw
    .map((r) => ({
      trimestre: r.trimestre,
      ano_ref: parseNumber(r.ano_ref),
      tri_ref: parseNumber(r.tri_ref),
      divulgacao_ibge_aprox: r.divulgacao_ibge_aprox,
      focus_ultima_mediana_pct: parseNumber(r.focus_ultima_mediana_pct),
      focus_ultima_survey_date: r.focus_ultima_survey_date,
      focus_n_respondentes: parseNumber(r.focus_n_respondentes),
      n_surveys_focus: parseNumber(r.n_surveys_focus),
      ibge_vol_yoy_trim_pct: parseNumber(r.ibge_vol_yoy_trim_pct),
      ibge_vol_qoq_pct: parseNumber(r.ibge_vol_qoq_pct),
      ibge_vol_acum4_yoy_pct: parseNumber(r.ibge_vol_acum4_yoy_pct),
      erro_focus_vs_ibge_yoy_pp: parseNumber(r.erro_focus_vs_ibge_yoy_pp),
    }))
    .sort((a, b) => a.ano_ref * 10 + a.tri_ref - (b.ano_ref * 10 + b.tri_ref));

  const joined: FocusJoinedRow[] = joinedRaw.map((r) => ({
    survey_date: r.survey_date,
    tri_ref: parseNumber(r.tri_ref),
    ano_ref: parseNumber(r.ano_ref),
    pib_focus_trim_med_pct: parseNumber(r.pib_focus_trim_med_pct),
    numeroRespondentes: parseNumber(r.numeroRespondentes),
    ibge_vol_yoy_trim_pct: r.ibge_vol_yoy_trim_pct ? parseNumber(r.ibge_vol_yoy_trim_pct) : null,
    ibge_vol_qoq_pct: r.ibge_vol_qoq_pct ? parseNumber(r.ibge_vol_qoq_pct) : null,
    ibge_vol_acum4_yoy_pct: r.ibge_vol_acum4_yoy_pct ? parseNumber(r.ibge_vol_acum4_yoy_pct) : null,
    ibge_vol_ytd_yoy_pct: r.ibge_vol_ytd_yoy_pct ? parseNumber(r.ibge_vol_ytd_yoy_pct) : null,
  }));

  const ipcaMensal: IpcaMensalRow[] = ipcaMensalRaw.map((r) => ({
    ref_yyyymm: r.ref_yyyymm,
    survey_date_previsao: r.survey_date_previsao,
    ipca_focus_med_mensal_pct: parseNumber(r.ipca_focus_med_mensal_pct),
    ipca_ibge_mensal_pct: parseNumber(r.ipca_ibge_mensal_pct),
    erro_prev_menos_real_pp: parseNumber(r.erro_prev_menos_real_pp),
    ipca_focus_mensal_nresp: parseNumber(r.ipca_focus_mensal_nresp),
  }));

  const ipcaMensalInicial: IpcaMensalRow[] = ipcaMensalInicialRaw.map((r) => ({
    ref_yyyymm: r.ref_yyyymm,
    survey_date_previsao: r.survey_date_previsao,
    ipca_focus_med_mensal_pct: parseNumber(r.ipca_focus_med_mensal_pct),
    ipca_ibge_mensal_pct: parseNumber(r.ipca_ibge_mensal_pct),
    erro_prev_menos_real_pp: parseNumber(r.erro_prev_menos_real_pp),
    ipca_focus_mensal_nresp: parseNumber(r.ipca_focus_mensal_nresp),
  }));

  const ipcaAnualFechamento: IpcaAnualFechamentoRow[] = ipcaAnualFechamentoRaw.map((r) => ({
    ano_ref: parseNumber(r.ano_ref),
    survey_date_primeira_previsao: r.survey_date_primeira_previsao || r.survey_date_ultima_previsao || "",
    ipca_focus_ano_pct: parseNumber(r.ipca_focus_ano_pct),
    ipca_ibge_acum_ano_dez_pct: parseNumber(r.ipca_ibge_acum_ano_dez_pct),
    erro_prev_menos_real_pp: parseNumber(r.erro_prev_menos_real_pp),
  }));

  const realizedMap = new Map<number, number>();
  ipcaAnualFechamento.forEach((f) => {
    if (!isNaN(f.ipca_ibge_acum_ano_dez_pct)) {
      realizedMap.set(f.ano_ref, f.ipca_ibge_acum_ano_dez_pct);
    }
  });

  const ipcaAnual: IpcaAnualRow[] = ipcaAnualRaw.map((r) => {
    const year = parseNumber(r.ipca_year_ref);
    const realized = realizedMap.get(year) ?? NaN;
    const focus = parseNumber(r.ipca_focus_ano_pct);
    return {
      survey_date: r.survey_date,
      ipca_focus_ano_pct: focus,
      ipca_year_ref: year,
      ipca_ibge_acum_ano_dez_pct: realized,
      erro_prev_menos_real_pp: isNaN(realized) ? NaN : focus - realized,
      ipca_focus_ano_nresp: parseNumber(r.ipca_focus_ano_nresp),
      meta_centro: parseNumber(r.meta_centro),
      meta_inferior: parseNumber(r.meta_inferior),
      meta_superior: parseNumber(r.meta_superior),
      desancoragem_centro: parseNumber(r.desancoragem_centro),
      desancoragem_absoluta: parseNumber(r.desancoragem_absoluta),
    };
  });

  const selicMensal: SelicMensalRow[] = selicMensalRaw.map((r) => ({
    ref_yyyymm: r.ref_yyyymm,
    survey_date_previsao: r.survey_date_previsao,
    selic_focus_pct: parseNumber(r.selic_focus_pct),
    reuniao_focus: r.reuniao_focus,
    selic_sgs_pct_aa_aprox: parseNumber(r.selic_sgs_pct_aa_aprox),
    erro_prev_menos_real_pp: parseNumber(r.erro_prev_menos_real_pp),
    selic_focus_nresp: parseNumber(r.selic_focus_nresp),
  }));

  // comparacao_selic_ano_calendario.csv columns:
  // ano_ref;...;selic_sgs_pct_aa_aprox;selic_meta_primeira_survey_pct;selic_meta_primeira_survey_data;...
  const selicAnual: SelicAnualRow[] = selicAnualRaw.map((r) => {
    const year = parseNumber(r.ano_ref);
    const realized = parseNumber(r.selic_sgs_pct_aa_aprox);
    const metaPrimeiraRaw = parseNumber(r.selic_meta_primeira_survey_pct);
    const metaInicioLegacy = parseNumber(r.selic_meta_inicio_ano_pct);
    const metaPrimeira = Number.isFinite(metaPrimeiraRaw)
      ? metaPrimeiraRaw
      : Number.isFinite(metaInicioLegacy)
        ? metaInicioLegacy
        : NaN;
    const focus = parseNumber(r.selic_focus_pct);
    return {
      survey_date: r.survey_date_previsao || r.survey_date,
      selic_focus_ano_pct: focus,
      selic_year_ref: year,
      selic_sgs_pct_aa_aprox: realized,
      selic_meta_primeira_survey_pct: Number.isFinite(metaPrimeira) ? metaPrimeira : realized,
      erro_prev_menos_real_pp: parseNumber(r.erro_prev_menos_real_pp),
    };
  });

  // Build selicAnualFechamento: first Focus per year (initial estimate) + Dec realized rate
  const _selicYearFirst = new Map<number, SelicAnualRow>();
  const _selicYearLast = new Map<number, SelicAnualRow>();
  for (const row of selicAnual) {
    const y = row.selic_year_ref;
    if (!Number.isFinite(y)) continue;
    const existing = _selicYearFirst.get(y);
    if (!existing || row.survey_date < existing.survey_date) {
      _selicYearFirst.set(y, row);
    }
    const existingLast = _selicYearLast.get(y);
    if (!existingLast || row.survey_date > existingLast.survey_date) {
      _selicYearLast.set(y, row);
    }
  }
  const selicAnualFechamento: SelicAnualFechamentoRow[] = Array.from(_selicYearFirst.keys())
    .sort((a, b) => a - b)
    .map((y) => {
      const first = _selicYearFirst.get(y)!;
      const last = _selicYearLast.get(y)!;
      const realized = last.selic_sgs_pct_aa_aprox;
      return {
        ano_ref: y,
        survey_date_primeira_previsao: first.survey_date,
        selic_focus_ano_pct: first.selic_focus_ano_pct,
        selic_sgs_pct_aa_aprox: realized,
        erro_prev_menos_real_pp: Number.isFinite(realized) ? first.selic_focus_ano_pct - realized : NaN,
      };
    });

  const painel: PainelRow[] = painelRaw.map((r) => ({
    survey_date: r.survey_date,
    ipca_med12m: parseNumber(r.ipca_med12m),
    selic_mediana_pct: parseNumber(r.selic_mediana_pct),
    usdbrl_med_fwd: parseNumber(r.usdbrl_med_fwd),
    pib_med_pct: parseNumber(r.pib_med_pct),
    usd_sgs_med: parseNumber(r.usd_sgs_med),
    ibov_fech: parseNumber(r.ibov_fech),
    vix: parseNumber(r.vix),
    commodities: parseNumber(r.commodities),
    dummy_lula: parseNumber(r.dummy_lula),
    dummy_pandemia: parseNumber(r.dummy_pandemia),
    ipca_meta_centro_12m: parseNumber(r.ipca_meta_centro_12m),
    ipca_meta_inferior_12m: parseNumber(r.ipca_meta_inferior_12m),
    ipca_meta_superior_12m: parseNumber(r.ipca_meta_superior_12m),
    desancoragem_centro_12m: parseNumber(r.desancoragem_centro_12m),
    desancoragem_absoluta_12m: parseNumber(r.desancoragem_absoluta_12m),
    dbgg_med_pct: parseNumber(r.dbgg_med_pct),
    dbgg_year_ref: parseNumber(r.dbgg_year_ref),
  }));

  const parseCoefs = (raw: Record<string, string>[]): EconometriaCoefRow[] => {
    return raw.map((r) => ({
      variavel: r.variavel || "",
      coef: parseNumber(r.coef),
      stderr: parseNumber(r.std_err || r.stderr),
      t: parseNumber(r.t_stat || r.t),
      pvalue: parseNumber(r.p_value || r.pvalue),
      conf_low: parseNumber(r["[0.025"] || r.conf_low),
      conf_high: parseNumber(r["0.975]"] || r.conf_high),
    }));
  };

  const econometriaCoefs = parseCoefs(econCoefRaw);
  const econometriaSelicCoefs = parseCoefs(econSelicCoefRaw);
  const econometriaPibCoefs = parseCoefs(econPibCoefRaw);
  const econometriaTaylorCoefs = parseCoefs(econTaylorCoefRaw);

  const pibAnualFechamento: PibAnualFechamentoRow[] = pibAnualFechamentoRaw.map((r) => ({
    ano_ref: parseNumber(r.ano_ref),
    survey_date_primeira_previsao: r.survey_date_primeira_previsao || r.survey_date_previsao || "",
    pib_focus_ano_pct: parseNumber(r.pib_focus_ano_pct),
    pib_ibge_4tri_yoy_pct: parseNumber(r.pib_ibge_4tri_yoy_pct),
    erro_prev_menos_real_pp: parseNumber(r.erro_prev_menos_real_pp),
  }));

  const pibRealizedMap = new Map<number, number>();
  pibAnualFechamento.forEach((f) => {
    if (!isNaN(f.pib_ibge_4tri_yoy_pct)) {
      pibRealizedMap.set(f.ano_ref, f.pib_ibge_4tri_yoy_pct);
    }
  });

  const pibAnual: PibAnualRow[] = pibAnualRaw.map((r) => {
    const year = parseNumber(r.ano_ref || r.pib_year_ref);
    const realized = pibRealizedMap.get(year) ?? NaN;
    const focus = parseNumber(r.pib_focus_ano_pct);
    return {
      survey_date: r.survey_date_previsao || r.survey_date,
      pib_focus_ano_pct: focus,
      pib_year_ref: year,
      pib_ibge_4tri_yoy_pct: realized,
      erro_prev_menos_real_pp: isNaN(realized) ? NaN : focus - realized,
    };
  });

  const dbggAnualFechamento: DbggAnualFechamentoRow[] = dbggRaw.map((r) => ({
    ano: parseNumber(r.ano),
    divulgacao_aprox: r.divulgacao_aprox || "",
    focus_ultima_mediana_pct_pib: parseNumber(r.focus_ultima_mediana_pct_pib),
    focus_ultima_survey_date: r.focus_ultima_survey_date || "",
    focus_n_respondentes: parseNumber(r.focus_n_respondentes),
    n_surveys_focus: parseNumber(r.n_surveys_focus),
    dbgg_realizado_dez_pct_pib: parseNumber(r.dbgg_realizado_dez_pct_pib),
    dbgg_realizado_yoy_pp: parseNumber(r.dbgg_realizado_yoy_pp),
    erro_focus_vs_realizado_pp: parseNumber(r.erro_focus_vs_realizado_pp),
  }));

  const dbggMensal: DbggMensalRow[] = dbggMensalRaw.map((r) => ({
    data_obs: r.data_obs,
    mes: parseNumber(r.mes),
    dbgg_sgs_pct_pib: parseNumber(r.dbgg_sgs_pct_pib),
    ano_ref: parseNumber(r.ano_ref),
  })).sort((a, b) => a.data_obs.localeCompare(b.data_obs));

  const dbggTrajetorias: DbggTrajetoriaRow[] = dbggTrajetoriasRaw.map((r) => ({
    survey_date: r.survey_date,
    ano_ref: parseNumber(r.ano_ref),
    dbgg_focus_med_pct_pib: parseNumber(r.dbgg_focus_med_pct_pib),
    dbgg_sgs_pct_pib: r.dbgg_sgs_pct_pib ? parseNumber(r.dbgg_sgs_pct_pib) : null,
  })).sort((a, b) => a.survey_date.localeCompare(b.survey_date));

  const dbggSimulacao: DbggSimulacaoRow[] = dbggSimulacaoRaw.map((r) => ({
    ano: parseNumber(r.ano),
    dbgg_realizado: parseNumber(r.dbgg_realizado),
    pib_nominal: parseNumber(r.pib_nominal),
    primario_realizado: parseNumber(r.primario_realizado),
    g_nominal: r.g_nominal ? parseNumber(r.g_nominal) : null,
    custo_implicito: r.custo_implicito ? parseNumber(r.custo_implicito) : null,
    sim_bols_com_fiscal_lula: parseNumber(r.sim_bols_com_fiscal_lula),
    sim_lula_com_fiscal_bols: parseNumber(r.sim_lula_com_fiscal_bols),
  })).sort((a, b) => a.ano - b.ano);

  return {
    pib: { comparacao, joined },
    pibAnual,
    pibAnualFechamento,
    ipcaMensal,
    ipcaMensalInicial,
    ipcaAnual,
    ipcaAnualFechamento,
    selicMensal,
    selicAnual,
    selicAnualFechamento,
    painel,
    econometriaCoefs,
    econometriaDiagnosticos: econDiag,
    econometriaSummary: econSumm,
    econometriaSelicCoefs,
    econometriaSelicDiagnosticos: econSelicDiag,
    econometriaSelicSummary: econSelicSumm,
    econometriaPibCoefs,
    econometriaPibDiagnosticos: econPibDiag,
    econometriaPibSummary: econPibSumm,
    econometriaTaylorCoefs,
    econometriaTaylorDiagnosticos: econTaylorDiag,
    econometriaTaylorSummary: econTaylorSumm,
    dbggAnualFechamento,
    dbggMensal,
    dbggTrajetorias,
    dbggSimulacao,
  };
}

export function trimestresDisponiveis(data: PibData): string[] {
  const set = new Set<string>();
  for (const r of data.comparacao) {
    if (r.trimestre) set.add(r.trimestre);
  }
  return [...set];
}

export function serieConvergencia(
  joined: FocusJoinedRow[],
  ano: number,
  tri: number,
): { date: string; focus: number; ibge: number | null }[] {
  return joined
    .filter((r) => r.ano_ref === ano && r.tri_ref === tri && Number.isFinite(r.pib_focus_trim_med_pct))
    .sort((a, b) => a.survey_date.localeCompare(b.survey_date))
    .map((r) => ({
      date: r.survey_date.slice(0, 10),
      focus: r.pib_focus_trim_med_pct,
      ibge: r.ibge_vol_yoy_trim_pct,
    }));
}
