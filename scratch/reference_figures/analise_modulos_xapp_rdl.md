# Análise dos Principais Módulos do Projeto xApp-RDL

## 1. Visão Geral

Este documento apresenta uma leitura técnica dos principais módulos do projeto **xApp-RDL (Resource and Decision Layer)**, com foco no caminho crítico de execução da xApp no Near-RT RIC. A análise descreve o papel de cada script, suas funções principais, a lógica executada e o estado atual de maturidade das implementações.

O fluxo principal do sistema pode ser resumido da seguinte forma:

```text
main.py
   ↓
rdl_xapp.py
   ↓
PerceptionAgent
   ↓
ReasoningAgent
   ↓
MAPPOCoordinator
   ↓
RefinementAgent
   ↓
RCEncoder / RMR
   ↓
Near-RT RIC / E2 Node

                  ↑
             E2SM-KPM
                  ↑
             KpmDecoder
```

---

# 2. `src/main.py`

## Função

É o ponto de entrada mínimo da aplicação.

```python
from src.rdl_xapp import RDLxApp

if __name__ == '__main__':
    app = RDLxApp()
    app.start()
```

### Linha 1

```python
from src.rdl_xapp import RDLxApp
```

Importa a classe principal da xApp.

### Linha 3

```python
if __name__ == '__main__':
```

Garante que a aplicação seja inicializada somente quando o arquivo é executado diretamente.

### Linha 4

```python
app = RDLxApp()
```

Cria a instância central da xApp.

### Linha 5

```python
app.start()
```

Inicia métricas, RMR, callbacks e o ciclo de decisão.

**Resumo:** `main.py` funciona apenas como bootstrap da aplicação.

---

# 3. `src/rdl_xapp.py`

Este é o principal script de integração do sistema.

Ele conecta:

- RMR;
- Decision Window;
- Perception Agent;
- Reasoning Agent;
- Refinement Agent;
- KPM Decoder;
- RC Encoder;
- memória/SDL;
- métricas.

## 3.1 Imports básicos

```python
import time
import threading
import json
import os
```

### `time`

Usado no loop temporal da Decision Window.

```python
time.sleep(0.05)
```

O sistema verifica o buffer a cada 50 ms.

### `threading`

Permite executar em paralelo:

- recepção RMR;
- Decision Loop;
- processamento de conflitos.

### `json`

Usado para converter propostas recebidas por RMR para objetos Python e para serializar comandos de controle.

### `os`

Usado para ler variáveis de ambiente, como:

```text
USE_FAKE_SDL
```

---

## 3.2 Tipagem

```python
from typing import Dict, Any, List
```

Fornece anotações de tipo para melhorar legibilidade e manutenção.

---

## 3.3 Framework O-RAN

```python
from ricxappframe.xapp_frame import Xapp
```

Importa o framework que gerencia:

- RMR;
- callbacks;
- ciclo de vida da xApp;
- buffers de mensagens.

---

## 3.4 Logger

```python
from src.observability.logging import setup_logger, now_ts
```

`setup_logger` cria logging estruturado.

`now_ts()` fornece timestamps usados para medir a Decision Window e latências.

---

## 3.5 Memória

```python
from src.infrastructure.sdl_repository import SdlRepository
from src.infrastructure.memory_module import MemoryModule
```

Há dois modos de persistência:

```text
Laboratório → MemoryModule
Produção    → SDL / Redis
```

---

## 3.6 Agentes

```python
from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
```

Representam três estágios:

```text
PERCEPTION
    ↓
interpreta o cenário

REASONING
    ↓
resolve conflitos

REFINEMENT
    ↓
valida segurança
```

---

## 3.7 Mensagens RMR

```python
RIC_INDICATION = 12050
RIC_CONTROL_REQ = 12010
RIC_CONTROL_ACK = 12011
RIC_CONTROL_FAILURE = 12012
RDL_ACTION_PROPOSAL = 30000
```

Significados:

| Código | Mensagem | Direção |
|---:|---|---|
| 12050 | RIC_INDICATION | E2 Node → RDL |
| 30000 | RDL_ACTION_PROPOSAL | xApp → RDL |
| 12010 | RIC_CONTROL_REQUEST | RDL → E2 Node |
| 12011 | RIC_CONTROL_ACK | E2 Node → RDL |
| 12012 | RIC_CONTROL_FAILURE | E2 Node → RDL |

---

## 3.8 Inicialização da xApp

```python
class RDLxApp:
```

Classe principal da aplicação.

### Seleção entre memória fake e SDL

```python
use_fake_sdl = os.getenv("USE_FAKE_SDL", "True").lower() in ("true", "1", "yes")
```

Se `USE_FAKE_SDL=true`, usa memória local.

```python
self.memory = MemoryModule()
```

Caso contrário:

```python
self.memory = SdlRepository()
```

---

## 3.9 Inicialização dos agentes

```python
self.perception = PerceptionAgent()
self.reasoning = ReasoningAgent(self.memory, config={})
self.refinement = RefinementAgent(self.memory)
```

Cria os três estágios cognitivos.

---

## 3.10 Métricas

```python
self.metrics = MetricsServer(port=8081)
```

As métricas são expostas na porta 8081.

---

## 3.11 KPM Decoder e RC Encoder

```python
self.asn1_decoder = KpmDecoder()
self.rc_encoder = RCEncoder()
```

O primeiro converte E2SM-KPM em dados Python.

O segundo converte decisões em E2SM-RC/APer.

---

## 3.12 Decision Window

```python
self.proposal_buffer: List[XAppAction] = []
self.buffer_lock = threading.Lock()
self.window_start: float = 0.0
self.WINDOW_DURATION_MS = 200
```

Essas linhas implementam o agrupamento temporal das propostas.

Em vez de resolver cada ação assim que chega, o sistema acumula as propostas durante 200 ms.

```text
A ─┐
B ─┼──→ buffer → decisão conjunta
C ─┘
```

### `buffer_lock`

Evita race conditions entre threads.

---

## 3.13 Instância do framework xApp

```python
self.xapp = Xapp(
    entrypoint=self._entrypoint,
    rmr_port=4560,
    rmr_wait_for_ready=True,
    use_fake_sdl=use_fake_sdl
)
```

Configura:

- porta RMR 4560;
- função de entrada;
- espera pelo RMR;
- modo fake SDL.

---

## 3.14 Registro de callbacks

```python
self.xapp.register_callback(self._kpm_indication_handler, RIC_INDICATION)
self.xapp.register_callback(self._action_proposal_handler, RDL_ACTION_PROPOSAL)
self.xapp.register_callback(self._control_ack_handler, RIC_CONTROL_ACK)
self.xapp.register_callback(self._control_failure_handler, RIC_CONTROL_FAILURE)
```

Cada tipo de mensagem é encaminhado para seu handler.

---

# 4. KPM Handler

```python
def _kpm_indication_handler(...):
```

Executado quando chega uma `RIC_INDICATION`.

### Registra métrica

```python
self.metrics.record_kpm()
```

### Extrai payload

```python
payload = summary.get("payload")
```

### Decodifica

```python
reports_data = self.asn1_decoder.decode_indication(payload)
```

### Converte para `KPMReport`

```python
report = KPMReport(...)
```

### Atualiza percepção

```python
self.perception.update_kpm_report(report)
```

O Perception Agent passa a guardar a telemetria mais recente.

### Libera buffer RMR

```python
xapp_instance.rmr_free(sbuf)
```

---

# 5. Handler de propostas das xApps

```python
def _action_proposal_handler(...):
```

Recebe propostas via `RDL_ACTION_PROPOSAL`.

### Decodifica JSON

```python
data = json.loads(payload.decode('utf-8'))
```

### Cria entidade de domínio

```python
action = XAppAction(...)
```

### Protege o buffer

```python
with self.buffer_lock:
```

### Inicia janela

```python
if not self.proposal_buffer:
    self.window_start = now_ts()
```

A primeira ação inicia a janela temporal.

### Adiciona ação

```python
self.proposal_buffer.append(action)
```

---

# 6. `_process_action_group()`

Responsável por processar o lote da Decision Window.

### Registra ações

```python
for act in actions:
    self.memory.add_action(act)
```

### Detecta conflitos

```python
conflicts = self.perception.register_action_group(actions)
```

### Atualiza número de xApps ativas

```python
self.metrics.update_active_xapps(...)
```

### Para cada conflito

```python
for conflict in conflicts:
```

Executa:

```text
Perception
   ↓
Reasoning
   ↓
Refinement
   ↓
Control
```

### Reasoning

```python
resolution = self.reasoning.resolve(conflict)
```

### Safety Guard

```python
is_valid, level, reason = self.refinement.validate(resolution, conflict)
```

### Latência

```python
latency = now_ts() - t0
```

### Persistência

```python
self.memory.add_resolution(resolution)
```

### Envio de ações vencedoras

```python
if is_valid and resolution.winning_actions:
```

Cada ação aprovada é enviada com:

```python
self._send_control(...)
```

---

# 7. Decision Loop

```python
def _decision_loop(self):
```

Executa enquanto a xApp estiver ativa.

```python
while self.running:
```

### Intervalo de 50 ms

```python
time.sleep(0.05)
```

### Cálculo da janela

```python
elapsed_ms = (now_ts() - self.window_start) * 1000
```

### Fechamento

```python
if elapsed_ms >= self.WINDOW_DURATION_MS:
```

Se passar de 200 ms, copia o lote:

```python
actions_to_process = list(self.proposal_buffer)
```

Limpa a fila:

```python
self.proposal_buffer.clear()
```

E inicia processamento em outra thread:

```python
threading.Thread(...).start()
```

Isso evita bloquear a recepção RMR.

---

# 8. Envio de controle

```python
def _send_control(...):
```

### Codificação APER

```python
aper_payload = self.rc_encoder.encode_control_request(node_id, parameter, value)
```

### Construção do envelope

```python
payload_dict = {
    "node_id": node_id,
    "parameter": parameter,
    "value": value,
    "aper_bytes": aper_payload.hex()
}
```

### Serialização

```python
payload_bytes = json.dumps(payload_dict).encode('utf-8')
```

### Envio RMR

```python
self.xapp.rmr_send(payload=payload_bytes, mtype=RIC_CONTROL_REQ)
```

---

# 9. `PerceptionAgent`

Responsável pela detecção de conflitos.

## 9.1 Grafo de dependências KPI

```python
self.kpi_dependency_graph = {
    "PRB_QUOTA": ["DRB.UEThpDl", "RRU.PrbUsedDl"],
    "SCHEDULER_WEIGHT": ["DRB.UEThpDl", "DRB.RlcSduDelayDl"],
    "TX_POWER": ["L1M.DL-sinr", "DRB.UEThpDl"]
}
```

Esse mapa codifica relações causais simplificadas.

Exemplo:

```text
TX_POWER
   ↓
SINR
   ↓
Throughput
```

---

## 9.2 Registro de ações

```python
self._action_registry: Dict[str, Dict[str, XAppAction]] = {}
```

Organização:

```text
node_id
  └── parâmetro
        └── última ação
```

---

## 9.3 Último KPM

```python
self.latest_kpm: Optional[KPMReport] = None
```

Guarda a telemetria mais recente.

### Observação crítica

No código atual, o KPM é armazenado, mas ainda não é efetivamente usado na lógica de detecção de conflitos.

---

## 9.4 Conflito direto

Critério:

```python
action_a.node_id == action_b.node_id
and action_a.parameter == action_b.parameter
and action_a.xapp_id != action_b.xapp_id
```

Significa:

```text
mesmo nó
+
mesmo parâmetro
+
xApps diferentes
```

Exemplo:

```text
QoS-xApp → PRB = 70
Energy-xApp → PRB = 30
```

Resultado:

```text
DIRECT / HIGH
```

---

## 9.5 Conflito indireto

```python
common_kpis = set(kpis_a).intersection(set(kpis_b))
```

Se dois parâmetros diferentes afetam o mesmo KPI, há conflito indireto.

Exemplo:

```text
TX_POWER → Throughput
PRB_QUOTA → Throughput
```

Resultado:

```text
INDIRECT / MEDIUM
```

---

## 9.6 Complexidade

O agente compara ações par a par:

```python
for i in range(len(actions)):
    for j in range(i + 1, len(actions)):
```

Complexidade:

```text
O(N²)
```

---

## 9.7 Problemas atuais

- `networkx` é importado, mas não usado;
- `itertools` é importado, mas não usado nesse script;
- não há TTL explícito no registry;
- ações antigas podem permanecer indefinidamente;
- KPM ainda não participa da detecção real.

---

# 10. `ReasoningAgent`

Responsável por escolher a estratégia de resolução.

Fluxo atual:

```text
Conflict
   ↓
History?
   ├── sim → reuse
   ↓ não
DIRECT?
   ├── sim → TVS
   ↓ não
MAPPO
```

---

## 10.1 Inicialização MAPPO

```python
self.mappo = MAPPOCoordinator(
    n_agents=2,
    obs_dim=10,
    action_dim=5,
    config=config
)
```

Atualmente os valores são fixos.

---

## 10.2 Reuso de histórico

```python
similar_resolutions = self.memory.get_similar_resolutions(conflict)
```

Se a confiança for maior que 0,8:

```python
if best_res.confidence > 0.8:
```

reutiliza a decisão anterior.

Isso se aproxima de um mecanismo de case-based reasoning.

---

## 10.3 Conflito direto

```python
if conflict.conflict_type.name == "DIRECT":
```

Usa por padrão:

```python
policy="TVS"
```

TVS = Throughput Violation-based Selection.

---

## 10.4 Geração do power set

```python
for i in range(1, len(actions) + 1):
    powerset.extend(list(itertools.combinations(actions, i)))
```

Gera todos os subconjuntos não vazios.

Quantidade:

```text
2^N - 1
```

Exemplos:

| xApps | Combinações |
|---:|---:|
| 2 | 3 |
| 5 | 31 |
| 10 | 1.023 |
| 15 | 32.767 |
| 20 | 1.048.575 |

Essa parte pode se tornar um gargalo de escalabilidade.

---

## 10.5 Avaliação heurística

```python
score = self._mock_evaluate_subset(...)
```

A função é explicitamente mock.

Logo, ainda não representa avaliação real da RAN.

---

## 10.6 Inconsistência física

```python
if key in param_targets and param_targets[key] != act.value:
    return -9999.0
```

Penaliza combinações que tentam aplicar dois valores diferentes ao mesmo parâmetro.

---

## 10.7 TVS e EEVS

TVS prioriza redução de violações de throughput.

EEVS adiciona penalização para alto consumo energético.

Atualmente, ambas são heurísticas simplificadas.

---

## 10.8 Integração MAPPO

```python
kpm_state = {}
winning_action, confidence = self.mappo.decide(conflict, kpm_state)
```

O `kpm_state` ainda é vazio.

Isso significa que a integração:

```text
KPM → MARL
```

ainda não está implementada de fato.

---

# 11. `mappo_agent.py`

Contém a estrutura Actor-Critic.

## 11.1 Actor

```python
class ActorNetwork(nn.Module):
```

Arquitetura:

```text
obs
 ↓
Linear 128
 ↓
ReLU
 ↓
Linear 256
 ↓
ReLU
 ↓
Linear 128
 ↓
ReLU
 ↓
Linear action_dim
 ↓
Softmax
```

O Actor representa:

```text
πθ(a|o)
```

---

## 11.2 Critic

```python
class CriticNetwork(nn.Module):
```

Recebe observação global e produz um valor escalar:

```text
V(s)
```

A estrutura é coerente com CTDE:

```text
Centralized Training
Decentralized Execution
```

---

## 11.3 Hiperparâmetros

```python
lr=3e-4
gamma=0.99
clip_eps=0.2
```

São valores típicos do PPO.

---

## 11.4 Seleção de ação

```python
probs = self.actor(obs_tensor)
```

Obtém probabilidades.

```python
dist = torch.distributions.Categorical(probs)
```

Cria distribuição categórica.

```python
action = dist.sample()
```

Amostra a ação.

```python
log_prob = dist.log_prob(action)
```

Calcula log-probabilidade, necessária para a razão PPO.

---

## 11.5 Problema principal

```python
def update(...):
    return {"actor_loss": 0.0, "critic_loss": 0.0}
```

O treinamento ainda não está implementado.

Faltam:

- returns;
- advantages;
- GAE;
- PPO clipped objective;
- critic loss;
- entropy;
- backward;
- optimizer step.

---

## 11.6 Decisão mock

```python
winning_action = conflict.involved_xapps[0]
confidence = 0.85
```

Atualmente a decisão real não é feita pela rede neural.

O código escolhe a primeira ação envolvida no conflito.

---

# 12. `RefinementAgent`

Implementa o Safety Guard.

Fluxo:

```text
Decision
   ↓
Existe ação?
   ↓
Frequência segura?
   ↓
PRB válido?
   ↓
TX Power válido?
   ↓
Node válido?
   ↓
APPROVED
```

---

## 12.1 Intervalo mínimo

```python
"minimum_control_interval_ms": 1000
```

Impõe pelo menos 1 segundo entre controles equivalentes.

---

## 12.2 Target Key

```python
target_key = f"{action.node_id}_{action.parameter}"
```

Exemplo:

```text
gnb01_PRB_QUOTA
```

---

## 12.3 Anti-ping-pong

```python
if (now - last_time) < self.config.get("minimum_control_interval_ms", 1000):
```

Evita oscilações rápidas.

---

## 12.4 Limites PRB

```python
if action.value < 0 or action.value > 100:
```

Restringe PRB a:

```text
0 ≤ PRB ≤ 100
```

---

## 12.5 Limites TX Power

```python
if action.value < -10 or action.value > 23:
```

Restringe potência a:

```text
-10 dBm ≤ Ptx ≤ 23 dBm
```

---

## 12.6 Node vazio

```python
if action.node_id == "":
```

Rejeita target vazio.

Ainda não verifica se o node existe de fato no E2 Manager.

---

## 12.7 Problema potencial

```python
self.last_control_time[target_key] = now
```

O tempo é atualizado durante a validação, antes da confirmação de envio ou ACK.

Idealmente, essa atualização deveria ocorrer após:

```text
RIC_CONTROL_ACK
```

ou pelo menos após envio bem-sucedido.

---

# 13. `KpmDecoder`

Responsável pela transformação:

```text
E2SM-KPM APER
      ↓
ASN.1
      ↓
KpmMeasurement
      ↓
KPMReport
```

---

## 13.1 Estrutura de medição

```python
@dataclass
class KpmMeasurement:
```

Campos:

- node_id;
- ue_id;
- metric_name;
- value;
- timestamp.

---

## 13.2 Decodificação APER

```python
msg.from_aper(indication_message)
```

Tenta interpretar o payload real.

---

## 13.3 Fallback mock

Quando a decodificação falha, o código injeta valores simulados:

```text
DRB.UEThpDl = 15.5
RRU.PrbUsedDl = 45.0
```

Isso é útil em laboratório, mas perigoso em experimentos formais se não for explicitamente desativado.

---

# 14. `RCEncoder`

Executa o caminho inverso:

```text
Decision
   ↓
RCEncoder
   ↓
ASN.1
   ↓
APER
   ↓
RIC_CONTROL_REQUEST
```

---

## 14.1 Mapeamento de parâmetros

```python
self.param_map = {
    "PRB_QUOTA": 1,
    "SCHEDULER_WEIGHT": 2,
    "TX_POWER": 3
}
```

Converte nomes lógicos em IDs da RAN.

---

## 14.2 Parâmetro desconhecido

```python
param_id = self.param_map.get(parameter, 99)
```

Um parâmetro não conhecido recebe ID 99.

Isso pode ser perigoso.

Seria melhor lançar uma exceção.

---

## 14.3 Header RC

```python
header.set_val({
    'ricControlStyleType': 1,
    'ricControlActionID': 1
})
```

Os valores estão fixos e devem ser alinhados à RAN Function Definition do E2 Node real.

---

## 14.4 Perda de precisão

```python
'ranParameterValue': int(value)
```

Um valor como:

```text
22.7
```

vira:

```text
22
```

Isso pode ser inadequado para parâmetros contínuos.

---

## 14.5 Problema do Header

O código gera:

```python
header_aper
```

mas retorna apenas:

```python
msg_aper
```

Assim, o header não participa do retorno final.

Isso precisa ser revisado para integração E2SM-RC real.

---

# 15. `ControlDispatcher`

Conceitualmente, deveria executar:

```text
Decision
 ↓
RC Encoder
 ↓
UUID
 ↓
SDL tracking
 ↓
RMR
 ↓
ACK / Failure
 ↓
Rollback
```

---

## 15.1 Tracking

Cria um UUID para cada controle:

```python
control_request_id = str(uuid.uuid4())
```

E salva no SDL.

---

## 15.2 ACK e Failure

Atualmente usa:

```python
req_id = "simulated_req_id"
```

Ou seja, ACK e Failure ainda são mockados.

---

## 15.3 Rollback

```python
def trigger_rollback(...):
```

Ainda é placeholder.

---

## 15.4 Incompatibilidade importante

`control_dispatcher.py` tenta importar:

```python
E2SMRCEncoder
ControlAction
```

mas o `rc_encoder.py` atual define:

```python
RCEncoder
```

Isso indica inconsistência entre os módulos.

---

## 15.5 Dispatcher não usado no fluxo principal

O `RDLxApp` envia controle diretamente com `_send_control()`.

Logo hoje existem dois caminhos:

```text
CAMINHO ATUAL
RDLxApp
 ↓
RCEncoder
 ↓
rmr_send
```

```text
CAMINHO PROJETADO
Reasoning
 ↓
Decision
 ↓
ControlDispatcher
 ↓
SDL tracking
 ↓
RC
 ↓
RMR
 ↓
ACK
```

Essa duplicidade deve ser eliminada.

---

# 16. Estado Atual dos Principais Componentes

| Componente | Estado |
|---|---|
| Estrutura xApp / RMR | Implementada |
| Decision Window 200 ms | Implementada |
| Buffer concorrente | Implementado |
| Detecção de conflito direto | Implementada |
| Detecção de conflito indireto | Implementada por regras |
| Registry histórico | Parcial |
| Telemetria KPM | Implementada com fallback mock |
| E2SM-RC Encoder | Protótipo |
| Safety Guard | Implementado |
| TVS/EEVS | Heurístico/mock |
| MAPPO Actor | Estrutura implementada |
| MAPPO Critic | Estrutura implementada |
| MAPPO select_action | Implementado |
| MAPPO treinamento PPO | Não implementado |
| KPM → observação MARL | Não integrado |
| Knowledge/history lookup | Parcial |
| ACK correlation | Mock |
| Failure correlation | Mock |
| Rollback | Placeholder |
| ControlDispatcher | Desconectado/incompatível |
| Closed-loop completo | Parcial |

---

# 17. Pipeline Real Atual

```text
                 ┌──────────────────┐
                 │   QoS xApp       │
                 ├──────────────────┤
                 │ Energy xApp      │
                 ├──────────────────┤
                 │ Mobility xApp    │
                 └────────┬─────────┘
                          │
                   ACTION PROPOSAL
                          │
                          ▼
             ┌────────────────────────┐
             │ DECISION WINDOW 200 ms │
             └────────────┬───────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │ Perception Agent     │
              │ Direct Conflict      │
              │ Indirect Conflict    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Reasoning Agent      │
              │ History              │
              │ TVS heuristic        │
              │ MAPPO mock           │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Refinement Agent     │
              │ Safety Guard         │
              └──────────┬───────────┘
                         │
                         ▼
                 ┌──────────────┐
                 │ RC Encoder   │
                 │ ASN.1 / APER │
                 └──────┬───────┘
                        │
                RIC CONTROL REQUEST
                        │
                        ▼
                      gNB
```

Telemetria:

```text
gNB
 │
 │ RIC_INDICATION 12050
 ▼
KpmDecoder
 │
 ▼
KPMReport
 │
 ▼
PerceptionAgent.latest_kpm
```

---

# 18. Principal Lacuna Científica

O maior passo para maturidade do projeto é fechar o pipeline de aprendizado:

```text
KPM
 ↓
MARL observation vector
 ↓
Actor
 ↓
action
 ↓
reward
 ↓
rollout
 ↓
GAE
 ↓
PPO update
 ↓
policy atualizada
```

Hoje o projeto possui uma base arquitetural consistente para essa evolução, mas o MAPPO ainda está no nível estrutural.

---

# 19. Recomendações Técnicas Prioritárias

1. Implementar treinamento PPO/MAPPO completo.
2. Integrar KPM real ao vetor de observação MARL.
3. Implementar reward function baseada em SLA, throughput, delay, energia e estabilidade.
4. Corrigir incompatibilidade entre `ControlDispatcher` e `RCEncoder`.
5. Unificar o caminho de envio de controle.
6. Implementar correlação real de ACK e FAILURE.
7. Implementar rollback real.
8. Eliminar fallback mock em modo produção.
9. Implementar TTL/expiração no registry de ações.
10. Validar `node_id` via E2 Manager.
11. Tornar os hiperparâmetros MAPPO configuráveis.
12. Implementar E2SM-RC completo com Header e Message coerentes.
13. Integrar Knowledge Graph de forma operacional ao histórico e à resolução.
14. Medir latência por estágio do pipeline.
15. Criar testes experimentais para conflitos diretos, indiretos, temporais e de recursos.

---

# 20. Conclusão

A xApp-RDL já apresenta uma arquitetura modular e coerente para resolução de conflitos entre xApps no Near-RT RIC. A implementação atual cobre adequadamente o fluxo de recepção de propostas, agrupamento temporal, detecção de conflitos, aplicação de políticas heurísticas, validação de segurança e envio de controle.

Entretanto, alguns módulos ainda são protótipos ou mocks. Os pontos mais críticos são o treinamento MAPPO, a integração KPM-MARL, a correlação ACK/FAILURE, o rollback e a consolidação do pipeline de controle.

A evolução natural do projeto é transformar a estrutura cognitiva já existente em um closed-loop realmente adaptativo, onde telemetria real da RAN alimente diretamente os agentes MARL, as ações sejam aprendidas por experiência e a segurança seja validada antes da atuação física.
