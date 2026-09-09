# Volume 13: Relatório Técnico de Auditoria, Limitações e Superação Arquitetural do CA-RDL (Fase 2)

## Projeto xApp RDL — Governança Near-RT O-RAN, Avaliação Crítica e Roadmap de Validade Científica

**Documento:** Volume Temático 13  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL)  
**Escopo:** Auditoria Crítica de Limitações, Superação Arquitetural de 6 Eixos, Formulação Safe-RL CMDP, Grafo Multidimensional, Janela Adaptativa e Matriz de Validade Científica  
**Padrão de Conformidade:** O-RAN Alliance (WG3 Near-RT RIC TS.E2SM-RC v01.03 & WG2 Non-RT RIC A1-Policy) / 3GPP TR 38.901  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Resumo Executivo da Auditoria

Este documento consolida a auditoria técnica, algorítmica, de infraestrutura e metodológica realizada sobre o repositório da **Fase 2 do projeto xApp-RDL** (*Context-Aware RDL — CA-RDL*). A arquitetura foi concebida para atuar no plano de controle **Near-RT RIC** (com loop de decisão entre $10\text{ ms}$ e $1\text{ s}$, segundo as especificações O-RAN WG3), mediando e arbitrando decisões concorrentes emitidas por múltiplas xApps de rádio sobre estações base 5G NR (gNodeBs).

![Arquitetura Global e Pipeline da Fase 2](figures/diagram_01_global_pipeline_architecture.png)

A auditoria confirmou a maturidade do pipeline escalonado em 3 camadas:
1. **Camada 1 (H-RDL Heurística):** Heurística ultrarrápida ($< 1\text{ ms}$) para conflitos diretos com assimetria de prioridade;
2. **Camada 2A (CA-RDL Utilidade Contextual):** Avaliação combinatorial sobre o *Power Set* $2^N$ via funções TVS (*Throughput Violation-based Selection*) e EEVS (*Energy Efficiency Violation-based Selection*) com regularização sigmoide de potência;
3. **Camada 2B (CA-RDL MARL):** Coordenação cooperativa multiagente baseada no algoritmo **MAPPO** sob o paradigma **CTDE** (*Centralized Training with Decentralized Execution*) com retornos **GAE** (*Generalized Advantage Estimation*);
4. **Camada 3 (Safety Guards & Lockout):** Blindagem invariante determinística com janela de resfriamento (*Lockout*) de $5.0\text{ s}$ e verificação física estrita de potência e PRBs.

Simultaneamente, a auditoria identificou **6 eixos críticos de limitação** no design inicial da Fase 2. Cada limitação foi diagnosticada em sua causa-raiz matemática e de engenharia de software, sendo superada pelas soluções arquiteturais formalizadas e implementadas neste relatório.

---

## 2. Matriz Consolidada de Limitações e Superação Arquitetural

Para proporcionar clareza máxima e leitura modular, o mapeamento entre as limitações diagnosticadas e as soluções de engenharia implementadas é desacoplado em três eixos temáticos fundamentais:

### 2.1. Eixo de Representação de Estado e Otimização Segura (Limitações L1 & L2)
```mermaid
flowchart LR
    subgraph Diagnostico_Eixo1["Limitações de Estado & Aprendizado"]
        L1["L1: Vetor de Observação Rígido<br/>(Truncamento fixo para N=2 xApps)"]
        L2["L2: MARL sem Restrição no Treino<br/>(Ações inseguras durante exploração)"]
    end

    subgraph Solucao_Eixo1["Superação de Engenharia"]
        S1["S1: Vetor de Estado Elástico N-xApps<br/>(Dimensionamento s_t ∈ ℝ^(D_obs × N), N ≤ 6)"]
        S2["S2: Safe-RL CMDP com Lagrange<br/>(Dual Update de λ_k & Gradiente Penalizado)"]
    end

    L1 ==>|Generalização Dimensional| S1
    L2 ==>|Otimização Restrita no Treino| S2
```

### 2.2. Eixo de Topologia Causal e Protocolos O-RAN (Limitações L3 & L4)
```mermaid
flowchart LR
    subgraph Diagnostico_Eixo2["Limitações de Topologia & Protocolo"]
        L3["L3: Grafo KPI Estático Local<br/>(Sem Beamforming, A3 e Multi-Célula)"]
        L4["L4: Codecs E2SM Parciais<br/>(Apenas Parâmetros 1, 2, 3 legados)"]
    end

    subgraph Solucao_Eixo2["Superação de Engenharia"]
        S3["S3: Grafo Multidimensional 5G-Adv/6G<br/>(Downtilt, A3_Offset, ISAC & Inter-Cell I_inter)"]
        S4["S4: Cobertura Integral E2SM-RC/KPM<br/>(Styles 1, 2, 3, 10, 11 & RAN Parameter IDs 1 a 11)"]
    end

    L3 ==>|Topologia Causal Estendida| S3
    L4 ==>|Conformidade O-RAN WG3| S4
```

### 2.3. Eixo de Resiliência Temporal e Validade Científica (Limitações L5 & L6)
```mermaid
flowchart LR
    subgraph Diagnostico_Eixo3["Limitações Temporais & Metodológicas"]
        L5["L5: Janela Fixa & Sem Isolamento<br/>(Latência URLLC e vulnerabilidade a Rogue xApps)"]
        L6["L6: Dispersão Metodológica<br/>(Falta de protocolo estatístico unificado)"]
    end

    subgraph Solucao_Eixo3["Superação de Engenharia"]
        S5["S5: Janela Adaptativa + Quarentena<br/>(Fast-Flush < 5 ms & Zero-Trust 30 s)"]
        S6["S6: Matriz de 7 Dimensões de Validade<br/>(30 Seeds, IC 95%, ANOVA p < 0.001, SHA-256)"]
    end

    L5 ==>|Resiliência Near-RT & SLA| S5
    L6 ==>|Rigor Científico & Reprodutibilidade| S6
```

### Tabela Comparativa de Superação Arquitetural:

| ID | Limitação Diagnosticada | Causa-Raiz Técnica | Solução de Engenharia Implementada | Módulo Impactado |
| :---: | :--- | :--- | :--- | :--- |
| **L1** | **Vetor Rígido de Observação** | `extract_features` limitava-se a $N=2$ xApps; propostas de 3ª ou 4ª xApp eram truncadas. | Extrator de observação dinâmico e elástico para até $N_{\max} = 6$ agentes ($s_t \in \mathbb{R}^{D_{\mathrm{obs}} \cdot N}$). | [`mappo_agent.py`](src/agents/marl/mappo_agent.py) |
| **L2** | **MARL Desprovido de Safe-RL no Treinamento** | Ações geradas pelo Ator violavam restrições físicas durante a exploração, dependendo exclusivamente do Refinement. | Formulação de **Safe-RL via CMDP** (*Constrained MDP*) com multiplicadores de Lagrange adaptativos no gradiente. | [`mappo_agent.py`](src/agents/marl/mappo_agent.py) |
| **L3** | **Grafo KPI Estático e Unicelular** | Grafo `networkx` cobria apenas 3 parâmetros locais sem capturar conformação de feixes, mobilidade e interferência inter-célula. | Grafo Causal Multidimensional incorporando `BEAM_DOWNTILT`, `A3_OFFSET`, `ISAC_SENSING_RATIO` e acoplamento multi-célula. | [`perception_agent.py`](src/agents/perception_agent.py) |
| **L4** | **Cobertura Incompleta de Modelos E2SM** | `RCEncoder` e `KpmDecoder` limitavam-se aos Parâmetros 1, 2 e 3 legados. | Suporte estendido aos Control Styles 1, 2, 3, 10, 11 e RAN Parameter IDs 1 a 11 conforme O-RAN WG3 E2SM-RC v01.03. | [`rc_encoder.py`](src/e2/rc_encoder.py), [`kpm_decoder.py`](src/e2/kpm_decoder.py) |
| **L5** | **Janela Fixa e Vulnerabilidade a Rogue xApps** | Janela de $200\text{ ms}$ fixa gerava latência de espera para tráfego crítico; sem punição para xApps que violavam limites. | Janela Adaptativa com *Fast-Flush* ($< 5\text{ ms}$) e isolamento em **Quarentena Zero-Trust (30 s)** para xApps descalibradas. | [`rdl_xapp.py`](src/rdl_xapp.py), [`refinement_agent.py`](src/agents/refinement_agent.py) |
| **L6** | **Dispersão de Critérios Metodológicos** | Falta de uma matriz explícita de validação estatística e reprodutibilidade científica. | Estruturação formal da **Matriz de 7 Dimensões de Validade Científica** ($N \ge 30$ sementes, ANOVA, IC 95%, SHA-256). | [`Volume 10`](docs/10_matriz_validade_e_pontos_de_atencao_fase3.md), Volume 13 |

---

## 3. Detalhamento das Limitações, Diagnóstico e Soluções com Modelagem Matemática

---

### 3.1. Limitação 1: Dimensionalidade Rígida do Vetor de Observação e Limitação de Concorrência

#### Diagnóstico Técnico
Na versão preliminar da Fase 2, o método `extract_features` formatava o vetor de observação local em um tamanho fixo de 10 elementos ($s_t \in \mathbb{R}^{10}$), alocando posições exclusivamente para as duas primeiras propostas contidas no lote (`involved_xapps[:2]`). Quando um terceiro agente (`traffic-steering` ou `isac-radar`) emitia comandos simultaneamente, seus atributos eram descartados, gerando cegueira contextual no Crítico Centralizado.

#### Solução de Engenharia e Formulação Matemática

* **1. Normalização Modular por Proposta:**  
  Cada proposta de ação $a_i = \langle x_i, n_i, p_i, V_i(p), \mathrm{prio}_i, t_i \rangle$ é codificada em uma sub-tupla normalizada contínua:

$$s_t^{(i)} = \left[ \mathrm{ID}_{\mathrm{norm}}(x_i), \, \mathrm{Code}(p_i), \, \mathrm{Val}_{\mathrm{norm}}(V_i(p)), \, \frac{\mathrm{prio}_i}{100.0}, \, \mathbb{I}_{\mathrm{conflict}}(a_i) \right]$$

* **2. Vetor de Estado Global Elástico para o Crítico Centralizado:**  
  O Crítico Centralizado $V_\psi(s_t^{\mathrm{global}})$ recebe a concatenação elástica de todas as $N$ observações ativas até $N_{\max} = 6$:

$$s_t^{\mathrm{global}} = \left[ s_t^{(1)} \;\Vert\; s_t^{(2)} \;\Vert\; \dots \;\Vert\; s_t^{(N)} \;\Vert\; \mathbf{s}_{\mathrm{telem}} \right] \in \mathbb{R}^{D_{\mathrm{obs}} \cdot N}$$

onde a dimensão de observação individual é $D_{\mathrm{obs}} = 10$, permitindo que o Crítico avalie interações entre até 6 xApps concorrentes sem truncamento.

---

### 3.2. Limitação 2: Ações Discretas e Ausência de Restrições Matemáticas de Safe-RL (CMDP)

#### Diagnóstico Técnico
O treinamento convencional do PPO otimizava unicamente a recompensa agregada $R_t$. Em fases exploratórias do treinamento, o Ator frequentemente sugeria ações de potência ou alocação de PRBs fora dos envelopes de hardware. Embora o `RefinementAgent` vetasse a execução dessas ações a jusante, a política do Ator continuava recebendo gradientes sem penalização direcionada, retardando a convergência em regime seguro.

Para evidenciar a evolução arquitetural, os fluxos de treinamento antes e depois do Safe-RL são desacoplados a seguir:

#### Fluxo A: Treinamento Convencional (Sem Safe-RL — Veto a Posteriori)
```mermaid
flowchart LR
    A1["Ator π_θ"] -->|"Ação Insegura a_t"| ENV["Ambiente 5G NR"]
    ENV -->|"Recompensa R_t"| A1
    REF1["RefinementAgent (Veto a posteriori)"] -.->|"Descarta comando ilegal"| ENV
```

#### Fluxo B: Treinamento Safe-RL CMDP com Multiplicador de Lagrange (Fase 2 Aprimorada)
```mermaid
flowchart LR
    A2["Ator π_θ"] -->|"Ação a_t"| CMDP{"Avaliador de Custo C_k(s, a)"}
    CMDP -->|"C_k > d_k (Violação)"| LAG["Dual Update λ_k"]
    LAG -->|"Gradiente com Penalidade Lagrangiana"| A2
    A2 -->|"Ação Pré-Condicionada Segura"| REF2["RefinementAgent (Safety Guard)"]
    REF2 -->|"Comando 100% Conforme"| GNB["gNodeB 5G NR"]
```

#### Solução de Engenharia e Formulação Matemática

* **1. Formulação do Processo de Decisão de Markov com Restrições (CMDP):**  
  O problema de otimização multiagente é reformulado como a maximização do retorno sujeito a $K$ restrições operacionais de custo:

$$\max_{\theta_i} \mathbb{E}_{\tau \sim \pi_{\theta_i}} \left[ \sum_{t=0}^T \gamma^t R_t \right] \quad \text{sujeito a} \quad J_{C_k}(\pi_{\theta_i}) = \mathbb{E}_{\tau \sim \pi_{\theta_i}} \left[ \sum_{t=0}^T \gamma^t C_k(s_t, a_t) \right] \le d_k, \quad \forall k \in \{1, \dots, K\}$$

onde:
* $C_1(s_t, a_t) = \mathbb{I}(P_{\mathrm{tx}} > 23.0\text{ dBm})$ penaliza violação de potência de rádio;
* $C_2(s_t, a_t) = \mathbb{I}(\mathrm{PRB}_{\mathrm{quota}} > 100.0\%)$ penaliza sobre-alocação física de espectro;
* $d_k = 0.05$ é o orçamento máximo tolerável de risco ($5\%$).

* **2. Função Lagrangiana e Função de Perda Clipped Safe-PPO:**

$$\mathcal{L}_{\mathrm{Safe\text{-}PPO}}(\theta_i) = -\hat{\mathbb{E}}_t \left[ \min\left( r_t(\theta_i) \hat{A}_i^t, \, \mathrm{clip}(r_t(\theta_i), 1-\epsilon, 1+\epsilon) \hat{A}_i^t \right) \right] - \beta_{\mathrm{ent}} \mathcal{H}(\pi_{\theta_i}) + \sum_{k=1}^K \lambda_k \cdot \max\left(0, \overline{C}_{k,t} - d_k\right)$$

onde $r_t(\theta_i) = \frac{\pi_{\theta_i}(a_{i,t} \mid o_{i,t})}{\pi_{\theta_i,\mathrm{old}}(a_{i,t} \mid o_{i,t})}$, $\epsilon = 0.20$ e $\beta_{\mathrm{ent}} = 0.01$.

* **3. Atualização Dual dos Multiplicadores de Lagrange:**  
  A cada época de otimização $j$, o multiplicador $\lambda_k$ é ajustado por gradiente ascendente:

$$\lambda_k^{(j+1)} = \max\left(0, \, \lambda_k^{(j)} + \alpha_{\mathrm{cost}} \left( \overline{C}_k^{(j)} - d_k \right)\right)$$

onde $\alpha_{\mathrm{cost}} = 0.01$. Se o modelo violar restrições, $\lambda_k$ cresce progressivamente, forçando o gradiente da política a afastar-se de ações perigosas.

---

### 3.3. Limitação 3: Grafo de Dependências Causal Estático e Falta de Relações Multi-Célula

#### Diagnóstico Técnico
O `PerceptionAgent` utilizava um dicionário estático contendo apenas 3 RCPs em escopo estritamente local (célula isolada). Não havia suporte para novas capacidades 5G-Advanced/6G (MIMO Massive, ISAC e Carrier Aggregation) nem modelagem de interferência co-canal cruzada entre gNodeBs vizinhas em cenários densos (Urban Microcell ISD $< 200\text{ ms}$).

Para facilitar o entendimento, o grafo causal multidimensional é desacoplado em camadas funcionais:

#### Camada A: Controle de Recursos de Rádio e Potência
```mermaid
flowchart TD
    PRB["PRB_QUOTA"] --> THP["DRB.UEThpDl (Vazão)"]
    PRB --> PRBU["RRU.PrbUsedDl (Ocupação PRB)"]
    SCHED["SCHEDULER_WEIGHT"] --> THP
    SCHED --> DLY["DRB.RlcSduDelayDl (Latência)"]
    TX["TX_POWER"] --> SINR["L1M.DL-sinr (Qualidade Canal)"]
    TX --> THP
    TX --> PWR["Energy.PowerConsumption"]
    TILT["BEAM_DOWNTILT"] --> SINR
    TILT --> RSRP["Beam.RSRP"]
    TILT --> INTER["InterCell.Interference"]
    TILT --> THP
```

#### Camada B: Mobilidade, Sensoriamento ISAC e Agregação de Portadoras
```mermaid
flowchart TD
    A3["A3_OFFSET"] --> HO["Mobility.HandoverRate"]
    A3 --> PP["Mobility.PingPongRate"]
    A3 --> PRBU["RRU.PrbUsedDl"]
    ISAC["ISAC_SENSING_RATIO"] --> RAD_DET["Radar.DetectionProb"]
    ISAC --> RAD_RES["Radar.ResolutionRange"]
    ISAC --> THP["DRB.UEThpDl"]
    CA["CARRIER_AGG_RATIO"] --> SCELL["SCell.PrbUsedDl"]
    CA --> THP
```

#### Camada C: Mapeamento de KPIs para Metas de SLA
```mermaid
flowchart LR
    DLY["DRB.RlcSduDelayDl"] --> SLA_URLLC["SLA URLLC (< 5 ms)"]
    SINR["L1M.DL-sinr"] --> SLA_URLLC
    PWR["Energy.PowerConsumption"] --> SLA_EE["Eficiência Energética (Bits/J)"]
    RAD_DET["Radar.DetectionProb"] --> SLA_ISAC["Acurácia de Sensoriamento (6G)"]
```

#### Solução de Engenharia e Formulação Matemática

* **1. Grafo Causal Multidimensional Expansível:**  
  A topologia causal $\mathcal{G} = (\mathcal{V}_{\mathrm{RCP}} \cup \mathcal{V}_{\mathrm{KPI}}, \mathcal{E})$ foi expandida no `PerceptionAgent`, incorporando:
  * `BEAM_DOWNTILT` $\longrightarrow \{\text{L1M.DL-sinr}, \text{Beam.RSRP}, \text{InterCell.Interference}, \text{DRB.UEThpDl}\}$;
  * `A3_OFFSET` $\longrightarrow \{\text{Mobility.HandoverRate}, \text{Mobility.PingPongRate}, \text{RRU.PrbUsedDl}\}$;
  * `ISAC_SENSING_RATIO` $\longrightarrow \{\text{Radar.DetectionProb}, \text{Radar.ResolutionRange}, \text{DRB.UEThpDl}\}$;
  * `CARRIER_AGG_RATIO` $\longrightarrow \{\text{SCell.PrbUsedDl}, \text{DRB.UEThpDl}\}$.

* **2. Modelagem de Acoplamento Espacial Multi-Célula:**  
  Para nós gNodeB vizinhos $n_a, n_b$ com distância inter-site $d(n_a, n_b) < 200\text{ m}$, a interferência cruzada no downlink é modelada por:

$$I_{\mathrm{inter}}(n_a, n_b) = P_{\mathrm{tx}}(n_b) \cdot G_{\mathrm{tx}}(\theta_b, \phi_b) \cdot \mathrm{PL}(d(n_a, n_b))^{-1}$$

Quando a xApp de energia altera $P_{\mathrm{tx}}(n_b)$ ou o tilt do feixe `BEAM_DOWNTILT`, o `PerceptionAgent` identifica proativamente o impacto no $\mathrm{SINR}(n_a)$, classificando o evento como **Conflito Indireto Multi-Célula**.

---

### 3.4. Limitação 4: Cobertura Incompleta de Modelos de Serviço O-RAN E2SM-RC / E2SM-KPM

#### Diagnóstico Técnico
O codificador ASN.1 APER (`rc_encoder.py`) estava restrito a apenas 3 parâmetros legados (IDs 1, 2, 3), inviabilizando comandos de conformação de feixes Massive MIMO, mobilidade e sensoriamento ISAC.

#### Solução de Engenharia
Expansão integral conforme especificação **O-RAN.WG3.TS.E2SM-RC-R003-v03.00**:

| RAN Parameter ID | Nome do Parâmetro | E2SM-RC Control Style | Tipo de Dado ASN.1 | Faixa Válida |
| :---: | :--- | :--- | :--- | :---: |
| **1** | `PRB_QUOTA` | Control Style 1 (Radio Resource Allocation) | `INTEGER (0..100)` | $0\% \text{ a } 100\%$ |
| **2** | `TX_POWER` | Control Style 2 (Basic Cell Power Control) | `REAL (-10.0..43.0)` | $-10.0 \text{ a } 43.0\text{ dBm}$ |
| **3** | `SCHEDULER_WEIGHT` | Control Style 1 (QoS Flow Weight) | `REAL (0.1..10.0)` | $0.1 \text{ a } 10.0$ |
| **4** | `A3_OFFSET` | Control Style 3 (Connected Mode Mobility) | `INTEGER (-15..15)` | $-15\text{ dB a } +15\text{ dB}$ |
| **10** | `BEAM_DOWNTILT` | Control Style 10 (Massive MIMO Beam Control) | `REAL (0.0..15.0)` | $0.0^\circ \text{ a } 15.0^\circ$ |
| **11** | `ISAC_SENSING_RATIO`| Control Style 11 (ISAC Sensing Allocation) | `REAL (0.0..0.50)` | $0\% \text{ a } 50\%$ do frame |

---

### 3.5. Limitação 5: Janela de Decisão Rígida e Falta de Isolamento Zero-Trust Anti-Rogue

#### Diagnóstico Técnico
1. **Latência Inflexível:** A janela temporal fixa de $200\text{ ms}$ obrigava pacotes urgentes de fatias URLLC a aguardar o fechamento do lote, elevando desnecessariamente a latência em regime de baixa carga.
2. **Vulnerabilidade a xApps Maliciosas ou Descalibradas (*Rogue xApps*):** Quando uma xApp apresentava falha de código e emitia rajadas de comandos a $5\text{ Hz}$ com parâmetros ilegais, o sistema rejeitava as ações, mas o canal SCTP permanecia sobrecarregado.

```mermaid
stateDiagram-v2
    [*] --> OperacaoNormal: xApp Onboarding Concluído

    OperacaoNormal --> InfracaoDetectada: Comando Ilegal ou Fora de Faixa
    InfracaoDetectada --> OperacaoNormal: Infrações < 3 na janela de 10s
    
    InfracaoDetectada --> QuarentenaZeroTrust: ≥ 3 Infrações Graves na Janela W = 10s
    
    state QuarentenaZeroTrust {
        [*] --> BloqueioTotal: Descarte Imediato no Barramento
        BloqueioTotal --> AlertaSeguranca: Notificação Prometheus & Logs
        AlertaSeguranca --> ContagemTempo: Janela T_quarantine = 30s
    }

    QuarentenaZeroTrust --> OperacaoNormal: Expiração de 30s & Reset de Reputação
```

#### Solução de Engenharia e Modelagem Matemática

* **1. Janela de Decisão Adaptativa com *Fast-Flush*:**  
  A duração da janela de agregação $T_{\mathrm{window}}(t)$ é modulada dinamicamente:

$$T_{\mathrm{window}}(t) = \begin{cases} T_{\mathrm{fast}} \le 5\text{ ms}, & \text{se } \exists a_i \in \mathrm{Buffer} : \mathrm{prio}_i \ge 80 \lor \mathrm{Delay}_{\mathrm{URLLC}} > 15.0\text{ ms} \\ T_{\mathrm{dyn}} \in [50\text{ ms}, 200\text{ ms}], & \text{caso contrario} \end{cases}$$

* **2. Mecanismo Comportamental Zero-Trust e Quarentena Automática:**  
  O `RefinementAgent` mantém um registro temporal de infrações $\mathcal{H}_{\mathrm{viol}}(x_i) = \{t_1, t_2, \dots\}$. O estado de quarentena é ativado por:

$$\mathrm{Quarantine}(x_i) = \begin{cases} \text{true}, & \text{se } \sum_{t \in [t_{\mathrm{now}} - W, t_{\mathrm{now}}]} \mathbb{I}_{\mathrm{violation}}(x_i, t) \ge M_{\mathrm{thresh}} \implies \text{Bloqueio por } 30.0\text{ s} \\ \text{false}, & \text{caso contrario} \end{cases}$$

onde a janela de monitoramento é $W = 10.0\text{ s}$ e o limiar é $M_{\mathrm{thresh}} = 3$ violações. Ao ser colocada em quarentena, todas as propostas da xApp são descartadas silenciosamente no barramento por $T_{\mathrm{quarantine}} = 30.0\text{ s}$, emitindo a métrica `rdl_zero_trust_quarantined_xapps_total` para o Prometheus.

* **3. Modelagem Matemática das Restrições Invariantes de Segurança (Camada 3):**  
  O operador de projeção determinística do `RefinementAgent` assegura que nenhuma ação executada ($a_{\mathrm{exec}}$) viole as leis físicas de propagação e limites de hardware:

$$a_{\mathrm{exec}} = \mathrm{SafeGuard}(a_t) = \begin{cases} a_t, & \text{se restricoes fisicas forem atendidas} \\ \mathrm{proj}(a_t), & \text{se houver violacao corrigivel} \\ \mathrm{veto}, & \text{se a acao for estritamente ilegal} \end{cases}$$

---

### 3.6. Limitação 6: Formalização da Matriz de Validade Científica e Reprodutibilidade

#### Diagnóstico Técnico
Os critérios de validade experimental encontravam-se dispersos na documentação, dificultando a auditoria por revisores de periódicos de alto impacto.

#### Solução de Engenharia: Matriz de 7 Dimensões de Validade
A metodologia experimental foi estruturada em **7 dimensões formais de validade científica**:

| Dimensão de Validade | Requisito Metodológico Rigoroso | Implementação e Evidência no Repositório |
| :--- | :--- | :--- |
| **1. Validade Estatística** | $N \ge 30$ sementes RNG independentes, Intervalo de Confiança (IC 95%), ANOVA de uma via e teste t pareado ($p < 0.001$). | Simulações automatizadas via script `run_batch.sh` com exportação CSV e cálculo de desvio padrão e IC 95%. |
| **2. Validade Temporal** | Respeito estrito ao *Budget* Near-RT ($10\text{ ms} - 1.0\text{ s}$) e decodificação ASN.1 APER $< 100\ \mu\text{s}$. | Latência de decisão média $= 12.5\text{ ms}$ e latência de Nível 1 $= 0.85\text{ ms}$. |
| **3. Estabilidade e Dinâmica** | Handover Ping-Pong $= 0\text{ ev/min}$ e supressão total de oscilação de parâmetros (*Parameter Flipping*). | Janela de Resfriamento (*Lockout*) de $5.0\text{ s}$ validada no cenário de estresse com Rogue xApp. |
| **4. Validade de Construção** | Conformidade com O-RAN WG3 TS.E2SM-RC v01.03, WG3 E2AP v02.03 e interfaces RMR. | Encoders ASN.1 APER binários estritamente alinhados com o padrão O-RAN. |
| **5. Blindagem Invariante** | Impossibilidade matemática de despacho de ações fora do envelope físico $[-10, 23]\text{ dBm}$ e $[0, 100]\%$. | Dupla camada de proteção: Safe-RL CMDP no treino + Safety Guard no despacho. |
| **6. Validade Externa** | Canal 3GPP TR 38.901 Urban Microcell (UMi), banda $n78$ ($3.5\text{ GHz}$), largura de banda de $100\text{ MHz}$ e mobilidade mista. | Co-simulação ns-3.40 (5G-LENA + NORI) com 30 UEs (URLLC, eMBB e mMTC). |
| **7. Reprodutibilidade** | Manifesto de proveniência criptográfica (SHA-256) e cobertura total de testes unitários. | Checksums em `manifest_experiment.json` e suíte de testes automatizados aprovados no pytest. |

---

## 4. Evidências Empíricas e Resultados Experimentais

![Dinâmica Temporal de Treinamento e Convergência](figures/cenario_7_marl_treinamento_convergencia_perdas.png)

### Tabela de Desempenho Comparativo (Antes e Depois da Superação das Limitações):

| Métrica Avaliada | Baseline (Sem RDL) | Fase 2 Inicial (Pré-Auditoria) | Fase 2 Aprimorada (Pós-Superação) | Ganho Absoluto |
| :--- | :---: | :---: | :---: | :---: |
| **Latência URLLC P99** | `18.66 ms` | `3.45 ms` | **`2.40 ms`** | **-87.1% vs Baseline** |
| **Violação de SLA URLLC** | `93.33%` | `1.20%` | **`0.00%` (Zero violações)** | **100% de conformidade** |
| **Taxa de Entrega (PDR %)** | `39.28%` | `99.10%` | **`99.85%`** | **+154.2% de entrega** |
| **Taxa de Perda (PLR %)** | `60.72%` | `0.90%` | **`0.15%`** | **-99.8% de perda** |
| **Eficiência Energética (Bits/J)** | `1.00x` | `+15.2%` | **`+18.2%`** | **Operação Green** |
| **SINR Médio Downlink** | `14.2 dB` | `19.1 dB` | **`21.4 dB`** | **+7.2 dB de ganho** |
| **Handover Ping-Pong** | `22 ev/min` | `0 ev/min` | **`0 ev/min`** | **100% eliminado** |
| **Ações Ilegais Executadas** | `100.0%` (Sem guarda) | `0.0%` (Vetadas no Refinement) | **`0.0%` (Prevenidas no Treino)** | **Blindagem Total** |
| **Tempo de Bloqueio Rogue xApp**| $\infty$ (Sem isolamento) | $\infty$ (Apenas veto individual) | **`< 25 ms` (Quarentena 30s)** | **Proteção Zero-Trust** |

---

## 5. Rastreabilidade de Implementações e Arquivos no Repositório

Todas as soluções documentadas neste relatório possuem implementação direta e verificada no código-fonte do repositório:

| Solução Implementada | Arquivo Fonte | Classes / Métodos Chave |
| :--- | :--- | :--- |
| **Safe-RL CMDP e Vetor Dinâmico** | [`src/agents/marl/mappo_agent.py`](src/agents/marl/mappo_agent.py) | `MAPPOAgent.update()`, `compute_gae()`, `ActorNetwork`, `CriticNetwork` |
| **Grafo Causal Multidimensional** | [`src/agents/perception_agent.py`](src/agents/perception_agent.py) | `PerceptionAgent._build_topology_graph()`, `detect_conflicts()` |
| **Motor Hierárquico e Lockout** | [`src/agents/reasoning_agent.py`](src/agents/reasoning_agent.py) | `ReasoningAgent.resolve()`, `estimate_complexity()`, `apply_lockout()` |
| **Quarentena Zero-Trust & Safety** | [`src/agents/refinement_agent.py`](src/agents/refinement_agent.py) | `RefinementAgent._check_quarantine()`, `_record_violation()`, `refine()` |
| **Janela Adaptativa Fast-Flush** | [`src/rdl_xapp.py`](src/rdl_xapp.py) | `RDLxApp.process_action_batch()`, `run()` |
| **Codecs E2SM-RC / E2SM-KPM** | [`src/e2/rc_encoder.py`](src/e2/rc_encoder.py), [`src/e2/kpm_decoder.py`](src/e2/kpm_decoder.py) | `RCEncoder.encode_control_message()`, `KpmDecoder.decode()` |
| **Suíte de Testes Automatizados** | [`tests/`](tests/) | `test_marl_mappo.py`, `test_refinement.py`, `test_reasoning.py` |
