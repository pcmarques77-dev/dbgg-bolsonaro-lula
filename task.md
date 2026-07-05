# Checklist do Simulador de Trajetória da DBGG (task.md)

## Tarefas Concluídas (V1)
- [x] Inicialização do projeto, instalação e configuração do React.
- [x] Construção da base de dados local via Python (`scripts/simular_dbgg.py`).
- [x] Lógica de simulação básica e interface do usuário com Recharts.
- [x] Deploy inicial de produção no Vercel e repositório GitHub criado.

## Backlog do Simulador Avançado (V2)

### 1. Ingestão de Dados Avançados (Python)
- [x] Atualizar `scripts/simular_dbgg.py` para injetar dados estruturais de 2020 (Covid-19) e projetar séries de 2026 a 2030.
- [x] Rodar o script e atualizar o CSV em `public/data/simulacao_dbgg_contra_fatual.csv`.

### 2. Infraestrutura React
- [x] Atualizar as interfaces de tipos no React (`src/types.ts`) e parse de dados (`src/loadData.ts`) com as novas colunas e extensão de anos até 2030.

### 3. Mecanismo de Simulação Avançado (App.tsx)
- [ ] Adicionar estados de controles no React para o Multiplicador Fiscal ($\mu$) e Sensibilidade de Juros ($\gamma$).
- [ ] Criar a alternância entre Primário Real e Primário Estrutural.
- [ ] Implementar a lógica de recálculo recursivo dinâmico de PIB nominal ($g_t$) e Juros implícitos ($i_t$) com base nos desvios fiscais.
- [ ] Calcular dinamicamente o Resultado Primário Estabilizador anual.

### 4. Interface Gráfica e Visualização
- [ ] Adicionar sliders de controle de multiplicadores na tela com design premium dark.
- [ ] Atualizar o gráfico da trajetória da dívida para ir até 2030 e plotar a linha do Primário Estabilizador.
- [ ] Atualizar a tabela de detalhamento anual de cálculos e adicionar os Bento Cards de comentários metodológicos atualizados.
- [ ] Validar a compilação local com `npm run build`.
- [ ] Subir as atualizações para o GitHub e Vercel.
