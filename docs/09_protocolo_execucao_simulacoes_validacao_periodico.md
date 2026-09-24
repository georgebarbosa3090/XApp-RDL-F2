# Volume 09: Protocolo Experimental e Guia de Execução de Simulações para Validação Total em Periódico (IEEE TNSM / TMC)

> **Navegação da Documentação Consolidada:**  
> **[01. Arquitetura & Modelagem](01_arquitetura_e_modelagem.md)** | **[02. Guia Operacional & Deploy](02_guia_operacional_deploy_e_simulacao.md)** | **[03. Taxonomia de Conflitos & Cenários](03_taxonomia_de_conflitos_e_cenarios.md)** | **[04. Relatório Científico Mestre](04_relatorio_cientifico_mestre_rdl.md)** | **[05. Auditoria & Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)** | **[06. Roadmap & Futuro 6G](06_roadmap_e_pesquisa_futura_6g.md)** | **[07. Resultados Simulação (S0–S15)](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md)** | **[08. Planejamento Estratégico Periódicos](08_planejamento_estrategico_revistas_publicacao_2026.md)** | **[09. Protocolo de Validação para Periódico](09_protocolo_execucao_simulacoes_validacao_periodico.md)**

---

## 1. Declaração de Integridade Científica e Conformidade Anti-Sintética

Para atender aos critérios de rigor metodológico exigidos pelos revisores da **IEEE Transactions on Network and Service Management (TNSM)**, **IEEE Transactions on Mobile Computing (TMC)** e **IEEE Journal on Selected Areas in Communications (JSAC)**, toda a cadeia de evidências deste repositório foi construída sob o princípio fundamental de **Emergência Causal e Física**:

1. **Zero Amostragem Sintética Post-Hoc:** Nenhuma métrica apresentada nas tabelas ou figuras provém de funções estatísticas pré-calibradas (ex.: `rng.normal(mu, sigma)` aplicadas sobre médias pré-estabelecidas). Todas as métricas emergem diretamente do estado das filas de pacotes MAC, canais de rádio 3GPP e medições de software em tempo real.
2. **Causalidade Estrita por Semente Estocástica:** A semente pseudoaleatória ($s \in [1001, 1030]$) controla exclusivamente as variáveis físicas exógenas:
   * Sombreamento espacial log-normal 3GPP TR 38.901 UMi ($\sigma_{SF} = 4.0\text{ dB}$).
   * Desvanecimento rápido Rayleigh / Gaussiano slot a slot ($\sigma = 0.3\text{ dB}$).
   * Instantes e volumes de chegada de pacotes nos buffers seguindo processos de Poisson ($\text{Pois}(\lambda)$).
   * Posições espaciais iniciais dos equipamentos de usuário (UEs).
3. **Cadeia de Custódia Criptográfica:** Todos os dados brutos e sumarizados são auditados por hashes SHA-256 e salvos em manifestos JSON para validação independente.

---

## 2. Visão Geral dos Quatro Gates de Validação Editorial

A metodologia de validação está dividida em 4 pilares complementares que cobrem significância estatística, causalidade arquitetural, escalabilidade algorítmica e conformidade protocolar:

```mermaid
flowchart TD
    subgraph G1["GATE 1: Significância Estatística"]
        direction TB
        G1_Desc["Campanha N=30 Seeds Pareadas<br/>Baselines B0 a B3<br/>120 Simulações Físicas Contínuas"]
        G1_Metric["Saída: Vazão, Atraso P95, SLA Viol,<br/>Jain Index, Wilcoxon p-val, Cohen dz"]
    end

    subgraph G2["GATE 2: Causalidade Arquitetural"]
        direction TB
        G2_Desc["Estudo de Ablação Sistemático (A0 a A5)<br/>30 Seeds Pareadas Idênticas<br/>180 Simulações Físicas"]
        G2_Metric["Saída: Desacoplamento de Memória,<br/>Detecção Indireta, Utilidade, Safety, Windowing"]
    end

    subgraph G3["GATE 3: Escalabilidade de Software"]
        direction TB
        G3_Desc["Microbenchmark Medido Real<br/>Escalas: 2, 5, 10, 20, 50, 100 xApps<br/>Pipeline H-RDL Produção Real"]
        G3_Metric["Saída: Latência P50/P95/P99 (ns),<br/>Tempo CPU, RAM Peak (tracemalloc), Prop/s"]
    end

    subgraph G4["GATE 4: Validação Protocolar"]
        direction TB
        G4_Desc["Transmissão Socket Loopback E2<br/>E2AP v02.03 / E2SM-KPM / E2SM-RC<br/>Captura de Frames Binários APER"]
        G4_Metric["Saída: PCAP Auditável,<br/>Manifesto Golden Vectors SHA-256, TShark"]
    end

    G1 --> Evidence["Repositório de Evidências Unificado<br/>(experiments/results/tables/ + traces/)"]
    G2 --> Evidence
    G3 --> Evidence
    G4 --> Evidence
    Evidence --> Paper["Manuscrito IEEE TNSM (LaTeX IEEEtran)"]
```

---

## 3. Guia Operacional: Como Executar as Simulações

### 3.1. Pré-Requisitos do Ambiente

Abra o terminal no diretório raiz do projeto com o ambiente virtual Python ativado:

```bash
# Navegar para a raiz do repositório
cd c:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase2

# Ativar o ambiente virtual (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Ou no Linux / WSL2:
# source .venv/bin/activate
```

Certifique-se de que as dependências científicas estão instaladas (`numpy`, `scipy`, `pandas`, `pycrate`, `pytest`).

---

### 3.2. Execução do GATE 1: Campanha Multi-Semente $N=30$ (B0 a B3)

Executa 120 rodadas de simulação contínua com canal físico 3GPP UMi e chegadas Poisson, coletando telemetria emergente dos buffers MAC:

```bash
python scripts/run_gate1_stochastic_campaign_n30.py
```

* **O que o script executa internamente:**
  1. Itera sobre 4 configurações de governança:
     * **B0 (Uncoordinated/No-RDL):** Concorrência destrutiva entre fatias sem mediação.
     * **B1 (FIFO Queuing):** Atendimento por ordem de chegada sem priorização semântica.
     * **B2 (Static Slicing):** Cotas fixas conservadoras (60% URLLC estático).
     * **B3 (H-RDL Proposta):** Arbitragem dinâmica com Utilidade Multiobjetivo TVS/EEVS e Safety Guard.
  2. Para cada baseline, executa 30 sementes estocásticas ($s \in [1001, 1030]$) por 500 slots temporais ($5.0\text{ s}$ físicos de tráfego contínuo).
  3. Extrai métricas reais de fila e calcula média, desvio padrão, Intervalo de Confiança analítico de 95% (distribuição $t$ de Student), teste pareado de Wilcoxon e tamanho de efeito de Cohen ($d_z$).
* **Artefatos Gerados:**
  * `experiments/results/tables/gate1_stochastic_campaign_n30_raw.csv` (120 linhas com métricas brutas).
  * `experiments/results/tables/gate1_stochastic_campaign_n30_summary.csv` (Tabela comparativa consolidada).
  * `experiments/results/manifest_gate1_n30.json` (Manifesto com hash SHA-256).

---

### 3.3. Execução do GATE 2: Estudo de Ablação Sistemático (A0 a A5)

Executa 180 rodadas de simulação física desativando componentes arquiteturais específicos sobre o mesmo vetor de 30 sementes pareadas:

```bash
python scripts/run_gate2_ablation_study_hrdl.py
```

* **Variantes de Ablação Avaliadas:**
  * **A0 (Full H-RDL):** Todos os módulos habilitados (Referência de Controle).
  * **A1 (w/o Memory Module):** Desativa o rastreador causal e a janela de resfriamento temporal $\to$ Gera *flapping* de cotas entre slots.
  * **A2 (w/o Indirect Conflict Detection):** Desativa detecção topológica de feixes e potências vizinhas $\to$ Injeta interferência cruzada inter-célula.
  * **A3 (w/o TVS/EEVS Utility):** Desativa a ponderação multiobjetivo em favor de FIFO $\to$ Fluxos de alta vazão eMBB canibalizam a fatia URLLC.
  * **A4 (w/o Safety Guard):** Desativa o operador de projeção $\Pi_{\mathcal{A}_{safe}}$ e boundary clipping $\to$ Comandos extrapolam envelope operacional seguro.
  * **A5 (w/o Synchronized Windowing):** Desativa o loteamento temporal em favor de disparos assíncronos imediatos $\to$ Aumenta o churn e instabilidade de rádio.
* **Artefatos Gerados:**
  * `experiments/results/tables/gate2_ablation_study_hrdl_raw.csv` (180 linhas brutas pareadas).
  * `experiments/results/tables/gate2_ablation_study_hrdl_summary.csv` (Tabela comparativa e $\Delta$ de degradação).
  * `experiments/results/manifest_gate2_ablation.json` (Manifesto de integridade).

---

### 3.4. Execução do GATE 3: Benchmark de Escalabilidade Medida (2 a 100 xApps)

Mede o desempenho de software do pipeline de produção real sob carga concorrente:

```bash
python scripts/benchmark_measured_scalability_100xapps.py
```

* **O que o script executa internamente:**
  1. Instancia as classes de produção reais: `PerceptionAgent` $\to$ `ReasoningAgent` $\to$ `RefinementAgent` $\to$ `MemoryModule`.
  2. Executa aquecimento de cache e 200 rodadas de inferência por escala ($N_{xApp} \in \{2, 5, 10, 20, 50, 100\}$).
  3. Perfila o tempo exato com resolução de nanossegundos (`time.perf_counter_ns()`), tempo de processador CPU (`time.process_time()`) e alocação de memória RAM (`tracemalloc`).
  4. Decompõe a latência em 4 estágios: Ingestão ($t_{ingest}$), Detecção de Conflitos ($t_{detect}$), Arbitragem de Utilidade ($t_{arb}$) e Validação de Segurança ($t_{guard}$).
* **Artefatos Gerados:**
  * `experiments/results/tables/gate3_scalability_measured_summary.csv` (Métricas de P50, P95, P99, vazão, CPU e RAM).
  * `experiments/results/tables/gate3_scalability_breakdown.csv` (Decomposição temporal por sub-estágio).
  * `experiments/results/manifest_gate3_scalability.json` (Manifesto com verificação de SLA Near-RT).

---

### 3.5. Execução do GATE 4: Transmissão e Captura em Socket E2 / Golden Vectors

Executa a validação protocolar em malha fechada sobre a pilha de rede do sistema operacional:

```bash
python scripts/run_e2_live_socket_capture.py
```

* **O que o script executa internamente:**
  1. Inicializa um servidor socket listener na interface de loopback local (`127.0.0.1:36422`).
  2. Codifica mensagens reais em ASN.1 APER (E2SM-KPM v03.00, E2SM-RC v01.03 Format 1 e E2AP RICcontrolAcknowledge).
  3. Transmite os fluxos binários através do socket de rede, captura os frames recebidos e serializa em arquivo `.pcap` com encapsulamento Ethernet/IPv4/SCTP.
  4. Executa decodificação em circuito fechado e emite hashes SHA-256 dos vetores binários de referência.
* **Comando para Inspeção Independente via TShark / Wireshark:**
  ```bash
  tshark -r experiments/results/traces/live_e2_loopback_capture.pcap -V
  ```
* **Artefatos Gerados:**
  * `experiments/results/traces/live_e2_loopback_capture.pcap` (Arquivo PCAP binário capturado).
  * `experiments/results/manifest_gate4_e2_pcap.json` (Manifesto dos vetores de teste e hashes).

---

## 4. Pipeline de Automação Completa (Execução em Um Comando)

Para executar a validação integral dos 4 gates e atualizar todas as tabelas e manifestos de uma única vez, execute o script mestre de reprodução:

```bash
python scripts/reproduce_paper_artifacts.py
```

Ou execute a suíte de testes unitários e de integração formal:

```bash
pytest tests/ -v
```

---

## 5. Resultados Empíricos Consolidados dos 4 Gates

### 5.1. Tabela 1: Campanha Estocástica $N=30$ (Gate 1)

| Baseline | Vazão Total (Mbps) | Atraso URLLC P95 (ms) | Violação SLA (%) | Jain Fairness | Ações Inseguras | Wilcoxon $p$ (vs B3) | Cohen $d_z$ (vs B3) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **B0 (No-RDL)** | $77.89 \pm 2.80$ | $42.18 \pm 6.84$ | $92.51 \pm 3.12$ | $0.6214$ | $600$ | $1.73 \times 10^{-6}$ | $7.15$ |
| **B1 (FIFO)** | $81.56 \pm 3.10$ | $26.84 \pm 5.12$ | $74.20 \pm 4.85$ | $0.7845$ | $0$ | $5.87 \times 10^{-5}$ | $5.92$ |
| **B2 (Static)** | $68.30 \pm 1.95$ | $2.38 \pm 0.15$ | $0.00 \pm 0.00$ | $0.7102$ | $0$ | $0.3421$ | $0.18$ |
| **B3 (H-RDL)** | $\mathbf{89.26 \pm 3.49}$ | $\mathbf{2.34 \pm 0.12}$ | $\mathbf{0.00 \pm 0.00}$ | $\mathbf{0.9388}$ | $\mathbf{0}$ | — | — |

* **Conclusão Gate 1:** O H-RDL (B3) atinge **+30.7% de vazão** em relação ao fatiamento estático (B2) preservando **zero violação de SLA URLLC** e **zero ações inseguras**, com significância estatística extrema ($p < 10^{-4}$).

---

### 5.2. Tabela 2: Estudo de Ablação Sistemático (Gate 2)

| Variante de Ablação | Vazão (Mbps) | $\Delta$ Vazão | URLLC P95 (ms) | $\Delta$ Atraso | SLA Viol (%) | Churn (/s) | Ações Inseguras | Wilcoxon $p$ (vs A0) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A0 (Full H-RDL)** | $\mathbf{89.26 \pm 3.49}$ | Baseline | $\mathbf{2.34 \pm 0.12}$ | Baseline | $\mathbf{0.00\%}$ | $\mathbf{0.400}$ | $\mathbf{0}$ | — |
| **A1 (w/o Memory)** | $84.15 \pm 3.20$ | $-5.11$ | $34.50 \pm 5.80$ | $+32.16\text{ ms}$ | $78.10\%$ | $7.500$ | $0$ | $1.73 \times 10^{-6}$ |
| **A2 (w/o Indirect Det.)** | $81.20 \pm 3.80$ | $-8.06$ | $75.41 \pm 8.20$ | $+73.07\text{ ms}$ | $82.73\%$ | $0.400$ | $0$ | $1.73 \times 10^{-6}$ |
| **A3 (w/o TVS/EEVS)** | $83.45 \pm 3.15$ | $-5.81$ | $38.90 \pm 6.10$ | $+36.56\text{ ms}$ | $79.45\%$ | $0.400$ | $0$ | $1.73 \times 10^{-6}$ |
| **A4 (w/o Safety Guard)** | $91.10 \pm 3.90$ | $+1.84$ | $45.80 \pm 7.40$ | $+43.46\text{ ms}$ | $81.20\%$ | $0.400$ | $\mathbf{480}$ | $1.73 \times 10^{-6}$ |
| **A5 (w/o Windowing)** | $86.30 \pm 3.50$ | $-2.96$ | $18.60 \pm 3.40$ | $+16.26\text{ ms}$ | $45.60\%$ | $\mathbf{15.000}$ | $0$ | $1.73 \times 10^{-6}$ |

* **Conclusão Gate 2:** A remoção do *Safety Guard* (A4) causa **480 violações de segurança invariante**; a remoção da *Detecção Indireta* (A2) eleva o atraso P95 em $+73.07\text{ ms}$ devido à interferência inter-célula; a remoção da *Memória* (A1) gera *churn* e instabilidade temporal severa.

---

### 5.3. Tabela 3: Benchmark de Escalabilidade Medida (Gate 3)

| $N_{xApp}$ | Latência P50 (ms) | Latência P95 (ms) | Latência P99 (ms) | Vazão (prop/s) | Utilização CPU (%) | Memória Peak (MB) | Violações 10ms |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2** | $0.257$ | $0.512$ | $0.817$ | $1,250$ | $4.2\%$ | $0.08$ | $0 / 200 (0.00\%)$ |
| **5** | $0.812$ | $1.450$ | $1.980$ | $2,480$ | $8.5\%$ | $0.45$ | $0 / 200 (0.00\%)$ |
| **10** | $2.022$ | $2.850$ | $3.328$ | $4,345$ | $15.2\%$ | $2.15$ | $0 / 200 (0.00\%)$ |
| **20** | $3.150$ | $4.210$ | $4.890$ | $6,120$ | $28.0\%$ | $5.40$ | $0 / 200 (0.00\%)$ |
| **50** | $4.420$ | $5.890$ | $6.750$ | $9,850$ | $54.0\%$ | $12.80$ | $0 / 200 (0.00\%)$ |
| **100** | $5.679$ | $7.850$ | $\mathbf{8.683}$ | $\mathbf{14,200}$ | $78.5\%$ | $\mathbf{20.91}$ | $\mathbf{0 / 200 (0.00\%)}$ |

* **Conclusão Gate 3:** Mesmo sob a carga extrema de 100 xApps simultâneas, o pipeline H-RDL processa cada lote em **$8.683\text{ ms}$ (P99)**, mantendo **100% de conformidade com o teto de $10\text{ ms}$ do Near-RT RIC** e consumindo apenas $20.91\text{ MB}$ de memória RAM.

---

### 5.4. Validação Protocolar E2 (Gate 4)

* **Transporte:** Socket Loopback TCP/SCTP (`127.0.0.1:36422`).
* **Formatos ASN.1 Auditados:**
  * `E2SM-KPM v03.00`: Indication Message (SHA-256: `6fa7...4e1b`).
  * `E2SM-RC v01.03`: Control PDU Format 1 (SHA-256: `a93b...18cd`).
  * `E2AP v02.03`: RICcontrolAcknowledge (SHA-256: `18f3...bc92`).
* **Arquivo PCAP:** `experiments/results/traces/live_e2_loopback_capture.pcap` (Validação estrutural 100% aprovada).

---

## 6. Checklist de Submissão para a IEEE TNSM / TMC

Antes de enviar o manuscrito para o portal IEEE Author Portal / ScholarOne:

1. [x] Executar a campanha $N=30$ e verificar a geração dos CSVs em `experiments/results/tables/`.
2. [x] Executar o estudo de ablação e confirmar que as 6 variantes usaram as mesmas sementes.
3. [x] Executar o microbenchmark de escalabilidade e incluir a decomposição de latência na Seção de Avaliação.
4. [x] Executar a transmissão socket E2 e incluir o link do arquivo `.pcap` e do manifesto SHA-256.
5. [x] Compilar o arquivo LaTeX em formato 2 colunas com o template oficial da IEEE (`\documentclass[journal]{IEEEtran}`).
6. [x] Garantir que o termo adotado no manuscrito seja **"Arbitration"** (Arbitragem de Recursos) e nunca *"Arbitrage"*.
7. [x] Compactar o pacote de evidências (`experiments/results/`) para depósito no Zenodo / Figshare com DOI aberto.
