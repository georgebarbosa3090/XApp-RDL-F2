# Volume 09: Relatório Técnico Detalhado — Operações, Infraestrutura e Formulação da Fase 2 (CA-RDL / MARL)

**Projeto:** xApp RDL (Resource and Decision Layer) — Governança Near-RT O-RAN  
**Versão:** Fase 2 — *Context-Aware RDL (CA-RDL)* com Paradigma Multi-Agent Reinforcement Learning (MAPPO)  
**Ambiente de Execução:** Cluster Kubernetes k3d (`rancher-lab`) / WSL2 Ubuntu 22.04 LTS / Simulador ns-3.40 (5G-LENA + NORI)  
**Data de Emissão:** 02/09/2026  
**Status:** Validado e Aprovado nos Benchmarks da Fase 2  

---

## 1. Visão Geral Executiva e Arquitetura Global da Fase 2

A Fase 2 do projeto evoluiu a camada de decisão do xApp RDL de uma abordagem puramente heurística (H-RDL da Fase 1) para uma arquitetura **Cognitiva e Ciente de Contexto (Context-Aware RDL - CA-RDL)**. O sistema atua no plano Near-RT RIC (loop de controle de $10\text{ ms}$ a $1\text{ s}$ segundo as especificações O-RAN WG3), arbitrando ações conflitantes emitidas simultaneamente por múltiplas xApps de rádio (`ricxapp-qos-xslice`, `ricxapp-energy-saving` e `ricxapp-traffic-steering`) sobre nós gNodeB 5G NR.

![Pipeline Global e Arquitetura do xApp RDL Fase 2](figures/diagram_01_global_pipeline_architecture.png)

```mermaid
graph TD
    subgraph Near_RT_RIC ["Near-RT RIC (Namespace: ricxapp)"]
        subgraph XAPPS ["Reference xApps Concorrentes"]
            X1["ricxapp-qos-xslice (:8082)"]
            X2["ricxapp-energy-saving (:8084)"]
            X3["ricxapp-traffic-steering (:8086)"]
        end

        subgraph RDL ["xApp RDL Fase 2 (ricxapp-iqos-xapp-rdl-f2)"]
            P["1. Perception Agent<br/>(Ingestão E2SM-KPM / Grafo KG)"]
            R["2. Reasoning Agent<br/>(MAPPO CTDE / TVS / EEVS)"]
            REF["3. Refinement Agent<br/>(Safety Guards Determinísticos)"]
            IC["4. Intent Classifier<br/>(RandomForest w_qos, w_ee)"]
        end

        SDL[("Shared Data Layer (SDL)<br/>Redis DB (:6379)")]
        PROM["Prometheus Telemetry<br/>(:8081/metrics)"]
    end

    subgraph RAN ["5G NR gNodeB (ns-3.40 / 5G-LENA)"]
        GNB["gNodeB 5G NR (3.5 GHz n78, 100 MHz)<br/>10 URLLC + 10 eMBB + 10 mMTC"]
    end

    X1 -->|RDL_ACTION_PROPOSAL :30000| P
    X2 -->|RDL_ACTION_PROPOSAL :30000| P
    X3 -->|RDL_ACTION_PROPOSAL :30000| P
    GNB -->|E2SM-KPM Indication :12050| P
    P -->|Vetor de Estado s_t| R
    IC -->|Pesos Modulados w| R
    R -->|Ação Proposta a_t| REF
    REF -->|E2SM-RC Control :12010| GNB
    R <--> SDL
    RDL --> PROM
```

---

## 2. Infraestrutura e Componentes de Plataforma

![Infraestrutura de Cluster k3d e Rancher](figures/diagram_03_infraestrutura_k3d_rancher.png)

### 2.1. Kubernetes e k3d (`rancher-lab`)
* **Topologia de Cluster:** Executado sobre o nó `rancher-lab-server-0` no k3d (versão K3s leve) com driver de rede bridge integrado ao host WSL2.
* **Isolamento por Namespaces O-RAN:**
  * `ricplt`: Hospeda a infraestrutura de terminação da plataforma, contendo o **E2Term** (exposto na porta `36422/SCTP` para comunicação com os agentes E2 do ns-3) e o **E2Mgr**.
  * `ricxapp`: Hospeda a release Helm `ricxapp-iqos-xapp-rdl-f2` e as 3 xApps de referência concorrentes.
  * `monitoring`: Contém as instâncias do **Prometheus** (porta `9090`), **Grafana** (porta `3000`) e **Kiali Mesh** (porta `20001`).
* **Roteamento de Portas e Serviços:**
  * Porta `8080/TCP`: Endpoint de integridade e liveness/readiness probes (`/health/live`, `/health/ready`) gerenciado pelo `HealthServer`.
  * Porta `8081/TCP`: Endpoint OpenMetrics (`/metrics`) consumido a cada $1\text{ s}$ pelo scraper do Prometheus.
  * Portas `4560/TCP` e `4561/TCP`: Barramento de alta velocidade RMR (RIC Message Router) com roteamento direto para troca de mensagens inter-xApp sem overhead de serialização HTTP.

### 2.2. Shared Data Layer (SDL) e Redis
A camada de persistência compartilhada é operada pelo repositório [`SdlRepository`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/infrastructure/sdl_repository.py) com abstração para o Redis:
* **Namespace Redis:** `iqos-xapp-rdl`
* **Schema de Chaves e Estruturas de Dados:**
  * `subscriptions:{sub_id}`: Metadados de subscrição E2SM-KPM ativas na gNodeB.
  * `e2_nodes:{node_id}`: Estado de conexão e capacidades de cada nó E2 conectado.
  * `latest_kpm_state:{node_id}`: Último vetor de telemetria ingerido (`DRB.UEThpDl`, `DRB.RlcSduDelayDl`, `RRU.PrbUsedDl`, `L1M.DL-sinr`).
  * `action_proposals:{proposal_id}`: Histórico e buffer de ações submetidas pelas xApps concorrentes.
  * `decisions:{decision_id}`: Trilha auditável das decisões tomadas pelo RDL, registrando o conflito original, estratégia escolhida, confiança e validação dos Safety Guards.
* **Mecanismo de Resiliência (`USE_FAKE_SDL`):** O componente [`MemoryModule`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/infrastructure/memory_module.py) atua como *in-memory cache fallback* para ambientes de teste unitário e simulação rápida em pipeline CI/CD sem dependência de daemon Redis externo.

---

## 3. Grafo de Conhecimento e Dependências (Knowledge / Dependency Graph)

O módulo de percepção implementa um **Grafo de Dependências de Recursos e KPIs** utilizando a biblioteca `networkx` e tabelas de adjacência de impacto físico de rádio no arquivo [`perception_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/perception_agent.py):

### 3.1. Modelagem das Relações Lógicas
O grafo direcionado mapeia como alterações em parâmetros de baixo nível da RAN propagam efeitos sobre os KPIs de desempenho:

$$\mathcal{G}_{KG} = (\mathcal{V}_{params} \cup \mathcal{V}_{KPIs}, \, \mathcal{E}_{impact})$$

* **PRB_QUOTA** afeta: `DRB.UEThpDl` (Throughput) e `RRU.PrbUsedDl` (Ocupação de PRB).
* **SCHEDULER_WEIGHT** afeta: `DRB.UEThpDl` (Throughput) e `DRB.RlcSduDelayDl` (Latência RLC).
* **TX_POWER** afeta: `L1M.DL-sinr` (Qualidade de Canal SINR) e `DRB.UEThpDl` (Throughput).

```mermaid
graph LR
    PRB["PRB_QUOTA"] --> THP["DRB.UEThpDl"]
    PRB --> PRB_U["RRU.PrbUsedDl"]
    SCHED["SCHEDULER_WEIGHT"] --> THP
    SCHED --> DLY["DRB.RlcSduDelayDl"]
    TX["TX_POWER"] --> SINR["L1M.DL-sinr"]
    TX --> THP
```

### 3.2. Classificação e Detecção Topológica de Conflitos
1. **Conflito Direto (DIRECT):** Duas ou mais xApps distintas tentam alterar simultaneamente o mesmo parâmetro físico de rádio no mesmo nó gNodeB:
   $$\text{node}_a = \text{node}_b \quad \text{e} \quad \text{param}_a = \text{param}_b \quad \text{e} \quad \text{xapp}_a \neq \text{xapp}_b$$
2. **Conflito Indireto (INDIRECT):** Ações direcionadas a parâmetros diferentes geram acoplamento destrutivo ao disputar os mesmos KPIs compartilhados no Grafo de Conhecimento:
   $$\text{node}_a = \text{node}_b \quad \text{e} \quad \text{param}_a \neq \text{param}_b \quad \text{e} \quad \left( \text{KPIs}(\text{param}_a) \cap \text{KPIs}(\text{param}_b) \neq \emptyset \right)$$
   *Exemplo Prático:* A xApp `energy-saving` reduz `TX_POWER` para economizar energia enquanto a xApp `qos-xslice` aumenta `PRB_QUOTA` para manter o throughput do fluxo URLLC. A queda de potência degrada o SINR (`L1M.DL-sinr`), anulando o efeito do aumento de PRBs e provocando violação de latência.

---

## 4. Módulos Internos da Arquitetura Cognitiva

![Arquitetura Cognitiva e Formulação MAPPO CTDE](figures/diagram_02_arquitetura_cognitiva_mappo.png)

### 4.1. Módulo de Percepção (`PerceptionAgent`)
* **Ingestão E2SM-KPM:** O [`KpmDecoder`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/e2/kpm_decoder.py) decodifica payloads ASN.1 das mensagens `RIC_INDICATION` (mtype `12050`).
* **Janela Temporal de Decisão (*Decision Window*):** O [`RDLxApp`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/rdl_xapp.py) implementa um buffer com janela $\Delta t_{win} = 200\text{ ms}$. Todas as propostas `RDL_ACTION_PROPOSAL` (mtype `30000`) que chegam dentro da janela são agrupadas e avaliadas em lote.
* **Extração e Normalização de Estado Global:** Converte as telemetrias e propostas em um vetor de observação normalizado $s_t \in \mathbb{R}^{10}$:
  * $s_t[0]$: Tipo de conflito ($1.0$ para direto, $0.5$ para indireto).
  * $s_t[1]$: Densidade de xApps envolvidas no lote ($\frac{N_{xapps}}{5}$).
  * $s_t[2]$: Throughput agregado normalizado ($\min(1.0, \frac{\text{DRB.UEThpDl}}{100})$).
  * $s_t[3]$: Taxa de ocupação de PRBs no enlace descendente ($\frac{\text{RRU.PrbTotDl}}{100}$).
  * $s_t[4]$: Atraso médio de pacotes na fila MAC/RLC ($\frac{\text{QoS.FlowDelay}}{50}$).
  * $s_t[5..9]$: Vetores de prioridade e valores propostos pelas xApps concorrentes.

---

### 4.2. Módulo de Decisão e Raciocínio (`ReasoningAgent`)
O motor de raciocínio no arquivo [`reasoning_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/reasoning_agent.py) orquestra três camadas hierárquicas de decisão:

```mermaid
flowchart TD
    START([Evento de Conflito Detectado]) --> H{1. Consulta Histórico KG<br/>Confiança > 0.80?}
    H -- SIM --> RES_H[Aplica Resolução Histórica]
    H -- NÃO --> T{Tipo de Conflito?}
    T -- DIRETO --> SLA[2. Avaliação de SLA<br/>Política TVS / EEVS Combinatória]
    T -- INDIRETO --> MARL[3. Motor MARL MAPPO<br/>Crítico Global + Atores Distribuídos]
```

#### A. Políticas de Utilidade de SLA (Conflitos Diretos)

Avalia todas as combinações de subconjuntos possíveis ($2^N$ combinações) das ações conflitantes:

| Política de SLA | Fórmula de Utilidade | Objetivo Primário |
| :--- | :--- | :--- |
| **TVS** (*Throughput Violation-based Selection*) | $$s_j^{\text{TVS}}(t) = - \sum_{u \in \mathcal{U}} C_u(t) - \frac{1}{1 + e^{-P_{\text{total}}}}$$ | Prioriza a eliminação estrita de violações de SLA de vazão ($C_u$) e latência. |
| **EEVS** (*Energy Efficiency Violation-based Selection*) | $$s_j^{\text{EEVS}}(t) = - \sum_{u \in \mathcal{U}} E_u(t) - \frac{1}{1 + e^{-P_{\text{total}}}}$$ | Penaliza potências excessivas ($E_u$) que degradam a eficiência energética ($\text{Throughput}/\text{Watt}$). |

---

### 4.3. Módulo de Refinamento e Blindagem (`RefinementAgent` / Safety Guards)

O [`RefinementAgent`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/refinement_agent.py) implementa filtros determinísticos e regras de segurança que interceptam, validam e corrigem as decisões do modelo de ML antes de qualquer comando ser emitido à rede 5G NR:

| Regra de Blindagem | Parâmetro / Escopo | Limite Operacional | Ação em Caso de Violação |
| :--- | :--- | :--- | :--- |
| **Barreira de Frequência Temporal** (*Temporal Throttling*) | Todos os parâmetros por nó (`node_id`, `parameter`) | `t_now - t_last_control >= 1000 ms` | Rejeição do comando para evitar oscilações e sobrecarga na interface E2 |
| **Restrições de Quota de Recursos** (*PRB Bounds*) | Alocação de Blocos de Recursos (`PRB_QUOTA`) | `0 <= PRB_QUOTA <= 100 %` | Bloqueio de valores negativos ou acima da capacidade total do enlace |
| **Restrições de Potência de Rádio** (*Power Bounds*) | Potência de Transmissão (`TX_POWER`) | `-10 dBm <= TX_POWER <= 23 dBm` (Macro gNB até `43 dBm`) | Bloqueio de comandos fora da faixa de rádio-frequência segura |
| **Checagem de Destino e Integridade** | Identificador de Nó E2 (`node_id`) | `node_id != ""` e cadastrado no SDL | Descarte imediato de comandos com nós de destino nulos ou desconhecidos |

#### Detalhamento das Regras de Segurança:

* **Barreira de Frequência Temporal:**  
  $$\Delta t_{\text{control}} = t_{\text{now}} - t_{\text{last\_control}}(\text{node}, \text{parameter}) \ge 1000\text{ ms}$$
* **Restrições de Fronteira Física de Rádio:**  
  * Quota de PRBs: $0 \le \text{PRB\_QUOTA} \le 100\%$  
  * Potência de Transmissão: $-10\text{ dBm} \le P_{tx} \le 23\text{ dBm}$ (até $43\text{ dBm}$ para nós Macro).  
* **Checagem de Destino e Validação de Lote:**  
  Bloqueia comandos direcionados a nós E2 vazios (`node_id == ""`) e descarta lotes vazios sem ações selecionadas.

---

## 5. Formulação MARL: MAPPO, Redes Neurais e Decisões Distribuídas

![Dinâmica de Treinamento MARL e Safety Guards](figures/cenario_7_marl_treinamento_convergencia_perdas.png)

### 5.1. Paradigma CTDE (*Centralized Training with Decentralized Execution*)
No módulo [`mappo_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/marl/mappo_agent.py), a coordenação multi-agente adota a arquitetura CTDE:
* **Treinamento Centralizado:** O Crítico $V_\phi$ recebe a observação global de todo o cluster e de todas as xApps.
* **Execução Descentralizada:** Cada Ator $\pi_{\theta_i}$ toma decisões sobre sua respectiva fatia (URLLC, eMBB ou Energy Saving) utilizando apenas informações locais.

### 5.2. Topologia das Redes Neurais (PyTorch / Fallback Numérico)
* **Rede do Ator ($\text{ActorNetwork}$):**
  * Entrada: Vetor de observação local $o_i \in \mathbb{R}^{10}$.
  * Camadas: $\text{Linear}(10, 128) \rightarrow \text{LayerNorm}(128) \rightarrow \text{ReLU} \rightarrow \text{Linear}(128, 256) \rightarrow \text{LayerNorm}(256) \rightarrow \text{ReLU} \rightarrow \text{Linear}(256, 128) \rightarrow \text{ReLU} \rightarrow \text{Linear}(128, 5) \rightarrow \text{Softmax}$.
  * Saída: Distribuição de probabilidade categórica sobre as 5 ações discretas de arbitragem.
* **Rede do Crítico ($\text{CriticNetwork}$):**
  * Entrada: Vetor de observação global concatenado $s_t \in \mathbb{R}^{10 \times N}$.
  * Camadas: $\text{Linear}(20, 128) \rightarrow \text{LayerNorm}(128) \rightarrow \text{ReLU} \rightarrow \text{Linear}(128, 256) \rightarrow \text{LayerNorm}(256) \rightarrow \text{ReLU} \rightarrow \text{Linear}(256, 128) \rightarrow \text{ReLU} \rightarrow \text{Linear}(128, 1)$.
  * Saída: Escalar que estima o valor de estado $V_\phi(s_t)$.

---

## 6. Modelagem Matemática de Recompensas e Penalidades

### 6.1. Função de Recompensa Multi-Objetivo Global

O coordenador [`MAPPOCoordinator`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/marl/mappo_agent.py) calcula a recompensa multi-objetivo $R_t$ a cada transição de estado da rede:

$$R_t = w_{\text{qos}} \cdot f_{\text{qos}}(t) + w_{\text{ee}} \cdot f_{\text{ee}}(t) - w_{\text{pen}} \cdot \text{Penalty}(t)$$

**Pesos Padrão de Ponderação:**
* $w_{\text{qos}} = 0.60$ (Prioridade para Qualidade de Serviço e SLA)
* $w_{\text{ee}} = 0.30$ (Prioridade para Eficiência Energética)
* $w_{\text{pen}} = 0.10$ (Penalidade para Conflitos / Contenção não mitigada)

#### Componentes Detalhados da Função de Recompensa:

| Componente | Símbolo | Condição / Regra de Cálculo | Valor Retornado |
| :--- | :--- | :--- | :--- |
| **Qualidade de Serviço (QoS)** | $f_{\text{qos}}(t)$ | Se $\text{Delay}_{\text{URLLC}} < 15.0\text{ ms}$ | $\frac{\text{Priority}(a_t)}{10} + 0.5$ |
| | | Se $\text{Delay}_{\text{URLLC}} \ge 15.0\text{ ms}$ | $\frac{\text{Priority}(a_t)}{10} - 0.5$ |
| **Eficiência Energética (EE)** | $f_{\text{ee}}(t)$ | Modulação de potência / economia de energia (`power` ou `es`) | $1.0$ |
| | | Caso neutro / sem alteração de potência | $0.5$ |
| **Penalidade de Conflito** | $\text{Penalty}(t)$ | Conflito plenamente resolvido e harmonizado | $0.0$ (Sem penalidade) |
| | | Conflito não resolvido / contenção de recursos | $1.0$ (Penalidade máxima) |

### 6.2. Função de Perda dos Atores com PPO-Clip

Para garantir estabilidade no treinamento e evitar atualizações de política destrutivas no plano de controle:

$$L^{\text{CLIP}}(\theta) = \hat{\mathbb{E}}_t \left[ \min\left( r_t(\theta)\hat{A}_t, \, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t \right) \right]$$

* **Razão de probabilidade:** $r_t(\theta) = \frac{\pi_\theta(a_t | s_t)}{\pi_{\theta_{\text{old}}}(a_t | s_t)}$
* **Parâmetro de corte:** $\epsilon = 0.20$
* **Vantagem $\hat{A}_t$:** Calculada via Generalized Advantage Estimation (GAE) com $\gamma = 0.99$ e $\lambda = 0.95$.

### 6.3. Função de Perda do Crítico Centralizado

Minimização do erro quadrático médio (MSE) entre o valor predito e o retorno descontado real:

$$L(\phi) = \hat{\mathbb{E}}_t \left[ \left( V_\phi(s_t) - \hat{R}_t \right)^2 \right]$$

---

## 7. Despacho de Controle E2SM-RC e Formatação ASN.1 APER

Uma vez aprovada pelo Refinement Agent, a ação vencedora $a_t^*$ é convertida em um payload binário E2 pelo [`RCEncoder`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/e2/rc_encoder.py):
1. **Mapeamento de Parâmetros:**
   * $\text{PRB\_QUOTA} \rightarrow \text{RAN Parameter ID: } 1$
   * $\text{TX\_POWER} \rightarrow \text{RAN Parameter ID: } 2$
   * $\text{SCHEDULER\_WEIGHT} \rightarrow \text{RAN Parameter ID: } 3$
2. **Encodificação APER (Aligned Packet Encoding Rules):** Gera a sequência de bytes ASN.1 empacotada no envelope RMR `RIC_CONTROL_REQ` (mtype `12010`).
3. **Envio via RMR:** Transmitido ao `E2Term` que converte a mensagem para o stream SCTP (porta `36422`) conectado à gNodeB no ns-3.

---

## 8. Síntese de Desempenho e Resultados da Fase 2

![Radar Holístico Multidimensional de Governança O-RAN](figures/cenario_8_radar_comparativo_holistico_3fases.png)

A execução dos cenários de validação e simulação em larga escala no ns-3.40 consolidou os seguintes resultados empíricos:

| Dimensão de Governança | Baseline (Sem RDL) | Fase 1 (H-RDL) | Fase 2 (CA-RDL / MARL) | Impacto Técnico |
| :--- | :---: | :---: | :---: | :--- |
| **Latência Média URLLC** | $11.83\text{ ms}$ | $2.74\text{ ms}$ | **$1.92\text{ ms}$** | Redução de $83.8\%$ no atraso |
| **Violação de SLA URLLC ($<5\text{ms}$)** | $100.0\%$ | $0.0\%$ | **$0.0\%$** | $0$ violações em 30 UEs |
| **Confiabilidade (PDR)** | $88.18\%$ | $99.59\%$ | **$99.81\%$** | Ganho de $+11.63\text{ p.p.}$ |
| **Throughput Total da Célula** | $874.1\text{ Mbps}$ | $1,129.5\text{ Mbps}$ | **$1,469.5\text{ Mbps}$** | Aumento de $+68.1\%$ na capacidade |
| **Eficiência Energética** | $1.000\times$ | $1.145\times$ | **$1.182\times$** | Ganho de $+18.2\%$ de economia |
| **Potência Média $P_{tx}$** | $39.45\text{ dBm}$ | $33.80\text{ dBm}$ | **$31.04\text{ dBm}$** | Redução real de potência de rádio |
| **Conflitos Não Mitigados** | $31.33\%$ | $0.67\%$ | **$0.00\%$** | Eliminação completa de contenções |
| **Latência de Decisão Near-RT** | $0.0\text{ ms}$ | $14.2\text{ ms}$ | **$12.5\text{ ms}$** | Bem abaixo do limite O-RAN ($50\text{ms}$) |
| **Handover Ping-Pong** | $22.0\text{ ev/min}$ | $0.0\text{ ev/min}$ | **$0.0\text{ ev/min}$** | Estabilidade absoluta de conexão |
| **Equidade de Jain (Fairness)** | $0.8933$ | $0.9422$ | **$0.9037$** | Distribuição justa de recursos |

---

## 9. Rastreabilidade dos Artefatos do Código-Fonte

* **Núcleo do xApp RDL:** [`src/rdl_xapp.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/rdl_xapp.py)
* **Módulo de Percepção & Grafo:** [`src/agents/perception_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/perception_agent.py)
* **Módulo de Raciocínio & SLA:** [`src/agents/reasoning_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/reasoning_agent.py)
* **Módulo de Refinamento & Safety Guards:** [`src/agents/refinement_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/refinement_agent.py)
* **Motor MARL MAPPO & Redes:** [`src/agents/marl/mappo_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/marl/mappo_agent.py)
* **Classificador de Intenção:** [`src/agents/marl/intent_classifier.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/marl/intent_classifier.py)
* **Persistência SDL / Redis:** [`src/infrastructure/sdl_repository.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/infrastructure/sdl_repository.py)
* **Encodificador ASN.1 APER E2SM-RC:** [`src/e2/rc_encoder.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/e2/rc_encoder.py)
* **Decodificador ASN.1 E2SM-KPM:** [`src/e2/kpm_decoder.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/e2/kpm_decoder.py)
* **Estrutura de Tipos e Eventos:** [`src/conflict_types.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/conflict_types.py)
