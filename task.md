# Checklist do Simulador de Trajetória da DBGG (task.md)

## Tarefas Pendentes (Backlog)

### 1. Configuração e Dependências
- [x] Executar `npm install` no novo diretório para criar `node_modules`.
- [ ] Ativar/configurar o ambiente virtual Python se necessário para futuras atualizações de dados.

### 2. Infraestrutura do React
- [x] Criar o carregador de dados `loadSimulationData` em `src/loadData.ts` para ler `public/data/simulacao_dbgg_contra_fatual.csv`.
- [x] Definir a interface TypeScript para os dados da simulação em `src/types.ts`.

### 3. Interface do Usuário (App.tsx)
- [x] Limpar a estrutura de abas macro (PIB, IPCA, Selic) e centralizar a visualização no simulador.
- [x] Criar o painel lateral ou cabeçalho de controles (Sliders e Toggles).
- [x] Implementar a lógica de cálculo em tempo real no React (permitir que juros e PIB nominal fiquem constantes e recalcular a trajetória conforme os sliders de resultado primário são arrastados).
- [x] Desenhar os Bento Cards Analíticos de resumo dinâmicos (Dívida Realizada, Cenários Contra-fatuais, Diferença em p.p.).
- [x] Adicionar os gráficos Recharts específicos:
  - Trajetória histórica vs simulada da DBGG (gráfico de linha).
  - Resultado primário real vs simulado (gráfico de barras).

### 4. Validação e Deploy
- [x] Testar a consistência da simulação em tempo real (sliders em 0 ou valores originais devem reproduzir o realizado histórico exatamente).
- [x] Executar o build local (`npm run build`).
- [ ] Deploy da nova aplicação no Vercel (`vercel`).
- [ ] Subir para um novo repositório GitHub.
