# Volume 06: Observabilidade Service Mesh com Kiali, Istio e Injeção de Tráfego O-RAN

**Documento:** Volume Temático 06  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Métricas Prometheus, Telemetria Cognitiva MARL, Service Mesh Istio, Padronização de Portas e Dashboard Kiali  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Visão Geral da Arquitetura de Observabilidade

A infraestrutura O-RAN 5G-Advanced da CA-RDL opera sobre uma malha de serviços (**Istio Service Mesh**) no Kubernetes, permitindo rastreabilidade, monitoramento de latência e governança em tempo real entre todas as xApps e os componentes do Near-RT RIC.

```mermaid
graph TD
    subgraph Mesh["Namespace ricxapp (Istio Service Mesh)"]
        RDL["ricxapp-iqos-xapp-rdl-f2<br/>(Pod 2/2: App + Envoy)"]
        XS["ricxapp-qos-xslice<br/>(Pod 2/2: App + Envoy)"]
        ES["ricxapp-energy-saving<br/>(Pod 2/2: App + Envoy)"]
        TS["ricxapp-traffic-steering<br/>(Pod 2/2: App + Envoy)"]
        BF["ricxapp-beamformer<br/>(Pod 2/2: App + Envoy)"]
        IS["ricxapp-isac-radar<br/>(Pod 2/2: App + Envoy)"]
        RS["ricxapp-rogue-stress<br/>(Pod 2/2: App + Envoy)"]
        GEN["traffic-generator<br/>(Injetor Contínuo)"]
    end

    subgraph RIC["Namespace ricplt"]
        DBAAS["ricplt-dbaas (Redis SDL)<br/>(Pod 2/2: App + Envoy)"]
        E2T["service-ricplt-e2term-rmr"]
        SUB["service-ricplt-submgr-rmr"]
    end

    GEN -->|HTTP Health/Metrics| RDL
    GEN -->|HTTP Health/Metrics| XS
    GEN -->|HTTP Health/Metrics| ES
    GEN -->|HTTP Health/Metrics| TS
    GEN -->|HTTP Health/Metrics| BF
    GEN -->|HTTP Health/Metrics| IS
    GEN -->|HTTP Health/Metrics| RS

    RDL <-->|TCP RMR 4560/4561| RIC
    XS <-->|TCP RMR 4562| RIC
    ES <-->|TCP RMR 4563| RIC
    TS <-->|TCP RMR 4564| RIC

    Mesh -.->|Telemetria Envoy / Envoy Proxies| PROM["Prometheus Scraper"]
    RIC -.->|Telemetria Envoy| PROM
    PROM --> KIALI["Kiali Service Mesh Dashboard<br/>(Visualização de Topologia e Tráfego)"]
```

---

## 2. Métricas de Observabilidade Prometheus da Fase 2

A xApp RDL Fase 2 exporta métricas cognitivas e de governança na porta `8081` (`/metrics`):

| Métrica Prometheus | Tipo | Descrição |
| :--- | :---: | :--- |
| `rdl_decision_latency_seconds` | Histogram | Tempo de inferência e arbitragem do motor MAPPO / Safe-RL (meta < 50ms). |
| `rdl_conflicts_total` | Counter | Total de conflitos de rádio interceptados e mitigados pela CA-RDL. |
| `marl_actor_loss` | Gauge | Perda (Loss) da rede neural do Ator durante o treinamento online. |
| `marl_critic_loss` | Gauge | Perda (Loss) da rede neural do Crítico Centralizado. |
| `rdl_sla_compliance_ratio` | Gauge | Taxa percentual de cumprimento de SLA por fatia de rede (URLLC/eMBB/mMTC). |
| `rdl_action_propagation_latency_ms` | Histogram | Latência fim a fim ($t_{\text{ack}} - t_{\text{arrival}}$) de propagação E2SM-RC. |

---

## 3. Requisitos e Padrões Obrigatórios do Istio e Kiali

Para que o Kiali exiba o grafo de tráfego, as conexões ativas e as métricas sem alertas de erro, os manifestos do Kubernetes devem aderir estritamente a três regras fundamentais:

### 3.1. Injeção Automática de Sidecar (`istio-injection: enabled`)
Todos os namespaces monitorados (`ricxapp` e `ricplt`) devem possuir a label de injeção automática:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ricxapp
  labels:
    istio-injection: enabled
```
* **Verificação:** Ao rodar `kubectl get pods -n ricxapp`, a coluna `READY` deve mostrar `2/2` (indicando o container principal + o container `istio-proxy` Envoy).

### 3.2. Padronização de Nomenclatura de Portas (Regra `KIA0601`)
O Istio e o Kiali exigem que o nome de qualquer porta em `Service` e `Deployment` siga o padrão:
$$\text{formato: } \langle\text{protocol}\rangle\text{[-}\langle\text{suffix}\rangle\text{]}$$

* **Portas HTTP:** Devem ser nomeadas como `http-health`, `http-metrics` ou `http-api`.
* **Portas TCP/RMR:** Devem ser nomeadas como `tcp-rmr-data`, `tcp-rmr-route` ou `tcp-redis`.
* ❌ **Nomes Inválidos (geram erro `KIA0601`):** `metrics`, `rmr-data`, `rmr-route`, `rmr`, `redis`.

### 3.3. Labels Canônicos de Workload (`app` e `version`)
Todo `Deployment` e `PodTemplate` deve possuir as labels `app` e `version`:
```yaml
metadata:
  labels:
    app: ricxapp-beamformer
    version: "1.1.0"
```

---

## 4. Guia de Resolução de Problemas (Troubleshooting Kiali)

| Sintoma / Alerta no Kiali | Causa Raiz | Procedimento de Correção |
| :--- | :--- | :--- |
| **"Empty Graph: No graph traffic for the time period"** | Não houve requisições trafegando pelos proxies Envoy nos últimos 5 minutos (janela ociosa) ou as portas estavam sem prefixo de protocolo. | 1. Iniciar o gerador de tráfego: `kubectl apply -f deploy/kubernetes/traffic-generator.yaml -n ricxapp`<br/>2. Ou rodar o script interativo: `./scripts/inject_mesh_traffic.sh 300` |
| **`KIA0601 Port name must follow <protocol>[-suffix] form`** | Porta nomeada sem o prefixo do protocolo (ex.: `metrics` na porta 8089). | Renomear para `http-metrics`, `http-health` ou `tcp-rmr-data` no `Service` e `Deployment`. |
| **`Pod has no Istio sidecar`** / **`Istio sidecar container not found`** | Namespace não rotulado para injeção ou Pod criado antes da habilitação do Istio. | 1. `kubectl label namespace ricxapp istio-injection=enabled --overwrite`<br/>2. `kubectl rollout restart deployment -n ricxapp` |
| **`version label is missing`** | O Deployment ou Pod não possui a tag `version`. | Adicionar `version: "1.0.0"` (ou versão apropriada) em `spec.template.metadata.labels`. |
| **`zsh: permission denied: ./scripts/...`** | Arquivo `.sh` sem permissão de execução no SO. | Executar `chmod +x scripts/*.sh` ou rodar via `bash ./scripts/...`. |

---

## 5. Procedimento de Implantação e Injeção de Tráfego

### Passo 1: Atualizar o Repositório e Conceder Permissões
```bash
git pull origin main
chmod +x scripts/*.sh
```

### Passo 2: Reaplicar as Reference xApps e Plataforma RIC
```bash
# Aplica os manifestos corrigidos com sidecar e portas Istio
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml -n ricplt
./scripts/deploy_reference_xapps.sh
```

### Passo 3: Ativar o Gerador Contínuo de Tráfego
```bash
# Inicia requisições contínuas a todas as 6 Reference xApps + CA-RDL Fase 2
kubectl apply -f deploy/kubernetes/traffic-generator.yaml -n ricxapp
```

Ou executar a injeção sob demanda via terminal:
```bash
./scripts/inject_mesh_traffic.sh 300
```

---

## 6. Como Navegar e Visualizar no Dashboard do Kiali

1. **Acessar o Kiali:**
   - Acesse a interface web do Kiali (via NodePort, Ingress ou Rancher Dashboard).
2. **Abrir a Visualização de Grafo:**
   - No menu lateral esquerdo, clique no ícone **Graph** (segundo ícone).
3. **Configurar os Filtros no Topo:**
   - **Namespace:** Marque as caixas `ricxapp` e `ricplt`.
   - **Graph Type:** Selecione `Workload` ou `App graph`.
   - **Time Range:** Selecione `Last 1m` ou `Last 5m`.
   - **Refresh:** Selecione `Every 10s`.
4. **Habilitar Opções de Exibição (Menu *Display*):**
   - ☑ **Traffic Animation:** Mostra as partículas de tráfego fluindo entre os componentes em tempo real.
   - ☑ **Request Rates:** Exibe a taxa de requisições por segundo (RPS / HTTP RPS) em cada aresta do grafo.
   - ☑ **Response Time:** Exibe a latência média de resposta em milissegundos.
   - ☑ **Security:** Exibe cadeados indicando mTLS ativo entre os proxies Envoy.

---

## 7. Registro de Auditoria e Resolução de Não-Conformidades da Malha Istio

### 7.1. Diagnóstico dos Alertas no Kiali (`ricplt` e `ricxapp`)

Durante a validação operacional da malha no Kiali, foram identificadas e auditadas as seguintes não-conformidades de infraestrutura:

1. **`Pod has no Istio sidecar` / `Istio sidecar container not found in Pod(s)`**:
   * **Causa Raiz:** O namespace `ricplt` (e `ricxapp`) não possuía a label `istio-injection=enabled`.
   * **Impacto:** Os Pods operavam como container único (`1/1 READY`) sem o proxy Envoy (`istio-proxy`) acoplado, impedindo a interceptação de tráfego e geração de telemetria no Prometheus.
2. **`Pod has no version label` / `version label is missing`**:
   * **Causa Raiz:** O Deployment do DBAAS Redis (`ricplt-dbaas`) e das Reference xApps não possuíam o label canônico `version: "1.0.0"`.
   * **Impacto:** O Kiali emitia alertas de aviso e impedia a correlação temporal de versões de workloads.
3. **`KIA0601 Port name must follow <protocol>[-suffix] form`**:
   * **Causa Raiz:** Portas nomeadas como `metrics`, `rmr-data`, `rmr-route` e `redis` violavam a sintaxe de protocolos do Istio.
   * **Impacto:** Desativação de inspeção L7/HTTP nos endpoints de métricas e saúde.

### 7.2. Rastreabilidade de Modificações e Cadeia de Custódia (Commits `ccd0e3d` e `68de60a`)

| Arquivo Inspecionado / Modificado | Linhas Alteradas | Ação Realizada |
| :--- | :--- | :--- |
| [`deploy/kubernetes/namespace.yaml`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/deploy/kubernetes/namespace.yaml) | L4-14 | Adicionado `istio-injection: enabled` nos namespaces `ricplt` e `ricxapp`. |
| [`deploy/kubernetes/near-rt-ric.yaml`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/deploy/kubernetes/near-rt-ric.yaml) | L5-25 | Adicionadas labels `version: "1.0.0"`, anotação `sidecar.istio.io/inject: "true"` e porta `tcp-redis`. |
| [`deploy/kubernetes/deployment.yaml`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/deploy/kubernetes/deployment.yaml) | L6-24 | Inseridas labels `version: "2.0.0"`, anotação de injeção Istio e portas `tcp-rmr-data`/`tcp-rmr-route`. |
| [`deploy/kubernetes/xapp-qos-xslice.yaml`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/deploy/kubernetes/xapp-qos-xslice.yaml) | L5-24, L40-44 | Inseridas labels `version: "1.1.0"`, anotação de injeção Istio e porta `tcp-rmr-data`. |
| [`deploy/kubernetes/xapp-energy-saving.yaml`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/deploy/kubernetes/xapp-energy-saving.yaml) | L5-24, L40-44 | Inseridas labels `version: "1.1.0"`, anotação de injeção Istio e porta `tcp-rmr-data`. |
| [`deploy/kubernetes/xapp-traffic-steering.yaml`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/deploy/kubernetes/xapp-traffic-steering.yaml) | L5-24, L40-44 | Inseridas labels `version: "1.1.0"`, anotação de injeção Istio e porta `tcp-rmr-data`. |
| [`scripts/deploy_reference_xapps.sh`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/scripts/deploy_reference_xapps.sh) | L12-20, L65-80, L85-140 | Injeção de labels Istio nos namespaces, servidor Python multi-porta (`http-health`/`http-metrics`), anotações de sidecar e portas prefixadas. |
| [`scripts/deploy_rdl_phase2.sh`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/scripts/deploy_rdl_phase2.sh) | L58-66 | Rotulagem garantida de injeção Istio em `ricplt` e `ricxapp` e reinicialização de Pods via `rollout restart`. |
| [`scripts/inject_mesh_traffic.sh`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/scripts/inject_mesh_traffic.sh) | L1-56 (Novo) | Utilitário de injeção contínua L7/L4 com sondas diretas a todas as xApps. |
| Permissões Git (`100755`) | `scripts/*.sh` | Definido bit de execução executável nativo em todos os scripts bash via `git update-index --chmod=+x`. |

