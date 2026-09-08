# Volume 05: Guia de Simulação 5G NR no ns-3, Testes e Benchmarks Científicos

**Documento:** Volume Temático 05  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Instalação e Compilação do ns-3 NORI / 5G-LENA, Co-Simulação 5G NR no ns-3, Execução dos Cenários de Conflito em Tempo Real, Conexão E2 ao Near-RT RIC, Pipeline de Benchmarks e Análise de ML  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Arquitetura da Co-Simulação ns-3 / 5G-LENA

A validação experimental é realizada com o simulador de eventos discretos **ns-3 v3.40** integrado aos módulos:
* **5G-LENA (CTTC-LENA NR):** Pilha completa 3GPP Release 15/16/17 (PHY, MAC, RLC, PDCP, SDAP, BWP, Beamforming e Canais 3GPP TR 38.901).
* **ns-O-RAN / NORI:** Implementação do agente E2 na gNodeB com protocolo SCTP para o Near-RT RIC.
* **NrPointToPointEpcHelper (User Plane Core):** Roteamento IP fim a fim com tunelamento GTP-U e mapeamento de portadores de QoS (5QI).

![Arquitetura Fim-a-Fim](figures/cenario_3_arquitetura_cosimulacao_ns3_oran.png)

---

## 2. Instalação e Compilação do Ambiente ns-3 NORI / 5G-LENA

Para executar as simulações e co-simulações com o Near-RT RIC, o ambiente de simulação **ns-3 com 5G-LENA (CTTC-LENA NR) e ns-O-RAN (NORI)** precisa ser configurado e compilado.

### 2.1. Opção A: Instalação Automatizada (Recomendada)

O script automatizado instala todas as dependências do sistema (pacotes apt, GCC 11/12 para C++20, CMake >= 3.25), clona os repositórios oficiais e compila o ns-3 com CMake/Ninja:

```bash
# Executa o setup completo via Makefile:
make setup-ns3

# Ou execute diretamente o script bash:
bash scripts/setup_ns3.sh
```

> [!NOTE]
> O script cria o workspace em **`~/ns3-oran-workspace/ns-3-oran`** e compila o ns-3 com perfil otimizado (`-d optimized`), limitando o uso de threads paralelas para evitar estouro de memória RAM (OOM) no WSL2.

---

### 2.2. Opção B: Instalação Manual Passo a Passo

Caso prefira instalar manualmente ou customizar o diretório:

#### Passo 1: Instalar Dependências do Sistema (Ubuntu / Debian / WSL2)
```bash
sudo apt-get update -y && sudo apt-get install -y   build-essential cmake ninja-build git python3-dev python3-pip   pkg-config wget curl ca-certificates libsctp-dev lksctp-tools   libzmq3-dev libboost-all-dev libsqlite3-dev libgsl-dev libxml2-dev   tcpdump wireshark gcc-11 g++-11
```

#### Passo 2: Configurar o Compilador GCC/G++ 11+ (Suporte C++20 Obrigatório)
```bash
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 110 --slave /usr/bin/g++ g++ /usr/bin/g++-11
export CC=gcc-11
export CXX=g++-11
```

#### Passo 3: Clonar o ns-3-dev e o Módulo 5G-LENA (CTTC NR)
```bash
mkdir -p ~/ns3-oran-workspace && cd ~/ns3-oran-workspace
git clone https://gitlab.com/nsnam/ns-3-dev.git ns-3-oran --depth 1
cd ns-3-oran

# Clonar o módulo 5G-LENA (nr) dentro de contrib/
mkdir -p contrib
git clone https://gitlab.com/cttc-lena/nr.git contrib/nr --depth 1
```

#### Passo 4: Sincronizar os Cenários C++ do Projeto xApp RDL
```bash
# Copia os arquivos de simulação para a pasta scratch do ns-3:
mkdir -p scratch
cp simulations/ns3/*.cc scratch/
```

#### Passo 5: Configurar com CMake e Compilar com Ninja
```bash
cd ~/ns3-oran-workspace/ns-3-oran

# Configura o build otimizado com suporte a exemplos e testes:
./ns3 configure -d optimized --enable-examples --enable-tests

# Compila o núcleo e os cenários do scratch:
./ns3 build -j$(nproc)
```

---

### 2.3. Opção C: Execução com Caminho Personalizado (NS3_DIR)
Se o seu ns-3 estiver instalado em um caminho customizado (ex: `/opt/ns-3-dev` ou `/root/ns-allinone-3.40/ns-3.40`), passe a variável `NS3_DIR`:

```bash
make run-scenario1 NS3_DIR=/caminho/do/ns-3-oran
make run-scenario2 NS3_DIR=/caminho/do/ns-3-oran
```

---

## 3. Detalhamento dos Cenários de Simulação e Concorrência das 6 xApps

A validação experimental do projeto **xApp RDL (Fase 2: CA-RDL / MARL)** abrange uma matriz de **6 xApps concorrentes** operando sobre **5 cenários de simulação C++ no ns-3/5G-LENA/NORI** cobrindo 5G NR, 5G-Advanced (Rel. 18/19) e 6G AI-Native (IMT-2030):

### 3.0. Matriz das 6 xApps de Referência

| # | xApp de Referência | Diretório no Projeto | Objetivo / Ação Controlada | Tipo de Conflito Mitigado |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `ricxapp-qos-xslice` | [`reference-xapps/qos-xslice`](reference-xapps/qos-xslice) | Alocação de fatias (Slices) e garantia estrita de SLA URLLC/eMBB | Concorrência por Quotas de PRB e Prioridade |
| **2** | `ricxapp-energy-saving` | [`reference-xapps/energy-saving`](reference-xapps/energy-saving) | Redução de potência TX ($P_{\mathrm{tx}}$) e suspensão de portadoras | Degradação de SLA de usuários de borda |
| **3** | `ricxapp-traffic-steering` | [`reference-xapps/traffic-steering`](reference-xapps/traffic-steering) | Handover forçado por offset A3 e balanceamento de carga | Handover Ping-Pong e instabilidade de célula |
| **4** | `ricxapp-beamformer` | [`reference-xapps/beamformer`](reference-xapps/beamformer) | Controle de Downtilt elétrico e feixes Massive MIMO UPA ($16 \times 4$) | Interferência Intercelular e perda de cobertura |
| **5** | `ricxapp-isac-radar` | [`reference-xapps/isac-radar`](reference-xapps/isac-radar) | Alocação de feixes/símbolos de sensoriamento mmWave ($28\text{ GHz}$) | Competição de espectro ISAC vs Fluxos de Dados |
| **6** | `ricxapp-rogue-xapp` | [`reference-xapps/rogue-xapp`](reference-xapps/rogue-xapp) | Injeção de políticas conflitantes e anomalias de alta frequência ($5\text{ Hz}$) | Conflitos não-cooperativos e *Parameter Flipping* |

---

### 3.1. Cenário 1: Conflito Economia de Energia vs QoS / Slicing (EEVS — 5G NR)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_energy_vs_qos.cc`](simulations/ns3/scenario_rdl_energy_vs_qos.cc)
* **xApps Envolvidas:** `ricxapp-energy-saving` vs `ricxapp-qos-xslice`
* **Dinâmica:** A xApp `energy-saving` propõe redução de potência de transmissão (`TX_POWER`) e throttling de PRB para reduzir consumo elétrico, colidindo com a `qos-xslice`, que exige garantia de SLA com baixa latência para URLLC.
* **Topologia:** 1 Macro gNB ($3.5\text{ GHz}$, $50\text{ MHz}$) + 1 Micro gNB (Small Cell), 20 UEs com carga dinâmica.
* **Comandos:**
  ```bash
  make run-scenario1          # Modo RDL com interface E2 ativa
  make run-scenario1-baseline # Modo Baseline (sem RDL)
  ```

---

### 3.2. Cenário 2: Conflito Traffic Steering vs QoS / Handover Ping-Pong (TVS — 5G NR)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_tvs_conflict.cc`](simulations/ns3/scenario_rdl_tvs_conflict.cc)
* **xApps Envolvidas:** `ricxapp-traffic-steering` vs `ricxapp-qos-xslice`
* **Dinâmica:** A xApp `traffic-steering` tenta balancear carga forçando handovers de UEs entre duas células, gerando risco de instabilidade, handover ping-pong e degradação da fatia URLLC.
* **Topologia:** 2 gNodeBs separadas por 80 metros, 30 UEs divididos em 3 fatias de rede (URLLC 5QI 82, eMBB 5QI 9, mMTC 5QI 79).
* **Comandos:**
  ```bash
  make run-scenario2          # Modo RDL com interface E2 ativa
  make run-scenario2-baseline # Modo Baseline (sem RDL)
  ```

---

### 3.3. Cenário 3: 5G-Advanced Multi-Carrier FR1/FR3 & Massive MIMO UPA (16x4)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_5ga_multicarrier_mimo.cc`](simulations/ns3/scenario_rdl_5ga_multicarrier_mimo.cc)
* **xApps Envolvidas:** `ricxapp-beamformer`, `ricxapp-traffic-steering` e `ricxapp-qos-xslice`
* **Dinâmica:** Otimização coordenada de *vertical downtilt* ($6^\circ-8^\circ$), agregação de portadoras FR1 ($3.5\text{ GHz}$) + FR3 ($10.5\text{ GHz}$) e quotas de fatiamento sob mobilidade heterogênea (estáticos, pedestres e veiculares).
* **Topologia:** 3 gNodeBs em corredor urbano UMi ($1000\text{ m} \times 400\text{ m}$), 60 UEs, antenas UPA $16 \times 4$.

---

### 3.4. Cenário 4: Coexistência 6G ISAC (Radar Sensing vs Comunicação mmWave 28 GHz)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_6g_isac_sensing_coexistence.cc`](simulations/ns3/scenario_rdl_6g_isac_sensing_coexistence.cc)
* **xApps Envolvidas:** `ricxapp-isac-radar` vs `ricxapp-qos-xslice`
* **Dinâmica:** Competição direta por símbolos OFDM e feixes direcionais entre sensoriamento radar ($\Delta R = \frac{c}{2B}$) e tráfego de dados de ultra-alta capacidade.
* **Topologia:** 2 gNodeBs ISAC Dual-Function operando a $28\text{ GHz}$ ($400\text{ MHz}$ de banda), 30 UEs e alvos móveis.

---

### 3.5. Cenário 5: Governança Cross-Tier 6G & Escudo Anti-Rogue xApp
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_6g_cross_tier_governance.cc`](simulations/ns3/scenario_rdl_6g_cross_tier_governance.cc)
* **xApps Envolvidas:** `ricxapp-rogue-xapp` vs todas as xApps legítimas (`qos-xslice`, `energy-saving`, etc.)
* **Dinâmica:** Injeção contínua de ações conflitantes e maliciosas de alta frequência ($5\text{ Hz}$); contenção via *Lockout Cooling Window* de 5 segundos e *Safety Guards*.
* **Topologia:** Grade $2 \times 2$ com 4 gNodeBs e 40 UEs.

---

### 3.6. Execução Automatizada da Suíte Completa de Todos os Cenários
Para executar a suíte completa de todos os 5 cenários com múltiplas sementes aleatórias ($N=30$):
```bash
make run-all-scenarios
# Ou diretamente: bash scripts/run_all_scenarios_suite.sh
```

> [!NOTE]
> Para especificações aprofundadas de modelagem matemática, equações de recompensa MARL e formulação teórica de cada cenário, consulte o [Volume 11: Especificação de Cenários 5G/5GA/6G](docs/11_cenarios_de_teste_5g_5ga_6g_e_requisitos.md).


---

## 4. Parâmetros Reais dos Cenários em C++

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

## 5. Execução da Suíte Experimental e Benchmarks no Prompt

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

---

## 6. Galeria de Resultados Científicos e Cenários Simulados (Fase 2)

### 6.1. Cenário 1: Topologia Espacial e Conflito de Fatias de Rádio
![Cenário 1: Topologia](figures/cenario_1_topologia_tvs_conflict.png)

### 6.2. Cenário 2: Superfície de Trade-off Energy Saving vs QoS / Slicing
![Cenário 2: Trade-off](figures/cenario_2_tradeoff_energy_vs_qos.png)

### 6.3. Cenário 3: Arquitetura de Co-Simulação Fim-a-Fim ns-3 + Near-RT RIC
![Cenário 3: Arquitetura](figures/cenario_3_arquitetura_cosimulacao_ns3_oran.png)

### 6.4. Cenário 4: Comparativo Multidimensional de Métricas Reais (CDF, Boxplot, PDR e Governança)
![Cenário 4: Métricas Reais](figures/cenario_4_comparativo_multidimensional_metricas.png)

### 6.5. Cenário 5: Throughput Agregado, Alocação por Fatia e Equidade de Jain
![Cenário 5: Throughput e Jain Fairness](figures/cenario_5_vazao_throughput_e_jain_fairness.png)

### 6.6. Cenário 6: Agilidade de Decisão Near-RT, Perda de Pacotes e Estabilidade de Handover
![Cenário 6: Latência de Decisão e Handover](figures/cenario_6_latencia_decisao_e_estabilidade_handover.png)

### 6.7. Cenário 7: Dinâmica de Treinamento MARL, Convergência de Perdas e Safety Guards
![Cenário 7: Treinamento MARL](figures/cenario_7_marl_treinamento_convergencia_perdas.png)

### 6.8. Cenário 8: Radar Holístico Multidimensional de Governança O-RAN (Baseline vs Fase 1 vs Fase 2)
![Cenário 8: Radar Holístico](figures/cenario_8_radar_comparativo_holistico_3fases.png)

---

## 7. Procedimentos de Desinstalação e Limpeza Pós-Simulação

Ao término de qualquer simulação de cenário ou suíte de benchmarks, execute os comandos de desinstalação abaixo:

### 7.1. Desinstalação da xApp RDL Fase 2 (CA-RDL / MARL)
```bash
make helm-uninstall-f2
# ou: helm uninstall ricxapp-iqos-xapp-rdl-f2 -n ricxapp
```

### 7.2. Desinstalação Simultânea de Todas as Versões RDL
```bash
make uninstall-all-rdl
```

### 7.3. Verificação de Término e Status dos Pods
```bash
kubectl get pods -n ricxapp -o wide
```
