import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";
import { loadDashboardData } from "./loadData";
import type { DashboardData } from "./types";
import "./App.css";

// Paleta de cores premium dark
const REALIZED_COLOR = "#f97316"; // Laranja/Coral para o realizado
const BOLS_SIM_COLOR = "#06b6d4";  // Ciano para simulação Bolsonaro
const LULA_SIM_COLOR = "#a855f7";  // Roxo para simulação Lula 3
const GRID_COLOR = "rgba(255, 255, 255, 0.08)";

export default function App() {
  const [rawData, setRawData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Estado de controle do simulador
  const [fiscalMode, setFiscalMode] = useState<"historical" | "custom">("historical");
  const [customBolsPrim, setCustomBolsPrim] = useState<number>(-2.71); // Padrão Bolsonaro
  const [customLulaPrim, setCustomLulaPrim] = useState<number>(-1.08); // Padrão Lula 3

  useEffect(() => {
    loadDashboardData()
      .then((res) => {
        setRawData(res);
      })
      .catch((err) => {
        console.error(err);
        setError("Erro ao carregar os dados históricos de simulação da DBGG.");
      });
  }, []);

  // Lógica de cálculo dinâmico da simulação de trajetória da dívida
  const simulatedData = useMemo(() => {
    if (!rawData?.dbggSimulacao || rawData.dbggSimulacao.length === 0) return [];

    const D0 = 75.27; // Dívida Bruta Realizada em 2018 (ponto de partida)
    let currentBolsDebt = D0;
    let currentLulaDebt = D0;

    return rawData.dbggSimulacao.map((row) => {
      if (row.ano === 2018) {
        return {
          ano: 2018,
          dbgg_realizado: row.dbgg_realizado,
          primario_realizado: row.primario_realizado,
          sim_bols: D0,
          sim_lula: D0,
          prim_sim_bols: row.primario_realizado,
          prim_sim_lula: row.primario_realizado,
          custo_implicito: 0,
          g_nominal: 0,
        };
      }

      const g_t = row.g_nominal ?? 0;
      const i_t = row.custo_implicito ?? 0;

      // 1. Definição do resultado primário contra-fatual de Bolsonaro (2019-2022)
      let s_t_bols = row.primario_realizado;
      if (row.ano >= 2019 && row.ano <= 2022) {
        s_t_bols = fiscalMode === "historical" ? -1.077 : customBolsPrim;
      }

      // 2. Definição do resultado primário contra-fatual de Lula 3 (2023-2025)
      let s_t_lula = row.primario_realizado;
      if (row.ano >= 2023 && row.ano <= 2025) {
        s_t_lula = fiscalMode === "historical" ? -2.707 : customLulaPrim;
      }

      // Equação de dinâmica da dívida intertemporal:
      // D_t = D_{t-1} * (1 + i_t) / (1 + g_t) - S_t
      currentBolsDebt = currentBolsDebt * (1 + i_t) / (1 + g_t) - s_t_bols;
      currentLulaDebt = currentLulaDebt * (1 + i_t) / (1 + g_t) - s_t_lula;

      return {
        ano: row.ano,
        dbgg_realizado: row.dbgg_realizado,
        primario_realizado: row.primario_realizado,
        sim_bols: parseFloat(currentBolsDebt.toFixed(2)),
        sim_lula: parseFloat(currentLulaDebt.toFixed(2)),
        prim_sim_bols: parseFloat(s_t_bols.toFixed(2)),
        prim_sim_lula: parseFloat(s_t_lula.toFixed(2)),
        custo_implicito: i_t,
        g_nominal: g_t,
      };
    });
  }, [rawData, fiscalMode, customBolsPrim, customLulaPrim]);

  // Recupera o último ano simulado para exibir nos cards bento
  const finalYearData = useMemo(() => {
    if (simulatedData.length === 0) return null;
    return simulatedData[simulatedData.length - 1];
  }, [simulatedData]);

  if (error) {
    return (
      <div className="error fade-in">
        <div className="error-card glass-card">
          <h1>Falha de Conexão</h1>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!rawData) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p style={{ fontFamily: "var(--font-title)", color: "var(--color-text-muted)" }}>
          Carregando simulador de dinâmica da dívida pública...
        </p>
      </div>
    );
  }

  return (
    <div className="app fade-in">
      {/* Hero Section */}
      <header className="hero">
        <h1>Simulador de Dívida Pública (DBGG)</h1>
        <p>
          Simule trajetórias contra-fatuais interativas para a Dívida Bruta do Governo Geral (% PIB).
          Veja como seria o estoque da dívida caso os governos **Bolsonaro (2019-2022)** e **Lula 3 (2023-2025)** tivessem trocado suas políticas fiscais de resultado primário ou adotado metas personalizadas.
        </p>
        <div className="meta">
          Fórmula estrutural calibrada: D_t = D_t-1 × (1+i_t)/(1+g_t) - S_t
        </div>
      </header>

      {/* Mode Selector and Sliders */}
      <div className="chart-card" style={{ marginBottom: "2rem" }}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h2>Configurações do Cenário Fiscal</h2>
            <p>Escolha a dinâmica de resultado primário dos governos para rodar a simulação.</p>
          </div>
          
          <div className="subtabs-nav" style={{ margin: 0 }}>
            <button
              className={fiscalMode === "historical" ? "active" : ""}
              onClick={() => {
                setFiscalMode("historical");
                setCustomBolsPrim(-2.71);
                setCustomLulaPrim(-1.08);
              }}
            >
              📊 Cenário Histórico Cruzado
            </button>
            <button
              className={fiscalMode === "custom" ? "active" : ""}
              onClick={() => setFiscalMode("custom")}
            >
              🎛️ Simulador Personalizado
            </button>
          </div>
        </header>

        {fiscalMode === "custom" ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2.5rem", marginTop: "1.5rem" }}>
            <div className="glass-card" style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(6, 182, 212, 0.25)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <span style={{ fontWeight: 600, color: "var(--color-accent)" }}>Governo Bolsonaro (2019-2022)</span>
                <span className="text-neon text-bold">{customBolsPrim > 0 ? "+" : ""}{customBolsPrim.toFixed(2)}% do PIB</span>
              </div>
              <p style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", margin: "0 0 1rem 0" }}>
                Simular o resultado primário médio anual do governo central durante este período (Realizado médio: -2,71%).
              </p>
              <input
                type="range"
                min="-6.0"
                max="2.0"
                step="0.1"
                value={customBolsPrim}
                onChange={(e) => setCustomBolsPrim(parseFloat(e.target.value))}
                style={{ width: "100%", cursor: "pointer", accentColor: "var(--color-accent)" }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "0.25rem" }}>
                <span>Déficit de -6%</span>
                <span>Superávit de +2%</span>
              </div>
            </div>

            <div className="glass-card" style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(168, 85, 247, 0.25)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <span style={{ fontWeight: 600, color: "var(--color-accent)" }}>Governo Lula 3 (2023-2025)</span>
                <span className="text-neon text-bold">{customLulaPrim > 0 ? "+" : ""}{customLulaPrim.toFixed(2)}% do PIB</span>
              </div>
              <p style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", margin: "0 0 1rem 0" }}>
                Simular o resultado primário médio anual do governo central durante este período (Realizado médio: -1,08%).
              </p>
              <input
                type="range"
                min="-6.0"
                max="2.0"
                step="0.1"
                value={customLulaPrim}
                onChange={(e) => setCustomLulaPrim(parseFloat(e.target.value))}
                style={{ width: "100%", cursor: "pointer", accentColor: "var(--color-accent)" }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "0.25rem" }}>
                <span>Déficit de -6%</span>
                <span>Superávit de +2%</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="glass-card" style={{ padding: "1.25rem", borderRadius: "10px", marginTop: "1rem" }}>
            <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--color-text-muted)", lineHeight: "1.6" }}>
              💡 **Cenário Histórico Cruzado:** Mostra o efeito aritmético de transpor as políticas fiscais médias. A linha de simulação de 
              **Bolsonaro** aplica a média fiscal de Lula 3 (`-1,08%` de primário) no período 2019-2022. 
              A linha de simulação de **Lula 3** aplica a média fiscal de Bolsonaro (`-2,71%` de primário) no período 2023-2025.
            </p>
          </div>
        )}
      </div>

      {/* Summary Metrics Row (Bento Style) */}
      <div className="summary-cards" style={{ marginBottom: "2rem" }}>
        <div className="summary-card" style={{ borderLeft: `4px solid ${REALIZED_COLOR}` }}>
          <h3>Dívida Realizada (Fechamento 2025)</h3>
          <p className="value" style={{ background: `linear-gradient(120deg, #fff, ${REALIZED_COLOR})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {finalYearData?.dbgg_realizado.toFixed(2)}%
          </p>
          <p className="subtitle">Dado oficial apurado pelo Banco Central (SGS 13762)</p>
        </div>

        <div className="summary-card" style={{ borderLeft: `4px solid ${BOLS_SIM_COLOR}` }}>
          <h3>Bolsonaro Simulado (Cenário 2025)</h3>
          <p className="value" style={{ background: `linear-gradient(120deg, #fff, ${BOLS_SIM_COLOR})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {finalYearData?.sim_bols.toFixed(2)}%
          </p>
          <p className="subtitle">
            Diferença: {finalYearData ? (finalYearData.sim_bols - finalYearData.dbgg_realizado).toFixed(2) : "0"} p.p.
          </p>
        </div>

        <div className="summary-card" style={{ borderLeft: `4px solid ${LULA_SIM_COLOR}` }}>
          <h3>Lula 3 Simulado (Cenário 2025)</h3>
          <p className="value" style={{ background: `linear-gradient(120deg, #fff, ${LULA_SIM_COLOR})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {finalYearData?.sim_lula.toFixed(2)}%
          </p>
          <p className="subtitle">
            Diferença: {finalYearData ? (finalYearData.sim_lula - finalYearData.dbgg_realizado).toFixed(2) : "0"} p.p.
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid-2" style={{ marginBottom: "2rem" }}>
        <div className="chart-card">
          <header>
            <h2>Trajetória da DBGG (% PIB)</h2>
            <p>Comparativo da evolução da relação Dívida/PIB Realizada vs. Cenários Simulados.</p>
          </header>
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={simulatedData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
              <XAxis dataKey="ano" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
              <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
              <Tooltip
                contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }}
                itemStyle={{ color: "#f3f4f6" }}
                formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
              />
              <Legend />
              <Line type="monotone" dataKey="dbgg_realizado" name="Dívida Realizada (SGS)" stroke={REALIZED_COLOR} strokeWidth={3} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="sim_bols" name="Simulação Bolsonaro (Período 19-22)" stroke={BOLS_SIM_COLOR} strokeWidth={2.5} strokeDasharray="5 5" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="sim_lula" name="Simulação Lula 3 (Período 23-25)" stroke={LULA_SIM_COLOR} strokeWidth={2.5} strokeDasharray="5 5" dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <header>
            <h2>Resultado Primário Anual (% PIB)</h2>
            <p>Comparativo do Superávit/Déficit fiscal realizado vs. Cenário contra-fatual adotado.</p>
          </header>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={simulatedData.filter(d => d.ano > 2018)} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
              <XAxis dataKey="ano" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
              <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} />
              <Tooltip
                contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }}
                formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
              />
              <Legend />
              <ReferenceLine y={0} stroke="#6b7280" />
              <Bar dataKey="primario_realizado" name="Primário Realizado" fill={REALIZED_COLOR} opacity={0.8} radius={[4, 4, 0, 0]} />
              <Bar dataKey="prim_sim_bols" name="Primário Sim. Bolsonaro" fill={BOLS_SIM_COLOR} radius={[4, 4, 0, 0]} />
              <Bar dataKey="prim_sim_lula" name="Primário Sim. Lula 3" fill={LULA_SIM_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Math Data Table */}
      <div className="chart-card" style={{ marginBottom: "2rem" }}>
        <header>
          <h2>Detalhamento Anual de Cálculo Fiscais</h2>
          <p>Valores extraídos e apurados que guiam a dinâmica da simulação da dívida pública.</p>
        </header>
        <div className="table-responsive">
          <table className="premium-table">
            <thead>
              <tr>
                <th>Ano</th>
                <th>Crescimento PIB Nominal (g)</th>
                <th>Custo Juro Implícito (i)</th>
                <th>Primário Realizado</th>
                <th>Primário Sim. Bolsonaro</th>
                <th>Primário Sim. Lula 3</th>
                <th>Dívida Realizada</th>
                <th>Dívida Sim. Bolsonaro</th>
                <th>Dívida Sim. Lula 3</th>
              </tr>
            </thead>
            <tbody>
              {simulatedData.map((row) => (
                <tr key={row.ano}>
                  <td className="bold">{row.ano}</td>
                  <td>{row.ano === 2018 ? "—" : `${((row.g_nominal ?? 0) * 100).toFixed(2)}%`}</td>
                  <td>{row.ano === 2018 ? "—" : `${((row.custo_implicito ?? 0) * 100).toFixed(2)}%`}</td>
                  <td className={row.primario_realizado >= 0 ? "text-green" : "text-red"}>
                    {row.primario_realizado > 0 ? "+" : ""}{row.primario_realizado.toFixed(2)}%
                  </td>
                  <td className={row.prim_sim_bols >= 0 ? "text-green" : "text-red"}>
                    {row.prim_sim_bols > 0 ? "+" : ""}{row.prim_sim_bols.toFixed(2)}%
                  </td>
                  <td className={row.prim_sim_lula >= 0 ? "text-green" : "text-red"}>
                    {row.prim_sim_lula > 0 ? "+" : ""}{row.prim_sim_lula.toFixed(2)}%
                  </td>
                  <td className="text-bold">{row.dbgg_realizado.toFixed(2)}%</td>
                  <td className="text-neon text-bold">{row.sim_bols.toFixed(2)}%</td>
                  <td className="text-neon text-bold">{row.sim_lula.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bento Grid Comments */}
      <div className="comments-bento-grid" style={{ marginBottom: "2rem" }}>
        <div className="bento-card card-0 fade-in">
          <div className="bento-card-header">
            <span className="bento-card-title">O Efeito Pandemia (2020)</span>
            <div className="bento-card-icon">🦠</div>
          </div>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-text-main, #f3f4f6)", lineHeight: "1.5" }}>
            O ano de 2020 registrou o maior déficit primário da história recente (`-9,79%` do PIB) para financiar o auxílio emergencial e gastos extraordinários de saúde. Isso reduziu drasticamente o resultado fiscal médio do governo Bolsonaro. No cenário simulado de Lula 3, a transposição da média de Bolsonaro espalha essa ineficiência fiscal nas projeções futuras, impulsionando a curva simulada para cima.
          </p>
        </div>

        <div className="bento-card card-1 fade-in">
          <div className="bento-card-header">
            <span className="bento-card-title">O Custo dos Juros (2023-2025)</span>
            <div className="bento-card-icon">📈</div>
          </div>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-text-main, #f3f4f6)", lineHeight: "1.5" }}>
            O custo implícito da dívida subiu fortemente de `4,49%` em 2022 para `10,87%` em 2025 devido à taxa Selic restritiva. Sob juros elevados, qualquer déficit primário é amplificado na bola de neve da dívida. É por isso que, mantidos os juros altos reais históricos do período, a dívida sob o primário de Bolsonaro teria crescido mais rápido, fechando em `83,61%` do PIB.
          </p>
        </div>

        <div className="bento-card card-2 fade-in">
          <div className="bento-card-header">
            <span className="bento-card-title">PIB Nominal e Denominador</span>
            <div className="bento-card-icon">🧮</div>
          </div>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-text-main, #f3f4f6)", lineHeight: "1.5" }}>
            A relação Dívida/PIB depende fortemente do crescimento nominal do PIB (denominador). Em 2021, o PIB nominal cresceu `18,43%` (influenciado pelo repique da inflação e reabertura do comércio), o que encolheu aritmeticamente a dívida real. Nas simulações contra-fatuais, essa dinâmica do PIB real é conservada integralmente, garantindo o isolamento do efeito fiscal puro.
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="foot">
        <div className="foot-content">
          <span>MBA Economia FIPE — TCC Análise de Trajetórias de Expectativas</span>
          <span>Dados Oficiais Extraídos do SGS do Banco Central do Brasil</span>
        </div>
      </footer>
    </div>
  );
}
