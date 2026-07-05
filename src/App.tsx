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

const REALIZED_COLOR = "#f97316"; // Laranja/Coral para o realizado
const BOLS_SIM_COLOR = "#06b6d4";  // Ciano para simulação Bolsonaro
const LULA_SIM_COLOR = "#a855f7";  // Roxo para simulação Lula 3
const STABILIZING_COLOR = "#10b981"; // Verde para o primário estabilizador
const GRID_COLOR = "rgba(255, 255, 255, 0.08)";

export default function App() {
  const [rawData, setRawData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Controles Macroeconômicos Avançados
  const [primaryType, setPrimaryType] = useState<"realizado" | "estrutural">("realizado");
  const [fiscalMode, setFiscalMode] = useState<"historical" | "custom">("historical");
  const [multiplier, setMultiplier] = useState<number>(0.6); // Multiplicador fiscal (Keynesian drag)
  const [interestSensitivity, setInterestSensitivity] = useState<number>(0.4); // Sensibilidade dos juros (Risk premium)
  
  // Sliders de simulação customizada
  const [customBolsPrim, setCustomBolsPrim] = useState<number>(-2.71); 
  const [customLulaPrim, setCustomLulaPrim] = useState<number>(-1.08); 
  const [customFuturePrim, setCustomFuturePrim] = useState<number>(0.0); // 2026-2030

  useEffect(() => {
    loadDashboardData()
      .then((res) => {
        setRawData(res);
      })
      .catch((err) => {
        console.error(err);
        setError("Erro ao carregar os dados de simulação macro-fiscal.");
      });
  }, []);

  // Calcula dinamicamente as médias históricas/estruturais a partir dos dados carregados
  const mandateBaselines = useMemo(() => {
    if (!rawData?.dbggSimulacao) return { bolsAvg: -2.71, lulaAvg: -1.08 };
    
    const bolsRows = rawData.dbggSimulacao.filter(r => r.ano >= 2019 && r.ano <= 2022);
    const lulaRows = rawData.dbggSimulacao.filter(r => r.ano >= 2023 && r.ano <= 2025);
    
    const bolsField = primaryType === "realizado" ? "primario_realizado" : "primario_estrutural";
    const lulaField = primaryType === "realizado" ? "primario_realizado" : "primario_estrutural";
    
    const bolsAvg = bolsRows.reduce((sum, r) => sum + r[bolsField], 0) / bolsRows.length;
    const lulaAvg = lulaRows.reduce((sum, r) => sum + r[lulaField], 0) / lulaRows.length;
    
    return { bolsAvg, lulaAvg };
  }, [rawData, primaryType]);

  // Atualiza os sliders de simulação quando mudamos o tipo de resultado primário no modo histórico
  useEffect(() => {
    if (fiscalMode === "historical") {
      setCustomBolsPrim(mandateBaselines.bolsAvg);
      setCustomLulaPrim(mandateBaselines.lulaAvg);
    }
  }, [mandateBaselines, fiscalMode]);

  // Lógica recursiva avançada do simulador macro-fiscal (Frentes 1, 2, 3 e 4)
  const simulatedData = useMemo(() => {
    if (!rawData?.dbggSimulacao || rawData.dbggSimulacao.length === 0) return [];

    const D0 = 75.27; // Dívida Bruta em 2018 (ponto de partida)
    let currentBolsDebt = D0;
    let currentLulaDebt = D0;

    return rawData.dbggSimulacao.map((row) => {
      const is2018 = row.ano === 2018;
      
      // Define a linha de base primária ativa (Realizada ou Estrutural sem Covid)
      const basePrim_t = primaryType === "realizado" ? row.primario_realizado : row.primario_estrutural;
      const g_t_real = row.g_nominal ?? 0;
      const i_t_real = row.custo_implicito ?? 0;

      if (is2018) {
        return {
          ano: 2018,
          dbgg_realizado: row.dbgg_realizado,
          primario_baseline: basePrim_t,
          g_nominal: 0,
          custo_implicito: 0,
          sim_bols: D0,
          sim_lula: D0,
          prim_sim_bols: basePrim_t,
          prim_sim_lula: basePrim_t,
          estabilizador_bols: 0,
          estabilizador_lula: 0,
          i_sim_bols: 0,
          g_sim_bols: 0,
          i_sim_lula: 0,
          g_sim_lula: 0,
        };
      }

      // 1. Define o resultado primário simulado para o caminho do cenário "Bolsonaro"
      let s_t_bols_sim = basePrim_t;
      if (row.ano >= 2019 && row.ano <= 2022) {
        s_t_bols_sim = fiscalMode === "historical" ? mandateBaselines.lulaAvg : customBolsPrim;
      } else if (row.ano >= 2026 && row.ano <= 2030) {
        s_t_bols_sim = customFuturePrim;
      }

      // 2. Define o resultado primário simulado para o caminho do cenário "Lula 3"
      let s_t_lula_sim = basePrim_t;
      if (row.ano >= 2023 && row.ano <= 2025) {
        s_t_lula_sim = fiscalMode === "historical" ? mandateBaselines.bolsAvg : customLulaPrim;
      } else if (row.ano >= 2026 && row.ano <= 2030) {
        s_t_lula_sim = customFuturePrim;
      }

      // 3. Efeitos de Transmissão Macro-Fiscal (Bolsonaro Path)
      const deltaS_bols_dec = (s_t_bols_sim - basePrim_t) / 100;
      const g_t_bols_sim = g_t_real - multiplier * deltaS_bols_dec; // Austeridade reduz PIB
      const i_t_bols_sim = i_t_real - interestSensitivity * deltaS_bols_dec; // Austeridade reduz prêmio de juros
      
      // 4. Efeitos de Transmissão Macro-Fiscal (Lula 3 Path)
      const deltaS_lula_dec = (s_t_lula_sim - basePrim_t) / 100;
      const g_t_lula_sim = g_t_real - multiplier * deltaS_lula_dec;
      const i_t_lula_sim = i_t_real - interestSensitivity * deltaS_lula_dec;

      // Guarda a dívida anterior para o cálculo do estabilizador
      const prevBolsDebt = currentBolsDebt;
      const prevLulaDebt = currentLulaDebt;

      // 5. Cálculo Recursivo da Dívida Simulações: D_t = D_{t-1} * (1 + i) / (1 + g) - S
      currentBolsDebt = currentBolsDebt * (1 + i_t_bols_sim) / (1 + g_t_bols_sim) - s_t_bols_sim;
      currentLulaDebt = currentLulaDebt * (1 + i_t_lula_sim) / (1 + g_t_lula_sim) - s_t_lula_sim;

      // 6. Cálculo do Superávit Primário Estabilizador usando D_{t-1}
      const est_bols = prevBolsDebt * (i_t_bols_sim - g_t_bols_sim) / (1 + g_t_bols_sim);
      const est_lula = prevLulaDebt * (i_t_lula_sim - g_t_lula_sim) / (1 + g_t_lula_sim);

      return {
        ano: row.ano,
        dbgg_realizado: row.dbgg_realizado,
        primario_baseline: basePrim_t,
        g_nominal: g_t_real,
        custo_implicito: i_t_real,
        sim_bols: parseFloat(currentBolsDebt.toFixed(2)),
        sim_lula: parseFloat(currentLulaDebt.toFixed(2)),
        prim_sim_bols: parseFloat(s_t_bols_sim.toFixed(2)),
        prim_sim_lula: parseFloat(s_t_lula_sim.toFixed(2)),
        estabilizador_bols: parseFloat(est_bols.toFixed(2)),
        estabilizador_lula: parseFloat(est_lula.toFixed(2)),
        i_sim_bols: i_t_bols_sim,
        g_sim_bols: g_t_bols_sim,
        i_sim_lula: i_t_lula_sim,
        g_sim_lula: g_t_lula_sim,
      };
    });
  }, [rawData, primaryType, fiscalMode, mandateBaselines, customBolsPrim, customLulaPrim, customFuturePrim, multiplier, interestSensitivity]);

  // Recupera o último ano simulado da projeção (2030)
  const finalProjData = useMemo(() => {
    if (simulatedData.length === 0) return null;
    return simulatedData[simulatedData.length - 1];
  }, [simulatedData]);

  if (error) {
    return (
      <div className="error fade-in">
        <div className="error-card glass-card">
          <h1>Falha na Carga de Dados</h1>
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
          Carregando simulador macro-fiscal da dívida pública brasileira...
        </p>
      </div>
    );
  }

  return (
    <div className="app fade-in">
      {/* Hero Header */}
      <header className="hero">
        <h1>Simulador Macro-Fiscal da DBGG (Projeção 2030)</h1>
        <p>
          Simulador avançado de dinâmica intertemporal da Dívida Bruta do Governo Geral (% PIB).
          Explore a influência do **Multiplicador Fiscal** e da **Sensibilidade dos Juros** sob a política contábil fiscal de Bolsonaro e Lula 3.
        </p>
        <div className="meta">
          Modelagem Comportamental com feedbacks dinâmicos de crescimento e taxas de juros de mercado.
        </div>
      </header>

      {/* Control Grid Dashboard */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginBottom: "2rem" }}>
        
        {/* Left Card: Macroeconomics Config */}
        <div className="chart-card" style={{ margin: 0 }}>
          <header>
            <h2>⚙️ Regras Macroeconômicas</h2>
            <p>Configure os parâmetros de transmissão macroeconômica da simulação.</p>
          </header>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", marginTop: "1rem" }}>
            
            {/* Toggles */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>Tipo de Resultado Primário:</span>
              <div className="subtabs-nav" style={{ margin: 0 }}>
                <button
                  className={primaryType === "realizado" ? "active" : ""}
                  onClick={() => setPrimaryType("realizado")}
                >
                  Realizado (c/ Covid)
                </button>
                <button
                  className={primaryType === "estrutural" ? "active" : ""}
                  onClick={() => setPrimaryType("estrutural")}
                >
                  Estrutural (s/ Covid)
                </button>
              </div>
            </div>

            {/* Multiplier Slider */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                <span>Multiplicador Fiscal (Efeito PIB):</span>
                <span className="text-neon text-bold">{multiplier.toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.5"
                step="0.1"
                value={multiplier}
                onChange={(e) => setMultiplier(parseFloat(e.target.value))}
                style={{ width: "100%", cursor: "pointer", accentColor: "var(--color-accent)" }}
              />
              <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)" }}>
                Mede quanto a atividade econômica desacelera ao cortar gastos (ajustar superávit).
              </span>
            </div>

            {/* Interest Sensitivity Slider */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                <span>Sensibilidade dos Juros (Efeito Prêmio Risco):</span>
                <span className="text-neon text-bold">{interestSensitivity.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={interestSensitivity}
                onChange={(e) => setInterestSensitivity(parseFloat(e.target.value))}
                style={{ width: "100%", cursor: "pointer", accentColor: "var(--color-accent)" }}
              />
              <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)" }}>
                Mede quanto os juros implícitos caem quando a política fiscal é mais austera.
              </span>
            </div>

          </div>
        </div>

        {/* Right Card: Fiscal Simulator Config */}
        <div className="chart-card" style={{ margin: 0 }}>
          <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h2>🎛️ Metas e Cenários Fiscais</h2>
              <p>Configure as metas de resultado primário médio das administrações.</p>
            </div>
            <div className="subtabs-nav" style={{ margin: 0 }}>
              <button
                className={fiscalMode === "historical" ? "active" : ""}
                onClick={() => setFiscalMode("historical")}
              >
                Cruzado
              </button>
              <button
                className={fiscalMode === "custom" ? "active" : ""}
                onClick={() => setFiscalMode("custom")}
              >
                Customizado
              </button>
            </div>
          </header>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1rem" }}>
            
            {/* Sliders */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                <span>Primário Médio Bolsonaro (19-22):</span>
                <span className="text-neon text-bold">{customBolsPrim > 0 ? "+" : ""}{customBolsPrim.toFixed(2)}% do PIB</span>
              </div>
              <input
                type="range"
                min="-6.0"
                max="2.0"
                step="0.1"
                disabled={fiscalMode === "historical"}
                value={customBolsPrim}
                onChange={(e) => setCustomBolsPrim(parseFloat(e.target.value))}
                style={{ width: "100%", cursor: fiscalMode === "historical" ? "not-allowed" : "pointer" }}
              />
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                <span>Primário Médio Lula 3 (23-25):</span>
                <span className="text-neon text-bold">{customLulaPrim > 0 ? "+" : ""}{customLulaPrim.toFixed(2)}% do PIB</span>
              </div>
              <input
                type="range"
                min="-6.0"
                max="2.0"
                step="0.1"
                disabled={fiscalMode === "historical"}
                value={customLulaPrim}
                onChange={(e) => setCustomLulaPrim(parseFloat(e.target.value))}
                style={{ width: "100%", cursor: fiscalMode === "historical" ? "not-allowed" : "pointer" }}
              />
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                <span>Primário Futuro Projetado (26-30):</span>
                <span className="text-neon text-bold">{customFuturePrim > 0 ? "+" : ""}{customFuturePrim.toFixed(2)}% do PIB</span>
              </div>
              <input
                type="range"
                min="-4.0"
                max="3.0"
                step="0.1"
                value={customFuturePrim}
                onChange={(e) => setCustomFuturePrim(parseFloat(e.target.value))}
                style={{ width: "100%", cursor: "pointer", accentColor: "var(--color-primary)" }}
              />
            </div>

          </div>
        </div>
      </div>

      {/* Summary Bento metrics */}
      <div className="summary-cards" style={{ marginBottom: "2rem" }}>
        <div className="summary-card" style={{ borderLeft: `4px solid ${REALIZED_COLOR}` }}>
          <h3>Dívida Projetada Baseline (2030)</h3>
          <p className="value" style={{ background: `linear-gradient(120deg, #fff, ${REALIZED_COLOR})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {finalProjData?.dbgg_realizado.toFixed(2)}%
          </p>
          <p className="subtitle">Se mantido o primário nulo (0,0%) de 2026 a 2030</p>
        </div>

        <div className="summary-card" style={{ borderLeft: `4px solid ${BOLS_SIM_COLOR}` }}>
          <h3>Bolsonaro Simulado (Cenário 2030)</h3>
          <p className="value" style={{ background: `linear-gradient(120deg, #fff, ${BOLS_SIM_COLOR})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {finalProjData?.sim_bols.toFixed(2)}%
          </p>
          <p className="subtitle">
            Diferença: {finalProjData ? (finalProjData.sim_bols - finalProjData.dbgg_realizado).toFixed(2) : "0"} p.p.
          </p>
        </div>

        <div className="summary-card" style={{ borderLeft: `4px solid ${LULA_SIM_COLOR}` }}>
          <h3>Lula 3 Simulado (Cenário 2030)</h3>
          <p className="value" style={{ background: `linear-gradient(120deg, #fff, ${LULA_SIM_COLOR})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {finalProjData?.sim_lula.toFixed(2)}%
          </p>
          <p className="subtitle">
            Diferença: {finalProjData ? (finalProjData.sim_lula - finalProjData.dbgg_realizado).toFixed(2) : "0"} p.p.
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid-2" style={{ marginBottom: "2rem" }}>
        
        {/* Trajectory line chart */}
        <div className="chart-card" style={{ margin: 0 }}>
          <header>
            <h2>Trajetória Projetada da DBGG até 2030</h2>
            <p>Evolução comparada da relação Dívida/PIB com feedbacks de multiplicador e risco.</p>
          </header>
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={simulatedData} margin={{ top: 12, right: 8, left: -20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
              <XAxis dataKey="ano" tick={{ fill: "#9ca3af", fontSize: 11 }} stroke={GRID_COLOR} />
              <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" stroke={GRID_COLOR} domain={["auto", "auto"]} />
              <Tooltip
                contentStyle={{ backgroundColor: "#111827", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }}
                formatter={(v: number, name) => [`${v.toFixed(2)}%`, name]}
              />
              <Legend />
              <Line type="monotone" dataKey="dbgg_realizado" name="Dívida Baseline / Real" stroke={REALIZED_COLOR} strokeWidth={3} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="sim_bols" name="Cenário Bolsonaro" stroke={BOLS_SIM_COLOR} strokeWidth={2.5} strokeDasharray="5 5" dot={{ r: 3 }} />
              <Line type="monotone" dataKey="sim_lula" name="Cenário Lula 3" stroke={LULA_SIM_COLOR} strokeWidth={2.5} strokeDasharray="5 5" dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Primary Stabilization Bar Chart */}
        <div className="chart-card" style={{ margin: 0 }}>
          <header>
            <h2>Resultado Primário vs. Primário Estabilizador (Lula 3)</h2>
            <p>Diferença fiscal entre o primário simulado e a meta necessária para a dívida estabilizar.</p>
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
              <Bar dataKey="prim_sim_lula" name="Resultado Primário Simulado (Lula 3)" fill={LULA_SIM_COLOR} radius={[4, 4, 0, 0]} />
              <Bar dataKey="estabilizador_lula" name="Primário Estabilizador (D_t = D_t-1)" fill={STABILIZING_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

      </div>

      {/* Detailed Math Data Table */}
      <div className="chart-card" style={{ marginBottom: "2rem" }}>
        <header>
          <h2>Matriz de Cálculo da Dinâmica Fiscal Estrutural</h2>
          <p>Valores anuais que compõem o motor macro-fiscal dinâmico com os feedbacks ajustados.</p>
        </header>
        <div className="table-responsive">
          <table className="premium-table">
            <thead>
              <tr>
                <th>Ano</th>
                <th>PIB Nom. Sim. (Lula)</th>
                <th>Juro Implic. Sim. (Lula)</th>
                <th>Primário Baseline</th>
                <th>Primário Sim. Bols</th>
                <th>Primário Sim. Lula</th>
                <th>Dívida Baseline</th>
                <th>Dívida Sim. Bols</th>
                <th>Dívida Sim. Lula</th>
                <th>Estabilizador Lula</th>
              </tr>
            </thead>
            <tbody>
              {simulatedData.map((row) => (
                <tr key={row.ano}>
                  <td className="bold">{row.ano}</td>
                  <td>{row.ano === 2018 ? "—" : `${((row.g_sim_lula ?? 0) * 100).toFixed(2)}%`}</td>
                  <td>{row.ano === 2018 ? "—" : `${((row.i_sim_lula ?? 0) * 100).toFixed(2)}%`}</td>
                  <td className={row.primario_baseline >= 0 ? "text-green" : "text-red"}>
                    {row.primario_baseline > 0 ? "+" : ""}{row.primario_baseline.toFixed(2)}%
                  </td>
                  <td className={row.prim_sim_bols >= 0 ? "text-green" : "text-red"}>
                    {row.prim_sim_bols > 0 ? "+" : ""}{row.prim_sim_bols.toFixed(2)}%
                  </td>
                  <td className={row.prim_sim_lula >= 0 ? "text-green" : "text-red"}>
                    {row.prim_sim_lula > 0 ? "+" : ""}{row.prim_sim_lula.toFixed(2)}%
                  </td>
                  <td className="text-bold">{row.dbgg_realizado.toFixed(2)}%</td>
                  <td className="text-neon text-bold" style={{ color: BOLS_SIM_COLOR }}>{row.sim_bols.toFixed(2)}%</td>
                  <td className="text-neon text-bold" style={{ color: LULA_SIM_COLOR }}>{row.sim_lula.toFixed(2)}%</td>
                  <td className={row.estabilizador_lula >= 0 ? "text-green text-bold" : "text-red text-bold"}>
                    {row.ano === 2018 ? "—" : `${row.estabilizador_lula > 0 ? "+" : ""}${row.estabilizador_lula.toFixed(2)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Advanced Methodological Bento Cards */}
      <div className="comments-bento-grid" style={{ marginBottom: "2rem" }}>
        
        <div className="bento-card card-0 fade-in">
          <div className="bento-card-header">
            <span className="bento-card-title">Resultado Primário Estrutural (Frente 2)</span>
            <div className="bento-card-icon">🛡️</div>
          </div>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-text-main, #f3f4f6)", lineHeight: "1.5" }}>
            A exclusão dos gastos emergenciais da Covid-19 em 2020 (cerca de `6,8%` do PIB) revela que o déficit estrutural básico do governo Bolsonaro (`-1,01%` do PIB) foi quase idêntico ao de Lula 3 (`-1,08%`). Em termos de gastos recorrentes de rotina, as duas gestões operaram em níveis fiscais equivalentes, diferenciando-se majoritariamente pelo tratamento de choques excepcionais.
          </p>
        </div>

        <div className="bento-card card-1 fade-in">
          <div className="bento-card-header">
            <span className="bento-card-title">O Trade-off do Crescimento (Frente 3)</span>
            <div className="bento-card-icon">📉</div>
          </div>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-text-main, #f3f4f6)", lineHeight: "1.5" }}>
            A alteração fiscal tem custos: o **Multiplicador Fiscal** simula que consolidar as contas públicas (reduzir déficits) gera uma contração imediata do PIB nominal no curto prazo. Sob as regras keynesianas calibradas, a busca rápida por superávits reduz o denominador da equação da dívida, limitando a velocidade de queda da relação Dívida/PIB nos primeiros trimestres.
          </p>
        </div>

        <div className="bento-card card-2 fade-in">
          <div className="bento-card-header">
            <span className="bento-card-title">Endogenização do Juro (Frente 1)</span>
            <div className="bento-card-icon">⚡</div>
          </div>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-text-main, #f3f4f6)", lineHeight: "1.5" }}>
            A calibragem da **Sensibilidade de Juros** simula que a responsabilidade fiscal é premiada pelo mercado com a queda nos prêmios de risco soberano. A melhora simulada do resultado primário reduz dinamicamente o custo de rolagem da dívida pública, gerando um efeito redutor virtuoso na dinâmica de acúmulo da dívida que contra-balança o drag do PIB.
          </p>
        </div>

      </div>

      {/* Footer */}
      <footer className="foot">
        <div className="foot-content">
          <span>MBA Economia FIPE — TCC Análise de Trajetórias de Expectativas</span>
          <span>Estatísticas Macroeconômicas de Longo Prazo Avançadas (2018-2030)</span>
        </div>
      </footer>
    </div>
  );
}
