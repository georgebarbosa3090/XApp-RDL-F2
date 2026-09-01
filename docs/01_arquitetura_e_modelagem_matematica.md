# Volume 01: Arquitetura de Software e Modelagem Matemática da Fase 2 (CA-RDL / MARL)

**Documento:** Volume Temático 01  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL)  
**Escopo:** Tríade de Agentes Autônomos, Formulação MAPPO (Multi-Agent PPO), Espaço de Estados/Ações, Recompensa Multi-Objetivo e Safety Guards  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Visão Geral da Arquitetura Cognitiva

A Fase 2 introduz uma arquitetura orientada a agentes cognitivos com **Aprendizado por Reforço Multiagente (MARL)** baseado no paradigma **MAPPO (Multi-Agent Proximal Policy Optimization)** com **Treinamento Centralizado e Execução Descentralizada (CTDE)**.

```mermaid
graph TD
    subgraph Perception_Layer["Perception Layer (PerceptionAgent)"]
        E2["E2SM-KPM Metrics (gNodeB)"] --> FE["Feature Engineering & Normalização"]
        XAPP_IN["Propostas das 3 xApps (RMR)"] --> FE
        FE --> S_T["Vetor de Estado Global: s_t"]
    end

    subgraph Reasoning_Layer["Reasoning Layer (ReasoningAgent - MAPPO)"]
        S_T --> CRITIC["Crítico Centralizado: V_phi(s_t)<br/>(Estima o Valor Global da Rede)"]
        S_T --> ACT_URLLC["Ator Descentralizado: pi_theta1(a_1|o_1)<br/>(Fatia URLLC)"]
        S_T --> ACT_EMBB["Ator Descentralizado: pi_theta2(a_2|o_2)<br/>(Fatia eMBB)"]
        S_T --> ACT_ES["Ator Descentralizado: pi_theta3(a_3|o_3)<br/>(Energy Saving)"]
    end

    subgraph Refinement_Layer["Refinement Layer (RefinementAgent)"]
        ACT_URLLC --> SG["Safety Guards Determinísticos<br/>(Limites Físicos de Potência e PRB)"]
        ACT_EMBB --> SG
        ACT_ES --> SG
        SG --> HARMONIZED["Ações Harmonizadas e Seguras: a*_t"]
    end

    HARMONIZED --> E2_OUT["Interface E2 / E2SM-RC -> gNodeB"]
```

---

## 2. Modelagem Matemática do MAPPO

### 2.1. Espaço de Estados Global ($\mathcal{S}$)
O vetor de estado $s_t \in \mathcal{S}$ capturado pelo `PerceptionAgent` inclui:
$$s_t = \left[ \text{SINR}_t, \text{RSRP}_t, \text{PRB}_{\text{demanded}}, \text{PRB}_{\text{available}}, \text{Load}_{\text{traffic}}, P_{tx}, N_{ue}, \text{ConflictFlag}, \text{SliceType} \right]$$

### 2.2. Função de Perda do Ator (Clipping PPO)
Cada ator descentralizado $\pi_{\theta_i}$ otimiza a política com o mecanismo de clipagem de probabilidade:
$$L^{CLIP}(\theta_i) = \hat{\mathbb{E}}_t \left[ \min \left( r_t(\theta_i) \hat{A}_t, \text{clip}(r_t(\theta_i), 1 - \epsilon, 1 + \epsilon) \hat{A}_t \right) \right]$$
Onde $r_t(\theta_i) = \frac{\pi_{\theta_i}(a_i | o_i)}{\pi_{\theta_i, \text{old}}(a_i | o_i)}$ e $\hat{A}_t$ é a vantagem calculada pelo Crítico Centralizado via GAE (Generalized Advantage Estimation).

### 2.3. Função de Recompensa Multi-Objetivo ($R_t$)
A recompensa unificada equilibra múltiplos objetivos ponderados pelo `IntentClassifier`:
$$R_t = w_{qos} R_{qos}(t) + w_{ee} R_{ee}(t) - w_{pen} P_{viol}(t)$$
* **$R_{qos}(t)$:** Proximidade do cumprimento do SLA URLLC ($\text{Delay} \le 5\text{ ms}$).
* **$R_{ee}(t)$:** Eficiência energética calculada em $\frac{\text{Throughput (Mbps)}}{P_{tx} (\text{Watts})}$.
* **$P_{viol}(t)$:** Penalidade proporcional a conflitos não mitigados e violações de recursos.

---

## 3. Tríade de Agentes Autônomos

| Agente | Classe Python | Responsabilidade Principal |
| :--- | :--- | :--- |
| **Perception Agent** | `src.agents.perception.PerceptionAgent` | Ingestão E2SM-KPM, extração de features, normalização robusta e detecção de anomalias de rádio. |
| **Reasoning Agent** | `src.agents.reasoning.ReasoningAgent` | Avaliação de contexto, execução da rede neural MAPPO e geração de propostas de controle. |
| **Refinement Agent** | `src.agents.refinement.RefinementAgent` | Verificação de invariantes físicos, Safety Guards de SLA e formatação de mensagens E2SM-RC. |
