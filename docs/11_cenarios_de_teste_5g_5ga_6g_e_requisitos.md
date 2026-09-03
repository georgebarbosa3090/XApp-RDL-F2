# Volume 11: Especificação de Cenários de Teste 5G, 5G-Advanced e 6G, Características e Requisitos Técnicos

## Projeto xApp RDL — Roadmap de Avaliação Experimental e Benchmarks

---

## 1. Visão Geral e Taxonomia dos Cenários de Teste

Este documento formaliza a suíte de cenários de teste para validação da **xApp-RDL** em ambientes de co-simulação e bancada física, cobrindo o espectro evolutivo de **5G NR**, **5G-Advanced (3GPP Rel. 18/19)** e **6G AI-Native (IMT-2030)**.

```mermaid
graph LR
    subgraph S5G["1. 5G NR Baseline"]
        C1["EEVS: Energy vs QoS<br/>(Potência & SLA URLLC)"]
        C2["TVS: Traffic Steering vs Slicing<br/>(Handover & Quotas PRB)"]
    end

    subgraph S5GA["2. 5G-Advanced (Rel. 18/19)"]
        C3["Multi-Carrier FR1/FR3 + Massive MIMO<br/>(3 gNBs, 60 UEs, UPA 16x4, Slicing)"]
    end

    subgraph S6G["3. 6G AI-Native (IMT-2030)"]
        C4["ISAC: Radar Sensing vs Comunicação<br/>(28 GHz mmWave, Contenção de Feixe)"]
        C5["Cross-Tier & Anti-Rogue Shield<br/>(Multi-Loop rApp-xApp-dApp, Lockout 5s)"]
    end

    S5G --> S5GA
    S5GA --> S6G
```

---

## 2. Detalhamento dos Cenários de Teste e Código-Fonte `.cc`

### 2.1. Cenários 5G NR (Fase 1 e Fase 2)

#### Cenário 1: EEVS (Eficiência Energética vs. Garantia de SLA URLLC)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_energy_vs_qos.cc`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/simulations/ns3/scenario_rdl_energy_vs_qos.cc)
* **Topologia:** 1 Macro gNB (Banda n78 $3.5\text{ GHz}, 50\text{ MHz}$) + 1 Small Cell, 20 UEs com carga dinâmica.
* **Conflito:** `xApp-Energy` tenta reduzir potência de transmissão para $15\text{ dBm}$ enquanto `xApp-QoS` exige potência $> 23\text{ dBm}$ para manter atraso URLLC $< 5\text{ ms}$.
* **Resolução RDL:** Nível 2A (Função de utilidade EEVS com penalidade sigmoide de potência).

#### Cenário 2: TVS (Traffic Steering vs. Slicing e Handover)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_tvs_conflict.cc`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/simulations/ns3/scenario_rdl_tvs_conflict.cc)
* **Topologia:** 2 gNBs adjacentes com zona de sobreposição e 30 UEs divididos em 3 fatias (URLLC 5QI 82, eMBB 5QI 9, mMTC 5QI 79).
* **Conflito:** `xApp-TrafficSteering` força handover de UEs de borda por carga, enquanto `xApp-Slicing` altera quotas de PRB, gerando instabilidade na fronteira.
* **Resolução RDL:** Nível 2A/2B (TVS e MAPPO) eliminando 100% dos eventos de *handover ping-pong*.

---

### 2.2. Cenário 5G-Advanced: Multi-Carrier, Massive MIMO e Fatiamento Dinâmico

* **Arquivo C++:** [`simulations/ns3/scenario_rdl_5ga_multicarrier_mimo.cc`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/simulations/ns3/scenario_rdl_5ga_multicarrier_mimo.cc)
* **Topologia & Espectro:**
  - 3 gNBs em corredor urbano UMi ($1000\text{ m} \times 400\text{ m}$, ISD $500\text{ m}$);
  - Espectro Multi-Portadora: FR1 ($3.5\text{ GHz}, 100\text{ MHz}, 273\text{ PRBs}$) + FR3 Upper Mid-Band ($10.5\text{ GHz}, 200\text{ MHz}$);
  - Antenas Massive MIMO UPA $16 \times 4$ (64 elementos com controle de *vertical downtilt* na gNB) e $2 \times 2$ (UEs);
  - 60 UEs sob mobilidade heterogênea (20 Estáticos, 20 Pedestres a $3-5\text{ km/h}$, 20 Veiculares a $54\text{ km/h}$).
* **xApps Envolvidas:**
  1. `xApp-Beamformer`: Modifica tilt elétrico e pesos de feixe (E2SM-RC Style 10 Action 2);
  2. `xApp-TrafficSteering`: Redireciona UEs via $A_3\text{-Offset}$ (E2SM-RC Style 3 Action 2);
  3. `xApp-PRBQuota` (ORIGAMI PIOR): Aloca quotas dinâmicas `RRMPolicyRatio` (E2SM-RC Style 1 Action 1).
* **Mecanismo de Arbitragem:** Escalonamento Híbrido com **MAPPO sob CTDE** (Nível 2B): O Crítico Centralizado avalia a interferência intercelular global e orienta os Atores locais.

---

### 2.3. Cenários 6G AI-Native (IMT-2030)

#### Cenário 4: Coexistência ISAC (Sensoriamento Radar vs. Comunicação de Dados)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_6g_isac_sensing_coexistence.cc`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/simulations/ns3/scenario_rdl_6g_isac_sensing_coexistence.cc)
* **Topologia & Frequência:** 2 gNBs ISAC Dual-Function operando em $28\text{ GHz}$ mmWave ($400\text{ MHz}$ de largura de banda) com 30 UEs de dados e alvos de rastreamento radar em movimento.
* **Conflito:** Competição direta por símbolos OFDM e feixes de transmissão entre a `xApp-RadarSensing` (exige resolução fina $\Delta R = \frac{c}{2B}$) e a `xApp-eMBB-Plus` (demanda vazão $> 1\text{ Gbps}$).
* **Mecanismo de Arbitragem:** **Safe-RL com CMDP (Constrained MDP)** garantindo restrição mínima de probabilidade de detecção de radar ($P_d \ge 95\%$) enquanto maximiza a taxa de comunicação.

#### Cenário 5: Governança Cross-Tier e Escudo Anti-Rogue xApp
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_6g_cross_tier_governance.cc`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/simulations/ns3/scenario_rdl_6g_cross_tier_governance.cc)
* **Topologia & Operação:** Grade $2 \times 2$ com 4 gNBs e 40 UEs sob alta carga estocástica. Injeção de ações conflitantes de alta frequência ($5\text{ Hz}$) geradas por uma `xApp-Rogue-Vendor`.
* **Mecanismo de Arbitragem:** Ativação da **Janela de Resfriamento (*Lockout Cooling Window*) de 5 s** e atuação do **Safety Guard Invariante**, eliminando completamente o *parameter flipping* e mantendo estabilidade operacional.

---

## 3. Matriz Completa de Métricas de Avaliação

| Dimensão de Análise | Métrica Específica | Unidade | Cenário Alvo | Meta / Valor de Referência |
| :--- | :--- | :---: | :---: | :---: |
| **QoS & Latência Telecom** | Latência Média URLLC | $\text{ms}$ | 5G / 5GA / 6G | $< 2.0\text{ ms}$ |
| | Latência Percentil 99 (P99) | $\text{ms}$ | 5G / 5GA / 6G | $< 3.0\text{ ms}$ |
| | Taxa de Violação de SLA | $\%$ | Todos | $\mathbf{0.0\%}$ |
| | Throughput Agregado | $\text{Mbps} / \text{Gbps}$ | 5GA / 6G ISAC | $+20\%$ a $+50\%$ vs. Baseline |
| | Packet Delivery Ratio (PDR) | $\%$ | Todos | $\ge 99.85\%$ |
| **Sustentabilidade & Energia** | Eficiência Energética (EE) | $\text{Bits/Joule}$ | EEVS / 5GA | $+18.2\%$ a $+60\%$ (COMIX) |
| | Redução de Consumo de Potência | $\%$ | EEVS / 5GA | $-30\%$ a $-60\%$ |
| **Governança & Estabilidade** | Eficiência de Arbitragem | $\%$ | Todos | $\mathbf{100.0\%}$ |
| | Handover Ping-Pong | $\text{ev/min}$ | TVS / 5GA | $\mathbf{0\text{ ev/min}}$ |
| | Oscilações (*Parameter Flipping*) | $\text{eventos}$ | 6G Cross-Tier | $\mathbf{0\text{ com Lockout 5s}}$ |
| | Macro-F1 de Classificação | $\%$ | Todos | $> 99.4\%$ (SMOTE-GNN) |
| **Sensoriamento ISAC (6G)** | Resolução de Distância ($\Delta R$) | $\text{metros}$ | 6G ISAC | $< 0.5\text{ m}$ |
| | Probabilidade de Detecção ($P_d$) | $\%$ | 6G ISAC | $\ge 95\%$ |
| **Performance do Sistema / ML** | Latência de Decisão Near-RT | $\text{ms}$ | Todos | $< 15\text{ ms}$ (Python) / $< 1\text{ ms}$ (C++) |
| | Fidelidade Preditiva do Gêmeo | $\%$ | Todos | $> 90.7\%$ (XGBoost 5s) |

---

## 4. Instruções de Compilação e Execução no ns-3

Para compilar e executar os novos cenários C++ no ambiente do simulador:

```bash
# 1. Copiar cenários para o diretório scratch do ns-3
cp simulations/ns3/scenario_rdl_5ga_multicarrier_mimo.cc ~/ns3-oran-workspace/ns-3-oran/scratch/
cp simulations/ns3/scenario_rdl_6g_isac_sensing_coexistence.cc ~/ns3-oran-workspace/ns-3-oran/scratch/
cp simulations/ns3/scenario_rdl_6g_cross_tier_governance.cc ~/ns3-oran-workspace/ns-3-oran/scratch/

# 2. Configurar e compilar via CMake / Ninja
cd ~/ns3-oran-workspace/ns-3-oran
./ns3 configure --build-profile=optimized -G Ninja
./ns3 build scratch/scenario_rdl_5ga_multicarrier_mimo \
            scratch/scenario_rdl_6g_isac_sensing_coexistence \
            scratch/scenario_rdl_6g_cross_tier_governance

# 3. Execução individual com passagem dinâmica de sementes e flags
./ns3 run "scratch/scenario_rdl_5ga_multicarrier_mimo --seed=42 --enableE2=true"
./ns3 run "scratch/scenario_rdl_6g_isac_sensing_coexistence --seed=101 --sensingRatio=0.3"
./ns3 run "scratch/scenario_rdl_6g_cross_tier_governance --seed=2026 --lockout=true"
```
