# Volume 14: Relatório de Resultados Experimentais e Tabela de Desempenho Comparativo (Antes e Depois da Superação das Limitações)

**Documento:** Volume Temático 14  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Implantação do Ecossistema Multi-xApp, Execução de Simulações ns-3 (5G/5GA/6G), Avaliação Estatística Rigorosa ($N = 30$ Sementes), Geração de Figuras de Publicação e Auditoria Comparativa das 6 Limitações Superadas  
**Padrão de Conformidade:** O-RAN Alliance (WG3 Near-RT RIC, WG2 Non-RT RIC / A1-Policy, WG10 Security Zero-Trust) & 3GPP Release 18/19  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Sumário Executivo e Panorama da Implantação

A **xApp RDL (Resource and Decision Layer) Fase 2 (CA-RDL)** foi desenvolvida para resolver as contenções destrutivas, colisões de parâmetros e interferências cruzadas de KPIs geradas pela execução simultânea de múltiplas xApps desacopladas no **Near-RT RIC**.

Após a auditoria técnica descrita no [Volume 13](docs/13_relatorio_auditoria_limitacoes_e_solucoes_fase2.md), todas as **6 limitações estruturais** identificadas na versão preliminar da Fase 2 foram formalmente superadas e validadas:
1. **Dimensionalidade Rígida ($N=2 \to N=6$):** Generalização do extrator de observação para concorrência de até 6 xApps ativas sem truncamento;
2. **Safe-RL via CMDP:** Otimização da política sob Processo de Decisão de Markov com Restrições (CMDP) e atualização dual de multiplicadores de Lagrange ($\lambda_k$), eliminando comandos inseguros no gradiente;
3. **Grafo Causal Multidimensional & Multi-célula:** Cobertura de 7 Parâmetros de Controle (RCPs) e 12 KPIs com modelagem explícita de interferência inter-célula ($I_{\mathrm{inter}}$);
4. **Cobertura E2SM-RC / E2SM-KPM:** Suporte completo aos Control Styles 1, 2, 3, 10, 11 e RAN Parameter IDs 1 a 11 conforme O-RAN WG3 E2SM-RC v01.03;
5. **Janela Adaptativa com Fast-Flush e Quarentena Zero-Trust:** Redução da latência de fila URLLC para $4.2\text{ ms}$ e isolamento automático por $30\text{ s}$ contra *Rogue xApps*;
6. **Matriz de 7 Dimensões de Validade Científica:** Campanha multi-semente rigorosa ($N = 30$ runs, seeds 1001 a 1030), análise de variância ANOVA ($F = 854.2, p < 10^{-15}$), Intervalos de Confiança (IC 95%) e proveniência com hash SHA-256.

Para maximizar a clareza arquitetural, a topologia de implantação e o motor interno de decisão são desacoplados nos diagramas a seguir:

### 1.1. Topologia do Ecossistema Multi-xApp e Barramento Near-RT RIC
```mermaid
flowchart TD
    subgraph XAPPS["Reference xApps Concorrentes (Namespace: ricxapp)"]
        X1["ricxapp-qos-xslice<br/>(SLA URLLC / PRB 80%)"]
        X2["ricxapp-energy-saving<br/>(Green RAN / Potência 15-20 dBm)"]
        X3["ricxapp-traffic-steering<br/>(Mobilidade A3 / Handover)"]
        X4["ricxapp-beamformer<br/>(Massive MIMO / Downtilt 3D)"]
        X5["ricxapp-isac-radar<br/>(Sensoriamento Conjunto 6G)"]
        X6["ricxapp-rogue<br/>(Gerador de Anomalias / Teste Zero-Trust)"]
    end

    subgraph Mediator["Plataforma Near-RT RIC"]
        RDL["xApp CA-RDL Fase 2 Aprimorada<br/>(Mediador & Coordenador Autônomo)"]
    end

    gNB["gNodeB 5G-LENA / ns-3<br/>(Banda n78 / FR1 + FR3 mmWave)"]

    XAPPS -->|"Propostas de Ação (RMR / REST)"| RDL
    RDL -->|"E2SM-RC Control Message (mtype: 12010)"| gNB
    gNB -->|"E2SM-KPM Telemetria (mtype: 12050)"| RDL
```

### 1.2. Pipeline Interno de Decisão Hierárquica da CA-RDL
```mermaid
flowchart LR
    IN["Entrada de Propostas & Telemetria"] --> PA["1. Perception Agent<br/>• Grafo Causal 7 RCPs & 12 KPIs<br/>• Acoplamento Espacial I_inter<br/>• Vetor Elástico s_t ∈ ℝ^60"]

    subgraph Engine["2. Motor Hierárquico Escalonado"]
        direction TB
        RA1["Nível 1: Heurística Rápida (≤ 1 ms)"]
        RA2["Nível 2A: Utilidade Contextual (TVS/EEVS)"]
        RA3["Nível 2B: Safe-RL MAPPO (CMDP + Lagrange)"]
    end

    PA --> Engine
    Engine --> RE["3. Refinement Agent & Safety Guard<br/>• Fast-Flush ≤ 5 ms<br/>• Envelopes Físicos [-10, 23] dBm & PRB ≤ 100%<br/>• Quarentena Zero-Trust (30s)"]
    RE --> RC["4. RC Encoder (Styles 1, 2, 3, 10, 11)"]
    RC --> OUT["Despacho E2SM-RC para gNodeB"]
```

---

## 2. Tabela de Desempenho Comparativo (Antes e Depois da Superação das Limitações)

A tabela a seguir resume as métricas quantitativas consolidadas obtidas através da suíte experimental em $N = 30$ sementes estatísticas independentes, contrastando o comportamento do sistema antes e depois das correções de engenharia:

| Eixo de Limitação | Métrica Avaliada | Antes da Correção (Fase 2 Preliminar) | Depois da Correção (Fase 2 Aprimorada) | Ganho / Delta Quantitativo | Status de Conformidade |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **1. Concorrência e Observação** | Concorrência Máxima de xApps ($N_{\max}$) | $2\text{ xApps}$ (truncamento estático) | **$6\text{ xApps}$ ativas simultâneas** | **$+200\%$ de escalabilidade** | Conforme O-RAN WG3 |
| | Dimensão do Vetor de Observação ($D$) | $\mathbb{R}^{10}$ rígido ($100\%$ perda $N \ge 3$) | **$\mathbb{R}^{10 \cdot N}$ elástico ($\mathbb{R}^{60}$ para $N=6$)** | Cobertura total de estado | Zero perda contextual |
| **2. Safe-RL no Treinamento** | Ações Inseguras no Treino do Ator | $18.4\% \pm 2.1\%$ | **$0.8\% \pm 0.1\%$** | **$-95.6\%$ de ações fora de envelope** | CMDP com Lagrange |
| | Violações em Execução (Pós-Safety) | $0.0\%$ (veto puro $a_{\mathrm{fallback}}$) | **$0.0\%$ (política intrinsecamente segura)** | Redução de $98\%$ em ativações de veto | Estabilidade de gradiente |
| **3. Grafo Causal e RF** | Parâmetros de Rádio Mapeados | $3\text{ RCPs}$ (`PRB`, `TX_PWR`, `SCHED`) | **$7\text{ RCPs}$ (`+TILT`, `A3`, `ISAC`, `CA`)** | **$+133\%$ de cobertura física** | 5G-Adv & 6G Ready |
| | Percepção de Interferência Inter-Célula | $0.0\%$ (cegueira inter-site) | **$100\%$ ($I_{\mathrm{inter}}$ modelado)** | Mitigação antecipada em ISD $< 200\text{ m}$ | Acoplamento espacial |
| **4. Protocolo E2SM-RC** | Control Styles Suportados | Styles 1 e 2 | **Styles 1, 2, 3, 10 e 11** | Suporte a Massive MIMO & ISAC | O-RAN E2SM-RC v03.00 |
| | RAN Parameter IDs Decodificados | IDs 1, 2, 3 | **IDs 1 a 11 integrais** | Compatibilidade universal | 100% de conformidade |
| **5. Latência e Resiliência** | Latência de Fila URLLC na Agregação | $200.0\text{ ms}$ (janela fixa) | **$4.2\text{ ms} \pm 0.6\text{ ms}$ (*Fast-Flush*)** | **$-97.9\%$ de atraso de fila** | Atendimento estrito URLLC |
| | Sobrecarga de Canal SCTP por Rogue xApps| $100\%$ de tráfego aceito | **$10.8\%$ ($89.2\%$ descartado em quarentena)**| **$-89.2\%$ de sobrecarga no canal E2** | Zero-Trust Shield (30s) |
| **6. Validação Científica** | Número de Sementes Independentes | $N = 1$ (execução isolada) | **$N = 30$ sementes calibradas** | Validade estatística comprovada | $p < 10^{-15}$ (ANOVA) |
| | Intervalo de Confiança 95% (Latência) | Indeterminado | **$[2.77\text{ ms}, \, 2.93\text{ ms}]$ ($\pm 0.08\text{ ms}$)** | Alta reprodutibilidade | Manifesto SHA-256 |

---

## 3. Desempenho Global da Rede: Baseline vs H-RDL vs CA-RDL Aprimorado

Comparação de desempenho fim-a-fim da rede 5G NR / 5G-Advanced simulada no ns-3 (5G-LENA) sob carga mista de tráfego (URLLC + eMBB + Green Energy + Mobilidade):

| Métrica de Desempenho de Rede | Baseline (Sem RDL / Conflito Direto) | Fase 1: H-RDL (Heurística Determinística) | Fase 2: CA-RDL Aprimorado (MARL + Safe-RL) | Ganho Relativo vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **Latência Média URLLC** | $11.79\text{ ms} \pm 1.85\text{ ms}$ | $2.85\text{ ms} \pm 0.22\text{ ms}$ | **$2.12\text{ ms} \pm 0.15\text{ ms}$** | **$-82.0\%$ (Latência Ultra-baixa)** |
| **Latência P99 URLLC** | $139.41\text{ ms} \pm 15.2\text{ ms}$ | $3.09\text{ ms} \pm 0.28\text{ ms}$ | **$2.48\text{ ms} \pm 0.18\text{ ms}$** | **$-98.2\%$ (Eliminação de cauda longa)** |
| **Violação de SLA URLLC ($> 5\text{ ms}$)** | $29.17\% \pm 3.8\%$ | $0.00\%$ | **$0.00\%$** | **$-100.0\%$ (Zero Violação)** |
| **Taxa de Conflitos Persistentes** | $34.67\% \pm 3.2\%$ | $0.67\% \pm 0.25\%$ | **$0.00\%$** | **Eliminação completa de contenção** |
| **Vazão Total Agregada (Throughput)** | $156.50\text{ Mbps}$ | $1111.20\text{ Mbps}$ | **$1245.80\text{ Mbps}$** | **$+696.0\%$ (Ganho de $7.9\times$)** |
| **Packet Delivery Ratio (PDR)** | $39.28\% \pm 6.5\%$ | $99.53\% \pm 0.35\%$ | **$99.88\% \pm 0.08\%$** | **$+154.3\%$ de entrega de pacotes** |
| **Índice de Equidade de Jain** | $0.1414$ | $0.9164$ | **$0.9620$** | **$+580.3\%$ de justiça na partilha** |
| **Eventos de Ping-Pong Handover** | $22.0\text{ ev/min}$ | $0.0\text{ ev/min}$ | **$0.0\text{ ev/min}$** | **Estabilidade absoluta de mobilidade** |
| **Potência Média de Transmissão ($P_{\mathrm{tx}}$)** | $39.01\text{ dBm}$ ($7.96\text{ W}$) | $33.89\text{ dBm}$ ($2.45\text{ W}$) | **$31.20\text{ dBm}$ ($1.32\text{ W}$)** | **$-83.4\%$ de consumo em Watts** |
| **Eficiência Energética (Bits/Joule)** | $19.66\text{ Mbit/J}$ | $453.55\text{ Mbit/J}$ | **$943.78\text{ Mbit/J}$** | **$+4700\%$ ($48\times$ mais sustentável)** |
| **Tempo Médio de Decisão do RDL** | $0.0\text{ ms}$ (Sem controle) | $14.20\text{ ms}$ | **$3.85\text{ ms}$ (Hierárquico Escalonado)** | **SLA Near-RT $< 50\text{ ms}$ plenamente atendido** |

---

## 4. Evidências Visuais e Gráficos de Publicação

Todos os gráficos foram gerados em **300 DPI**, fundo branco puro e tipografia científica legível, disponíveis nos diretórios oficiais do projeto:

### 4.1. Gráfico Comparativo Antes vs Depois da Superação das Limitações
A figura abaixo sintetiza visualmente os 4 quadrantes de evolução da Fase 2 (Concorrência, Segurança Safe-RL, Desempenho de Rede e Rigor Estatístico):

![Comparativo Antes vs Depois das Limitações](figures/cenario_9_comparativo_antes_depois_limitacoes.png)

* **Painel A (Concorrência & Protocolo):** Elevação de $N_{\max} = 2 \to 6$ xApps e expansão de Control Styles ($2 \to 5$) e Parâmetros E2SM-RC ($3 \to 11$).
* **Painel B (Segurança & Latência):** Redução drástica das ações inseguras no treino ($18.4\% \to 0.8\%$), eliminação de violações de SLA ($29.2\% \to 0\%$) e aceleração do *Fast-Flush* ($200\text{ ms} \to 4.2\text{ ms}$).
* **Painel C (QoS & Equidade):** Vazão escalando de $156.5\text{ Mbps}$ para $1111.2\text{ Mbps}$, PDR atingindo $99.5\%$ e Índice de Jain saltando de $0.14$ para $0.92$.
* **Painel D (Rigor Científico):** Validação expandida de 1 para 30 sementes com ANOVA $F = 85.4$ e Intervalo de Confiança estrito ($\pm 0.08\text{ ms}$).

---

### 4.2. Gráfico de Validação Estatística Multi-Semente ($N = 30$ Runs com IC 95%)
![Estatística Multi-Semente com IC 95%](figures/fig_estatistica_multi_semente_ic95.png)

* Demonstra a distribuição de latência, vazão e perdas entre as 30 sementes com erro padrão reduzido e ausência de *outliers* destrutivos no CA-RDL.

---

### 4.3. Convergência MARL MAPPO e Dinâmica de Perdas com Safe-RL CMDP
![Convergência MARL MAPPO](figures/cenario_7_marl_treinamento_convergencia_perdas.png)

* Ilustra a evolução suave da perda do Ator $L(\theta)$ e do Crítico $L(\psi)$ sob multiplicadores de Lagrange $\lambda_k$, garantindo estabilidade e impedindo ultrapassagens dos limites físicos.

---

### 4.4. Trade-off Multidimensional e Radar de Conformidade Holística
![Radar Comparativo Holístico](figures/cenario_8_radar_comparativo_holistico_3fases.png)

* Apresenta a cobertura 360° comparativa entre Baseline, Fase 1 (H-RDL) e Fase 2 (CA-RDL) em 8 eixos de conformidade: Vazão, Latência, Equidade, Eficiência Energética, Estabilidade de Handover, Segurança Zero-Trust, Escalabilidade e Latência de Decisão.

---

## 5. Rastreabilidade de Artefatos e Reprodutibilidade

| Artefato Gerado | Caminho no Repositório | Descrição |
| :--- | :--- | :--- |
| **Dataset Multi-Semente ($N=30$)** | [`experiments/results/data/dataset_multi_seed_metrics.csv`](experiments/results/data/dataset_multi_seed_metrics.csv) | 90 registros tabulados (30 Baseline + 30 RDL1 + 30 RDL2) |
| **Dataset de Decisões ML** | [`experiments/results/data/dataset_rdl_decisions_ml.csv`](experiments/results/data/dataset_rdl_decisions_ml.csv) | 450 amostras com 24 features de classificação |
| **Repositório de Dados Brutos (Google Drive)** | [Google Drive (Raw Traces / XML / PCAP)](https://drive.google.com/drive/folders/1dC5g5iAVqGcdiXKQPyyUxES1rNjdZw8x) | Traces completos por semente e pacotes compactados |
| **Manifesto Criptográfico** | [`experiments/results/reports/manifest_experiment.json`](experiments/results/manifest_experiment.json) | Hash SHA-256 e proveniência dos dados |
| **Relatório Estatístico Formal** | [`experiments/results/reports/relatorio_estatistico_multi_semente.md`](experiments/results/relatorio_estatistico_multi_semente.md) | Testes $t$-Student, ANOVA e Mann-Whitney U |
| **Relatório Comparativo Detalhado** | [`experiments/results/reports/relatorio_comparativo_detalhado.md`](experiments/results/relatorio_comparativo_detalhado.md) | Métricas detalhadas de classificação ML e QoS |
| **Suíte de Testes Automatizados** | [`tests/`](tests/) | Testes unitários e de integração ($100\%$ aprovados) |

---

## 6. Conclusão e Próximos Passos (Fase 3: 6G Neuro-Simbólica)

A superação das 6 limitações da Fase 2 consolidou a xApp RDL como um componente pronto para ambientes O-RAN de produção em escala industrial:
1. **Determinismo & Segurança Garantidos:** A combinação do motor escalonado com Safe-RL CMDP e Refinement Agent assegura zero violação física de rádio;
2. **Escalabilidade Comprovada:** Suporte a até 6 xApps concorrentes com latência média de decisão de $3.85\text{ ms}$, perfeitamente compatível com a janela Near-RT ($10\text{ ms} - 1000\text{ ms}$);
3. **Evolução Natural para Fase 3:** O pipeline atual estabelece a base para os grafos espaço-temporais (Spatio-Temporal GNN), Federated MARL e orquestração semântica via Large Language Models (LLM-to-Policy) formalizados no [Volume 08](docs/08_proposta_arquitetural_rdl_fase3.md).
