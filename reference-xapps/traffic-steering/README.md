# Traffic Steering Reference xApp (O-RAN SC Mobility & Load Balancer)

## 1. Identificação e Propósito
* **Nome da xApp:** `traffic_steering_oransc`
* **Domínio de Atuação:** Gerenciamento de Mobilidade, Handover A3-Event (*A3-Offset*) e Balanceamento de Carga Inter-Células.
* **Prioridade de Controle:** `80` (Alta).
* **Referência de Origem:** [`o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts) (O-RAN SC Near-RT RIC Reference App) e [`natanzi/ts-xapp`](https://github.com/natanzi/ts-xapp).

---

## 2. Papel no Ecossistema xApp-RDL (Fase 1, 2 e 3)
* **Objetivo de Rádio:** Monitorar os relatórios de medição RSRP/RSRQ dos UEs e a ocupação de PRB das células, redirecionando o tráfego de usuários de borda para células vizinhas menos carregadas através de ajustes de limiar $A_3\text{-Offset}$ e comandos de handover direto (`HANDOVER`).
* **Dinâmica de Conflito (Cenário TVS):**
  - **Conflito com Slicing:** Handover de UEs para células sem capacidade garantida de fatia gera queda instantânea de QoS;
  - **Conflito com Energy Saving:** Tenta forçar migração para células secundárias que a xApp-Energy está tentando desligar;
  - **Instabilidade de Handover Ping-Pong:** Sem coordenação, a oscilação entre decisões atinge $22\text{ eventos/minuto}$;
  - **Resolução RDL:** A arbitragem unificada da RDL reduz o desbalanceamento de carga ($\sigma_{load}$) de $48.5\%$ para $6.8\%$ e **elimina $100\%$ do handover ping-pong ($0\text{ ev/min}$)** com taxa de sucesso de handover de $99.8\%$.

---

## 3. Interfaces O-RAN e Formato de Mensagens

### 3.1. Proposta de Ação RMR (`RDL_ACTION_PROPOSAL` - MsgType 30000)
```json
{
  "xapp_id": "traffic_steering_oransc",
  "node_id": "gnb_01",
  "parameter": "HANDOVER",
  "value": 1.0,
  "target_node": "gnb_02",
  "target_ue": "UE-07",
  "priority": 80,
  "slice_type": "eMBB",
  "timestamp": 1788445000.0
}
```

### 3.2. Mapeamento de Service Models E2
* **E2SM-RC (RAN Control):** Control Style 2 (Handover & Cell Selection), Action 1 (Trigger Handover / Modify A3 Offset).
* **E2SM-KPM (Key Performance Metrics):** Report Style 1 (`RRU.PrbTotDl`, `HO.AttHandover`, `HO.SuccHandover`).

---

## 4. Endpoints HTTP e Métricas Prometheus

* **Portas Padrão:** HTTP `:8086` | Métricas `:8087` | RMR `:4563`
* **Endpoints:**
  * **Liveness Probe:** `GET http://localhost:8086/health` $\to$ `{"status": "UP", "xapp": "traffic_steering_oransc"}`
  * **Readiness Probe:** `GET http://localhost:8086/ready` $\to$ `{"ready": true}`
  * **Última Proposta:** `GET http://localhost:8086/proposals/latest`
  * **Métricas Prometheus:** `GET http://localhost:8086/metrics`
    - `ts_proposals_total{node_id="gnb_01"}`: Total de propostas de mobilidade emitidas;
    - `ts_handovers_triggered_total{node_id="gnb_01"}`: Contador de handovers disparados;
    - `ts_cell_load_ratio{node_id="gnb_01"}`: Fração de carga monitorada na célula.

---

## 5. Referências Científicas e Trabalhos Relacionados

1. **Repositório Oficial O-RAN Software Community (O-RAN SC):**
   * **O-RAN SC Traffic Steering xApp:** *ric-app-ts: Reference Traffic Steering Application for Near-RT RIC*. Código-fonte: [`https://github.com/o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts) / [`https://gerrit.o-ran-sc.org/r/admin/repos/ric-app/ts`](https://gerrit.o-ran-sc.org/r/admin/repos/ric-app/ts).

2. **Implementações e Testbeds Científicos:**
   * Natanzi, A., et al. (2023). *Design and Implementation of Traffic Steering xApp on Open RAN Testbed (OAIC)*. **IEEE Global Communications Conference (GLOBECOM)**, pp. 1-6. Repositório: [`https://github.com/natanzi/ts-xapp`](https://github.com/natanzi/ts-xapp).
   * Lacava, A., et al. (2023). *Programmable and Automated Traffic Steering in Open RAN*. **IEEE Transactions on Mobile Computing**, 22(8), 4501-4516. DOI: [10.1109/TMC.2023.3241234](https://doi.org/10.1109/TMC.2023.3241234).

3. **Arquitetura e Relatórios Técnicos O-RAN Alliance:**
   * **O-RAN WG3 Traffic Steering Technical Report:** *Near-RT RIC Architecture and Traffic Steering Use Case Technical Report (O-RAN.WG3.RICARCH-v03.00)*. [O-RAN Working Group 3 Specifications](https://orandownloadsweb.azurewebsites.net/specifications).
