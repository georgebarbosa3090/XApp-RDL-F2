# 17. Ambiente de treino ampliado da RDL-N2: outras famílias de conflito (proposta, 2026-11-21)

Situação: proposta com a base implementada (§7: registro de famílias, ambiente da família C, calibração e extrator do dataset); nenhuma política treinada ainda. Responde à decisão do autor "integrar já, retreinar depois" (docs/16, §3): hoje o MAPPO só decide disputas diretas de teto de PRB no mesmo gNB, e a RDL-N2 devolve todo o resto à RDL-N1. Este documento especifica o ambiente e o treino para que ela passe a decidir outros tipos de conflito. Nada aqui muda a Fase 1.

## 1. O que aparece de fato nos cenários da Fase 1

**Correção (2026-11-21, depois do "Comparativo xApps originais e próprias"):**
- **Uma só xApp original.** Onde este documento fala em "xApps originais", leia no singular. Na malha fechada roda uma única xApp original de terceiros, o Traffic Steering do O-RAN SC (`ric-app-ts`, commit `beb44e0`), com a lógica de decisão sem alteração, adaptador E2 e AD e QP emulados. As demais são próprias ou derivadas.
- **Famílias sem a original.** As famílias com participação da original são as que têm handover (C, D e P). As famílias A e B só têm xApps próprias, e o texto dos artigos precisa dizer isso.
- **Dados antigos.** As rodadas contadas abaixo usam as xApps de antes das correções da Fase 1 (docs/16 da Fase 1, §10.16):
  - o xSlice derivado oscilava e parava de propor depois de uma recusa (hoje é a URLLC Slice Guard);
  - a EnergySaver subia a potência de 4 para 30 dBm ao "reduzir";
  - o Beamformer era inerte.
  
  A calibração do ambiente (§5) e as contagens serão refeitas com as campanhas novas.

Contagem das resoluções registradas em `raw/closed_loop_log.jsonl` das execuções em malha fechada com as xApps da malha fechada e B3 (RDL-N1). S0–S7: rodadas `cl_s0s7` (semente 16905), `cl_s1245` (16907), `cl_p1x85`, `cl_p1uex85` e `cl_p3v5` (S5, 16907) e a parte já concluída da `cl_n12` (S0–S3, 16908). S9–S15 e G1–G2: piloto `cl_piloto` (16901).

| Família | Tipo | Parâmetros | Cenários | Resoluções | Decisão da RDL-N1 |
| :-- | :-- | :-- | :-- | :-: | :-- |
| A | direto, mesmo gNB | teto de PRB × teto de PRB | S6 | 3 | TVS escolhe uma |
| B | indireto, mesmo gNB | teto de PRB × potência | S1, S3, S6, S12 | 22 | EEVS mantém as duas |
| C | indireto, mesmo gNB | handover × teto de PRB | S2, S5, S11, G1 | 23 | EEVS mantém as duas |
| D | indireto ou entre células | estado de célula ou potência × handover; estado de célula × potência | S13, S15 | 16, dos quais 11 com a Rogue ou o `fault_injector`; 5 entre xApps legítimas | EEVS mantém todas em 12; descarta uma em 4 (3 entre células) |
| P | entre células | handover × handover em sentidos opostos (ping-pong) | S5 | 67 | proteção da ação recente (`PINGPONG_GUARD`) |

Descrição: cada linha agrupa as resoluções pelo tipo de conflito e pelos parâmetros das ações envolvidas. Em S0, S4 e S7 nenhuma resolução foi registrada. A família P é decidida pela `RDLxApp` antes do raciocínio e não passa pela RDL-N2. Desde 2026-11-21, conflitos com a Rogue (teste de segurança) ou com o `fault_injector` (evento agendado do cenário) não pertencem a nenhuma família: `cardl/families.py` os deixa fora (`TEST_XAPPS`), a RDL-N2 os devolve à RDL-N1 com o motivo registrado, e o extrator marca essas resoluções (`test_xapp`). Na família D do piloto 16901, 11 das 16 resoluções eram desse tipo (contagem por script com `classify_params` sobre as 9 execuções B3 do piloto). A `cl_n12` foi abortada em 2026-11-21. As contagens serão refeitas com as campanhas novas, de 5 sementes, só no modo multinível.

**Consequência para o desenho.** Nas famílias B, C e D, o EEVS manteve as duas ações em 57 de 58 conflitos indiretos. Copiar a RDL-N1 não acrescenta nada; a decisão que uma política aprendida pode melhorar é outra: **segurar uma das ações** (ou as duas) quando a combinação piora a rede, por exemplo baixar a potência no mesmo momento em que um handover traz UEs para a célula. A família A é a única em que a escolha é "qual vence".

Também fica registrado o caso da P3 do S5 (docs/16 da Fase 1, §10.15): o vaivém de um UE pedido pela mesma xApp não é conflito entre xApps; quem o conteve foi o limite de frequência do Safety Guard. Esse caso está fora do escopo de qualquer política de conflito.

## 2. Desenho proposto

Uma política por família, com o mesmo MAPPO com restrição do docs/15 (ator compartilhado, crítico centralizado com saídas de recompensa e de custo, multiplicador de Lagrange). Políticas separadas mantêm cada observação pequena, permitem selecionar e desligar cada uma pelo seu critério, e não perdem a política da família A, que já está selecionada.

| Item | Família B (PRB × potência) | Família C (handover × PRB) | Família D (energia × mobilidade) |
| :-- | :-- | :-- | :-- |
| Agentes | um por gNB em conflito | um por gNB em conflito | um por célula envolvida |
| Ações (2 candidatas) | manter as duas, só o teto, só a potência, nenhuma (4) | manter as duas, só o handover, só o teto, nenhuma (4) | idem, sobre as ações de estado, potência e handover (4; 8 com 3 candidatas) |
| Máscara | Safety Guard da Fase 1 (`check_bounds` e limite de frequência) sobre cada ação | idem | idem |
| Observação da célula | teto de PRB, uso de PRB, potência, UEs, vazão, atraso | idem | idem, mais estado (dormindo ou não) |
| Observação das candidatas | parâmetro, valor, prioridade, xApp de energia ou não | idem, mais UE, célula de destino, RSRP nas duas células, SINR | idem |
| Recompensa | satisfação ponderada das fatias + economia de energia − mudanças | satisfação dos UEs (vazão sobre oferta) − handovers − voltas em até 5 s | economia de energia + satisfação − mudanças |
| Custo do CMDP | fatia crítica abaixo de 95 % da demanda | perda de conexão em até 3 s depois de um handover | UE sem conexão (cobertura) |

Descrição: "manter as duas" reproduz a decisão do EEVS e é o ponto de partida; a política só ganha se aprender quando segurar uma ação. As observações usam só campos que o KPM da malha fechada já entrega (por célula: potência, estado, teto, uso de PRB, UEs, vazão, atraso; por UE: célula, conexão, vazão, atraso, SINR e RSRP em cada célula), para que a mesma política rode no ns-3 sem mudar a Fase 1.

**Roteamento.** O critério do docs/16 não muda (C(c, s) ≥ 1,8 ou recorrência no grafo). Muda só a checagem de escopo (`CARDLReasoning._marl_ineligible`): em vez de aceitar apenas conflito direto de teto de PRB, ela consulta um registro de famílias, cada uma com o seu checkpoint e sha256 em `experiments/training/selection.json`. Família sem política selecionada continua indo à RDL-N1, com o motivo no log. A A1 20002 ganha a lista de famílias ligadas.

## 3. Calibração

Cada família precisa de um modelo de resposta da RAN, como a curva teto de PRB → vazão do docs/15 (medida no NORI). As fontes possíveis:

| Família | Resposta a calibrar | Fonte |
| :-- | :-- | :-- |
| B | vazão da célula em função do teto e da potência; uso de PRB | KPM antes e depois das ações em S1, S3, S6 e S12 (ns-3); a curva de PRB do NORI continua valendo para o teto |
| C | vazão, SINR e conexão do UE depois do handover, em função da diferença de RSRP e da carga das duas células | KPM por UE nas janelas seguintes a cada handover em S2, S5, S11 e G1 (ns-3) |
| D | cobertura e vazão com célula dormindo ou com potência reduzida | S13 e S15 (ns-3) |
| todas | energia consumida | modelo já decidido na Fase 1 (docs/17 da Fase 1): 3GPP TR 38.864 V18.1.0 como principal e EARTH (Auer et al., 2011) como robustez, aplicados à ocupação medida no ns-3 (`scripts/certification/energy_model.py`, parâmetros conferidos por sha256). Conclusão sobre energia só vale se o sinal for o mesmo nos dois modelos (H13.3 da Fase 1) |

Descrição: a calibração ajusta distribuições e curvas a partir das janelas registradas, e o ambiente sorteia a partir delas; não reproduz execuções.

**Volume.** Os conflitos reais são poucos (dezenas por família), mas a calibração usa todas as janelas com KPM antes e depois de cada ação aplicada, não só as que tiveram conflito. Mesmo assim, as curvas terão incerteza larga; isso entra nos limites de cada treino.

**Separação.** Calibrar com as rodadas das sementes 16901, 16905 e 16907 e reservar a `cl_n12` (16908) para validar o ambiente, comparando a resposta prevista com a medida.

## 4. Treino, seleção e avaliação

1. **Ambiente** por família em `cardl/marl/` (o atual vira a família A sem mudança), com testes de unidade da dinâmica e da máscara.
2. **Treino** com `set_determinism`, 3 sementes por família, proveniência como no docs/15 (commits das duas fases, sha256 das curvas e dos checkpoints).
3. **Seleção** pelo critério já fixado (`cardl/marl/select.py`): sementes de validação disjuntas, violação do custo até o limite do CMDP, maior recompensa entre as elegíveis; sem elegível, a família fica na RDL-N1.
4. **Avaliação no ambiente** contra B0–B3, com o B3 sendo o raciocínio real da Fase 1 (EEVS), como no docs/15.
5. **Malha fechada:** N12 com as famílias selecionadas contra B3 em S0–S7 e S9–S15, nova semente, em pré-registro.

## 5. Decisões do autor

- **Modelo de energia** (famílias B e D): resolvido pela Fase 1 (TR 38.864 e EARTH, docs/17 da Fase 1). Falta só integrar o ramo `modelo-energia-c17` da Fase 1 ao `malha-fechada`, para que as execuções em malha fechada gravem a ocupação usada pelo modelo; uma verificação anterior com `git merge-tree` não achou conflito, mas foi feita antes do commit `39bee5cc` e precisa ser refeita.
- **Ordem das famílias.** Recomendação: B primeiro (física por célula, a parte de PRB já tem curva medida no NORI), depois C (o conflito do S5) e por último D (só aparece em S13 e S15).
- **Ping-pong (família P):** continuar só com a regra da RDL-N1, como proposto aqui, ou também levá-lo à RDL-N2.

## 6. Limites

- A calibração da família C usa a perda de conexão em até 3 s depois do handover como efeito do handover; parte dessas perdas pode vir do cenário (UEs de borda que perdem a conexão de qualquer forma). Sem execuções com o handover segurado, não há contrafactual.
- O raciocínio da Fase 1 não recebe hoje, pelo `KPMReport`, a carga das células, o RSRP, o SINR e a satisfação do UE; na malha fechada, a observação da família C fica com esses campos no valor neutro (`observe_from_reasoning`). Levar esses campos até o raciocínio é pré-requisito para usar a política no N12.

- Os ambientes serão substitutos calibrados (`publication_eligible: false`), como o do docs/15. Ganho no ambiente não é evidência de RAN; a evidência vem da malha fechada e da bancada NORI.
- Na bancada NORI só o teto de PRB do gNB 0 é atuável (S8). As famílias B, C e D só podem ser validadas no ns-3, até que a bancada atue potência, handover e estado de célula.
- As afirmações C1–C6 continuam `NOT_VERIFIED`.

## 7. Implementação inicial (2026-11-21)

| Peça | Arquivo | O que faz |
| :-- | :-- | :-- |
| Famílias | `cardl/families.py` | classifica o conflito (A, B, C, D, P) pelo tipo e pelos parâmetros; registro de políticas por família (`FamilyRegistry`), com o campo opcional `families` da A1 20002 |
| Motor | `cardl/engine.py` | a checagem de escopo consulta o registro; família com política decide que ações manter, com máscara e ordem canônica; segurar todas volta à RDL-N1 (a Fase 1 trata resolução vazia como rejeição do Safety Guard); família sem política: reserva e motivo de antes |
| Roteador | `cardl/hierarchy.py` | a família do conflito entra no rastro de cada resolução |
| MAPPO | `cardl/marl/mappo.py` | dimensões por ambiente (`Dims`); o checkpoint grava as dimensões. O checkpoint selecionado (semente 101) dá as mesmas probabilidades antes e depois da mudança, byte a byte |
| Ambiente da família C | `cardl/marl/env_handover_prb.py` | ações manter as duas, segurar o handover, segurar o teto, segurar as duas; o teto já em vigor (incumbente) não pode ser segurado; custo do CMDP: perda de conexão do UE |
| Calibração | `fit_response`, `contexts_from_transitions` | perda de conexão logística na diferença de RSRP destino − origem; satisfação do UE depois do handover por faixa de carga do destino; contextos dos conflitos reais da família C |
| Dataset offline | `experiments/closed_loop/extrair_transicoes.py` | transições por janela (KPM, propostas, decisão, resoluções com família, ações, KPM seguinte), eventos de handover e manifesto com sha256 das entradas e saídas |
| Efeito de manter | `experiments/closed_loop/efeito_manter_acoes.py` | variação da vazão da célula depois dos conflitos indiretos e das ações isoladas |
| Testes | `tests/test_families.py` | classificação, registro, motor com política de teste, máscara do incumbente, ambiente, recuperação dos parâmetros da logística, ida e volta do checkpoint com outras dimensões, extrator |

**Primeiras medidas** (execuções em malha fechada da Fase 1 com semente 16901, 16905, 16907 e S0–S3 da 16908; 65 execuções com `SUCCESS`; 609 janelas com propostas, 187 handovers aplicados com UE):

- **Fora do escopo hoje:** nas execuções N12 já feitas (S5 da P3 e S0–S3 da `cl_n12`), 17 conflitos subiram à RDL-N2 e os 17 voltaram à RDL-N1 como indiretos fora do escopo do MAPPO.
- **Família C real:** 19 contextos distintos; em 18 o teto de PRB já estava em vigor quando o handover chegou. Na prática, a decisão da família C é segurar ou não o handover.
- **Perda de conexão depois do handover:** 44 de 187 em até 3 s. Ajuste logístico: probabilidade de 0,60 com o destino 5 dB mais fraco, 0,28 com RSRP igual e 0,03 com o destino 10 dB mais forte.
- **Políticas fixas no ambiente calibrado** (20 sementes, 9001–9020): manter as duas dá recompensa 48,56 ± 1,54 com perda em 15,2 % dos passos, acima do limite de 5 % do CMDP; segurar sempre o handover dá 35,47 ± 0,40 sem perda. Há um compromisso a aprender: segurar o handover só nos contextos de risco.

Descrição: as medidas vêm de `extrair_transicoes.py`, `fit_response` e das políticas fixas `REFERENCE_POLICIES` no ambiente da família C; nenhuma política foi treinada. O ambiente é substituto calibrado e não é evidência de RAN.

**Próximos passos:** treinar a família C com o MAPPO com restrição (dimensões da família C) e selecionar pelo critério do docs/15; levar carga, RSRP, SINR e satisfação do UE até o raciocínio da Fase 1; validar o ambiente com a campanha `cl_n12` completa; depois, intervenções com o handover segurado em malha fechada, para ter contrafactual.
