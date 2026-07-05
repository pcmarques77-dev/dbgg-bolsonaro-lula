import { useState, type ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ReferenceArea,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { ComparacaoTrimestre, IpcaMensalRow, IpcaAnualRow, IpcaAnualFechamentoRow, SelicMensalRow, SelicAnualRow, SelicAnualFechamentoRow, PainelRow, PibAnualRow, PibAnualFechamentoRow, DbggMensalRow, DbggAnualFechamentoRow, DbggTrajetoriaRow } from "../types";

// Paleta de Cores Premium Dark
const FOCUS_COLOR = "#3b82f6";     // Azul Vibrante
const IBGE_COLOR = "#f97316";      // Coral / Laranja
const ACCENT_CYAN = "#06b6d4";     // Ciano Neon
const ACCENT_GOLD = "#eab308";     // Dourado
const ACCENT_PURPLE = "#a855f7";   // Roxo
const GRID_COLOR = "rgba(255, 255, 255, 0.08)";

export function ComparacaoBarras({ data }: { data: ComparacaoTrimestre[] }) {
  const chartData = data.map((d) => ({
    name: d.trimestre,
    Focus: d.focus_ultima_mediana_pct,
    IBGE: d.ibge_vol_yoy_trim_pct,
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="focusBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={FOCUS_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="ibgeBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={IBGE_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#c2410c" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v.toFixed(2)}%`]}
        />
        <Legend wrapperStyle={{ color: "#fff", paddingTop: 10 }} />
        <ReferenceLine y={0} stroke="#4b5563" />
        <Bar dataKey="Focus" fill="url(#focusBarGrad)" name="Focus (última mediana pré-divulgação)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="IBGE" fill="url(#ibgeBarGrad)" name="IBGE YoY (Volume, SIDRA 5932)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ErroPrevisao({ data }: { data: ComparacaoTrimestre[] }) {
  const chartData = data.map((d) => ({
    name: d.trimestre,
    erro: d.erro_focus_vs_ibge_yoy_pp,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="errorPosGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#991b1b" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="errorNegGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#065f46" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v >= 0 ? "+" : ""}${v.toFixed(2)} p.p.`, "Erro (Focus - IBGE)"]}
        />
        <ReferenceLine y={0} stroke="#6b7280" />
        <Bar dataKey="erro" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.erro > 0 ? "url(#errorPosGrad)" : "url(#errorNegGrad)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DispersaoFocusIbge({ data }: { data: ComparacaoTrimestre[] }) {
  const pts = data.map((d) => ({
    trimestre: d.trimestre,
    ibge: d.ibge_vol_yoy_trim_pct,
    focus: d.focus_ultima_mediana_pct,
  }));
  const vals = pts.flatMap((p) => [p.ibge, p.focus]);
  const lo = Math.min(...vals) - 0.5;
  const hi = Math.max(...vals) + 0.5;

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ScatterChart margin={{ top: 16, right: 16, bottom: 8, left: -20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis type="number" dataKey="ibge" name="IBGE" tickFormatter={(val) => `${val}%`} domain={[lo, hi]} tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis type="number" dataKey="focus" name="Focus" tickFormatter={(val) => `${val}%`} domain={[lo, hi]} tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <ZAxis range={[70, 70]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#1f2937", borderColor: "rgba(255,255,255,0.1)", borderRadius: "6px" }}
          itemStyle={{ color: "#f3f4f6" }}
          cursor={{ strokeDasharray: "3 3", stroke: "#9ca3af" }}
          formatter={(v: number) => [`${v.toFixed(2)}%`]}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.trimestre ?? ""}
        />
        <ReferenceLine segment={[{ x: lo, y: lo }, { x: hi, y: hi }]} stroke="#6b7280" strokeDasharray="4 4" />
        <Scatter name="Trimestres" data={pts} fill={ACCENT_CYAN} fillOpacity={0.7} stroke="#0891b2" strokeWidth={1} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

interface ConvProps {
  series: { date: string; focus: number; ibge: number | null }[];
}

export function ConvergenciaFocus({ series }: ConvProps) {
  const ibgeVal = series.find((s) => s.ibge != null)?.ibge ?? null;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={series} margin={{ top: 8, right: 8, left: -20, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} minTickGap={28} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v.toFixed(2)}%`]}
        />
        <Legend />
        {ibgeVal != null && (
          <ReferenceLine y={ibgeVal} stroke={IBGE_COLOR} strokeDasharray="6 4" label={{ value: `IBGE ${ibgeVal.toFixed(1)}%`, fill: "#f97316", position: "top" }} />
        )}
        <Line type="monotone" dataKey="focus" name="Mediana Focus" stroke={FOCUS_COLOR} dot={false} strokeWidth={3} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// 5. IPCA Mensal Chart (Inflação)
export function IPCAMensalChart({ data }: { data: IpcaMensalRow[] }) {
  const chartData = data.map((d) => ({
    name: `${d.ref_yyyymm.slice(4)}/${d.ref_yyyymm.slice(0, 4)}`,
    Focus: d.ipca_focus_med_mensal_pct,
    IBGE: d.ipca_ibge_mensal_pct,
  }));

  const isLarge = chartData.length > 30;

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} minTickGap={25} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v.toFixed(2)}%`]}
        />
        <Legend />
        <Line type="monotone" dataKey="Focus" name="Focus (Mediana)" stroke={FOCUS_COLOR} strokeWidth={isLarge ? 1.8 : 2.5} dot={isLarge ? { r: 1.5 } : { r: 4 }} activeDot={{ r: 6 }} />
        <Line type="monotone" dataKey="IBGE" name="IBGE Realizado (SIDRA 1737)" stroke={IBGE_COLOR} strokeWidth={isLarge ? 1.8 : 2.5} dot={isLarge ? { r: 1.5 } : { r: 4 }} activeDot={{ r: 6 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function IPCAMensalBarras({ data }: { data: IpcaMensalRow[] }) {
  const chartData = data.map((d) => ({
    name: `${d.ref_yyyymm.slice(4)}/${d.ref_yyyymm.slice(0, 4)}`,
    Focus: d.ipca_focus_med_mensal_pct,
    IBGE: d.ipca_ibge_mensal_pct,
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="focusIpcaMensalBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={FOCUS_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="ibgeIpcaMensalBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={IBGE_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#c2410c" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} minTickGap={20} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
        />
        <Legend wrapperStyle={{ color: "#fff", paddingTop: 10 }} />
        <ReferenceLine y={0} stroke="#4b5563" />
        <Bar dataKey="Focus" fill="url(#focusIpcaMensalBarGrad)" name="Focus (expectativa)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="IBGE" fill="url(#ibgeIpcaMensalBarGrad)" name="IBGE Realizado" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function IPCAMensalErroChart({ data }: { data: IpcaMensalRow[] }) {
  const chartData = data.map((d) => ({
    name: `${d.ref_yyyymm.slice(4)}/${d.ref_yyyymm.slice(0, 4)}`,
    erro: d.erro_prev_menos_real_pp,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="ipcaErrorPosGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#991b1b" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="ipcaErrorNegGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#065f46" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} minTickGap={25} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v >= 0 ? "+" : ""}${v.toFixed(2)} p.p.`, "Erro (Focus - IBGE)"]}
        />
        <ReferenceLine y={0} stroke="#6b7280" />
        <Bar dataKey="erro" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.erro > 0 ? "url(#ipcaErrorPosGrad)" : "url(#ipcaErrorNegGrad)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// 6. IPCA Anual Chart (Trajetórias)
export function IPCAAnualChart({ data }: { data: IpcaAnualRow[] }) {
  // Ordena os dados de trajetórias cronologicamente e realiza amostragem (mensal)
  const sortedData = [...data].sort((a, b) => a.survey_date.localeCompare(b.survey_date));
  const sampledData = sortedData.filter((_, idx) => idx % 20 === 0);

  const chartData = sampledData.map((d) => ({
    date: d.survey_date.slice(0, 10),
    Expectativa: d.ipca_focus_ano_pct,
    Realizado: d.ipca_ibge_acum_ano_dez_pct,
    ano: d.ipca_year_ref,
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} stroke={GRID_COLOR} minTickGap={30} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
        />
        <Legend />
        <Line type="monotone" dataKey="Expectativa" name="Mediana Focus" stroke={ACCENT_CYAN} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        <Line type="step" dataKey="Realizado" name="IBGE Realizado" stroke={IBGE_COLOR} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} strokeDasharray="5 5" connectNulls={true} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function IPCAAnualFechamentoBarras({ data }: { data: IpcaAnualFechamentoRow[] }) {
  const chartData = data.map((d) => ({
    name: String(d.ano_ref),
    Focus: d.ipca_focus_ano_pct,
    IBGE: d.ipca_ibge_acum_ano_dez_pct,
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="focusIpcaBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={FOCUS_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="ibgeIpcaBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={IBGE_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#c2410c" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
        />
        <Legend wrapperStyle={{ color: "#fff", paddingTop: 10 }} />
        <ReferenceLine y={0} stroke="#4b5563" />
        <Bar dataKey="Focus" fill="url(#focusIpcaBarGrad)" name="Focus (expectativa inicial)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="IBGE" fill="url(#ibgeIpcaBarGrad)" name="IBGE Realizado (jan-dez)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function IPCAAnualFechamentoErro({ data }: { data: IpcaAnualFechamentoRow[] }) {
  const chartData = data.map((d) => ({
    name: String(d.ano_ref),
    erro: d.erro_prev_menos_real_pp,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="ipcaAnualErrorPosGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#991b1b" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="ipcaAnualErrorNegGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#065f46" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v >= 0 ? "+" : ""}${v.toFixed(2)} p.p.`, "Erro (Focus - IBGE)"]}
        />
        <ReferenceLine y={0} stroke="#6b7280" />
        <Bar dataKey="erro" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.erro > 0 ? "url(#ipcaAnualErrorPosGrad)" : "url(#ipcaAnualErrorNegGrad)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SelicAnualChart({ data }: { data: SelicAnualRow[] }) {
  const sorted = [...data].sort((a, b) => a.survey_date.localeCompare(b.survey_date));

  const chartData = sorted.map((d, i, arr) => {
    const isFirstInYear = i === 0 || arr[i - 1].selic_year_ref !== d.selic_year_ref;
    const isLastInYear = i === arr.length - 1 || arr[i + 1].selic_year_ref !== d.selic_year_ref;
    const metaInicio = Number.isFinite(d.selic_meta_primeira_survey_pct)
      ? d.selic_meta_primeira_survey_pct
      : d.selic_sgs_pct_aa_aprox;
    const metaFim = d.selic_sgs_pct_aa_aprox;
    // Degrau: meta SGS 432 na 1ª survey do ano até nov; salto para fechamento em dez
    const realizado = isLastInYear ? metaFim : metaInicio;

    return {
      date: d.survey_date.slice(0, 10),
      Expectativa: d.selic_focus_ano_pct,
      Realizado: realizado,
      ano: d.selic_year_ref,
      isFirstInYear,
      isLastInYear,
      metaInicio,
      metaFim,
    };
  });

  const renderMetaDot = (props: { cx?: number; cy?: number; index?: number }) => {
    const { cx, cy, index = 0 } = props;
    if (cx == null || cy == null) {
      return <circle cx={0} cy={0} r={0} fill="none" stroke="none" />;
    }
    const row = chartData[index];
    const show = row?.isFirstInYear || row?.isLastInYear;
    // Recharts não traça segmentos se o dot retorna null — usar r=0 nos demais pontos
    return (
      <circle
        cx={cx}
        cy={cy}
        r={show ? 4 : 0}
        fill={show ? "#fff" : "none"}
        stroke={show ? IBGE_COLOR : "none"}
        strokeWidth={show ? 2 : 0}
      />
    );
  };

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} stroke={GRID_COLOR} minTickGap={30} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number, name: string, item) => {
            if (name === "Meta Selic (SGS 432)" && item?.payload) {
              const p = item.payload as { isFirstInYear?: boolean; isLastInYear?: boolean; metaInicio?: number; metaFim?: number };
              if (p.isFirstInYear && !p.isLastInYear) {
                return [`${p.metaInicio?.toFixed(2)}% (meta na 1ª survey)`, name];
              }
              if (p.isLastInYear) {
                return [`${p.metaFim?.toFixed(2)}% (fechamento dez)`, name];
              }
            }
            return [`${v.toFixed(2)}%`, name];
          }}
        />
        <Legend />
        <Line type="monotone" dataKey="Expectativa" name="Mediana Focus" stroke={ACCENT_CYAN} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        <Line
          type="stepAfter"
          dataKey="Realizado"
          name="Meta Selic (SGS 432)"
          stroke={IBGE_COLOR}
          strokeWidth={2.5}
          dot={renderMetaDot}
          activeDot={{ r: 6, fill: "#fff", stroke: IBGE_COLOR, strokeWidth: 2 }}
          strokeDasharray="5 5"
          connectNulls
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SelicAnualFechamentoBarras({ data }: { data: SelicAnualFechamentoRow[] }) {
  const chartData = data.map((d) => ({
    name: String(d.ano_ref),
    Focus: d.selic_focus_ano_pct,
    SGS: d.selic_sgs_pct_aa_aprox,
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="focusSelicBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={FOCUS_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="sgsSelicBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={IBGE_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#c2410c" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
        />
        <Legend wrapperStyle={{ color: "#fff", paddingTop: 10 }} />
        <ReferenceLine y={0} stroke="#4b5563" />
        <Bar dataKey="Focus" fill="url(#focusSelicBarGrad)" name="Focus (expectativa inicial)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="SGS" fill="url(#sgsSelicBarGrad)" name="Meta Selic Realizada (SGS 432)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SelicAnualFechamentoErro({ data }: { data: SelicAnualFechamentoRow[] }) {
  const chartData = data.map((d) => ({
    name: String(d.ano_ref),
    erro: d.erro_prev_menos_real_pp,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="selicAnualErrorPosGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#991b1b" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="selicAnualErrorNegGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#065f46" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v >= 0 ? "+" : ""}${v.toFixed(2)} p.p.`, "Erro (Focus - Meta Selic)"]}
        />
        <ReferenceLine y={0} stroke="#6b7280" />
        <Bar dataKey="erro" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.erro > 0 ? "url(#selicAnualErrorPosGrad)" : "url(#selicAnualErrorNegGrad)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

const PIB_REALIZADO_DEFAULTS: Record<number, number> = {
  2018: 1.8,
  2019: 1.2,
  2020: -3.3,
  2021: 4.8,
  2022: 3.0,
  2023: 3.2,
  2024: 3.4,
  2025: 2.3,
};

// 6.5. PIB Anual Charts (Trajetórias e Fechamento)
export function PibAnualChart({ data }: { data: PibAnualRow[] }) {
  const sorted = [...data].sort((a, b) => a.survey_date.localeCompare(b.survey_date));
  
  const chartData = sorted.map((d) => {
    const Y = d.pib_year_ref;
    const month = d.survey_date.slice(5, 7);
    let realizado: number | null = null;
    
    if (month === "01") {
      const prevYear = Y - 1;
      realizado = PIB_REALIZADO_DEFAULTS[prevYear] !== undefined ? PIB_REALIZADO_DEFAULTS[prevYear] : null;
    } else if (month === "12") {
      realizado = PIB_REALIZADO_DEFAULTS[Y] !== undefined ? PIB_REALIZADO_DEFAULTS[Y] : null;
    }
    
    return {
      date: d.survey_date.slice(0, 10),
      Expectativa: d.pib_focus_ano_pct,
      Realizado: realizado,
      ano: Y,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} stroke={GRID_COLOR} minTickGap={30} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: any, name: string, entry: any) => {
            if (name === "IBGE Realizado (4T acum.)" && entry?.payload) {
              const p = entry.payload;
              const month = p.date.slice(5, 7);
              if (month === "01") {
                return [`${Number(v).toFixed(2)}%`, `PIB ${p.ano - 1}`];
              }
              if (month === "12") {
                return [`${Number(v).toFixed(2)}%`, `PIB ${p.ano}`];
              }
            }
            return [v !== null && v !== undefined && !isNaN(v) ? `${Number(v).toFixed(2)}%` : "-", name];
          }}
        />
        <Legend />
        <Line type="monotone" dataKey="Expectativa" name="Mediana Focus" stroke={ACCENT_CYAN} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        <Line type="step" dataKey="Realizado" name="IBGE Realizado (4T acum.)" stroke={IBGE_COLOR} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} strokeDasharray="5 5" connectNulls={true} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function PibAnualFechamentoBarras({ data }: { data: PibAnualFechamentoRow[] }) {
  const chartData = data.map((d) => ({
    name: String(d.ano_ref),
    Focus: d.pib_focus_ano_pct,
    IBGE: d.pib_ibge_4tri_yoy_pct,
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="focusPibBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={FOCUS_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="ibgePibBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={IBGE_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#c2410c" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
        />
        <Legend wrapperStyle={{ color: "#fff", paddingTop: 10 }} />
        <ReferenceLine y={0} stroke="#4b5563" />
        <Bar dataKey="Focus" fill="url(#focusPibBarGrad)" name="Focus (expectativa inicial)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="IBGE" fill="url(#ibgePibBarGrad)" name="IBGE Realizado (4T acum.)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function PibAnualFechamentoErro({ data }: { data: PibAnualFechamentoRow[] }) {
  const chartData = data.map((d) => ({
    name: String(d.ano_ref),
    erro: d.erro_prev_menos_real_pp,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="pibAnualErrorPosGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#991b1b" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="pibAnualErrorNegGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#065f46" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v >= 0 ? "+" : ""}${v.toFixed(2)} p.p.`, "Erro (Focus - IBGE)"]}
        />
        <ReferenceLine y={0} stroke="#6b7280" />
        <Bar dataKey="erro" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.erro > 0 ? "url(#pibAnualErrorPosGrad)" : "url(#pibAnualErrorNegGrad)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// 7. Selic Reuniões Copom Chart
export function SelicCopomChart({ data }: { data: SelicMensalRow[] }) {
  const [showAll, setShowAll] = useState(true);

  const chartData = data.map((d) => ({
    name: `${d.ref_yyyymm.slice(4)}/${d.ref_yyyymm.slice(0, 4)}`,
    Expectativa: d.selic_focus_pct,
    Realizado: d.selic_sgs_pct_aa_aprox,
    reuniao: d.reuniao_focus,
  }));

  const filteredData = showAll ? chartData : chartData.slice(-16);

  return (
    <div>
      <div className="chart-range-selector">
        <button className={!showAll ? "active" : ""} onClick={() => setShowAll(false)}>
          Últimas 16 Reuniões
        </button>
        <button className={showAll ? "active" : ""} onClick={() => setShowAll(true)}>
          Histórico Completo ({chartData.length} reuniões)
        </button>
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={filteredData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
          <defs>
            <linearGradient id="selicFGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ACCENT_GOLD} stopOpacity={0.9} />
              <stop offset="100%" stopColor="#b45309" stopOpacity={0.7} />
            </linearGradient>
            <linearGradient id="selicRGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ACCENT_PURPLE} stopOpacity={0.9} />
              <stop offset="100%" stopColor="#6b21a8" stopOpacity={0.7} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
          <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} minTickGap={25} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
            formatter={(v: number, name, props) => [`${v.toFixed(2)}%`, name === "Expectativa" ? `Focus (${props.payload.reuniao})` : "SGS Realizado"]}
          />
          <Legend />
          <ReferenceLine y={0} stroke="#4b5563" />
          <Bar dataKey="Expectativa" fill="url(#selicFGrad)" name="Expectativa Focus Copom" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Realizado" fill="url(#selicRGrad)" name="Meta Selic (SGS 432)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// 8. Câmbio Timeline Chart (Forward vs Spot)
export function CambioTimelineChart({ data }: { data: PainelRow[] }) {
  // Pegamos uma observação a cada 5 linhas para o gráfico de série longa ficar mais limpo
  const sampledData = data.filter((_, idx) => idx % 5 === 0).map((d) => ({
    date: d.survey_date.slice(0, 10),
    Focus_Fwd: d.usdbrl_med_fwd,
    Spot_Real: d.usd_sgs_med,
  })).filter((d) => Number.isFinite(d.Focus_Fwd) && Number.isFinite(d.Spot_Real));

  return (
    <ResponsiveContainer width="100%" height={380}>
      <LineChart data={sampledData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} stroke={GRID_COLOR} minTickGap={40} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} tickFormatter={(val: number) => `R$ ${val.toFixed(2)}`} stroke={GRID_COLOR} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`R$ ${v.toFixed(4)}`]}
        />
        <Legend />
        <Line type="monotone" dataKey="Focus_Fwd" name="Expectativa Câmbio 12m (Focus)" stroke="#10b981" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Spot_Real" name="USD/BRL à Vista (SGS 1)" stroke="#3b82f6" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// 9. Desancoragem 12m Chart (Focus 12m vs Meta CMN)
export function Desancoragem12mChart({ data }: { data: PainelRow[] }) {
  const sampledData = data
    .filter((_, idx) => idx % 5 === 0)
    .map((d) => ({
      date: d.survey_date.slice(0, 10),
      Focus_12m: d.ipca_med12m,
      Meta_Centro: d.ipca_meta_centro_12m,
      Meta_Inferior: d.ipca_meta_inferior_12m,
      Meta_Superior: d.ipca_meta_superior_12m,
    }))
    .filter((d): d is { date: string; Focus_12m: number; Meta_Centro: number; Meta_Inferior: number; Meta_Superior: number } => 
      Number.isFinite(d.Focus_12m) && 
      d.Meta_Centro !== undefined && Number.isFinite(d.Meta_Centro) &&
      d.Meta_Inferior !== undefined &&
      d.Meta_Superior !== undefined
    );

  return (
    <ResponsiveContainer width="100%" height={380}>
      <LineChart data={sampledData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} stroke={GRID_COLOR} minTickGap={40} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v.toFixed(2)}%`]}
        />
        <Legend />
        <ReferenceArea x1="2019-01-02" x2="2022-12-30" fill="rgba(16, 185, 129, 0.04)" label={{ value: "Bolsonaro (2019-2022)", fill: "#10b981", position: "insideTopLeft", fontSize: 10, offset: 8 }} />
        <ReferenceArea x1="2023-01-02" fill="rgba(239, 68, 68, 0.04)" label={{ value: "Lula 3 (2023+)", fill: "#ef4444", position: "insideTopLeft", fontSize: 10, offset: 8 }} />
        <Line type="monotone" dataKey="Focus_12m" name="Expectativa Focus 12m" stroke={FOCUS_COLOR} strokeWidth={2.5} dot={false} />
        <Line type="monotone" dataKey="Meta_Centro" name="Centro da Meta CMN" stroke="#10b981" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Meta_Superior" name="Limite Superior" stroke="#ef4444" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
        <Line type="monotone" dataKey="Meta_Inferior" name="Limite Inferior" stroke="#eab308" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// 10. Desvio de Desancoragem (Expectativa - Centro da Meta)
export function DesancoragemCentroChart({ data }: { data: PainelRow[] }) {
  const sampledData = data
    .filter((_, idx) => idx % 5 === 0)
    .map((d) => ({
      date: d.survey_date.slice(0, 10),
      desvio: d.desancoragem_centro_12m,
    }))
    .filter((d): d is { date: string; desvio: number } => d.desvio !== undefined && Number.isFinite(d.desvio));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={sampledData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="desposGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#991b1b" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="desnegGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#065f46" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} stroke={GRID_COLOR} minTickGap={40} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v >= 0 ? "+" : ""}${v.toFixed(2)} p.p.`, "Desvio do Centro da Meta"]}
        />
        <ReferenceLine y={0} stroke="#6b7280" />
        <Bar dataKey="desvio" radius={[2, 2, 0, 0]}>
          {sampledData.map((entry, i) => (
            <Cell key={i} fill={entry.desvio > 0 ? "url(#desposGrad)" : "url(#desnegGrad)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// 11. IPCA Anual com limites da meta (trajetória por ano)
export function IPCAAnualDesancoragemChart({ data }: { data: IpcaAnualRow[] }) {
  // Ordena os dados de trajetórias cronologicamente e realiza amostragem (mensal)
  const sortedData = [...data].sort((a, b) => a.survey_date.localeCompare(b.survey_date));
  const sampledData = sortedData.filter((_, idx) => idx % 20 === 0);

  const chartData = sampledData
    .map((d) => ({
      date: d.survey_date.slice(0, 10),
      Expectativa: d.ipca_focus_ano_pct,
      Realizado: d.ipca_ibge_acum_ano_dez_pct,
      Meta_Centro: d.meta_centro,
      Meta_Superior: d.meta_superior,
      Meta_Inferior: d.meta_inferior,
    }))
    .filter((d): d is { date: string; Expectativa: number; Realizado: number; Meta_Centro: number; Meta_Superior: number; Meta_Inferior: number } => 
      Number.isFinite(d.Expectativa) &&
      d.Meta_Centro !== undefined &&
      d.Meta_Superior !== undefined &&
      d.Meta_Inferior !== undefined
    );

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} stroke={GRID_COLOR} minTickGap={30} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
        />
        <Legend />
        <Line type="monotone" dataKey="Expectativa" name="Mediana Focus" stroke={FOCUS_COLOR} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        <Line type="step" dataKey="Realizado" name="IBGE Realizado" stroke={IBGE_COLOR} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} strokeDasharray="5 5" connectNulls={true} />
        <Line type="monotone" dataKey="Meta_Centro" name="Centro da Meta" stroke="#10b981" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Meta_Superior" name="Limite Superior" stroke="#ef4444" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
        <Line type="monotone" dataKey="Meta_Inferior" name="Limite Inferior" stroke="#eab308" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function ScatterFiscalMonetaria({ data }: { data: PainelRow[] }) {
  const ptsBolsonaro = data
    .filter((d) => d.dummy_lula === 0 && Number.isFinite(d.dbgg_med_pct) && Number.isFinite(d.selic_mediana_pct))
    .map((d) => ({
      dbgg: d.dbgg_med_pct,
      selic: d.selic_mediana_pct,
      date: d.survey_date.slice(0, 10),
    }));

  const ptsLula = data
    .filter((d) => d.dummy_lula === 1 && Number.isFinite(d.dbgg_med_pct) && Number.isFinite(d.selic_mediana_pct))
    .map((d) => ({
      dbgg: d.dbgg_med_pct,
      selic: d.selic_mediana_pct,
      date: d.survey_date.slice(0, 10),
    }));

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ScatterChart margin={{ top: 16, right: 16, bottom: 8, left: -20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis type="number" dataKey="dbgg" name="Expectativa DBGG" tickFormatter={(val) => `${val}%`} domain={["dataMin - 1", "dataMax + 1"]} tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis type="number" dataKey="selic" name="Expectativa Selic" tickFormatter={(val) => `${val}%`} domain={["dataMin - 1", "dataMax + 1"]} tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <ZAxis range={[50, 50]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#1f2937", borderColor: "rgba(255,255,255,0.1)", borderRadius: "6px" }}
          itemStyle={{ color: "#f3f4f6" }}
          cursor={{ strokeDasharray: "3 3", stroke: "#9ca3af" }}
          formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
        />
        <Legend />
        <Scatter name="Bolsonaro (2019-2022)" data={ptsBolsonaro} fill="#10b981" fillOpacity={0.65} stroke="#059669" strokeWidth={1} />
        <Scatter name="Lula 3 (2023-2026)" data={ptsLula} fill="#ef4444" fillOpacity={0.65} stroke="#dc2626" strokeWidth={1} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function ComparacaoErrosGovernos({
  ipcaB, ipcaL,
  selicB, selicL,
  pibB, pibL,
  dbggB, dbggL,
  metric,
}: {
  ipcaB: { mae: number; rmse: number; bias: number };
  ipcaL: { mae: number; rmse: number; bias: number };
  selicB: { mae: number; rmse: number; bias: number };
  selicL: { mae: number; rmse: number; bias: number };
  pibB: { mae: number; rmse: number; bias: number };
  pibL: { mae: number; rmse: number; bias: number };
  dbggB: { mae: number; rmse: number; bias: number };
  dbggL: { mae: number; rmse: number; bias: number };
  metric: "MAE" | "RMSE";
}) {
  const chartData = [
    { name: "IPCA", Bolsonaro_Error: metric === "MAE" ? ipcaB.mae : ipcaB.rmse, Lula3_Error: metric === "MAE" ? ipcaL.mae : ipcaL.rmse, Bolsonaro_Bias: ipcaB.bias, Lula3_Bias: ipcaL.bias },
    { name: "Selic", Bolsonaro_Error: metric === "MAE" ? selicB.mae : selicB.rmse, Lula3_Error: metric === "MAE" ? selicL.mae : selicL.rmse, Bolsonaro_Bias: selicB.bias, Lula3_Bias: selicL.bias },
    { name: "PIB", Bolsonaro_Error: metric === "MAE" ? pibB.mae : pibB.rmse, Lula3_Error: metric === "MAE" ? pibL.mae : pibL.rmse, Bolsonaro_Bias: pibB.bias, Lula3_Bias: pibL.bias },
    { name: "DBGG", Bolsonaro_Error: metric === "MAE" ? dbggB.mae : dbggB.rmse, Lula3_Error: metric === "MAE" ? dbggL.mae : dbggL.rmse, Bolsonaro_Bias: dbggB.bias, Lula3_Bias: dbggL.bias },
  ];

  return (
    <div className="grid-2 span-2">
      <div className="chart-wrapper glass-card" style={{ padding: 16 }}>
        <h4 style={{ textAlign: "center", marginBottom: 12, color: "#fff", fontSize: 13, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {metric === "MAE" ? "Erro Médio Absoluto (MAE) — Menor é Melhor" : "Erro Quadrático Médio (RMSE) — Menor é Melhor"}
        </h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
            <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
            <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
            <Tooltip contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }} formatter={(v: number) => [`${v.toFixed(3)} p.p.`]} />
            <Legend />
            <Bar dataKey="Bolsonaro_Error" fill="#10b981" name={`Bolsonaro (${metric})`} radius={[4, 4, 0, 0]} />
            <Bar dataKey="Lula3_Error" fill="#ef4444" name={`Lula 3 (${metric})`} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-wrapper glass-card" style={{ padding: 16 }}>
        <h4 style={{ textAlign: "center", marginBottom: 12, color: "#fff", fontSize: 13, textTransform: "uppercase", letterSpacing: "0.05em" }}>Viés de Previsão (Erro Médio) — Próximo a 0 é Melhor</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
            <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
            <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
            <Tooltip contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }} formatter={(v: number) => [`${v >= 0 ? "+" : ""}${v.toFixed(3)} p.p.`]} />
            <Legend />
            <ReferenceLine y={0} stroke="#4b5563" />
            <Bar dataKey="Bolsonaro_Bias" fill="#10b981" name="Bolsonaro (Viés)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Lula3_Bias" fill="#ef4444" name="Lula 3 (Viés)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section className="chart-card">
      <header>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </header>
      {children}
    </section>
  );
}

// 12. Componentes de Dívida Bruta (DBGG)
export function DbggMensalChart({ data }: { data: DbggMensalRow[] }) {
  const chartData = data.map((d) => ({
    name: `${String(d.mes).padStart(2, "0")}/${d.ano_ref}`,
    DBGG: d.dbgg_sgs_pct_pib,
  }));

  const isLarge = chartData.length > 30;

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} minTickGap={25} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v.toFixed(2)}%`]}
        />
        <Legend />
        <Line type="monotone" dataKey="DBGG" name="DBGG Realizada (SGS 13762)" stroke={IBGE_COLOR} strokeWidth={2.5} dot={isLarge ? { r: 1 } : { r: 4 }} activeDot={{ r: 6 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function DbggAnualFechamentoBarras({ data }: { data: DbggAnualFechamentoRow[] }) {
  const chartData = data.map((d) => ({
    name: String(d.ano),
    Focus: d.focus_ultima_mediana_pct_pib,
    Realizado: d.dbgg_realizado_dez_pct_pib,
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="focusDbggBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={FOCUS_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="realizedDbggBarGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={IBGE_COLOR} stopOpacity={0.9} />
            <stop offset="100%" stopColor="#c2410c" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number, name) => [`${v != null && !isNaN(v) ? `${v.toFixed(2)}%` : "N/A"}`, name]}
        />
        <Legend wrapperStyle={{ color: "#fff", paddingTop: 10 }} />
        <ReferenceLine y={0} stroke="#4b5563" />
        <Bar dataKey="Focus" fill="url(#focusDbggBarGrad)" name="Focus (última mediana pré-divulgação)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Realizado" fill="url(#realizedDbggBarGrad)" name="SGS Realizado (dezembro)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DbggAnualFechamentoErro({ data }: { data: DbggAnualFechamentoRow[] }) {
  const chartData = data
    .filter((d) => d.erro_focus_vs_realizado_pp !== null && !isNaN(d.erro_focus_vs_realizado_pp))
    .map((d) => ({
      name: String(d.ano),
      erro: d.erro_focus_vs_realizado_pp,
    }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
        <defs>
          <linearGradient id="dbggErrorPosGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#991b1b" stopOpacity={0.7} />
          </linearGradient>
          <linearGradient id="dbggErrorNegGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#065f46" stopOpacity={0.7} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" p.p." stroke={GRID_COLOR} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v >= 0 ? "+" : ""}${v.toFixed(2)} p.p.`, "Erro (Focus - SGS)"]}
        />
        <ReferenceLine y={0} stroke="#6b7280" />
        <Bar dataKey="erro" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.erro > 0 ? "url(#dbggErrorPosGrad)" : "url(#dbggErrorNegGrad)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DbggConvergenciaFocus({ data }: { data: DbggTrajetoriaRow[] }) {
  const chartData = data
    .filter((d) => d.dbgg_focus_med_pct_pib !== null && !isNaN(d.dbgg_focus_med_pct_pib))
    .map((d) => ({
      date: d.survey_date.slice(0, 10),
      Expectativa: d.dbgg_focus_med_pct_pib,
    }));

  const realizado = data.find((d) => d.dbgg_sgs_pct_pib !== null && !isNaN(d.dbgg_sgs_pct_pib))?.dbgg_sgs_pct_pib ?? null;

  // Calcula o domínio do YAxis para incluir tanto a trajetória Focus quanto o valor realizado
  const expectations = chartData.map((d) => d.Expectativa).filter((v) => !isNaN(v));
  let yMin = expectations.length > 0 ? Math.min(...expectations) : 70;
  let yMax = expectations.length > 0 ? Math.max(...expectations) : 90;

  if (realizado !== null) {
    yMin = Math.min(yMin, realizado);
    yMax = Math.max(yMax, realizado);
  }

  const padding = (yMax - yMin) * 0.05 || 1;
  const yMinAdjusted = Math.max(0, Number((yMin - padding).toFixed(1)));
  const yMaxAdjusted = Number((yMax + padding).toFixed(1));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData} margin={{ top: 20, right: 15, left: -20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} stroke={GRID_COLOR} minTickGap={30} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={[yMinAdjusted, yMaxAdjusted]} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)" }}
          formatter={(v: number) => [`${v.toFixed(2)}%`, "Expectativa Focus"]}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="Expectativa"
          name="Mediana Focus"
          stroke={FOCUS_COLOR}
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 6 }}
        />
        {realizado !== null && (
          <ReferenceLine
            y={realizado}
            stroke={IBGE_COLOR}
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{
              value: `Realizado (Dez): ${realizado.toFixed(2)}%`,
              fill: "#f3f4f6",
              position: "top",
              fontSize: 11,
              fontWeight: 600,
            }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
