# xApp RDL - Fase 2: Context-Aware Resource and Decision Layer (CA-RDL / MARL)

[![Open RAN](https://img.shields.io/badge/O--RAN-Near--RT--RIC-orange.svg)](https://o-ran.org)
[![Version](https://img.shields.io/badge/Version-2.0.0-blue.svg)](https://github.com/georgebarbosa3090/XApp-RDL-F2)
[![Helm](https://img.shields.io/badge/Helm-v3%20Chart%202.0.0-informational.svg)](deploy/helm/iqos-xapp-rdl)
[![Kubernetes](https://img.shields.io/badge/K8s-Native%20Kustomize-326CE5.svg)](deploy/kubernetes)
[![MARL](https://img.shields.io/badge/AI--Engine-MAPPO%20%2F%20Actor--Critic-brightgreen.svg)](src/agents/marl)
[![Tests](https://img.shields.io/badge/Tests-18%2F18%20Passing-success.svg)](tests/)

---

### Navegação Multi-Fases do Projeto RDL (Resource and Decision Layer)

| Fase do Projeto | Descrição e Paradigma de Controle | Status de Implementação | Repositório Oficial |
| :---: | :--- | :---: | :---: |
| **Fase 1** | **RDL Determinística e Segura (H-RDL)**<br/>*Janela em lote (200ms), heurísticas TVS/EEVS e Safety Guards físicos.* | **Concluída e Operacional** | [georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1) |
| **Fase 2 (Atual)** | **RDL Baseada em Contexto (CA-RDL)**<br/>*Aprendizado por Reforço Multiagente (MARL / MAPPO) e cognição contextual.* | **Ativa / Em Produção** | [georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2) |
| **Fase 3** | **RDL Autônoma e Federada 6G (Zero-Touch)**<br/>*Inteligência distribuída, orquestração por intenção (Intent-Driven) e O-Cloud 6G.* | **Roadmap / Planejada** | *Em especificação futura* |

---

## 1. Visão Geral da Fase 2 (CA-RDL)

A **xApp RDL Fase 2 (Context-Aware RDL)** é o motor de arbitragem cognitiva e autônoma de conflitos para o **Near-RT RIC (RAN Intelligent Controller)** do ecossistema O-RAN.

Evoluindo a abordagem determinística da Fase 1, a Fase 2 introduz **Aprendizado por Reforço Multi-Agente (MARL / MAPPO - Multi-Agent Proximal Policy Optimization)** com observação centralizada de telemetria de rádio (E2SM-KPM) e execução descentralizada de ações de controle (E2SM-RC), governando as decisões emitidas por **3 xApps de referência abertas da literatura**:

1. **xSlice (QoS & Slicing Optimizer) — [peihaoY/xslice-oran](https://github.com/peihaoY/xslice-oran):** Solicita cotas elevadas de PRBs (PRB_QUOTA = 80%, prioridade 90) para fatias URLLC/eMBB.
2. **Energy Saving (Green RAN Optimizer) — [Orange-OpenSource/ns-O-RAN-flexric](https://github.com/Orange-OpenSource/ns-O-RAN-flexric):** Solicita redução de potência (TX_POWER = 20 dBm, prioridade 65) e sono de células.
3. **Traffic Steering (Mobility Optimizer) — [o-ran-sc/ric-app-ts](https://github.com/o-ran-sc/ric-app-ts):** Solicita migração e balanceamento de tráfego (HANDOVER, prioridade 80).

`	ext
       +-------------------------------------------------------------+
       |             Near-RT RIC Platform (ricplt / O-RAN)           |
       |  [E2Term / SCTP 36422]  <-->  [Redis DBAAS / SDL 6379]      |
       +------------------------------+------------------------------+
                                      |
                         RMR Message Router (JSON / APER)
                                      |
       +------------------------------v------------------------------+
       |           xApp CA-RDL (Fase 2: MARL / MAPPO) (ricxapp)      |
       |                                                             |
       |  1. PerceptionAgent  --> Deteccao de Conflitos e Features   |
       |  2. ReasoningAgent   --> Redes Neurais Actor-Critic (MAPPO) |
       |  3. RefinementAgent  --> Safety Guards Físicos Rigorosos    |
       +------------------------------+------------------------------+
                                      |
       +------------------------------+------------------------------+
       |            3 Reference xApps Concorrentes (ricxapp)         |
       |  - xSlice QoS (:8082)       - Energy Saving (:8084)         |
       |  - Traffic Steering (:8086)                                 |
       +-------------------------------------------------------------+
`

---

## 2. Estrutura do Repositório

`	ext
.
├── configs/                     # Descritores de configuração xApp (config-file.json, routes.rt)
├── deploy/                      # Manifestos de Implantação
│   ├── helm/                    # Helm Charts oficiais (RDL, xSlice, Energy Saving, Traffic Steering)
│   └── kubernetes/              # Manifestos K8s puros (Near-RT RIC ricplt + 3 xApps + RDL ricxapp)
├── docs/                        # Portal de Documentação Técnica (Volumes 01 a 07)
│   └── README.md                # Índice e trilhas de leitura da documentação
├── reference-xapps/             # Adaptadores leves das 3 xApps de referência abertas
│   ├── qos-xslice/              # Baseado em peihaoY/xslice-oran
│   ├── energy-saving/           # Baseado em Orange-OpenSource/ns-O-RAN-flexric
│   └── traffic-steering/        # Baseado em o-ran-sc/ric-app-ts
├── scripts/                     # Automação de Deploy, Testes e Verificação
│   ├── deploy_helm.sh           # Pipeline Helm (Near-RT RIC -> 3 xApps -> RDL)
│   ├── deploy_k8s.sh            # Pipeline K8s/Kustomize equivalente
│   └── verify_3_xapps.sh        # Smoke test unificado de todas as xApps
├── src/                         # Código-Fonte Python da xApp CA-RDL
│   ├── agents/                  # Agentes de Percepção, Raciocínio e Refinamento
│   │   └── marl/                # Motor MAPPO / Actor-Critic e Intent Classifier
│   ├── e2/                      # Codecs ASN.1 APER (E2AP, KPM, RC)
│   └── observability/           # Servidores FastAPI (Health na 8080, Métricas na 8081)
├── tests/                       # Suíte de Testes Unitários com pytest (18/18 PASS)
└── Makefile                     # CLI unificada de operação, testes e benchmarks
`

---

## 3. Guia Rápido de Execução e Deploy

### Opção A: Deploy Governança Completa (Near-RT RIC + 3 Reference xApps + CA-RDL)
`ash
make helm-deploy
`

### Opção B: Deploy Baseline (Near-RT RIC + 3 Reference xApps SEM RDL)
`ash
make helm-deploy-baseline
`

### Opção C: Validação e Smoke Test das xApps
`ash
make test-3xapps
`

### Opção D: Testes Unitários e Validação de CI
`ash
make test
# Saída esperada: 18 passed in 0.45s (100% green)
`
