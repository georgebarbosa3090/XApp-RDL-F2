# Verifique revistas para publicação

**User:** Anonymous  
**Created:** 9/24/2026 4:04:52  
**Updated:** 9/24/2026 5:07:55  
**Exported:** 9/24/2026 8:15:29  
**Link:** [https://chatgpt.com/c/6ab4cb93-41a8-83e9-b1f7-3765c2924d30](https://chatgpt.com/c/6ab4cb93-41a8-83e9-b1f7-3765c2924d30)  

## Prompt:
24/09/2026, 04:06:12

Verifique em qual revista internacional ou nacional posso publicar meu projeto HRDL e/ CA RDL. Verifique mediante ultimos relatorios, resultados de experiemntos, maturidade, indique e os períodos de submissão, que tipo de adequação deveria fazer.

## Response:
24/09/2026, 04:06:15

Vou cruzar três coisas: maturidade técnica atual do H-RDL/CA-RDL, força experimental já demonstrada e aderência temática/escopo das revistas. Também vou separar opções “publicáveis agora” das que exigem mais maturidade experimental.

Os relatórios mais recentes mudam a estratégia: a H-RDL já está em fase de “fechamento científico”, enquanto a CA-RDL ainda precisa de campanha experimental mais robusta antes de mirar um periódico seletivo. Vou verificar agora escopo e calendário real de submissão dos periódicos.

Já há um ponto importante: para **H-RDL**, o periódico mais alinhado conceitualmente é o **IEEE TNSM**; para **CA-RDL**, o encaixe tende a migrar para TCCN/OJ-COMS/Computer Networks conforme a campanha MARL amadureça. Vou checar também periódicos focados especificamente em ML para comunicações e chamadas especiais ainda abertas.

> **Relembrando**
>
>
> **Pesquisando periódicos adequados**
>
> Estou identificando periódicos internacionais e brasileiros alinhados a redes, O-RAN, aprendizado por reforço, segurança e eficiência energética. Também vou verificar escopo editorial e distinguir submissões contínuas de chamadas especiais previstas para 2026.
>
> **Pesquisou periódicos adequados**
>
> 
>
> **Revisou relatórios, resultados, maturidade experimental e publicações recentes**
>
> 
>
> **Avaliando publicação e adequação**
>
> Estou cruzando maturidade, evidências experimentais e escopo editorial. A H-RDL parece próxima de submissão, enquanto a CA-RDL ainda exige campanha MARL mais robusta; vou separar opções imediatas de alvos condicionados a novos resultados.
>
> **Consolidando evidências**
>
> Estou priorizando os dados reconciliados de setembro: a H-RDL tem resultados promissores, mas ainda precisa de N=30, backend externo e hardware real. A CA-RDL possui resultados iniciais fortes, porém depende de múltiplas sementes, ablações e validação de robustez.
>
> **Avaliou publicação e consolidou evidências**
>
> 
>
> Pensou por 5m 23s

Sim. Fiz a análise considerando o estado mais recente que temos dos repositórios/relatórios, inclusive a consolidação da H-RDL de **18/09/2026**, os artefatos mais recentes da CA-RDL e as chamadas de periódicos disponíveis em **24/09/2026**.

Minha conclusão principal é: **não juntaria H-RDL e CA-RDL em um único artigo agora.** A H-RDL está muito mais próxima de um paper de periódico completo. A CA-RDL tem potencial para um periódico ainda mais orientado a IA/6G, mas precisa fechar melhor a campanha MARL.

### Estado científico atual

A **H-RDL/Fase 1** já deixou de ser somente uma implementação. O repositório passou a ter SSOT experimental, reconciliação automática das tabelas, política de zero dados sintéticos, cadeia causal KPM → decisão → RC → ACK → MAC → KPM, artefatos com hashes e adapter para evolução ao testbed. `Compilacao_Relatorios_03_04_05_06_HRDL_ATUALIZADO_2026-09-18.docx`

O ponto que ainda limita uma submissão muito forte é estatístico: a campanha experimental formal atualmente validada é **N=5 sementes reais para cada política, totalizando 35 runs B0-B6**. Na comparação pareada principal B1 FIFO × B3 H-RDL, o Wilcoxon exato é **p=0,0625**, embora os efeitos observados sejam relevantes: +13,30 Mbps, -7,20 ms em P95, -24 p.p. de violações de SLA e +0,29 de Jain fairness. `Compilacao_Relatorios_03_04_05_06_HRDL_ATUALIZADO_2026-09-18.docx`

Isso é importante porque evita usar indevidamente os antigos resultados “N=30/p<0,001”. Seu próprio processo de auditoria corrigiu essa questão. A versão de 18/09 recomenda explicitamente diferenciar os N=5 atuais da futura campanha N=30 e executar os próximos gates do testbed com USRP/UE COTS depois de congelar o perfil RF. `Compilacao_Relatorios_03_04_05_06_HRDL_ATUALIZADO_2026-09-18.docx`

Já a **CA-RDL/Fase 2** possui uma contribuição conceitualmente mais ambiciosa: Context-Aware RDL, CTDE/MAPPO, Safety Guards externos à política, Knowledge Graph/GNN e adaptação da recompensa ao contexto. Nos resultados atualmente reportados aparecem **1,85 ms de latência média, P99 2,40 ms, 100% de arbitragem, 0% de conflitos não mitigados e 1,182× em bits/J**. `apresentacao_resultados_RDL_Fase2_2026-09-01.pdf`

Porém o próprio relatório da Fase 2 diz que ainda faltam **múltiplas sementes e ICs, ablação, robustez a mudança de domínio, sensibilidade da recompensa, custo computacional e escalabilidade** antes de generalizar esses números. `apresentacao_resultados_RDL_Fase2_2026-09-01.pdf` Os artefatos mais recentes já mostram múltiplos treinamentos MAPPO, mas as figuras quantitativas continuam marcadas como **REVIEW_RAW_TRACES_BEFORE_PUBLICATION**, o que é um sinal correto de cautela científica. `manifest_figures.csv`

## Onde eu publicaria

| Periódico | Projeto que melhor encaixa | Situação da submissão | O que eu mudaria no artigo |
|---|---|---|---|
| **IEEE Transactions on Network and Service Management - TNSM** | **H-RDL** | **Regular papers: qualquer época do ano** | Transformar H-RDL em trabalho de *network/service management*: governança multi-xApp, conflict management, policies, safety, closed-loop, scalability e experimental evaluation. O próprio escopo pede performance evaluation, scalability e optimization. ([LastGen](https://lastgen.comsoc.org/publications/journals/ieee-tnsm/journal-information?utm_source=chatgpt.com)) |
| **Computer Networks - Elsevier** | **H-RDL agora; CA-RDL posteriormente** | Regular contínua; Special Issue **Wireless beyond limits: AI, 6G, Quantum… até 31/01/2027** | Dar mais peso a arquitetura de rede, operação, QoS, resource management, performance e principalmente experimentação/testbed. O escopo é muito aderente. ([Elsevier Shop](https://shop.elsevier.com/journals/computer-networks/1389-1286?utm_source=chatgpt.com)) |
| **IEEE Transactions on Machine Learning in Communications and Networking - TMLCN** | **CA-RDL** | Regular, portal aberto | Ideal quando MAPPO estiver fechado. Precisa provar contribuição de ML **e** contribuição de networking; reproducibilidade, código e dados são fortemente valorizados. APC 2026: US$ 2.160. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-tmlcn/policies-guidelines?utm_source=chatgpt.com)) |
| **IEEE Transactions on Cognitive Communications and Networking - TCCN** | **CA-RDL** | Regular, sem janela fixa | Excelente encaixe para percepção → conhecimento → reasoning → ação, KG, aprendizagem, adaptação e cognitive control. TCCN cita explicitamente perception, learning, reasoning, knowledge representation e cognitive network control. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-transactions-cognitive-communications-and-networking?utm_source=chatgpt.com)) |
| **IEEE Open Journal of the Communications Society - OJ-COMS** | CA-RDL | Regular contínua; há CFPs em andamento | Boa alternativa caso queira OA e espaço maior. Não tem limite de páginas; APC 2026 US$ 2.160. A chamada atual de Agentic AI/Human-Centric fecha **15/11/2026**, mas eu só usaria se o paper realmente atender esse foco, sem forçar enquadramento. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-ojcoms/policies-guidelines?utm_source=chatgpt.com)) |
| **IEEE Transactions on Green Communications and Networking - TGCN** | CA-RDL, se focar energia | Fluxo regular | Só escolheria se transformar energia/QoS no problema central: energy-aware MARL, Pareto, Joules/bit, eficiência energética × SLA. O escopo inclui Green AI/ML, 6G sustentável e energy-aware networking. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-transactions-green-communications-and-networking?utm_source=chatgpt.com)) |
| **JCIS - Journal of Communication and Information Systems, SBrT/IEEE ComSoc** | **H-RDL** | Portal regular, sem deadline fixo | Melhor alternativa brasileira diretamente ligada a telecom. Paper em inglês, template IEEE Transactions; Regular Paper ≥8 páginas. É Diamond OA e **não cobra submissão nem publicação**. ([Jornal de Sistemas de Informação](https://jcis.sbrt.org.br/jcis/about?utm_source=chatgpt.com)) |
| **JISA - Journal of Internet Services and Applications/SBC** | H-RDL | Fluxo de periódico | Alternativa brasileira caso a narrativa seja mais de networking, management, middleware, SDN/Open RAN e serviços. A SBC lista o periódico entre seus journals internacionais em inglês; bases atuais mostram atividade em 2026. ([Journals SBC](https://journals-sol.sbc.org.br/?utm_source=chatgpt.com)) |

### Para a H-RDL, eu miraria primeiro TNSM

O encaixe é excepcionalmente bom. H-RDL não é essencialmente um paper de PHY, nem somente de RL. O que você criou é uma **camada de governança e gerenciamento de recursos e decisões entre aplicações concorrentes do Near-RT RIC**. Isso está quase literalmente dentro do escopo de TNSM: architectures/frameworks, management functions, policies, reliability, quality assurance, enabling technologies, standards e experimental evaluation. ([LastGen](https://lastgen.comsoc.org/publications/journals/ieee-tnsm/journal-information?utm_source=chatgpt.com))

Além disso, a própria auditoria do seu projeto já chegou praticamente aos critérios que eu usaria para TNSM: **full campaign, cross-backend, scalability, ablation e artifact package**. `RELATORIO_AUDITORIA_PROFUNDA_RDL_F1_F2_2026-09-14.md`

Eu não enviaria a versão atual imediatamente. Faria uma campanha final e então submeteria. A TNSM recebe artigos regulares **o ano inteiro**, portanto não existe motivo para sacrificar qualidade tentando perseguir um deadline. ([LastGen](https://lastgen.comsoc.org/publications/journals/ieee-tnsm/journal-information?utm_source=chatgpt.com))

O paper ficaria mais forte com um título na linha de:

**“H-RDL: Deterministic and Auditable Multi-xApp Conflict Governance for O-RAN Near-RT RIC”**

e não com a narrativa genérica “uma nova arquitetura RDL”.

A novidade teria de ser explicitamente:

**multi-xApp governance → conflict detection → deterministic arbitration → safety → E2 actuation → causal verification**.

Isso diferencia seu trabalho de papers que simplesmente fazem resource allocation.

## O que falta para eu considerar a H-RDL pronta para TNSM/Computer Networks

Eu faria uma campanha final bastante objetiva:

1. **Congelar a H-RDL.** Não acrescentaria novas funcionalidades à Fase 1. Congelar SHA, versões do ns-3/5G-LENA/NORI, configuração de rádio e datasets.

2. **Executar N=30 sementes reais**, principalmente para a comparação **B1 FIFO × B3 H-RDL**, deixando B0 como referência secundária. Reportar média, mediana, IC95%, effect size e teste pareado apropriado. Isso resolve a maior fragilidade atual, que é o N=5/p=0,0625.

3. **Fazer ablation study da H-RDL.** Por exemplo: Full H-RDL; sem Safety Guard; sem janela/batching; sem conflict-aware arbitration; sem priority/utility refinement. Assim você prova qual componente produz cada ganho.

4. **Fazer scalability.** Não basta 30 UEs. Eu testaria algo como 30/60/120/240 UEs, 2/3/5/10 xApps concorrentes e 1/3/7 gNBs. Medir decision latency, CPU, memória, throughput, conflitos/s, SLA e churn. Isso conversa diretamente com o requisito de scalability da TNSM. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management?utm_source=chatgpt.com))

5. **Cross-backend.** O grande salto seria manter os experimentos canônicos no **ns-3.48 + 5G-LENA + NORI** e executar pelo menos um subconjunto equivalente em **srsRAN + Open5GS**. O RadioBackendAdapter que você já desenvolveu é justamente o caminho para isso.

6. **Testbed físico.** Se você conseguir um Golden Run usando USRP + UE COTS/OpenRAN@Brasil, mesmo que não repita os 30 seeds físicos, a força do paper cresce muito. Use simulação para estatística e testbed físico para validação externa.

7. **Artifact package publicável.** Cada claim deve poder apontar para seed → manifest → configuração → raw trace → PDU → FlowMonitor → script → tabela/figura. Essa é uma das características mais diferenciadas da sua H-RDL atual.

8. **Não misturar CA-RDL no resultado principal.** Cite a CA-RDL apenas como evolução/roadmap. Isso deixa a contribuição H-RDL muito mais limpa e evita que os reviewers questionem por que a parte MARL não recebeu a mesma validação experimental.

Com isso, eu consideraria a **TNSM um alvo plenamente justificável**, e **Computer Networks** uma alternativa internacional muito coerente.

## E a CA-RDL?

Aqui eu faria uma estratégia diferente. **Não enviaria a CA-RDL ainda para TMLCN/TCCN na forma atual**, apesar de os números preliminares serem muito bons.

O ponto central de um reviewer de TMLCN provavelmente seria:

> “Como sabemos que o ganho é consequência do Safe-MAPPO/context awareness e não da escolha de cenários, reward shaping ou seeds?”

Sua auditoria já antecipou exatamente como responder: comparação **B3 H-RDL → B4 Context → B5 Context+KG → B6 Full MAPPO**, usando mesmas seeds, mesmo backend e mesmo transport profile. `RELATORIO_AUDITORIA_PROFUNDA_RDL_F1_F2_2026-09-14.md`

E a ablação já está conceitualmente definida:

**Full / No Context / No KG / No MARL / No Safety**, sendo *No Safety* somente offline. `RELATORIO_AUDITORIA_PROFUNDA_RDL_F1_F2_2026-09-14.md`

Para MAPPO, eu exigiria ainda curvas de convergência multi-seed, média + IC, variância, safety cost, constraint violation, avaliação com estados/seeds nunca vistos e estabilidade da política - exatamente os pontos levantados na auditoria. `RELATORIO_AUDITORIA_PROFUNDA_RDL_F1_F2_2026-09-14.md`

Também é crítico manter:

**training seeds ∩ evaluation seeds = ∅**. `RELATORIO_AUDITORIA_PROFUNDA_RDL_F1_F2_2026-09-14.md`

Depois disso, o paper da CA-RDL ficaria muito forte para **IEEE TMLCN** porque a revista explicitamente procura trabalhos que avancem simultaneamente ML e networking e incentiva código, datasets e artefatos reproduzíveis. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-tmlcn/policies-guidelines?utm_source=chatgpt.com))

Um título mais adequado seria:

**“CA-RDL: Context-Aware Safe Multi-Agent Reinforcement Learning for Multi-xApp Conflict Governance in O-RAN”**

Aqui, ao contrário da H-RDL, o protagonista passa a ser **Safe-MARL**, e H-RDL vira o principal baseline determinístico.

## Uma oportunidade específica para janeiro de 2027

Há uma Special Issue da **Computer Networks** chamada **“Wireless beyond limits: AI, 6G, Quantum, and new horizons”**, com submissão até **31 de janeiro de 2027**. ([ScienceDirect](https://www.sciencedirect.com/browse/calls-for-papers?utm_source=chatgpt.com))

Para mim, essa data é muito mais interessante para a **CA-RDL** do que tentar correr agora.

Você teria outubro-dezembro de 2026 para fechar:

CA-RDL multi-seed → ablations → reward sensitivity → unseen evaluation → scalability → cross-backend.

E janeiro para fechar paper/artifacts.

Isso combina bem com seu roadmap técnico.

Há também uma chamada de **Computer Networks** sobre **AI-Native Federated Testbeds and Datasets for Next-Generation Communication and Networking Systems**, fechando **15/10/2026**. Ela menciona explicitamente Open RAN, RL/MARL, sim-to-real e experimental reproducibility. ([LinkedIn](https://www.linkedin.com/posts/research-spheredigital_callforpapers-computernetworks-ainetworking-activity-7464204019067146241-in0N?utm_source=chatgpt.com))

Tematicamente é quase perfeita para o que seu ecossistema RDL está se tornando, mas **eu não correria para 15 de outubro**. Seria necessário transformar o paper em contribuição de **testbed/dataset/reproducible experimentation**, e não simplesmente H-RDL/CA-RDL. Com o estado atual da validação, isso sacrificaria rigor para cumprir o deadline.

Há ainda a Special Issue **“Intent-Based Agentic AI for Next-Generation Networking”** da *Computer Communications*, deadline **31/10/2026**. ([ScienceDirect](https://www.sciencedirect.com/browse/calls-for-papers?subject=computer-networks-and-communications&utm_source=chatgpt.com)) Ela pode parecer tentadora porque você possui Intent Classifier e evolução zero-touch, mas eu não chamaria a CA-RDL atual de “Agentic AI” apenas para encaixar na chamada. Isso enfraqueceria o trabalho.

## Estratégia de publicação que eu adotaria

Minha sequência seria:

**Paper 1 - H-RDL / Fase 1**  
Out-Nov/2026: N=30 + ablation + scalability + cross-backend.  
Nov-Dez/2026: escrita.  
**Alvo: IEEE TNSM.**  
Backup: **Computer Networks**.  
Alternativa nacional: **JCIS**.

**Paper 2 - CA-RDL / Fase 2**  
Out-Dez/2026: MARL multi-seed + B3/B4/B5/B6 + ablation + generalização.  
Jan/2027: frozen policy em srsRAN/Open5GS se possível.  
**Alvo: IEEE TMLCN ou TCCN.**  
Se a campanha estiver fechada a tempo, avaliar a Special Issue da *Computer Networks* de **31/01/2027**.

**Paper 3 - RDL sim-to-real / testbed**, mais adiante.  
H-RDL + CA-RDL + NORI/ns-3 → srsRAN/Open5GS → OpenRAN@Brasil/USRP. Esse terceiro trabalho pode ser cientificamente ainda mais forte porque responde à pergunta de **generalização sim-to-real** que os relatórios atuais deixam em aberto. A própria auditoria já propõe treinar em NORI, avaliar política congelada em srsRAN e depois partir para o ambiente físico. `RELATORIO_AUDITORIA_PROFUNDA_RDL_F1_F2_2026-09-14.md`

### Minha indicação final

Neste momento, eu faria:

**H-RDL → IEEE TNSM**, depois da campanha N=30 + scalability + ablation + uma evidência cross-backend.

**CA-RDL → IEEE TMLCN**, depois de fechar Safe-MAPPO multi-seed, ablations, avaliação unseen e sim-to-real.

**Computer Networks → excelente terceira rota**, especialmente pela oportunidade até **31/01/2027**.

**JCIS → melhor rota brasileira diretamente alinhada a telecom/Open RAN**, principalmente se você quiser publicar a H-RDL antes de toda a validação física; não cobra APC. ([Jornal de Sistemas de Informação](https://jcis.sbrt.org.br/jcis/about?utm_source=chatgpt.com))

**JISA → alternativa brasileira boa para uma versão com maior ênfase em networking, management, SDN/Open RAN e serviços**, embora menos específica de telecom que JCIS. ([PubScope](https://pubscope.org/journal/1867-4828?utm_source=chatgpt.com))

O principal agora não é acrescentar mais arquitetura à H-RDL. **É transformar a excelente infraestrutura de evidência que você construiu em uma campanha experimental irrefutável.** Para a CA-RDL, o desafio é outro: demonstrar causalmente que **Context + KG + Safe-MAPPO** justificam a complexidade adicional sobre a H-RDL.

Posso também monitorar as chamadas de **TNSM, TMLCN, TCCN, Computer Networks, OJ-COMS e TGCN** e avisá-lo quando surgir uma Special Issue especificamente sobre **O-RAN, xApps, MARL, autonomous networks ou AI-native 6G**.

---

**Sources:**

- [Journal Information | IEEE Communications Society](https://lastgen.comsoc.org/publications/journals/ieee-tnsm/journal-information?utm_source=chatgpt.com)
- [Subscribe to Computer Networks - 1389-1286 | Elsevier Shop | Elsevier Shop](https://shop.elsevier.com/journals/computer-networks/1389-1286?utm_source=chatgpt.com)
- [IEEE Transactions on Machine Learning in Communications and Networking Policies and Guidelines | IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-tmlcn/policies-guidelines?utm_source=chatgpt.com)
- [About the Journal | Journal of Communication and Information Systems](https://jcis.sbrt.org.br/jcis/about?utm_source=chatgpt.com)
- [Digital Open Library of the Brazilian Computing Society | Journals](https://journals-sol.sbc.org.br/?utm_source=chatgpt.com)
- [Browse Calls for Papers | ScienceDirect.com](https://www.sciencedirect.com/browse/calls-for-papers?utm_source=chatgpt.com)
- [#callforpapers #computernetworks #ainetworking #federatedlearning #openran #wirelessnetworks #edgecomputing #iot #distributedsystems #networkingresearch #artificialintelligence #machinelearning… | Research Sphere](https://www.linkedin.com/posts/research-spheredigital_callforpapers-computernetworks-ainetworking-activity-7464204019067146241-in0N?utm_source=chatgpt.com)
- [Journal of Internet Services and Applications — Brazilian Computing Society | PubScope](https://pubscope.org/journal/1867-4828?utm_source=chatgpt.com)

## Prompt:
24/09/2026, 04:59:50

Quais desse nao cobra por publicação

## Response:
24/09/2026, 05:00:00

> **Verificando taxas editoriais**
>
> Estou conferindo as páginas oficiais, distinguindo periódicos híbridos — publicação tradicional geralmente sem APC, salvo custos adicionais — de revistas totalmente abertas, nas quais a taxa costuma ser obrigatória. Também estou checando possíveis cobranças por excesso de páginas.
>
> **Verificou taxas editoriais**
>
> 
>
> **Pesquisou 17 sites**
>
> 
>
> Pensou por 25s

Dos periódicos que citei, estes permitem publicar **sem pagar APC obrigatória**, escolhendo a modalidade tradicional quando aplicável:

| Revista | Pode publicar sem pagar? | Observação |
|---|---:|---|
| **JCIS - Journal of Communication and Information Systems** | ✅ **Sim, totalmente grátis** | Diamond Open Access: não cobra submissão nem publicação. Artigo fica aberto para todos. ([Jornal de Sistemas de Informação](https://jcis.sbrt.org.br/jcis/about?utm_source=chatgpt.com)) |
| **IEEE TNSM** | ✅ **Sim** | Até **10 páginas** na modalidade tradicional não há cobrança. Acima disso: **US$ 220/página adicional**. Open Access é opcional e custa US$ 2.800 em 2026. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-tnsm/policies-guidelines?utm_source=chatgpt.com)) |
| **IEEE TCCN** | ✅ **Sim** | Modalidade tradicional não exige APC. Acima de 10 páginas há cobrança obrigatória de **US$ 220/página**; OA é opcional. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-tccn/policies-guidelines?utm_source=chatgpt.com)) |
| **IEEE TGCN** | ✅ **Sim** | Tradicional sem APC até 10 páginas; acima disso, **US$ 220/página**. OA opcional custa US$ 2.800 em 2026. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-tgcn/policies-guidelines?utm_source=chatgpt.com)) |
| **Computer Networks - Elsevier** | ✅ **Sim** | É híbrida. Você pode escolher publicação por assinatura, **sem custo para o autor**; paga apenas se escolher Open Access. ([www.elsevier.com](https://www.elsevier.com/researcher/author/open-access/choice?utm_source=chatgpt.com)) |
| **JISA - Journal of Internet Services and Applications** | ✅ provavelmente | Atualmente aparece como Diamond OA/SBC em diretórios especializados; eu confirmaria diretamente as regras editoriais antes da submissão. ([openaccessfinder.de](https://openaccessfinder.de/subjects/computer-science/?utm_source=chatgpt.com)) |
| **IEEE TMLCN** | ❌ **Não** | Open Access obrigatório: **US$ 2.160** para artigos submetidos em 2026. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-tmlcn/policies-guidelines?utm_source=chatgpt.com)) |
| **IEEE OJ-COMS** | ❌ **Não** | Open Access obrigatório: **US$ 2.160** em 2026. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-ojcoms/policies-guidelines?utm_source=chatgpt.com)) |

### Para o seu H-RDL

Eu priorizaria três opções gratuitas:

**1. IEEE TNSM - minha escolha internacional para H-RDL.**  
Você consegue publicar **sem APC se mantiver o artigo em até 10 páginas IEEE**. Para o H-RDL, isso exigirá uma redação bem condensada, deixando detalhes experimentais e datasets no GitHub.

**2. Computer Networks - excelente alternativa internacional.**  
Você pode publicar no modelo tradicional **sem pagar APC**, e normalmente há mais espaço para uma descrição experimental extensa. A Elsevier confirma que autores em periódicos híbridos podem usar o modelo de assinatura **sem custo de publicação**. ([www.elsevier.com](https://www.elsevier.com/researcher/author/open-access/choice?utm_source=chatgpt.com))

**3. JCIS - melhor opção se você quiser Open Access realmente gratuito.**  
Não há APC, não há taxa de submissão e o artigo fica aberto para qualquer pessoa. É mantida pela SBrT e co-patrocinada pela IEEE Communications Society. ([Jornal de Sistemas de Informação](https://jcis.sbrt.org.br/jcis/about?utm_source=chatgpt.com))

### Um detalhe especialmente interessante para você

Como você é da **UFPA**, existe atualmente um acordo **CAPES-Elsevier 2026-2028**. Para autores correspondentes de instituições brasileiras elegíveis, a CAPES pode cobrir a APC de periódicos híbridos da Elsevier, permitindo publicar **Open Access sem você pagar**, desde que a revista e a instituição estejam incluídas no acordo. ([www.elsevier.com](https://www.elsevier.com/open-access/agreements/capes?utm_source=chatgpt.com))

Isso pode tornar **Computer Networks particularmente interessante**: mesmo que você queira o artigo totalmente Open Access, existe a possibilidade de a APC ser coberta pela CAPES.

Para o **H-RDL**, portanto, minha ordem prática seria **TNSM → Computer Networks → JCIS**. Para a **CA-RDL**, se o critério principal for não pagar, eu consideraria **TCCN → Computer Networks → TGCN**, evitando TMLCN e OJ-COMS por enquanto devido à APC obrigatória.

---

**Sources:**

- [About the Journal | Journal of Communication and Information Systems](https://jcis.sbrt.org.br/jcis/about?utm_source=chatgpt.com)
- [IEEE Transactions on Network and Service Management Policies and Guidelines | IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-tnsm/policies-guidelines?utm_source=chatgpt.com)
- [Choice of publishing options | Elsevier](https://www.elsevier.com/researcher/author/open-access/choice?utm_source=chatgpt.com)
- [Diamond Open Access Journals in Computer Science: 226 Free-to-Publish Journals Ranked](https://openaccessfinder.de/subjects/computer-science/?utm_source=chatgpt.com)

## Prompt:
24/09/2026, 05:06:06

Como projeto H-RDL poderia ser descrito 3 papers ou artigos diferentes para cada revista TNSM → Computer Networks → JCIS

## Response:
24/09/2026, 05:06:12

Sim. A melhor forma é tratar o **H-RDL como uma plataforma de pesquisa**, não como um único resultado, e extrair três perguntas científicas realmente distintas — evitando repetir contribuição, figuras e avaliação entre os artigos. Vou separar cada paper por **problema central, hipótese, experimentos e contribuição**, já alinhando ao perfil de TNSM, Computer Networks e JCIS.

> **Estruturando os três artigos**
>
> Estou separando os trabalhos por contribuição: governança para TNSM, arquitetura e escalabilidade para Computer Networks, e uma taxonomia experimental de conflitos O-RAN para JCIS. Também estou evitando sobreposição e definindo títulos, perguntas de pesquisa, novidades e experimentos distintos para cada manuscrito.
>
> **Estruturou os três artigos**
>
> 
>
> **Pesquisou 3 sites**
>
> 
>
> Pensou por 24s

Sim. O **H-RDL pode sustentar três artigos distintos**, desde que cada um tenha **pergunta científica, contribuição principal e campanha experimental próprias**. Isso é importante para não parecer fragmentação artificial do mesmo resultado. A TNSM enfatiza management architectures, policies, quality assurance, experiments e scalability; *Computer Networks* aceita arquitetura, protocolos, middleware, QoS, network operation/management e avaliação de desempenho; e o JCIS exige contribuição original em telecomunicações. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management?utm_source=chatgpt.com))

Eu estruturaria assim:

| Artigo | Revista | O que é o H-RDL nesse paper | Pergunta central |
|---|---|---|---|
| **Paper 1** | **IEEE TNSM** | Sistema de **governança multi-xApp** | Como governar conflitos concorrentes de forma determinística, segura e auditável? |
| **Paper 2** | **Computer Networks** | **Middleware O-RAN interoperável e escalável** | A arquitetura continua eficiente quando cresce e muda de backend? |
| **Paper 3** | **JCIS** | **Framework experimental + taxonomia de conflitos** | Como caracterizar, reproduzir e medir conflitos multi-xApp em O-RAN? |

## 1. Paper para IEEE TNSM
### H-RDL como sistema de governança e gerenciamento

Aqui eu colocaria o **coração científico da H-RDL**.

Um título forte seria:

> **H-RDL: Deterministic and Auditable Multi-xApp Conflict Governance for O-RAN Near-RT RIC**

ou:

> **Safe Multi-xApp Governance in O-RAN: A Deterministic Resource and Decision Layer for Near-RT RIC**

### Pergunta científica

**RQ1:** Como múltiplas xApps concorrentes podem ser coordenadas no Near-RT RIC sem instabilidade, violações de SLA ou ações contraditórias?

Hipótese:

> Uma camada intermediária de governança determinística, baseada em detecção de conflitos, arbitragem, políticas e Safety Guards, reduz conflitos e instabilidade sem violar o orçamento temporal do Near-RT RIC.

Isso encaixa extremamente bem na TNSM, que explicitamente procura contribuições em **management models, architectures/frameworks, management functions, policies, reliability, quality assurance, standards, experimental evaluation e scalability**. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management?utm_source=chatgpt.com))

### A contribuição científica

Eu apresentaria quatro contribuições principais:

1. **H-RDL como camada explícita de governança entre xApps e E2SM-RC**.
2. **Modelo formal de conflito e arbitragem determinística**.
3. **Safety Guards independentes das xApps**.
4. **Closed-loop auditável**:

**KPM(t₀) → proposta → conflito → arbitragem → Safety → RC → ACK → mudança MAC → KPM(t₁).**

Essa cadeia causal já é um dos diferenciais importantes da versão atual do projeto.

### Experimentos

Esse deve ser o paper com a campanha estatística principal.

Eu usaria:

**B0 - No RDL**  
**B1 - FIFO/basic arbitration**  
**B2 - prioridade simples**  
**B3 - H-RDL completa**

e faria pelo menos:

- 30 seeds;
- diferentes cargas;
- diferentes taxas de conflito;
- 30 / 60 / 120 / 240 UEs;
- 2 / 3 / 5 / 10 xApps;
- 1 / 3 / 7 gNBs.

Métricas:

- throughput;
- P95/P99 latency;
- SLA violation;
- PDR/PLR;
- Jain fairness;
- conflitos detectados;
- conflitos mitigados;
- arbitration success;
- action churn;
- ping-pong;
- decision latency;
- CPU/memória;
- E2 overhead.

### Ablation

Muito importante para TNSM:

**H-RDL Full**

vs.

- No Safety Guard;
- No batching/window;
- No conflict detector;
- No utility;
- No priority;
- FIFO.

Assim você responde:

> Qual componente da H-RDL realmente produz o ganho?

### O que NÃO colocar como protagonista

Não colocar:

- MAPPO;
- GNN;
- CA-RDL;
- Knowledge Graph;
- 6G SAGIN;
- NTN;
- ISAC.

Isso iria enfraquecer a narrativa.

Pode aparecer apenas no final como **future evolution**.

---

# 2. Paper para Computer Networks
## H-RDL como arquitetura de rede interoperável e escalável

Este paper seria muito diferente.

Aqui a pergunta deixa de ser:

> “H-RDL resolve conflitos?”

e passa a ser:

> **“Essa arquitetura realmente funciona como um componente de rede O-RAN portátil, escalável e interoperável?”**

Isso combina muito bem com *Computer Networks*, cujo escopo inclui **network architectures, protocols, middleware, QoS, signaling, mobility management, performance measurements, network modeling e network operation/management**. ([Elsevier Shop](https://shop.elsevier.com/journals/computer-networks/1389-1286?utm_source=chatgpt.com))

### Título

Eu usaria algo como:

> **A Backend-Agnostic Resource and Decision Layer for Scalable Multi-xApp Coordination in O-RAN**

ou:

> **From Simulation to Near-Real Deployment: An Interoperable Resource and Decision Layer for O-RAN**

Esse segundo título fica particularmente forte se conseguirmos fechar srsRAN/Open5GS.

### Pergunta científica

**RQ2:** A H-RDL permanece funcional e eficiente quando mudamos o backend RAN e aumentamos escala e carga?

Hipótese:

> A separação entre lógica de governança e backend RAN permite transportar H-RDL entre ambientes de simulação e implementação real sem alterar a semântica da decisão e com overhead controlado.

Aqui aparece um dos elementos mais interessantes que você já criou:

**RadioBackendAdapter.**

A arquitetura seria:

```text
             H-RDL
               |
      RadioBackendAdapter
          /          \
         /            \
ns-3/5G-LENA/NORI   srsRAN/Open5GS
```

E futuramente:

```text
               H-RDL
                 |
        RadioBackendAdapter
       /         |          \
    NORI      srsRAN     OpenRAN@Brasil
```

### Contribuições

Este artigo poderia reivindicar:

1. arquitetura backend-agnostic;
2. abstração padronizada de telemetry/control;
3. interoperabilidade E2;
4. capability discovery;
5. comportamento consistente cross-backend;
6. análise de overhead;
7. escalabilidade.

Aqui entram com força:

- E2AP;
- E2SM-KPM;
- E2SM-RC;
- SCTP;
- RAN Function Capability Registry;
- subscription lifecycle;
- RC acknowledgement/failure;
- RadioBackendAdapter.

Ou seja, este artigo fica muito mais próximo de **systems/network architecture**.

### Experimento principal

O experimento principal não deve ser simplesmente repetir B1 × B3.

Faça:

```text
Backend A
ns-3.48 + 5G-LENA + NORI

          ↓ mesma H-RDL

Backend B
srsRAN + Open5GS
```

Idealmente:

```text
Backend C
OpenRAN@Brasil + SDR/USRP
```

E compare:

- decisão produzida;
- KPM received;
- RC success;
- action latency;
- E2 RTT;
- throughput;
- SLA;
- overhead;
- CPU;
- memória;
- packet processing;
- control-plane load.

### Pergunta particularmente forte

Você pode introduzir:

**Decision Semantic Consistency**

Por exemplo:

Se o estado da rede é aproximadamente equivalente nos dois backends:

$$
s_{NORI} \approx s_{srsRAN}
$$

então a decisão deveria ser:

$$
D_{H-RDL}(s_{NORI}) \approx
D_{H-RDL}(s_{srsRAN})
$$

Isso pode virar uma métrica de **cross-backend consistency**.

Essa seria uma contribuição nova em relação ao paper TNSM.

### Scalability

Aqui eu aprofundaria muito mais:

$$
T_{decision}=f(N_{UE},N_{xApp},N_{conflict})
$$

Testando:

```text
UEs:
30
60
120
240
500

xApps:
2
3
5
10
20

Conflict rate:
low
medium
high
storm
```

E produzir curvas:

**decision latency × xApps**

**CPU × UEs**

**memory × active proposals**

**conflicts/s × arbitration latency**

**E2 messages/s × scale**

Esse paper pode ficar excelente para *Computer Networks*.

---

# 3. Paper para JCIS
## H-RDL como benchmark e metodologia científica para conflito O-RAN

Aqui eu faria uma mudança ainda maior.

O H-RDL não seria o principal objeto.

Ele seria a **reference implementation** usada para validar uma contribuição metodológica.

Título:

> **A Reproducible Taxonomy and Experimental Benchmark for Multi-xApp Conflicts in O-RAN Near-RT RIC**

ou, mantendo H-RDL:

> **H-RDL-Bench: A Reproducible Benchmark for Multi-xApp Conflict Detection and Mitigation in O-RAN**

Esse artigo pode ser muito interessante porque o JCIS procura pesquisa original relacionada a telecomunicações e é patrocinado pela SBrT e IEEE ComSoc. Além disso, é Diamond OA. ([Jornal de Sistemas de Informação](https://jcis.sbrt.org.br/jcis/about?utm_source=chatgpt.com))

### Pergunta científica

**RQ3:**

> Como conflitos entre xApps O-RAN podem ser classificados e reproduzidos de maneira padronizada e comparável?

Esse é outro problema científico.

Não é:

> “minha H-RDL é melhor”.

É:

> “como a comunidade deveria representar e avaliar conflito multi-xApp?”

### Aqui entra sua taxonomia

Você já possui uma base excelente.

Por exemplo:

### C1 - conflito direto

```text
xSlice
   ↓
PRB ↑

Energy Saving
   ↓
Power ↓
```

Dois controladores mexem diretamente em recursos incompatíveis.

---

### C2 - conflito indireto

```text
Traffic Steering
      ↓
   handover
      ↓
nova célula
      ↓
 altera PRB
      ↓
impacta slicing
```

As xApps controlam parâmetros diferentes, mas afetam o mesmo SLA.

---

### C3 - conflito implícito

Nenhum parâmetro diretamente colide.

Entretanto:

$$
a_1 \rightarrow KPI_1
\rightarrow KPI_2
\rightarrow SLA
$$

gera degradação indireta.

---

### C4 - conflito temporal

Duas decisões são individualmente válidas, mas:

```text
t0 xApp A
t1 xApp B
t2 xApp A
t3 xApp B
```

produzem oscilação.

---

### C5 - conflict storm

Muitas decisões concorrentes:

$$
N_{proposal}/\Delta t \gg normal
$$

causando sobrecarga e instabilidade.

### Contribuição central

Criaria uma definição formal:

$$
C=(A,R,T,I,S)
$$

onde:

- $A$: conjunto de ações;
- $R$: recursos envolvidos;
- $T$: relação temporal;
- $I$: impacto indireto;
- $S$: SLA afetado.

Assim:

$$
Conflict(a_i,a_j)=
f(R_i,R_j,T,I,S)
$$

Isso transforma algo de engenharia em contribuição científica.

---

# H-RDL-Bench

Eu criaria formalmente um benchmark como resultado do artigo:

```text
H-RDL-Bench
│
├── direct/
├── indirect/
├── implicit/
├── temporal/
├── storm/
│
├── scenarios/
│   ├── EEVS
│   ├── TVS
│   └── ...
│
├── datasets/
├── traces/
├── manifests/
├── pcaps/
└── reproduction/
```

Cada benchmark teria:

```yaml
scenario:
  name: EEVS
  conflict: direct

xapps:
  - slicing
  - energy_saving

resources:
  - prb
  - tx_power

seed: 1001

expected:
  conflict: true

affected_sla:
  - latency
  - throughput
```

Isso seria extremamente útil para outros pesquisadores.

---

# O diferencial do JCIS

Aqui eu exploraria algo que considero bastante forte no seu projeto:

**proveniência experimental.**

Você já desenvolveu:

```text
execution_manifest
       ↓
raw PDU
       ↓
decoded PDU
       ↓
FlowMonitor
       ↓
causal_chain
       ↓
hash
       ↓
metric
       ↓
figure
```

Então poderia propor:

## Evidence Chain

$$
Claim
\rightarrow Metric
\rightarrow Run
\rightarrow Seed
\rightarrow Trace
\rightarrow PDU
\rightarrow Hash
$$

Essa ideia é bem diferente dos outros dois artigos.

---

# Os três papers juntos

Veja como eles passam a formar uma sequência científica muito coerente:

```text
                    H-RDL PROJECT
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
     PAPER 1           PAPER 2          PAPER 3
      TNSM          Computer Networks      JCIS
        │                │                │
        ▼                ▼                ▼
    GOVERNANCE       ARCHITECTURE       BENCHMARK
        │                │                │
        ▼                ▼                ▼
 What decision?      Can it scale?    How reproduce?
        │                │                │
        ▼                ▼                ▼
Policies/Safety    Cross-backend       Taxonomy
Arbitration        Interoperability     Dataset
Management         Performance         Provenance
```

Essa separação é fundamental.

# Experimentos que podem ser compartilhados

Pode existir alguma base experimental comum, mas eu evitaria reutilizar tabelas inteiras.

Por exemplo:

### TNSM

```text
B0
B1
B2
B3

N=30

objetivo:
provar governança
```

### Computer Networks

```text
H-RDL
NORI
vs
srsRAN/Open5GS

scalability

objetivo:
provar arquitetura
```

### JCIS

```text
C1
C2
C3
C4
C5

benchmark dataset

objetivo:
reprodutibilidade
```

Assim praticamente não existe conflito entre os papers.

---

# Uma divisão ainda mais rigorosa das métricas

| Métrica | TNSM | Computer Networks | JCIS |
|---|:---:|:---:|:---:|
| SLA violations | ★★★ | ★ | ★ |
| Conflict mitigation | ★★★ | ★ | ★★★ |
| Fairness | ★★★ | ★ | - |
| Action churn | ★★★ | ★★ | ★ |
| Decision latency | ★★ | ★★★ | ★ |
| CPU | ★ | ★★★ | - |
| Memory | - | ★★★ | - |
| E2 RTT | ★ | ★★★ | ★ |
| Scalability | ★★ | ★★★ | ★ |
| Cross-backend | - | ★★★ | - |
| Taxonomy | ★ | - | ★★★ |
| Dataset | ★ | ★ | ★★★ |
| Provenance | ★★ | ★★ | ★★★ |
| Reproducibility | ★★ | ★★ | ★★★ |

Isso ajuda muito a evitar sobreposição.

# Ordem em que eu escreveria

Eu faria primeiro o **TNSM**, porque ele estabelece oficialmente o mecanismo H-RDL.

Depois:

**Computer Networks**:

> “Building upon the deterministic governance model introduced in our previous work…”

e passa imediatamente para interoperabilidade e sim-to-real.

Depois:

**JCIS**:

> “Rather than proposing another arbitration mechanism, this work addresses the lack of a reproducible methodology for evaluating multi-xApp conflicts…”

Assim fica evidente que não está republicando o H-RDL.

## Uma possibilidade ainda melhor de ordem

Na prática, entretanto, eu faria os **experimentos de todos os três conjuntamente**, embora escrevesse artigos diferentes.

Uma única campanha maior:

```text
30 seeds
   ×
B0-B3
   ×
C1-C5
   ×
UE scales
   ×
xApp scales
   ×
NORI
   ×
srsRAN
```

pode alimentar três conjuntos diferentes de hipóteses.

Isso economiza muito trabalho experimental sem duplicar contribuição científica.

---

# Minha arquitetura editorial para o projeto

Eu passaria a tratar formalmente a H-RDL como uma linha com três produtos:

### H-RDL Core

**IEEE TNSM**

> Governance.

### H-RDL Systems

**Computer Networks**

> Interoperability + scalability + sim-to-real.

### H-RDL Bench

**JCIS**

> Taxonomy + benchmarks + reproducibility.

E depois a CA-RDL começa uma segunda geração:

```text
H-RDL Core
       ↓
H-RDL Systems
       ↓
H-RDL Bench
       ↓
CA-RDL
       ↓
Safe-MAPPO
       ↓
KG/GNN
       ↓
Autonomous RAN
```

Isso é muito mais forte academicamente do que tentar colocar **H-RDL + CA-RDL + GNN + MARL + 6G + testbed** dentro de um único artigo.

E há um benefício adicional: a **TNSM aceita regular papers continuamente**, então você não precisa comprometer os experimentos para perseguir uma janela específica. ([IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management?utm_source=chatgpt.com))

Se você fechar **N=30 + ablation + scalability + srsRAN/Open5GS**, vejo material suficiente para sustentar os três trabalhos com contribuições cientificamente distintas - com o **TNSM como paper principal da H-RDL**, *Computer Networks* como paper de sistemas/interoperabilidade e **JCIS como paper de benchmark/reprodutibilidade**.

---

**Sources:**

- [IEEE Transactions on Network and Service Management | IEEE Communications Society](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management?utm_source=chatgpt.com)
- [Subscribe to Computer Networks - 1389-1286 | Elsevier Shop | Elsevier Shop](https://shop.elsevier.com/journals/computer-networks/1389-1286?utm_source=chatgpt.com)
- [About the Journal | Journal of Communication and Information Systems](https://jcis.sbrt.org.br/jcis/about?utm_source=chatgpt.com)



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)