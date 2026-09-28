# Auditoria Técnica Atualizada — XApp-RDL-F1 / H-RDL

## Plano de Conformidade O-RAN, Integração NORI e Referencial OpenRAN@Brasil

**Projeto avaliado:** `georgebarbosa3090/XApp-RDL-F1`  
**Escopo:** Fase 1 — H-RDL determinística e segura para Near-RT RIC  
**Data:** 10 de setembro de 2026

## 1. Resumo executivo

A Fase 1 do XApp-RDL apresenta uma base sólida no núcleo H-RDL:

`Perception → State → Reasoning → Conflict Detection → Safety Validation → Action Planning → Control`

A principal conclusão é que a lógica do H-RDL está mais madura que a interoperabilidade O-RAN. O projeto já avançou com remoção de fallbacks sintéticos, fluxo de Subscription Manager, descoberta via E2 Manager e estruturação do E2SM-RC, mas ainda não há comprovação normativa ponta a ponta.

A avaliação deve separar cinco níveis:

1. Software funcional
2. Protocol-valid
3. Interface interoperável
4. Sistema interoperável
5. Closed-loop validado

A Fase 1 deve ser considerada plenamente concluída somente quando demonstrar:

`KPM(t0) → H-RDL → E2SM-RC → E2AP RIC Control → RAN/NORI → alteração de estado → KPM(t1)`

## 2. Referenciais formais

### 2.1 O-RAN ALLIANCE — fonte normativa primária
https://www.o-ran.org/specifications

Usar para definir versões e requisitos de:
- E2AP
- E2SM-KPM
- E2SM-RC
- E2 Setup
- RIC Subscription
- RIC Indication
- RIC Control
- ACK/Failure
- RAN Functions

### 2.2 O-RAN Software Community — referência de implementação
https://docs.o-ran-sc.org/en/latest/

Usar para:
- xApp Framework
- RMR
- E2 Manager
- Subscription Manager
- SDL
- App Manager
- ciclo de vida de xApps
- serviços e namespaces Kubernetes

### 2.3 NORI — referência experimental E2/ns-3
https://github.com/lasseufpa/nori

Usar para validar:
- E2 Setup
- registro do E2 Node
- RAN Functions
- KPM
- Subscription
- RIC Indication
- RIC Control
- closed loop com ns-3/5G-LENA

### 2.4 OpenRAN@Brasil Blueprint v3 — referência de infraestrutura e implantação
https://github.com/LABORA-INF-UFG/openran-br-blueprint/wiki/OpenRAN@Brasil-Blueprint-v3

Repositório:
https://github.com/LABORA-INF-UFG/openran-br-blueprint

Usar como referência para:
- ambiente Near-RT RIC
- implantação de xApps
- Kubernetes
- RMR
- integração E2SIM/NORI
- replicação experimental

## 3. Hierarquia de confiança

| Prioridade | Fonte | Papel |
|---|---|---|
| 1 | O-RAN ALLIANCE | Normativa |
| 2 | O-RAN SC | Implementação de referência |
| 3 | NORI | Integração experimental |
| 4 | OpenRAN@Brasil Blueprint v3 | Infraestrutura/reprodutibilidade |
| 5 | Artigos científicos | Evidência e comparação |
| 6 | Código próprio | Implementação a validar |

Regra: o XApp-RDL deve ser adaptado às especificações e referências, e não o contrário.

## 4. Status técnico consolidado

| Componente | Status |
|---|---|
| H-RDL | 🟢 |
| Perception/State | 🟢 |
| Conflict Detection | 🟢 |
| Safety | 🟢 |
| Action Planning | 🟢 |
| KPM Decoder | 🟡 |
| KPM Event Trigger | 🔴 |
| KPM Action Definition | 🔴 |
| E2AP | 🔴 |
| E2 Setup | 🔴 |
| RAN Function Discovery | 🟡 |
| Subscription Manager | 🟡 |
| RIC Indication real | 🟡 |
| E2SM-RC | 🟡/🔴 |
| RIC Control Request | 🔴 |
| Control ACK/Failure | 🔴 |
| RMR | 🟡 |
| SDL | 🟡 |
| NORI | 🟡 |
| OpenRAN@Brasil Blueprint v3 | 🟡 |
| Gate 1 | 🟡 |
| Gate 2 | 🟢 |
| Gate 3 | 🔴 |
| Gate 4 | 🔴 |
| Testes | 🔴 |
| Reprodutibilidade | 🟡 |

## 5. H-RDL

Status: 🟢 funcional.

Preservar o núcleo durante a correção de interoperabilidade. Criar um contrato formal de saída:

```python
@dataclass
class RDLDecision:
    state: dict
    proposals: list
    conflicts: list
    safety_result: dict
    selected_actions: list
    reason: str
```

A lógica E2 não deve ficar dentro do Reasoning Agent.

## 6. KPM Decoder

Status: 🟡 parcialmente conforme.

A remoção de métricas sintéticas foi correta. Porém, é necessário comprovar que o ASN.1 corresponde exatamente à versão-alvo do E2SM-KPM.

Criar:

`docs/e2/version-matrix.md`

Documentar para cada interface:
- versão alvo
- release
- fonte ASN.1
- commit
- codec
- variante PER
- status de implementação

## 7. KPM Event Trigger

Status: 🔴.

Eliminar qualquer payload mock como `00000000`.

Criar:

`src/e2/kpm/event_trigger.py`

A função deve gerar APER real da versão-alvo:

```python
def build_kpm_event_trigger(report_period_ms: int) -> bytes:
    ...
```

Teste obrigatório: `encode → decode → semantic comparison`.

## 8. KPM Action Definition

Status: 🔴.

Criar:

`src/e2/kpm/action_definition.py`

Implementar:
- Style Type
- MeasurementInfo
- Cell/UE scope
- granularity
- matching condition
- formato normativo
- serialização APER

O Subscription Manager deve transportar a estrutura, não montá-la manualmente.

## 9. E2AP

Status: 🔴 conformidade não demonstrada.

Organizar:

```text
src/e2/e2ap/
├── constants.py
├── setup.py
├── subscription.py
├── indication.py
├── control.py
├── reset.py
└── error_indication.py
```

Prioridade F1:
1. E2 Setup Request/Response
2. RIC Subscription Request/Response/Failure
3. RIC Indication
4. RIC Control Request
5. RIC Control Acknowledge
6. RIC Control Failure

## 10. E2 Setup

Status: 🔴 sem validação ponta a ponta.

Validar com NORI e Near-RT RIC.

Salvar:
- E2 Node ID
- Global gNB ID
- PLMN
- RAN Functions
- RAN Function Revision
- timestamp
- retorno do E2 Manager

## 11. Descoberta de RAN Functions

Status: 🟡.

A descoberta dinâmica via E2 Manager é adequada. Remover defaults como KPM=2 ou RC=3 do modo interoperável.

```python
if mode == "O-RAN_INTEROP" and discovery_failed:
    raise RanFunctionDiscoveryError()
```

Fallback só em UNIT_TEST ou OFFLINE_SIMULATION.

## 12. Subscription Manager

Status: 🟡.

O uso do serviço O-RAN SC é adequado, mas Event Trigger e Action Definition precisam ser reais.

Estrutura recomendada:

```text
src/e2/subscription/
├── request.py
├── response.py
├── lifecycle.py
└── validation.py
```

## 13. RIC Indication

Status: 🟡.

Provar fluxo:

`5G-LENA → NORI → E2 → Near-RT RIC → RMR → H-RDL`

Registrar:
- timestamp
- experiment_id
- e2_node_id
- ran_function_id
- ric_requestor_id
- ric_instance_id
- ric_action_id
- ric_indication_sn
- payload length
- APER SHA-256
- decode status

## 14. E2SM-RC

Status: 🟡 estrutural / 🔴 normativo.

Estrutura recomendada:

```text
src/e2/rc/
├── asn1/
├── control_header.py
├── control_message.py
├── control_action.py
├── control_parameter.py
└── encoder.py
```

O PDU precisa corresponder exatamente à versão normativa escolhida.

## 15. Parâmetros RAN Control

Status: 🔴.

Não enviar diretamente pares arbitrários como `parameter="tx_power"`.

Criar camada de mapeamento:

`RDL Action → RC Control Action → RAN Parameter ID → ASN.1 value`

## 16. Principal blocker — RIC Control Request

Status: 🔴 P0.

Enviar JSON via RMR contendo `aper_bytes` não demonstra RIC Control Request E2AP válido.

Fluxo obrigatório:

```text
RDLDecision
→ RC Mapper
→ E2SM-RC Control Header
→ E2SM-RC Control Message
→ E2AP RIC Control Request
→ RMR
→ E2 Termination
→ NORI/E2 Node
```

Critério: receber RIC Control Acknowledge ou RIC Control Failure real.

## 17. RMR

Status: 🟡.

Remover fallback que retorna sucesso fictício no modo interoperável.

Usar modos explícitos:
- O_RAN_INTEROP
- OFFLINE_SIMULATION
- UNIT_TEST

Em O_RAN_INTEROP:
- sem fake RMR
- sem fake SDL
- sem synthetic KPM
- sem RAN Function ID default
- sem Event Trigger fake
- sem Action Definition fake

## 18. SDL

Status: 🟡.

Fake SDL somente para testes.

Default recomendado:

`ALLOW_FAKE_SDL=false`

## 19. NORI

Status: 🟡 preparado, ainda sem closed loop comprovado.

Arquitetura alvo:

```text
ns-3 / 5G-LENA
      ↓
     NORI
      ↓ E2
O-RAN SC Near-RT RIC
      ↓
   H-RDL xApp
```

Registrar commit exato do NORI em cada experimento.

## 20. OpenRAN@Brasil Blueprint v3

Usar como referência de implantação.

Criar:

```text
deploy/openran-br-v3/
├── values.yaml
├── config-map.yaml
├── deployment.yaml
├── service.yaml
├── rmr-route-table.yaml
└── README.md
```

Documentar:
- versão Blueprint
- versão O-RAN SC
- namespace
- Subscription Manager
- E2 Manager
- RMR
- onboarding da xApp
- NORI
- reprodução do cenário

## 21. Gates

### Gate 1 — KPM real
Status: 🟡

DoD:
- E2 Node no E2 Manager
- KPM RAN Function descoberta
- Subscription aceita
- RIC Indication recebida
- APER salvo
- decode válido
- métricas alimentam Perception

### Gate 2 — decisão H-RDL
Status: 🟢

`KPM → State → Reasoning → Safety → Action`

### Gate 3 — RC real
Status: 🔴

`H-RDL → E2SM-RC → E2AP RIC Control → E2 Node → ACK/Failure`

### Gate 4 — closed loop
Status: 🔴

`KPM(t0) → H-RDL → RC → RAN → alteração → KPM(t1)`

## 22. Arquitetura alvo

```text
┌──────────────────────────────────────────┐
│          O-RAN SC Near-RT RIC            │
│                                          │
│ E2 Manager     Subscription Manager      │
│      └────────── RMR ───────────┐        │
│                                 ▼        │
│                              H-RDL xApp  │
└──────────────────┬───────────────────────┘
                   │ E2AP / E2SM
                   ▼
                 NORI
                   ▼
           ns-3 + 5G-LENA
```

## 23. Plano por prioridade

### P0 — bloqueadores
1. Definir versões-alvo E2AP/KPM/RC.
2. Registrar fontes ASN.1.
3. Validar ASN.1 contra O-RAN.
4. Remover Event Trigger mock.
5. Remover Action Definition mock.
6. Remover RAN Function fallback em modo interoperável.
7. Remover RMR fallback.
8. Implementar E2AP RIC Control real.
9. Implementar ACK.
10. Implementar Failure.
11. Restaurar testes de protocolo.
12. Corrigir claims excessivos de conformidade no README.

### P1 — integração
13. Validar E2 Setup via NORI.
14. Validar discovery dinâmico.
15. Subscription KPM real.
16. RIC Indication real.
17. KPM → H-RDL.
18. H-RDL → RC.
19. Control real.
20. Alteração real no simulador.

### P2 — validação científica
21. Closed loop.
22. Logs estruturados.
23. Artefatos experimentais.
24. Fixar versões/commits.
25. Seeds.
26. Repetições.
27. Média/desvio/IC.
28. Baselines.
29. Latência.
30. Segurança.
31. Estabilidade.

### P3 — evolução
Somente após Gate 4:
32. rApp
33. DRL
34. MARL
35. MAPPO
36. dApp
37. LLM/SLM
38. Knowledge Graph

## 24. Sprints

### Sprint 1 — versionamento
Criar:
- `docs/e2/version-matrix.md`
- `docs/e2/specification-sources.md`

### Sprint 2 — ASN.1
Compilar módulos e testar roundtrip.

### Sprint 3 — E2 Setup/discovery
NORI registrado e RAN Functions validadas.

### Sprint 4 — KPM Subscription
Event Trigger e Action Definition reais.

### Sprint 5 — KPM Indication
Telemetria real e persistência do bruto/decodificado.

### Sprint 6 — H-RDL integration
`KPM → Perception → State → Reasoning`

### Sprint 7 — E2SM-RC
Header, Message, Action, Parameters.

### Sprint 8 — E2AP RIC Control
Encapsular RC e receber ACK/Failure.

### Sprint 9 — closed loop
Criar `simulations/ns3/scenario_rdl_closed_loop_nori.cc`.

### Sprint 10 — reprodução
Criar `scripts/reproduce_f1.sh`.

## 25. Testes

Restaurar:

```text
tests/
├── unit/
├── codec/
├── integration/
├── interoperability/
└── system/
```

Cobrir:
- conflict detection
- safety
- APER roundtrip
- malformed payload
- E2 Manager
- Subscription Manager
- RMR
- SDL
- O-RAN SC
- NORI
- closed loop

## 26. Artefatos experimentais

```text
experiments/
├── raw/
├── decoded/
├── decisions/
├── controls/
├── metrics/
└── traces/
```

Registrar:
- experiment_id
- git_commit
- seed
- ns3_version
- 5g_lena_version
- nori_commit
- openran_blueprint_version
- oran_sc_release
- e2ap_version
- kpm_version
- rc_version
- xapp_image_digest

## 27. Métricas

Rede:
- throughput
- latency
- jitter
- PDR
- packet loss
- PRB utilization
- SINR
- spectral efficiency

Energia:
- energy consumption
- energy efficiency
- energy per bit

H-RDL:
- decision latency
- conflicts detected
- actions rejected
- safety violations prevented
- actions executed

E2:
- subscription latency
- KPM interval
- decode latency
- control latency
- ACK latency
- failure rate

## 28. Baselines

- B0 — sem controle
- B1 — política estática
- B2 — threshold
- B3 — H-RDL
- B4 — futuro DRL/MARL

Mesmas seeds, topologia, UEs, canal e duração.

## 29. Reprodutibilidade

Criar:

```text
reproducibility/
├── versions.lock
├── docker-images.txt
├── git-commits.txt
├── environment.md
└── runbook.md
```

## 30. README

Evitar “Fully O-RAN compliant” enquanto Gate 4 não estiver concluído.

Formulação recomendada:

> Implementação experimental de uma xApp H-RDL para Near-RT RIC, com suporte em evolução às interfaces E2AP, E2SM-KPM e E2SM-RC. A interoperabilidade normativa ponta a ponta é validada incrementalmente contra O-RAN ALLIANCE, O-RAN SC, NORI e OpenRAN@Brasil Blueprint.

## 31. Definition of Done — F1

- [ ] H-RDL determinístico preservado
- [ ] versões E2AP/KPM/RC documentadas
- [ ] ASN.1 vinculado à especificação
- [ ] sem fallback sintético em modo interoperável
- [ ] E2 Setup validado
- [ ] E2 Node visível no E2 Manager
- [ ] RAN Functions dinâmicas
- [ ] Subscription KPM real
- [ ] Event Trigger real
- [ ] Action Definition real
- [ ] RIC Indication real
- [ ] KPM real decodificado
- [ ] H-RDL produz decisão
- [ ] decisão convertida para RC
- [ ] E2SM-RC válido
- [ ] E2AP RIC Control Request válido
- [ ] Control chega ao E2 Node
- [ ] ACK/Failure real
- [ ] ação altera estado RAN
- [ ] KPM posterior demonstra efeito
- [ ] closed loop reproduzível
- [ ] testes unitários
- [ ] testes de codec
- [ ] testes de integração
- [ ] testes de interoperabilidade
- [ ] testes de sistema
- [ ] logs científicos
- [ ] artefatos preservados
- [ ] ambiente reproduzível com NORI
- [ ] perfil compatível com OpenRAN@Brasil Blueprint v3

## 32. Conclusão

O XApp-RDL-F1 já apresenta mérito técnico relevante na camada H-RDL. A maior pendência é transformar a integração atual em interoperabilidade normativa e experimentalmente demonstrável.

Prioridade:

`O-RAN specs → E2AP/KPM/RC corretos → O-RAN SC → NORI → 5G-LENA → H-RDL → RC → closed loop`

Somente depois devem ser adicionados DRL, MARL, MAPPO, rApps, dApps e LLM/SLM.

## 33. Referências

1. O-RAN ALLIANCE — Specifications  
   https://www.o-ran.org/specifications

2. O-RAN Software Community — Documentation  
   https://docs.o-ran-sc.org/en/latest/

3. NORI  
   https://github.com/lasseufpa/nori

4. OpenRAN@Brasil Blueprint  
   https://github.com/LABORA-INF-UFG/openran-br-blueprint

5. OpenRAN@Brasil Blueprint v3  
   https://github.com/LABORA-INF-UFG/openran-br-blueprint/wiki/OpenRAN@Brasil-Blueprint-v3

## Nota metodológica

Este documento distingue:
- conformidade arquitetural
- conformidade de protocolo
- conformidade normativa
- interoperabilidade
- validação experimental

Um item só deve receber status 🟢 “perfeitamente conforme” quando houver evidência correspondente ao nível de conformidade exigido, não apenas porque o software executa sem erro.
