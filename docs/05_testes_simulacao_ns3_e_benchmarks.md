# Volume 05: Guia de Simulação 5G NR no ns-3, Testes e Benchmarks Científicos

**Documento:** Volume Temático 05  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Co-Simulação 5G NR no ns-3 (5G-LENA + NORI), Execução em Tempo Real dos 2 Cenários de Conflito, Conexão E2 ao Near-RT RIC, Pipeline de Benchmarks e Análise de ML  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Arquitetura da Co-Simulação ns-3 / 5G-LENA

A validação experimental é realizada com o simulador de eventos discretos **ns-3 v3.40** integrado aos módulos:
* **5G-LENA (CTTC-LENA NR):** Pilha completa 3GPP Release 15/16/17 (PHY, MAC, RLC, PDCP, SDAP, BWP, Beamforming e Canais 3GPP TR 38.901).
* **ns-O-RAN / NORI:** Implementação do agente E2 na gNodeB com protocolo SCTP para o Near-RT RIC.
* **NrPointToPointEpcHelper (User Plane Core):** Roteamento IP fim a fim com tunelamento GTP-U e mapeamento de portadores de QoS (5QI).

![Arquitetura Fim-a-Fim](figures/cenario_3_arquitetura_cosimulacao_ns3_oran.png)

---

## 2. Detalhamento e Execução dos 2 Cenários de Conflito em Tempo Real

A validação experimental da Fase 2 contempla **dois cenários críticos de contenção de rádio**:

### 2.1. Cenário 1: Conflito Economia de Energia vs QoS / Slicing (EEVS)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_energy_vs_qos.cc`](file:///simulations/ns3/scenario_rdl_energy_vs_qos.cc)
* **Dinâmica:** A xApp `ricxapp-energy-saving` propõe redução de potência de transmissão (`TX_POWER`) e throttling de PRB para reduzir consumo elétrico, colidindo frontalmente com a xApp `ricxapp-qos-xslice`, que exige garantia de SLA com baixa latência para fatias URLLC e alto throughput para eMBB.
* **Topologia:** 1 Macro gNB (Banda Alta) + 1 Micro gNB (Small Cell), 20 UEs com carga dinâmica.
* **Comando para Execução Visível no Console:**
```bash
cd ~/ns3-oran-workspace/ns-3-oran
cp /caminho/para/simulations/ns3/scenario_rdl_energy_vs_qos.cc scratch/
export NS_LOG="ScenarioRdlEnergyVsQos=level_all"
./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"
```

---

### 2.2. Cenário 2: Conflito Traffic Steering vs QoS / Handover Ping-Pong (TVS)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_tvs_conflict.cc`](file:///simulations/ns3/scenario_rdl_tvs_conflict.cc)
* **Dinâmica:** A xApp `ricxapp-traffic-steering` tenta balancear carga forçando handovers de UEs entre as duas células, gerando risco de instabilidade, handover ping-pong e degradação severa da fatia URLLC gerida pela xApp `ricxapp-qos-xslice`.
* **Topologia:** 2 gNodeBs separadas por 80 metros, 30 UEs divididos em 3 fatias de rede (URLLC 5QI 82, eMBB 5QI 9, mMTC 5QI 79).
* **Comando para Execução Visível no Console:**
```bash
cd ~/ns3-oran-workspace/ns-3-oran
cp /caminho/para/simulations/ns3/scenario_rdl_tvs_conflict.cc scratch/
export NS_LOG="ScenarioRdlTvsConflict=level_all"
./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"
```

---

## 3. Parâmetros Reais dos Cenários em C++

| Parâmetro | Valor Configurado no C++ | Justificativa Técnica |
| :--- | :--- | :--- |
| **Dimensões do Cenário** | `200.0 m x 120.0 m` | Grid espacial delimitado para contenção e alta interferência intercelular (ICI). |
| **Topologia de gNodeBs** | `2 gNodeBs` (Macro gNB 1 em X=60m, Micro gNB 2 em X=140m) | Distância intercelular de `80.0 m` com sobreposição de feixes. |
| **Altura das Antenas** | Base Station: `25.0 m` \| Usuários (UEs): `1.5 m` | Alturas padrão 3GPP TR 38.901 Urban Microcell (UMi). |
| **Espectro / Portadora** | `3.5 GHz` (Banda n78 FR1), Canal de `100 MHz` | Frequência canônica de 5G NR comercial no Brasil e Europa. |
| **Numerologia ($\mu$)** | $\mu=1$ (`SCS = 30 kHz`), Slot = `0.5 ms` | Latência reduzida de subquadro para atendimento a fluxos URLLC. |
| **Total de Usuários (UEs)** | `30 UEs` (15 por gNodeB) | 10 UEs URLLC (5QI 82), 10 UEs eMBB (5QI 9), 10 UEs mMTC (5QI 79). |
| **Interface E2 O-RAN** | Porta SCTP `36422` | Conexão de controle Near-RT com o E2Term do Near-RT RIC. |

![Topologia Espacial 2D](figures/cenario_1_topologia_tvs_conflict.png)

---

## 4. Execução da Suíte Experimental e Benchmarks no Prompt

Para processar a suíte experimental completa e acompanhar as tabelas de métricas ao vivo no console:
```bash
# No Linux / WSL2:
python3 scripts/evaluate_and_improve_algorithms.py
python3 scripts/run_experiment_suite.py
```
```powershell
# No Windows (PowerShell / CMD):
python scripts/evaluate_and_improve_algorithms.py
python scripts/run_experiment_suite.py
```

Os artefatos gerados são salvos em `experiments/results/YYYY-MM-DD/run_HHMMSS/` e espelhados em `experiments/results/latest/`:
* `dataset_flow_metrics.csv`: Métricas de cada fluxo de QoS extraídas do FlowMonitor.
* `dataset_rdl_decisions_ml.csv`: Decisões de arbitragem e atributos de rádio por janela de tempo.
* `relatorio_comparativo.json`: Consolidação de métricas científicas em JSON.
* `relatorio_comparativo.md`: Relatório executivo em Markdown.
* `relatorio_comparativo_detalhado.md`: Avaliação estatística completa com benchmarks de 6 modelos de ML.
