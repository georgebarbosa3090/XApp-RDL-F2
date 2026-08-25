# xApp RDL (Resource and Decision Layer) — Fase 2

[![O-RAN Compliance](https://img.shields.io/badge/O--RAN-Zero_to_Hero_Compliant-blue.svg)](https://o-ran.org)
[![Python Version](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://python.org)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20%2F%20DDD-orange.svg)](#3-arquitetura-do-sistema)
[![Decision Window](https://img.shields.io/badge/Decision%20Window-200ms%20Batch-purple.svg)](#6-janela-de-decisão-decision-windowing)
[![AI Engine](https://img.shields.io/badge/AI%20Engine-MAPPO%20%2B%20TVS%2FEEVS-red.svg)](#7-cadeia-de-decisão-reasoning-chain)
[![Tests](https://img.shields.io/badge/Tests-10%2F10%20Passing-brightgreen.svg)](#12-testes-automatizados)

---

## 1. Visão Geral e Contexto da Fase 2

A **xApp RDL (Resource and Decision Layer)** é um **Orquestrador Cognitivo de Ciclo Fechado (*Closed-Loop Cognitive Arbitrator*)** projetado para operar no **Near-RT RIC (RAN Intelligent Controller)** da arquitetura **O-RAN**.

Na Fase 1 (Prova de Conceito laboratorial), as decisões eram tomadas de forma pontual e reativa no modelo *First-Come, First-Served (FCFS)* com prioridades fixas, o que causava instabilidades, efeito *ping-pong* na antena e degradação de SLA quando xApps conflitavam.

Na **Fase 2 (*Zero to Hero Refactoring*)**, a RDL evoluiu para um sistema determinístico baseado em **Domain-Driven Design (DDD)** e **Clean Architecture**, incorporando:
1. **Janela Temporal de Decisão (*Decision Windowing* de 200 ms)** para agrupamento e avaliação em lote (*batch*).
2. **Percepção Situacional por Grafo de Dependências de KPIs** cruzada com telemetria **E2SM-KPM v3** decodificada em APER ASN.1.
3. **Classificação Rigorosa de Conflitos**: Conflitos Explícitos (*DIRECT*) vs. Não-Explícitos (*INDIRECT*).
4. **Cadeia de Decisão Híbrida em Cascata**: Cache Histórico no SDL ($<10\text{ ms}$) $\rightarrow$ Avaliação Combinatória $2^N$ com Políticas de SLA (**TVS** e **EEVS**) ($<20\text{ ms}$) $\rightarrow$ IA Multi-Agente (**MAPPO**) ($<100\text{ ms}$).
5. **Camada de Refinamento (*Safety Guard*)**: Proteção física da antena, histerese anti-oscilação e limites de RF.
6. **Conformidade Estrita com os Padrões O-RAN**: Integração com AppMgr, E2 Manager, Subscription Manager, SDL Redis, Prometheus e empacotamento Docker Multi-stage Non-root.

---

## 2. O Ciclo Fechado da RDL (Closed-Loop)

A RDL atua como árbitro cognitivo no plano de controle do Near-RT RIC:

```
                          ┌───────────────────────────┐
                          │    xApps Concorrentes     │
                          │ (QoS, Energy-Saving, etc) │
                          └─────────────┬─────────────┘
                                        │ RDL_ACTION_PROPOSAL (RMR 30000)
                                        ▼
┌──────────────┐ E2SM-KPM ┌───────────────────────────┐
│              ├─────────►│   1. Buffer Temporal      │
│   E2 Node    │ (12050)  │   (Decision Window 200ms) │
│  (srsRAN gNB)│          └─────────────┬─────────────┘
│              │                        ▼
│              │          ┌───────────────────────────┐
│              │          │   2. Cadeia de Percepção  │
│              │          │  (Grafo de KPIs + Estado) │
│              │          └─────────────┬─────────────┘
│              │                        ▼
│              │          ┌───────────────────────────┐
│              │          │   3. Cadeia de Decisão    │
│              │          │ (Cache -> TVS/EEVS -> IA) │
│              │          └─────────────┬─────────────┘
│              │                        ▼
│              │          ┌───────────────────────────┐
│              │          │  4. Safety Guard / Trava  │
│              │          │ (Histerese & Limites RF)  │
│              │          └─────────────┬─────────────┘
│              │                        │
│              │◄───────────────────────┘
└──────────────┘  E2SM-RC Control Request (RMR 12010 APER)
```

---

## 3. Arquitetura do Sistema

O projeto segue estritamente a separação entre o domínio cognitivo e os adaptadores de rede O-RAN:

```
iqos-xapp-rdl-phase2/
├── configs/                  # Schemas, descritores AppMgr e rotas RMR
│   ├── config-file.json      # Configuração centralizada
│   ├── schema.json           # Schema JSON Draft-07 estrito
│   ├── xapp_descriptor.json  # Descritor oficial O-RAN AppMgr
│   └── routes.rt.template    # Template de roteamento RMR
├── deploy/kubernetes/        # Manifestos Kubernetes para Near-RT RIC
│   ├── deployment.yaml       # Deployment com liveness/readiness probes
│   └── service.yaml          # Service RMR e HTTP
├── docker/                   # Build determinístico e seguro
│   ├── Dockerfile            # Multi-stage build com usuário não-root (USER xapp)
│   └── docker-compose.yml    # Ambiente de orquestração local
├── docs/                     # Documentação e relatórios de conformidade
├── scripts/                  # Automação de rotas e coleta de evidências de testes
│   ├── collect_evidence.sh   # Coleta de evidências de experimentos
│   └── render_routes.sh      # Renderizador dinâmico de rotas RMR
├── src/
│   ├── agents/               # Motores de Inteligência e Decisão
│   │   ├── perception_agent.py   # Grafo de KPIs e detecção de conflitos
│   │   ├── reasoning_agent.py    # Decisão em cascata (Cache, TVS/EEVS, MAPPO)
│   │   ├── refinement_agent.py   # Safety Guard e validação de limites físicos
│   │   └── marl/                 # Módulo de Reinforcement Learning
│   │       ├── mappo_agent.py        # Multi-Agent PPO (PyTorch)
│   │       └── intent_classifier.py  # Classificador de intenções
│   ├── coordination/         # Despacho e controle de transações
│   │   └── control_dispatcher.py # Handshake E2SM-RC e correlação ACK/FAILURE
│   ├── e2/                   # Decodificadores e Encoders APER ASN.1
│   │   ├── e2ap_decoder.py       # Extração do envelope E2AP RIC Indication
│   │   ├── kpm_decoder.py        # Decodificador E2SM-KPM v3
│   │   └── rc_encoder.py         # Codificador E2SM-RC v1.0
│   ├── infrastructure/       # Portas e Adaptadores (Infraestrutura O-RAN)
│   │   ├── config_manager.py     # Leitura e validação de schema
│   │   ├── e2_manager_client.py  # Descoberta de nós (/v1/nodeb/states)
│   │   ├── memory_module.py      # Fallback em memória para testes
│   │   ├── sdl_repository.py     # Integração SDL com Redis
│   │   └── subscription_manager.py # Injeção REST no SubMgr
│   ├── observability/        # Monitoramento e Telemetria
│   │   ├── health_server.py      # Servidor FastAPI (/health e /ready)
│   │   ├── logging.py            # Structured logging em JSON (structlog)
│   │   └── metrics.py            # Métricas Prometheus padronizadas
│   ├── conflict_types.py     # Entidades de Domínio e Dataclasses
│   ├── main.py               # Ponto de entrada de inicialização
│   └── rdl_xapp.py           # Core da aplicação e loop de decisão
└── tests/                    # Suíte de testes automatizados (pytest)
```

---

## 4. Cadeia de Percepção & Grafo de Dependências

O [`PerceptionAgent`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/perception_agent.py) constrói o estado situacional cruzando as propostas acumuladas no lote com o histórico de parâmetros ativos e o grafo causal de impacto em KPIs:

```
[PRB_QUOTA]         ──────► [DRB.UEThpDl] (Throughput Downlink)
                            ▲  ▲
[SCHEDULER_WEIGHT]  ────────┘  │
                               │
[TX_POWER]          ───────────┴──► [L1M.DL-sinr] (Interferência / SINR)
```

- **Mapeamento Causal:** Permite rastrear como uma alteração de potência ou cota de PRBs impacta múltiplos KPIs em cascata.
- **Rastreamento por Nó:** Indexação `node_id -> parameter -> XAppAction` para detecção temporal contínua.

---

## 5. Classificação de Conflitos: Explícitos vs. Não-Explícitos

A RDL classifica os conflitos formalmente via [`ConflictType`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/conflict_types.py):

| Tipo de Conflito | Classificação | Condição de Ocorrência | Mecanismo de Detecção | Resolução Aplicada |
| :--- | :--- | :--- | :--- | :--- |
| **Explícito (`DIRECT`)** | Conflito Direto | Duas ou mais xApps tentam alterar o **mesmo parâmetro** no **mesmo nó/célula** com valores divergentes. | Colisão direta de chave: `node_a == node_b` e `param_a == param_b`. | Avaliação combinatória $2^N$ com funções de utilidade de SLA (**TVS / EEVS**). |
| **Não-Explícito (`INDIRECT`)** | Conflito Indireto / Implícito | xApps atuam sobre **parâmetros distintos**, mas que impactam os **mesmos KPIs** na camada física/MAC. | Interseção no Grafo de KPIs: $\text{KPIs}(p_a) \cap \text{KPIs}(p_b) \neq \emptyset$. | Inferência Multi-Agente **MARL (MAPPO)** para encontrar o Equilíbrio de Nash. |

---

## 6. Janela de Decisão (*Decision Windowing*)

Em vez do processamento atômico FCFS, a RDL acumula propostas recebidas no canal RMR `30000` (`RDL_ACTION_PROPOSAL`) em uma **janela temporal de 200 ms** ([`rdl_xapp.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/rdl_xapp.py)):

- **Eliminação de Race Conditions:** xApps com respostas mais rápidas não canibalizam xApps com análises mais complexas.
- **Avaliação em Lote (*Batch*):** Permite analisar todas as intenções concorrentes de forma coordenada.
- **Descoberta de Complementaridade:** Identifica subconjuntos de ações que podem ser executadas conjuntamente sem conflito, aumentando a utilidade global da célula.

---

## 7. Cadeia de Decisão (*Reasoning Chain*)

O [`ReasoningAgent`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/reasoning_agent.py) implementa um pipeline em cascata de três níveis:

```
[Conflito Detectado]
        │
        ├──► 1. Histórico Cognitivo no SDL (< 10 ms)
        │       (Reutilização se similaridade/confiança > 0.8)
        │
        ├──► 2. Conflitos Diretos: Avaliação Combinatória 2^N (< 20 ms)
        │       • TVS (Throughput Violation-based Selection):
        │         U_TVS = - ∑ C_u(t) - 1 / (1 + exp(-p_total))
        │       • EEVS (Energy Efficiency Violation-based Selection):
        │         U_EEVS = - ∑ E_u(t) - 1 / (1 + exp(-p_total))
        │
        └──► 3. Conflitos Indiretos: MARL MAPPO (< 100 ms)
                (Redes Ator-Crítico via PyTorch para dinâmicas não-lineares)
```

---

## 8. Refinamento & *Safety Guard*

O [`RefinementAgent`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/refinement_agent.py) atua como barreira de segurança antes da transmissão do comando `RIC_CONTROL_REQUEST`:

- **Histerese Anti-Ping-Pong:** Bloqueia comandos para o mesmo nó/parâmetro em intervalos inferiores a `minimum_control_interval_ms` (1000 ms).
- **Limites Operacionais Físicos:**
  - `PRB_QUOTA`: Restrito ao intervalo $[0, 100]\%$.
  - `TX_POWER`: Restrito ao envelope de RF $[-10, 23]\text{ dBm}$.
- **Validação de Destino:** Rejeita ações direcionadas a `node_id` vazio ou nós não descobertos no E2 Manager.

---

## 9. Como a Percepção de Contexto Otimiza o Projeto

A percepção de contexto (Telemetria KPM + Grafo de Dependências + Histórico SDL) permite **reduzir esforço de desenvolvimento e computação sem generalização excessiva**:

1. **Evita Sobre-Engenharia de IA:** Não sobrecarrega o Near-RT RIC rodando inferências neurais pesadas para conflitos diretos e rotineiros. O sistema resolve em $<10\text{ ms}$ via TVS/EEVS ou cache histórico, acionando o MAPPO apenas quando estritamente necessário.
2. **Redução de Sinalização na Interface E2:** Consolida múltiplas propostas na janela de 200 ms, disparando apenas um comando `E2SM-RC` unificado e seguro para a rádio-base.
3. **Foco Estrito no Domínio O-RAN:** Mantém a aderência rigorosa às normas 3GPP e O-RAN WG3 (semântica de fatiamento de rede, modelos ASN.1 e interfaces de serviço), garantindo explicabilidade e determinismo para operadoras de telecom.

---

## 10. Requisitos e Instalação

### Pré-requisitos
- Python 3.10+ (ou gerenciador `uv`)
- Docker (para build de imagem O-RAN compliant)
- Redis / O-RAN SDL (opcional para execução local com `USE_FAKE_SDL=true`)

### Instalação Rápida
```bash
# Clonar o repositório
git clone https://github.com/georgebarbosa3090/xApp-RDL-Resource-and-Decision-Layer-.git
cd iqos-xapp-rdl-phase2

# Criar ambiente virtual e instalar dependências principais
uv venv --python 3.10
uv pip install -r requirements.txt

# Instalar dependências de desenvolvimento e testes
uv pip install -r requirements-dev.txt

# (Opcional) Instalar dependências para treinamento MARL com PyTorch
uv pip install -r requirements-ml.txt
```

---

## 11. Execução

### Modo de Desenvolvimento Local
```bash
export USE_FAKE_SDL=true
export RMR_SEED_RT=configs/routes.rt.template
uv run python src/main.py
```
- **Health Check:** `http://localhost:8080/health`
- **Readiness Check:** `http://localhost:8080/ready`
- **Métricas Prometheus:** `http://localhost:8081/metrics`

### Execução de Teste de Janela Temporal (*Batching*)
```bash
uv run python scripts/test_batching.py
```

### Build do Contêiner Docker
```bash
make build
# Produz a imagem iqos-xapp-rdl:1.1.0 (Non-root, multi-stage, segura)
```

---

## 12. Testes Automatizados

A suíte de testes unitários valida integralmente a integridade dos codecs APER, a percepção situacional, as estratégias de decisão e o *Safety Guard*:

```bash
uv run pytest
```

### Resultados da Suíte:
```
tests/test_aper_codecs.py::test_e2ap_decoder_mock_fallback PASSED        [ 10%]
tests/test_aper_codecs.py::test_kpm_decoder_fallback PASSED              [ 20%]
tests/test_aper_codecs.py::test_rc_encoder_generates_bytes PASSED        [ 30%]
tests/test_perception_agent.py::test_detect_direct_conflict PASSED       [ 40%]
tests/test_perception_agent.py::test_detect_indirect_conflict PASSED     [ 50%]
tests/test_perception_agent.py::test_no_conflict PASSED                  [ 60%]
tests/test_reasoning_agent.py::test_resolve_by_tvs_priority PASSED       [ 70%]
tests/test_reasoning_agent.py::test_marl_fallback PASSED                 [ 80%]
tests/test_refinement_agent.py::test_safety_guard_out_of_bounds PASSED   [ 90%]
tests/test_refinement_agent.py::test_safety_guard_frequency_limit PASSED [100%]

============================= 10 passed in 0.45s ==============================
```

---

## 13. Referências e Normativas

- **Artigo Base:** *"Managing O-RAN Networks: xApp Development from Zero to Hero"* (2026).
- **Artigo COMIX / MLO:** *"Conflict Mitigation via Decision Windowing and SLA-based Utility in Open RAN"* (2025/2026).
- **Especificações O-RAN Alliance:**
  - O-RAN WG3: Near-RT RIC Architecture & E2 General Aspects.
  - O-RAN E2SM-KPM v3.0 (Key Performance Metrics Service Model).
  - O-RAN E2SM-RC v1.0 (RAN Control Service Model).
