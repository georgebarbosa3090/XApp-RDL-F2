# Volume 01: Arquitetura de Software e Modelagem Matemática da Fase 2 (CA-RDL / MARL)

**Documento:** Volume Temático 01  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL)  
**Escopo:** Tríade de Agentes Autônomos, Formulação MAPPO (Multi-Agent PPO), Espaço de Estados/Ações, Recompensa Multi-Objetivo e Safety Guards  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Visão Geral da Arquitetura Cognitiva

A Fase 2 introduz uma arquitetura orientada a agentes cognitivos com **Aprendizado por Reforço Multiagente (MARL)** baseado no paradigma **MAPPO (Multi-Agent Proximal Policy Optimization)** com **Treinamento Centralizado e Execução Descentralizada (CTDE)**.

Para máxima clareza e manutenibilidade, a arquitetura é estruturada em três camadas funcionais desacopladas:

### 1.1. Camada de Percepção (Perception Layer)
```mermaid
flowchart LR
    E2["Métricas E2SM-KPM<br/>(gNodeB 5G NR)"] --> FE["Feature Engineering &<br/>Normalização Robusta"]
    XAPP_IN["Propostas das xApps<br/>(Barramento RMR / REST)"] --> FE
    FE --> S_T["Vetor de Estado Global Concatenado<br/>s_t ∈ ℝ^(D_obs × N)"]
```

### 1.2. Camada de Raciocínio e Coordenação (Reasoning Layer - MAPPO CTDE)
```mermaid
flowchart TD
    S_T["Vetor de Estado s_t"] --> CRITIC["Crítico Centralizado: V_ψ(s_t)<br/>(Avaliação de Valor Global da Rede)"]
    S_T --> ACT_URLLC["Ator 1: π_θ1(a_1 | o_1)<br/>(Fatia URLLC - Prioridade SLA)"]
    S_T --> ACT_EMBB["Ator 2: π_θ2(a_2 | o_2)<br/>(Fatia eMBB - Capacidade/Vazão)"]
    S_T --> ACT_ES["Ator 3: π_θ3(a_3 | o_3)<br/>(Energy Saving - Otimização Green)"]
```

### 1.3. Camada de Refinamento e Despacho E2 (Refinement Layer & Safety Guards)
```mermaid
flowchart LR
    ACT_OUT["Propostas de Ações<br/>{a_1, a_2, ..., a_N}"] --> SG["Safety Guards Determinísticos<br/>• Envelopes Físicos [-10, 23] dBm & PRB ≤ 100%<br/>• Quarentena Zero-Trust (30s)"]
    SG --> HARMONIZED["Ações Harmonizadas e Seguras: a*_t"]
    HARMONIZED --> E2_ENC["Codificador ASN.1 APER<br/>(E2SM-RC Control Message)"]
    E2_ENC --> E2_OUT["gNodeB 5G-LENA / ns-3<br/>(Interface E2 / mtype: 12010)"]
```

---

## 2. Modelagem Matemática do MAPPO

### 2.1. Espaço de Estados Global ($\mathcal{S}$)
O vetor de estado $s_t \in \mathcal{S}$ capturado pelo `PerceptionAgent` inclui:
$$s_t = \left[ \text{SINR}_t, \, \text{RSRP}_t, \, \text{PRB}_{\text{demanded}}, \, \text{PRB}_{\text{available}}, \, \text{Load}_{\text{traffic}}, \, P_{\text{tx}}, \, N_{\text{ue}}, \, \text{ConflictFlag}, \, \text{SliceType} \right]$$

### 2.2. Função de Perda do Ator (Clipping PPO)
Cada ator descentralizado $\pi_{\theta_i}$ otimiza a política com o mecanismo de clipagem de probabilidade:
$$L^{\text{CLIP}}(\theta_i) = \hat{\mathbb{E}}_t \left[ \min \left( r_t(\theta_i) \hat{A}_t, \, \text{clip}(r_t(\theta_i), 1 - \epsilon, 1 + \epsilon) \hat{A}_t \right) \right]$$
onde $r_t(\theta_i) = \frac{\pi_{\theta_i}(a_i \mid o_i)}{\pi_{\theta_i, \text{old}}(a_i \mid o_i)}$ e $\hat{A}_t$ é a vantagem calculada pelo Crítico Centralizado via GAE (*Generalized Advantage Estimation*).

### 2.3. Função de Recompensa Multi-Objetivo ($R_t$)
A recompensa unificada equilibra múltiplos objetivos ponderados pelo `IntentClassifier`:
$$R_t = w_{\text{qos}} R_{\text{qos}}(t) + w_{\text{ee}} R_{\text{ee}}(t) - w_{\text{pen}} P_{\text{viol}}(t)$$
* **$R_{\text{qos}}(t)$:** Proximidade do cumprimento do SLA URLLC ($\text{Delay} \le 5.0\text{ ms}$).
* **$R_{\text{ee}}(t)$:** Eficiência energética calculada em $\frac{\text{Throughput (Mbps)}}{P_{\text{tx}} (\text{Watts})}$.
* **$P_{\text{viol}}(t)$:** Penalidade proporcional a conflitos não mitigados e violações de recursos.

---

## 3. Tríade de Agentes Autônomos

| Agente | Classe Python | Responsabilidade Principal |
| :--- | :--- | :--- |
| **Perception Agent** | `src.agents.perception.PerceptionAgent` | Ingestão E2SM-KPM, extração de features, normalização robusta e detecção de anomalias de rádio. |
| **Reasoning Agent** | `src.agents.reasoning.ReasoningAgent` | Avaliação de contexto, execução da rede neural MAPPO e geração de propostas de controle. |
| **Refinement Agent** | `src.agents.refinement.RefinementAgent` | Verificação de invariantes físicos, Safety Guards de SLA e formatação de mensagens E2SM-RC. |
