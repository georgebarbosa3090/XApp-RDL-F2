# 16 — RDL hierárquica (N1 + N2) na malha fechada da Fase 1 (2026-11-20)

Decisão do autor (2026-11-20): a partir daqui, os dois níveis rodam juntos nos cenários S0–S8. A RDL-N1 (regras: TVS, EEVS, Safety Guard, grafo de conhecimento) resolve os conflitos de baixa complexidade, e a RDL-N2 (MAPPO com restrição, docs/15) os de alta. Tudo o que a Fase 1 tem no laço continua igual: as xApps da malha fechada, cadeia E2, Safety Guard, rApp GreenRAN e, agora também, o rApp de governança no Non-RT RIC simulado.

**Correção (2026-11-21, depois do "Comparativo xApps originais e próprias"):** onde este documento fala em "xApps originais", leia no singular. Na malha fechada roda uma única xApp original de terceiros, o Traffic Steering do O-RAN SC (`ric-app-ts`, commit `beb44e0`), com a lógica de decisão sem alteração, adaptador E2 e AD e QP emulados. As demais são próprias (EnergySaver-GreenRAN, Load Balancer, ISAC Radar, Beamformer, URLLC Slice Guard no papel do xSlice) ou derivadas. As rodadas citadas aqui (`cl_s0s7`, `cl_s1245`, `cl_n12`) usam as xApps de antes das correções de 2026-11-21 (docs/16 da Fase 1, §10.16) e serão substituídas pelas campanhas novas.

## 1. Critério de roteamento

| Item | Valor |
| :-- | :-- |
| Código | `cardl/hierarchy.py` (`HierarchicalReasoning`, subclasse de `CARDLReasoning`; `attach_hierarchical` liga à `RDLxApp`) |
| Complexidade | `Reasoning.compute_complexity` da Fase 1: C(c, s) = 1,0 (direto) ou 1,8 (indireto) + 0,3 por ação além de 2 + 0,4 por parâmetro além de 1 |
| Vai à RDL-N2 | C(c, s) ≥ 1,8 **ou** o grafo de conhecimento mostra ao menos 1 outro conflito no mesmo alvo (nó e parâmetro) nos últimos 5 s de tempo simulado |
| Fica na RDL-N1 | o resto: decisão idêntica à do B3 (`Reasoning.resolve`) |
| Fora do escopo do MAPPO | a RDL-N2 devolve à RDL-N1 com o motivo (`CARDLReasoning._marl_ineligible`: sem checkpoint, MARL desligado pela A1 20002, conflito não direto, parâmetro que não é teto de PRB, mais de 3 candidatos) ou pela confiança abaixo do mínimo e pelo orçamento de tempo |
| Depois da decisão | Safety Guard, refinamento e cadeia E2 da Fase 1, sem mudança: a RDL-N2 escolhe, a Fase 1 ainda pode barrar |
| Variáveis | `RDL_COMPLEXITY_THRESHOLD` (1,8), `RDL_KG_RECENT_THRESHOLD` (1), `RDL_KG_LOOKBACK_S` (5), `CARDL_MIN_CONFIDENCE` (0,5), `CARDL_TIME_BUDGET_MS` (20), `CARDL_SELECTION` ou `CARDL_CHECKPOINT` e `CARDL_CHECKPOINT_SHA256` |

Descrição: o limiar 1,8 é o valor que a própria fórmula da Fase 1 dá a um conflito indireto de duas ações; um conflito direto de duas ações (C = 1,0) só sobe à RDL-N2 se for recorrente no grafo.

**Por que o grafo entra no critério.** O único caso em que o MAPPO foi treinado (disputa direta de teto de PRB entre duas xApps no mesmo gNB) tem C = 1,0. Com C sozinho, o modelo nunca seria chamado. A recorrência no grafo é o sinal de que a regra fixa não está encerrando a disputa: é esse o caso em que se quer a política aprendida.

**Tempo.** O grafo da Fase 1 grava `detected_at` em tempo de parede. Para que a janela de 5 s valha no tempo simulado do executor, o roteador grava no nó `conflict:<id>` o atributo `t_route` com o relógio que recebe (`clock`), além do nível e da complexidade. Na malha fechada, o relógio é o do executor (`HrdlStream`), o mesmo das janelas de 0,2 s.

**Rastro.** Cada resolução no `raw/closed_loop_log.jsonl` traz `level`, `complexity`, `kg_recent_conflicts`, `route_reason`, `t_route`, `source` (`MAPPO` ou `H_RDL`), `fallback_reason`, `confidence` e `mappo_latency_ms`.

## 2. Integração na malha fechada da Fase 1

Na Fase 1 (`scripts/closed_loop/orchestrator.py`, docs/16 da Fase 1):

- **baseline `N12`**: a mesma `RDLxApp` do B3 (EEVS aditivo), com o raciocínio trocado pelo `HierarchicalReasoning`. O código da Fase 2 vem de `RDL_F2_ROOT` (padrão: este repositório, ao lado do da Fase 1), sem instalar o pacote;
- **cabeçalho do log** (`rdl_n2`): commit e estado da árvore da Fase 2, checkpoint (caminho relativo) e sha256 esperado e carregado, limiares, confiança mínima e orçamento de tempo;
- **Non-RT RIC simulado**: além do rApp GreenRAN (A1 20001, 21000, 21001), o rApp de governança da Fase 1 (`rapps/governance_rapp.py`) lê a cada 10 s o relatório de governança da RDL e publica a A1 20000 (modos e tetos de prioridade das xApps; quarentena a partir de 5 rejeições do Safety Guard ou 20 não autorizadas) quando ela muda. No N12, o RIC entrega também a A1 20002 (`marl_enabled: true`, `min_confidence`). A governança fica ligada no B3 e no N12, para que a comparação seja justa; `--sem-governanca` reproduz as rodadas anteriores. O B0 não tem RDL e não recebe nenhuma das duas;
- **testes**: `tests/unit/test_closed_loop_n12.py` (roteamento e rastro, quarentena pela governança, A1 20002, governança desligada).

Nesta Fase 2: `tests/test_hierarchy.py` (8 testes, 2 deles com PyTorch e um checkpoint gerado no teste) e dois scripts de leitura das execuções:

| Script | O que conta |
| :-- | :-- |
| `experiments/closed_loop/escopo_mappo.py` | nas execuções B3 já feitas, quantos conflitos arbitrados a RDL-N2 mandaria ao MAPPO pela regra do próprio motor, e por que os outros vão à reserva |
| `experiments/closed_loop/resumo_n12.py` | numa execução N12: conflitos por nível, motivo do roteamento, origem da decisão na RDL-N2, motivos da reserva, A1 entregues e publicações da 20000 |

## 3. Escopo do MAPPO nos cenários da Fase 1 (antes de rodar)

`escopo_mappo.py` sobre as rodadas B3 da Fase 1 com as xApps da malha fechada (`cl_s0s7`, `cl_s1245`; uma original, o TS, e as demais próprias ou derivadas): só o S6 teve conflitos que o MAPPO aceitaria (3 disputas diretas de teto de PRB). Os demais conflitos arbitrados foram indiretos ou entre células (handover, potência, estado de célula), fora do que o modelo conhece, e iriam à reserva. No S5, as resoluções eram recusas da proteção do ping-pong (`PINGPONG_GUARD`), que a `RDLxApp` decide antes da arbitragem e que não chegam ao raciocínio.

Consequência esperada para a campanha: a RDL-N2 recebe os conflitos de alta complexidade, mas na maioria deles devolve à RDL-N1 com motivo registrado. O N12 deve ficar próximo do B3 até que exista um ambiente de treino mais amplo (handover, potência, estado de célula, conflitos indiretos), calibrado com os registros de S0–S7, e um novo treino. Essa é a etapa seguinte, decidida pelo autor ("integrar já, retreinar depois").

## 4. Verificação

- Testes (Windows, venv da Fase 2 com PyTorch 2.14.1+cpu, Fase 1 local no `PYTHONPATH`): `tests/test_hierarchy.py` e `tests/test_cardl.py`, 21 passaram. Na Fase 1, os 3 testes de `test_closed_loop_n12.py` passaram, e a suíte de unidade teve 479 aprovados, 21 ignorados e 4 falhas de ambiente: os testes HTTP exigem o pacote `httpx2`, que o `starlette` desse venv pede e que não está instalado. Nenhum dos quatro importa os arquivos alterados.
- Ubuntu do WSL (venv da Fase 1, PyTorch 2.15.0+cpu instalado para esta etapa): com o checkpoint selecionado (`experiments/training/mappo_seed101/actor_critic.pt`, sha256 `77f88301…`, conferido ao carregar), uma disputa de teto de PRB repetida no mesmo gNB a cada 0,2 s ficou na RDL-N1 na primeira vez (C = 1,0, sem histórico) e foi à RDL-N2 nas duas seguintes (grafo: 1 e 2 conflitos no alvo em 5 s). O MAPPO decidiu, com confiança 0,996 e latência de 1,4 e 0,5 ms. O Safety Guard da Fase 1 barrou a ação escolhida pelo limite de frequência de controle do mesmo alvo, como faz com qualquer decisão.

## 5. Primeira rodada: S5 com UEs em movimento (2026-11-21)

S5 da Fase 1 com metade dos 24 UEs andando a 5 m/s entre as células (proposta P3, docs/16 da Fase 1, §10.15), semente 16907, B0, B3 e N12, cerca de 31 min por execução. As três terminaram com `SUCCESS`. Números de `avaliar_pingpong.py` e do painel da Fase 1 e, no N12, de `resumo_n12.py`.

| S5, P3 | ações | handovers pedidos | voltas em 5 s | vazão (Mb/s) | atraso (ms) | conflitos N1 / N2 | origem na N2 |
|---|---|---|---|---|---|---|---|
| B0 | 32 | 28 | 12 | 90,039 | 10,317 | sem RDL | sem RDL |
| B3 | 25 | 22 | 8 | 90,320 | 9,227 | 13 (só N1) | não se aplica |
| N12 | 25 | 22 | 8 | 90,320 | 9,227 | 0 / 13 | 13 reservas à RDL-N1 |

Descrição: no N12, os 13 conflitos foram indiretos (handover do Traffic Steering contra o teto de PRB do Load Balancer no mesmo gNB), com C(c, s) = 2,2; 1 subiu à RDL-N2 só pela complexidade e 12 pela complexidade e pela recorrência no grafo (1 a 5 conflitos no mesmo alvo em 5 s). Todos voltaram à RDL-N1 com `conflito INDIRECT fora do escopo do MAPPO`. O Non-RT RIC entregou a A1 20002 uma vez e a 20001 três vezes; a governança não publicou A1 20000.

- **N12 igual ao B3**, ação por ação, como previsto na §3: o MAPPO não decidiu nenhum conflito, porque não houve disputa direta de teto de PRB.
- **B3 e N12 contra B0**: a única diferença foi em t = 26,6 s, quando o limite de frequência do Safety Guard da Fase 1 recusou uma volta do UE 6 pedida pelo Traffic Steering 0,6 s depois do mesmo controle. No B0 o UE seguiu alternando entre as células até o fim. O detalhe está na §10.15 da Fase 1.
- **Roteamento**: o caminho completo funcionou na malha fechada com ns-3 (critério, rastro no log, reserva com motivo, A1 20002 e governança), com o checkpoint conferido pelo sha256 ao carregar. Latência do MAPPO não se aplica, porque nenhuma decisão foi dele.

## 6. Limites

- **Não é evidência de publicação.** O MAPPO só foi treinado no ambiente calibrado (`publication_eligible: false`, docs/15), e as afirmações C1–C6 seguem `NOT_VERIFIED`. As rodadas N12 são exploratórias.
- **Proveniência.** As primeiras execuções N12 rodam com esta árvore suja (`f2_git_dirty: true`, caminhos no cabeçalho), porque o roteador ainda não tem commit.
- **S8 (bancada NORI).** A decisão lá roda dentro da xApp `kpm-probe`, implantada por Helm a partir do código da Fase 1 com commit. Levar o N12 ao S8 exige commits nas duas fases, o pacote da Fase 2 e o checkpoint no ConfigMap, e o PyTorch para Python 3.10 no pod (outro download). Fica pendente de decisão do autor.
