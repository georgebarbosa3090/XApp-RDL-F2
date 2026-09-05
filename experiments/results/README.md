# Diretório de Resultados Experimentais e Benchmarks (xApp-RDL)

Este diretório centraliza todos os dados empíricos, conjuntos de dados (*datasets*), relatórios de avaliação estatística, gráficos de desempenho em alta resolução (300 DPI) e diagramas arquiteturais gerados durante as simulações e validações da arquitetura **xApp-RDL** (**Fase 1: H-RDL** e **Fase 2: CA-RDL / Safe-MARL**).

---

## 1. Estrutura e Taxonomia do Diretório

```
experiments/results/
├── README.md                      # Documentação técnica unificada dos resultados e datasets
├── data/                          # Datasets consolidados em formato CSV
│   ├── dataset_flow_metrics.csv       # Métricas de fluxos URLLC, eMBB e mMTC por slot temporal
│   ├── dataset_multi_seed_metrics.csv # Consolidação das 30 sementes com intervalos de confiança (IC 95%)
│   └── dataset_rdl_decisions_ml.csv   # Histórico de decisões, atributos de rádio e predições ML
├── reports/                       # Relatórios técnicos em Markdown e JSON estruturado
│   ├── relatorio_comparativo.md              # Resumo executivo da governança O-RAN
│   ├── relatorio_comparativo_detalhado.md    # Análise multidimensional aprofundada de QoS e energia
│   ├── relatorio_estatistico_multi_semente.md# Validação de hipóteses estatísticas (p < 0.001, ANOVA)
│   ├── relatorio_comparativo.json            # Métricas agregadas exportadas em JSON
│   ├── avaliacao_completa_metricas.json      # Avaliação completa de modelos de ML e cenários
│   └── manifest_experiment.json              # Manifesto imutável com checksums SHA-256
├── plots/                         # Gráficos e curvas de desempenho (300 DPI)
│   ├── cenario_1_topologia_tvs_conflict.png
│   ├── cenario_2_tradeoff_energy_vs_qos.png
│   ├── cenario_3_arquitetura_cosimulacao_ns3_oran.png
│   ├── cenario_4_comparativo_multidimensional_metricas.png
│   ├── cenario_5_vazao_throughput_e_jain_fairness.png
│   ├── cenario_6_latencia_decisao_e_estabilidade_handover.png
│   ├── cenario_7_marl_treinamento_convergencia_perdas.png
│   ├── cenario_8_radar_comparativo_holistico_3fases.png
│   ├── avaliacao_modelos_ml_rdl.png
│   ├── comparativo_completo_cenarios_rdl.png
│   ├── graficos_benchmarks_rdl.png
│   ├── fig_estatistica_multi_semente_ic95.png
│   ├── fig_latencia_confiabilidade_single_seed.png
│   ├── fig_vazao_alocacao_equidade_single_seed.png
│   └── fig_dinamica_temporal_safety_guards_single_seed.png
├── diagrams/                      # Diagramas arquiteturais e de conformidade O-RAN
│   ├── diagram_01_global_pipeline_architecture.png
│   ├── diagram_02_arquitetura_cognitiva_mappo.png
│   ├── diagram_03_infraestrutura_k3d_rancher.png
│   ├── diagram_04_observabilidade_prometheus_kiali.png
│   ├── diagram_05_conformidade_oran_standards.png
│   ├── diagram_06_proposta_arquitetural_fase3_6g.png
│   └── diagram_07_roadmap_gantt_fase3.png
├── runs/                          # Histórico de execuções organizadas por data
│   ├── 2026-08-27/
│   ├── 2026-08-31/
│   └── 2026-09-01/
├── raw/                           # Traces brutos de co-simulação ns-3 e logs RDL
│   ├── baseline/                      # FlowMonitor XML e logs do Baseline
│   ├── rdl_phase1/                    # FlowMonitor XML e logs da Fase 1 (H-RDL)
│   └── rdl_phase2/                    # FlowMonitor XML e logs da Fase 2 (CA-RDL)
└── latest/                        # Espelhamento canônico da execução mais recente
    ├── data/
    ├── reports/
    ├── plots/
    └── raw/
```

---

## 2. Dicionário de Dados e Esquemas dos Datasets (`data/`)

### 2.1. `dataset_flow_metrics.csv`
Armazena a série temporal com as métricas de nível de fluxo extraídas pelo `FlowMonitor` do ns-3:
* `time_sec` (float): Instante temporal da amostragem em segundos ($0.0 \le t \le 30.0$);
* `scenario` (string): Cenário arquitetural (`baseline`, `rdl_phase1`, `rdl_phase2`);
* `slice_type` (string): Categoria de serviço da fatia (`URLLC`, `eMBB`, `mMTC`);
* `flow_id` (int): Identificador do fluxo de pacotes IP;
* `mean_delay_ms` (float): Latência média calculada fim-a-fim no enlace de dados (ms);
* `jitter_ms` (float): Variação estatística do atraso de pacotes (ms);
* `throughput_mbps` (float): Vazão instantânea do fluxo (Mbps);
* `packet_loss_rate_pct` (float): Taxa percentual de descarte de pacotes (PLR \%);
* `sla_violated` (int): Indicador binário ($1 =$ violação de SLA de latência/vazão, $0 =$ em conformidade).

### 2.2. `dataset_multi_seed_metrics.csv`
Consolida as execuções Monte Carlo sob $N = 30$ sementes pseudoaleatórias independentes (Seeds 1001 a 1030):
* `seed` (int): Valor numérico da semente do gerador RNG;
* `scenario` (string): Identificador do cenário (`baseline`, `rdl_phase1`, `rdl_phase2`);
* `urllc_latency_mean_ms` (float): Latência média do tráfego URLLC na rodada;
* `urllc_sla_violations_pct` (float): Porcentagem de violações de SLA registradas;
* `packet_delivery_ratio_pdr_pct` (float): Taxa de entrega de pacotes alcançada;
* `aggregate_throughput_mbps` (float): Capacidade agregada de transmissão da célula (Mbps);
* `energy_efficiency_index` (float): Razão normalizada de eficiência energética (Bits/Joule);
* `mean_tx_power_dbm` (float): Potência média emitida pelo transmissor da gNodeB (dBm);
* `conflict_rate_pct` (float): Taxa de conflitos detectados entre xApps concorrentes;
* `rdl_decision_latency_ms` (float): Latência total de inferência e mediação no Near-RT RIC (ms);
* `handover_ping_pong_ev_min` (float): Frequência de eventos de oscilação de handover (eventos/minuto);
* `jains_fairness_index` (float): Índice de equidade de Jain para partição de recursos físicos.

### 2.3. `dataset_rdl_decisions_ml.csv`
Registra as variáveis de estado, atributos de tráfego e ações executadas pelo motor de decisão:
* `sample_id` (int): Índice único da solicitação de controle;
* `scenario` (string): Identificador de modo de operação;
* `slice_type` (string): Fatia de rede demandante;
* `ue_count` (int): Número de terminais de usuário conectados na célula;
* `traffic_load_mbps` (float): Volume instantâneo de tráfego de entrada (Mbps);
* `prb_demanded` (int): Quantidade de blocos de recursos solicitados pela xApp;
* `sinr_db` (float): Relação sinal-ruído-e-interferência média observada no enlace descendente;
* `rsrp_dbm` (float): Potência de sinal de referência recebida pelos terminais;
* `tx_power_dbm` (float): Potência de transmissão configurada na gNodeB;
* `queue_delay_ms` (float): Atraso acumulado nas filas MAC/RLC;
* `conflict_flag` (int): Indicador se houve contenção de parâmetros ($1 =$ sim, $0 =$ não);
* `action_taken` (string): Ação de arbitragem executada (`PASS`, `SCALE_DOWN`, `REJECT`, `MAPPO_RESOLVE`);
* `execution_time_ms` (float): Tempo de processamento do agente de raciocínio.

---

## 3. Resumo Consolidado dos Resultados Experimentais

A tabela abaixo resume os resultados científicos obtidos sob $N = 30$ sementes estocásticas independentes com Intervalos de Confiança de 95\% (IC 95\%):

| Métrica de Avaliação | Baseline (Sem RDL) | Fase 1: H-RDL | Fase 2: CA-RDL (Safe-MARL) | Impacto / Ganho (Fase 2) |
| :--- | :---: | :---: | :---: | :---: |
| **Latência Média URLLC** | $11,83 \pm 0,42\text{ ms}$ | $2,74 \pm 0,11\text{ ms}$ | **$1,92 \pm 0,05\text{ ms}$** | Redução de **83,8\%** ($p < 0,001$) |
| **Violação de SLA URLLC ($<5\text{ ms}$)** | $100,0\%$ | $0,0\%$ | **$0,0\%$** | **Zero violações** em 30 UEs |
| **Taxa de Entrega (PDR)** | $88,18 \pm 1,25\%$ | $99,59 \pm 0,08\%$ | **$99,81 \pm 0,03\%$** | Ganho de **+11,63 p.p.** |
| **Vazão Total Agregada** | $874,1 \pm 32,5\text{ Mbps}$ | $1129,5 \pm 18,2\text{ Mbps}$ | **$1469,5 \pm 12,4\text{ Mbps}$** | Aumento de **+68,1\%** |
| **Eficiência Energética** | $1,000\times$ | $1,145\times$ | **$1,182\times$** | Ganho de **+18,2\%** |
| **Potência Média ($P_{\text{tx}}$)** | $39,45\text{ dBm}$ | $33,80\text{ dBm}$ | **$31,04\text{ dBm}$** | Supressão de **8,41 dBm** |
| **Conflitos Não Mitigados** | $31,33\%$ | $0,67\%$ | **$0,00\%$** | **Eliminação total** de contenções |
| **Latência Near-RT RIC** | $0,0\text{ ms}$ | $14,2\text{ ms}$ | **$12,5 \pm 0,3\text{ ms}$** | Conforme norma ($<50\text{ ms}$) |
| **Handover Ping-Pong** | $22,0\text{ ev/min}$ | $0,0\text{ ev/min}$ | **$0,0\text{ ev/min}$** | **Estabilidade absoluta** |
| **Isolamento de Rogue xApp** | N/A | N/A | **$< 10\text{ s}$** | **100\% de contenção** |
| **Índice de Jain ($J$)** | $0,8933$ | $0,9422$ | **$0,9037$** | Partição equilibrada de PRBs |

---

## 4. Manifesto de Proveniência e Checksums SHA-256

Para assegurar auditabilidade, integridade e reprodutibilidade científica irrefutável dos experimentos, os arquivos de dados contidos em `data/` possuem os seguintes hashes criptográficos SHA-256:

| Arquivo | Caminho Relativo | Hash SHA-256 |
| :--- | :--- | :--- |
| `dataset_flow_metrics.csv` | `data/dataset_flow_metrics.csv` | `63e8295211208710004f21134ed910ad6edaf67a103e313d17c7b7f3e38ff31a` |
| `dataset_multi_seed_metrics.csv` | `data/dataset_multi_seed_metrics.csv` | `f0378f6cc0b0347b368c305aef6305055e22776f3d5788c5449f9d18d75b7f15` |
| `dataset_rdl_decisions_ml.csv` | `data/dataset_rdl_decisions_ml.csv` | `758f991a56a82fa84e517de879976007ac1fc558d782d8a365c6dde4115028a6` |

---

## 5. Como Regenerar e Avaliar os Resultados

Para reprocessar os datasets, treinar os modelos de Machine Learning (Ensemble RF+ET+GB+HGB) e gerar todos os gráficos e relatórios atualizados:

```bash
# 1. Executar pipeline de avaliação e treinamento de ML
python scripts/evaluate_and_improve_algorithms.py --input-dir experiments/results/data --output-dir experiments/results

# 2. Executar suíte de testes unitários automatizados
pytest tests/ -v
```
