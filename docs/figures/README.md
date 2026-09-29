# Catálogo Oficial de Figuras e Resultados Experimentais H-RDL / CA-RDL

Este diretório contém o acervo oficial, auditado e padronizado de figuras de arquitetura, topologias e resultados experimentais de co-simulação ns-3 / 5G-LENA / NORI / O-RAN Near-RT RIC para as **Fases 1 (H-RDL)** e **Fase 2 (CA-RDL)**.

Todas as figuras de resultados são disponibilizadas simultaneamente em três formatos de alta fidelidade:
1. **PNG (300 DPI)**: Pré-visualização rápida, relatórios web e apresentações.
2. **PDF Vetorial**: Publicação acadêmica, compilação LaTeX/Overleaf, papers IEEE/SBC.
3. **SVG**: Renderização vetorial escalável para documentação interativa.

---

## 📁 Estrutura de Diretórios

```
docs/figures/
├── 01_arquitetura_e_governanca/       # Diagramas arquiteturais de governança e pipeline O-RAN
├── 01_arquitetura_e_modelagem/        # Fluxo funcional e diagramas de blocos
├── 02_cenarios_e_topologias/          # Topologias espaciais e cenários canônicos (S0 a S15)
├── 03_resultados_e_benchmarks/        # Espelho unificado dos resultados experimentais
├── fase1_hrdl/                        # Resultados e Gráficos da Fase 1 (H-RDL Determinística)
└── fase2_cardl/                       # Resultados e Gráficos da Fase 2 (CA-RDL Cognitiva / Safe-RL)
```

---

## 📊 1. Fase 1: H-RDL (Heuristic Resource and Decision Layer)

A Fase 1 foca na governança determinística baseada em modelo matemático e árvore de decisão (L0 Heurística Direta, L1 Tabela de Conflitos, L2 Barganha de Nash / TVS / EEVS) e baselines **B0 (Uncoordinated)**, **B1 (FIFO Priority)**, **B2 (Static Slicing)** e **B3 (H-RDL Determinística)**.

### Gráficos Individuais (1 Gráfico por Página — Prontos para Inserção em Artigos)

| Arquivo Base | Métrica Principal | Descrição Científica |
| :--- | :--- | :--- |
| `fig_fase1_01_vazao_sla_baselines` | Vazão & Violação de SLA | Vazão agregada (Mbps) e taxa de violação de SLA (%) com IC 95% para B0..B3. |
| `fig_fase1_02_ecdf_latencia_urllc` | ECDF de Latência URLLC | Função de Distribuição Cumulativa Empírica confrontada com o limiar de 10 ms. |
| `fig_fase1_03_escalabilidade_decomposicao_temporal` | Sobrecarga de Decisão | Decomposição temporal de processamento do pipeline sob carga concorrente. |
| `fig_fase1_04_fechamento_causal_malha_e2` | Fechamento Causal E2 | Dinâmica temporal em malha fechada E2SM-KPM $\to$ H-RDL $\to$ E2SM-RC com injeção de perturbação. |
| `fig_fase1_05_equidade_jain_descarte` | Índice de Jain & Descarte | Equidade de alocação de recursos (Jain's Fairness Index) e taxa de descarte de pacotes por baseline. |
| `fig_fase1_06_eficiencia_energetica_potencia` | Eficiência Energética | Trade-off entre consumo de potência (W) e eficiência energética (Mbits/Joule) em regime de alta carga. |
| `fig_fase1_07_jitter_por_fatia` | Jitter por Fatia de Rede | Dispersão temporal de jitter (ms) estratificada para fatias eMBB, URLLC e mMTC. |
| `fig_fase1_08_action_churn_tempo_estabilizacao` | Churn & Estabilização | Taxa de oscilação de controle (Action Churn) e tempo de convergência/estabilização após anomalia. |

### Dinâmica Temporal de Convergência e Resolução por Cenário (Individuais)

| Arquivo Base | Cenário | Descrição Científica |
| :--- | :--- | :--- |
| `fig_fase1_cenario_s1_colisao_prb_temporal` | S1 (Colisão PRB) | Resolução de sobreposição espectral PRB entre xApp-A (eMBB) e xApp-B (URLLC). |
| `fig_fase1_cenario_s2_potencia_qos_temporal` | S2 (Potência vs QoS) | Arbitragem entre xApp-EE (Energy Efficiency) e xApp-QoS (Downlink Power). |
| `fig_fase1_cenario_s3_tvs_coupling_temporal` | S3 (TVS Coupling) | Governança de acoplamento de estados sob tráfego variável no tempo (Time-Varying State). |
| `fig_fase1_cenario_s4_traffic_steering_temporal` | S4 (Traffic Steering) | Coordenação entre xApp-TS (Traffic Steering) e xApp-MLB (Mobility Load Balancing). |
| `fig_fase1_cenario_s5_ping_pong_temporal` | S5 (Ping-Pong Handover)| Supressão de oscilações de handover veicular em células adjacentes. |
| `fig_fase1_cenario_s8_fechamento_causal_temporal`| S8 (Fechamento Causal) | Resposta temporal do ciclo E2SM-KPM / E2SM-RC sob surto estocástico de carga. |

### Painéis Compostos e Diagramas Arquiteturais

| Arquivo Base | Tipo | Descrição |
| :--- | :--- | :--- |
| `fig_fase1_benchmarks_principais` | Painel 2x2 | Conjunto consolidado de Vazão, ECDF de Latência, Escalabilidade e Fechamento Causal. |
| `fig_fase1_metricas_estendidas_baselines` | Painel 2x2 | Painel consolidado de Jain Fairness, Eficiência Energética, Jitter e Action Churn. |
| `fig_fase1_convergencia_conflitos_cenarios_tempo` | Painel 3x2 | Evolução temporal de conflitos e convergência nos 6 cenários da Fase 1. |
| `fig_fase1_radar_multidimensional_baselines` | Radar Polar | Comparativo holístico de 6 eixos (Vazão, Latência, SLA, Jain, Energia, Churn). |
| `fig_fase1_distribuicoes_multissemente_boxplots` | Boxplots ($N=30$) | Distribuições empíricas multissemente com dispersão estatística e outliers. |
| `fig_fase1_arquitetura_hrdl_deterministica` | Arquitetura | Pipeline determinístico H-RDL L0/L1/L2 com barramento E2 e Near-RT RIC. |
| `hrdl_architecture_preview` | Arquitetura Preview | Diagrama visual da arquitetura de governança H-RDL (Fase 1) em alta resolução. |

---

## 🧠 2. Fase 2: CA-RDL (Cognitive-Aware Contextual Conflict Resolution)

A Fase 2 integra inferência cognitiva, Safe-RL (PPO-Lagrangian com Action Masking), raciocínio sobre Knowledge Graphs e suporte a redes heterogêneas 5G-Adv/6G. Baselines analisados: **B0 (Uncoordinated)**, **B3 (H-RDL)**, **B4 (Non-Linear Utility)**, **B5 (Context-GNN)** e **B6 (CA-RDL / Safe-RL)**.

### Gráficos Individuais de Benchmarks Cognitivos

| Arquivo Base | Métrica Principal | Descrição Científica |
| :--- | :--- | :--- |
| `fig_fase2_01_vazao_eficiencia_cognitiva` | Vazão & SLA Cognitivo | Comparativo de vazão agregada e violação de restrições para B0, B3..B6. |
| `fig_fase2_02_latencia_media_p95_cognitiva` | Latência Média & P95 | Latência de decisão cognitiva e cauda P95 (0,04 a 1,84 ms) sob envelope de 10 ms. |
| `fig_fase2_03_sobrecarga_computacional_ric` | Sobrecarga de CPU/Memória | Custo de inferência do modelo Safe-RL/GNN em nós Near-RT RIC (Kubernetes). |
| `fig_fase2_04_robustez_cenarios_5gadv_6g` | Robustez em Cenários 6G | Taxa de sucesso de mediação em cenários críticos (NTN, UAV, V2X, TSN, ISAC). |

### Treinamento e Governança Safe-RL (PPO-Lagrangian)

| Arquivo Base | Componente Safe-RL | Descrição Científica |
| :--- | :--- | :--- |
| `fig_fase2_05_safe_rl_recompensa_convergencia` | Curva de Recompensa | Convergência de recompensa cumulativa ($R_t$) ao longo de 1.000 episódios de treino. |
| `fig_fase2_06_safe_rl_supressao_custo_restricao` | Custo de Restrição | Supressão de violação de restrições ($C_t \le d_{limit}$) garantida por Lagrangian multiplier. |
| `fig_fase2_07_safe_rl_dinamica_multiplicador_lagrange`| Multiplicador $\lambda$ | Estabilização adaptativa do multiplicador de Lagrange durante as fases de exploração e convergência. |
| `fig_fase2_08_safe_rl_eficacia_action_masking` | Taxa de Ações Inválidas | Eliminação completa de ações proibidas através do mecanismo de Action Masking no espaço de políticas. |

### Dinâmica Temporal em Cenários 5G-Advanced / 6G (Individuais)

| Arquivo Base | Cenário 5G-Adv/6G | Descrição Científica |
| :--- | :--- | :--- |
| `fig_fase2_cenario_s6_concorrencia_5xapps_temporal` | S6 (5 xApps Concorrentes) | Concorrência simultânea de 5 agentes (TS, EE, QoS, MLB, Anomaly). |
| `fig_fase2_cenario_s9_ntn_leo_doppler_temporal` | S9 (NTN LEO Doppler) | Handover preditivo sob deslocamento orbital Doppler em constelação satelital. |
| `fig_fase2_cenario_s10_uav_swarm_beamforming_temporal` | S10 (UAV Swarm Beamforming) | Reconfiguração dinâmica de feixes 3D em enxames de UAVs com restrição de bateria. |
| `fig_fase2_cenario_s11_v2x_platoon_latency_temporal` | S11 (V2X Highway Platoon) | Garantia de latência ultra-baixa ($P99 < 5\text{ ms}$) em comboios veiculares a 120 km/h. |
| `fig_fase2_cenario_s12_iiot_tsn_preemption_temporal` | S12 (IIoT Factory TSN) | Preempção determinística e isolamento de tráfego de missão crítica em automação industrial. |
| `fig_fase2_cenario_s14_isac_6g_partitioning_temporal` | S14 (ISAC 6G Partitioning) | Particionamento dinâmico de recursos entre sensoriamento ambiental e telecomunicações. |

### Painéis Compostos da Fase 2

| Arquivo Base | Tipo | Descrição |
| :--- | :--- | :--- |
| `fig_fase2_benchmarks_cognitivos` | Painel 2x2 | Painel consolidado de Vazão, Latência, Sobrecarga e Robustez 6G. |
| `fig_fase2_convergencia_treinamento_safe_rl` | Painel 2x2 | Painel 2x2 do pipeline Safe-RL (Recompensa, Restrição, $\lambda$ e Action Masking). |
| `fig_fase2_convergencia_conflitos_cenarios_tempo` | Painel 3x2 | Painel consolidado da dinâmica temporal nos 6 cenários avançados 5G-Adv/6G. |
| `fig_fase2_arquitetura_cardl` | Arquitetura | Diagrama da Arquitetura CA-RDL com Motor Cognitivo, Safe-RL e barramento Two-Tier dApp. |

---

## 🎨 Padrão Visual e Tipografia

Todas as figuras foram desenhadas seguindo rigorosamente os padrões visuais de periódicos de alto impacto (IEEE Transactions on Mobile Computing / Wireless Communications e SBC):
- **Paleta de Cores**: Tons harmoniosos e acessíveis baseados no padrão Seaborn/Deep (B0 cinza neutro `#7F8C8D`, B1 azul ardósia `#3498DB`, B2 âmbar `#F39C12`, B3 verde esmeralda `#2ECC71`, B4 púrpura `#9B59B6`, B5 índigo `#34495E`, B6 verde-março `#1ABC9C`).
- **Margens e Legendas**: Posicionamento dinâmico de legendas fora da área de colisão com curvas e dados, margens de respiro expandidas (`constrained_layout=True`) e tipografia legível (`fontsize=10..13` para rótulos e títulos).
- **Sem Sobreposição**: Cada gráfico individual isolado em folha própria (~8.5 x 5.5 polegadas) para máxima clareza em inserções diretas no LaTeX.
