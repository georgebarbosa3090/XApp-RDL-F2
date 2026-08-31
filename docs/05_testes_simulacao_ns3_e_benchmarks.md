# Volume 05: Guia de Simulação 5G NR no ns-3, Testes Automatizados e Benchmarks Científicos

**Documento:** Volume Temático 05  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Co-Simulação 5G NR no ns-3 (5G-LENA + NORI), Arquitetura EpcHelper (Plano de Usuário), Conexão E2 ao Near-RT RIC, Pipeline de Benchmarks e Análise de ML  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Arquitetura da Co-Simulação ns-3 / 5G-LENA

A validação experimental da Fase 2 é executada no simulador de eventos discretos **ns-3 v3.40** com os módulos:
* **5G-LENA (CTTC-LENA NR):** Pilha completa 3GPP Release 15/16/17 (PHY, MAC, RLC, PDCP, SDAP, BWP, Beamforming e Canais 3GPP TR 38.901).
* **ns-O-RAN / NORI:** Implementação de nós E2 Agent na gNodeB com conectividade SCTP para o Near-RT RIC.
* **NrPointToPointEpcHelper (User Plane Core):** Roteamento IP fim a fim com tunelamento GTP-U e mapeamento de portadores de QoS (5QI).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      Arquitetura de Co-Simulação ns-3 / 5G-LENA                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [Remote Host] (Servidor de Aplicações de Tráfego UDP/TCP)                            │
│         │                                                                              │
│   (Enlace Ponto a Ponto - Backhaul)                                                    │
│         │                                                                              │
│   [PGW / SGW] (Core Gateway - Instanciado via NrPointToPointEpcHelper)                 │
│         │ (Tunelamento GTP-U / S1-U / N3)                                              │
│   [gNodeB 5G NR] ◄──────── (Interface E2 / SCTP 36422) ────────► [Near-RT RIC (xApps)] │
│         │                                                                              │
│     (3.5 GHz n78 - 3GPP NR PHY/MAC/RLC/PDCP)                                           │
│         │                                                                              │
│   [UEs: URLLC / eMBB / mMTC]                                                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Por que o uso de `NrPointToPointEpcHelper` é o padrão canônico?
1. **Conformidade com a Arquitetura O-RAN:** A interface E2 termina na gNodeB (`E2AgentHelper`). O Near-RT RIC é completamente desacoplado dos microserviços de sinalização HTTP/2 SBA do 5GC.
2. **Plano de Dados Realista (GTP-U):** Encapsula os pacotes em túneis com enlace de backhaul configurável (latência e taxa), sem o overhead excessivo de emular o plano de controle SBA do Core.
3. **Mapeamento de Fatias (5QI):** Permite instanciar *Dedicated EPS/5G Bearers* com filtros TFT específicos para fluxos URLLC (5QI 82), eMBB (5QI 9) e mMTC (5QI 79).

---

## 2. Cenários de Simulação Implementados em C++

Os cenários estão disponíveis em `simulations/ns3/`:
1. **`scenario_rdl_tvs_conflict.cc`:** Conflito direto de PRBs e potência entre xSlice e Energy Saving em topologia multicelular densa (3.5 GHz Banda n78, 100 MHz, numerologia $\mu=1$).
2. **`scenario_rdl_energy_vs_qos.cc`:** Trade-off dinâmico entre economia de energia e cumprimento estrito de SLA URLLC ($<5	ext{ ms}$).

### Compilação e Execução dos Cenários no ns-3:
```bash
# 1. Configurar o ambiente ns-3 com CMake e Ninja
make setup-ns3

# 2. Executar cenário Baseline (Sem mediação RDL)
make run-baseline

# 3. Executar cenário com RDL Fase 2 (Mediação MARL via E2)
make run-rdl
```

---

## 3. Suíte de Testes Automatizados (Pytest)

A suíte unitária da Fase 2 cobre 100% dos componentes:
* Codecs APER E2AP, E2SM-KPM e E2SM-RC (`tests/test_aper_codecs.py`)
* Coordenação e Inferência MAPPO (`tests/test_marl_mappo.py`)
* Agentes de Percepção, Raciocínio e Refinamento (`tests/test_*_agent.py`)
* Tríades de conflito das Reference xApps (`tests/test_reference_xapps.py`)

```bash
# Execução dos 18 testes unitários
make test
# Saída esperada: 18 passed in < 1s (100% green)
```

---

## 4. Pipeline de Benchmarks e Estrutura de Resultados por Data

O orquestrador `scripts/run_experiment_suite.py` executa o pipeline experimental completo:
1. Coleta traces brutos (`RxPacketTrace.txt`, `flowmonitor_results.xml`, logs RDL).
2. Processa métricas de rede (latência URLLC, P95, P99, PDR, Throughput, Jain's Index).
3. Treina e valida os 6 modelos de Machine Learning / Ensembles.
4. Gera gráficos comparativos em alta resolução (300 DPI) e relatórios Markdown e JSON.
5. Salva em diretório isolado por data e timestamp: `experiments/results/YYYY-MM-DD/run_HHMMSS/` sem sobrescrever execuções anteriores.
6. Sincroniza automaticamente com o repositório GitHub (`origin main`).

### Execução da Suíte Completa:
```bash
# Executa simulação, benchmarks, ML e push para GitHub
make run-suite
# ou: python3 scripts/run_experiment_suite.py --push
```

---

## 5. Estrutura dos Resultados Gerados

```
experiments/results/
├── 2026-08-31/
│   ├── run_113445/
│   │   ├── dataset_flow_metrics.csv
│   │   ├── dataset_rdl_decisions_ml.csv
│   │   ├── relatorio_comparativo.md
│   │   ├── relatorio_comparativo_detalhado.md
│   │   ├── avaliacao_completa_metricas.json
│   │   ├── graficos_benchmarks_rdl.png
│   │   ├── comparativo_completo_cenarios_rdl.png
│   │   ├── avaliacao_modelos_ml_rdl.png
│   │   └── relatorio_tecnico_experimentos_2026-08-31.tex
└── latest/               <-- Espelho da última execução para compatibilidade
```
