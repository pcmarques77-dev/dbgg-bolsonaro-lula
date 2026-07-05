import { execSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = root;
const destDir = join(root, "public", "data");

mkdirSync(destDir, { recursive: true });

console.log("=== Sincronizando Dados para o Dashboard React ===");

// 1. Tenta rodar o script python para gerar e exportar todos os dados atualizados
let pythonSuccess = false;
let pythonCmd = "python";

const venvWin = join(repoRoot, ".venv", "Scripts", "python.exe");
const venvUnix = join(repoRoot, ".venv", "bin", "python");

if (existsSync(venvWin)) {
  pythonCmd = venvWin;
} else if (existsSync(venvUnix)) {
  pythonCmd = venvUnix;
}

try {
  console.log(`Rodando ${pythonCmd} scripts/exportar_dados_web.py no diretório ${repoRoot}...`);
  execSync(`"${pythonCmd}" scripts/exportar_dados_web.py`, { cwd: repoRoot, stdio: "inherit" });
  pythonSuccess = true;
  console.log("Dados atualizados via Python com sucesso!");
} catch (e) {
  console.warn("Aviso: Falha ao executar o script Python. Verifique se o ambiente virtual está ativo.");
  console.log("Iniciando cópia de fallback a partir dos arquivos já existentes em " + join(repoRoot, "output") + "...");
}

// 2. Se o Python falhar, copia os arquivos existentes no diretório output do repo principal como fallback
if (!pythonSuccess) {
  const rootOutput = join(repoRoot, "output");
  
  const filesToCopy = [
    // PIB
    { src: join(rootOutput, "PIB", "comparacao_focus_ibge_pib_trimestral.csv"), dest: "comparacao_focus_ibge_pib_trimestral.csv" },
    { src: join(rootOutput, "PIB", "focus_pib_total_com_ibge_realizado.csv"), dest: "focus_pib_total_com_ibge_realizado.csv" },
    { src: join(rootOutput, "comparacao_pib_ano_calendario.csv"), dest: "comparacao_pib_ano_calendario.csv" },
    { src: join(rootOutput, "comparacao_pib_ano_fechamento.csv"), dest: "comparacao_pib_ano_fechamento.csv" },
    // IPCA
    { src: join(rootOutput, "comparacao_ipca_mensal.csv"), dest: "comparacao_ipca_mensal.csv" },
    { src: join(rootOutput, "comparacao_ipca_ano_calendario.csv"), dest: "comparacao_ipca_ano_calendario.csv" },
    { src: join(rootOutput, "comparacao_ipca_ano_fechamento.csv"), dest: "comparacao_ipca_ano_fechamento.csv" },
    // Selic
    { src: join(rootOutput, "comparacao_selic_mensal.csv"), dest: "comparacao_selic_mensal.csv" },
    { src: join(rootOutput, "comparacao_selic_ano_calendario.csv"), dest: "comparacao_selic_ano_calendario.csv" },
    { src: join(rootOutput, "comparacao_selic_ano_fechamento.csv"), dest: "comparacao_selic_ano_fechamento.csv" },
    // Painel Completo e Econometria
    { src: join(rootOutput, "painel_focus_mvp.csv"), dest: "painel_focus_mvp.csv" },
    // IPCA OLS
    { src: join(rootOutput, "econometria_ols_ipca_med12m_coef.csv"), dest: "econometria_ols_ipca_med12m_coef.csv" },
    { src: join(rootOutput, "econometria_ols_ipca_med12m_diagnosticos.txt"), dest: "econometria_ols_ipca_med12m_diagnosticos.txt" },
    { src: join(rootOutput, "econometria_ols_ipca_med12m_summary.txt"), dest: "econometria_ols_ipca_med12m_summary.txt" },
    { src: join(rootOutput, "econometria_ols_ipca_med12m_chow.csv"), dest: "econometria_ols_ipca_med12m_chow.csv" },
    // Selic OLS
    { src: join(rootOutput, "econometria_ols_selic_mediana_pct_coef.csv"), dest: "econometria_ols_selic_mediana_pct_coef.csv" },
    { src: join(rootOutput, "econometria_ols_selic_mediana_pct_diagnosticos.txt"), dest: "econometria_ols_selic_mediana_pct_diagnosticos.txt" },
    { src: join(rootOutput, "econometria_ols_selic_mediana_pct_summary.txt"), dest: "econometria_ols_selic_mediana_pct_summary.txt" },
    { src: join(rootOutput, "econometria_ols_selic_mediana_pct_chow.csv"), dest: "econometria_ols_selic_mediana_pct_chow.csv" },
    // PIB OLS
    { src: join(rootOutput, "econometria_ols_pib_med_pct_coef.csv"), dest: "econometria_ols_pib_med_pct_coef.csv" },
    { src: join(rootOutput, "econometria_ols_pib_med_pct_diagnosticos.txt"), dest: "econometria_ols_pib_med_pct_diagnosticos.txt" },
    { src: join(rootOutput, "econometria_ols_pib_med_pct_summary.txt"), dest: "econometria_ols_pib_med_pct_summary.txt" },
    { src: join(rootOutput, "econometria_ols_pib_med_pct_chow.csv"), dest: "econometria_ols_pib_med_pct_chow.csv" },
    // Taylor Rule OLS
    { src: join(rootOutput, "econometria_ols_taylor_rule_coef.csv"), dest: "econometria_ols_taylor_rule_coef.csv" },
    { src: join(rootOutput, "econometria_ols_taylor_rule_diagnosticos.txt"), dest: "econometria_ols_taylor_rule_diagnosticos.txt" },
    { src: join(rootOutput, "econometria_ols_taylor_rule_summary.txt"), dest: "econometria_ols_taylor_rule_summary.txt" },
    // DBGG
    { src: join(rootOutput, "DIVIDA", "periodos", "2019-2026", "comparacao_focus_dbgg.csv"), dest: "comparacao_focus_dbgg.csv" },
    { src: join(rootOutput, "DIVIDA", "dbgg_sgs13762_mensal.csv"), dest: "dbgg_sgs13762_mensal.csv" },
    { src: join(rootOutput, "DIVIDA", "dbgg_trajetorias.csv"), dest: "dbgg_trajetorias.csv" },
  ];

  let copiedCount = 0;
  for (const item of filesToCopy) {
    if (existsSync(item.src)) {
      copyFileSync(item.src, join(destDir, item.dest));
      console.log(`Copiado (fallback): ${item.dest}`);
      copiedCount++;
    } else {
      console.warn(`Arquivo não encontrado para cópia: ${item.src}`);
    }
  }

  if (copiedCount === 0) {
    console.error("Nenhum arquivo de dados foi copiado! O dashboard pode falhar ao carregar.");
  } else {
    console.log(`Copiados ${copiedCount} arquivos de dados de fallback.`);
  }
}

console.log("=== Sincronização de dados concluída! ===\n");
