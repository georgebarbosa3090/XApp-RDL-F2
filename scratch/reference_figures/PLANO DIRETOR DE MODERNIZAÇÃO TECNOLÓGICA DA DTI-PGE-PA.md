# PLANO DIRETOR DE MODERNIZAÇÃO TECNOLÓGICA DA DTI/PGE-PA
## Automação, Dados e Inteligência Artificial — Horizonte 2026–2028

**Versão:** 1.0  
**Horizonte:** 24 meses  
**Unidade responsável:** Diretoria de Tecnologia da Informação — DTI  
**Abordagem:** Modular, API-First, Data-Driven e AI-Ready

---

## 1. SUMÁRIO EXECUTIVO

Este Plano Diretor propõe uma estratégia de modernização da Diretoria de Tecnologia da Informação da Procuradoria-Geral do Estado do Pará baseada na construção progressiva de ferramentas independentes de automação, inteligência artificial, gestão documental e análise de dados.

A estratégia evita iniciar o projeto pela construção de um sistema corporativo de grande porte.

Em seu lugar, propõe-se desenvolver pequenas soluções especializadas, capazes de resolver problemas concretos e produzir resultados mensuráveis.

Cada ferramenta deverá possuir arquitetura independente e interfaces padronizadas.

A evolução seguirá o modelo:

**Ferramenta → Serviço → API → Integração → Plataforma.**

Ao final do ciclo de modernização, esses componentes poderão constituir uma plataforma integrada denominada provisoriamente:

**PGE-PA Inteligente — Plataforma de Automação, Dados e Inteligência Artificial.**

---

# 2. OBJETIVOS ESTRATÉGICOS

O programa possui sete objetivos principais:

1. Automatizar tarefas operacionais repetitivas.
2. Melhorar a gestão e recuperação do conhecimento institucional.
3. Introduzir IA generativa de forma controlada e auditável.
4. Transformar dados institucionais em informação gerencial.
5. Criar infraestrutura moderna para desenvolvimento de sistemas.
6. Melhorar integração entre sistemas.
7. Construir gradualmente uma plataforma tecnológica corporativa.

---

# 3. PRINCÍPIOS

## 3.1 Modularidade

Cada ferramenta deverá possuir responsabilidade bem definida.

## 3.2 Independência

Uma ferramenta não deverá depender da interface de outra para funcionar.

## 3.3 API-First

As funcionalidades importantes deverão estar disponíveis por APIs documentadas.

## 3.4 Human-in-the-Loop

IA poderá recomendar, classificar, resumir e elaborar minutas.

Decisões jurídicas relevantes deverão permanecer sob responsabilidade humana.

## 3.5 Security by Design

Segurança deverá fazer parte da arquitetura desde a concepção.

## 3.6 AI-Ready

Novos sistemas deverão ser construídos considerando integração futura com serviços de IA.

## 3.7 Observabilidade

Todo serviço deverá produzir métricas, logs e trilhas de auditoria.

---

# 4. PORTFÓLIO DE PROJETOS

Propõe-se inicialmente um portfólio de 12 componentes.

| Código | Componente | Finalidade | Prioridade |
|---|---|---|---|
| P01 | PGE-Docs | Inteligência documental | Crítica |
| P02 | PGE-Search | Pesquisa institucional | Alta |
| P03 | PGE-RAG | Conhecimento institucional para IA | Crítica |
| P04 | PGE-Assistant | Assistente corporativo | Alta |
| P05 | PGE-Triagem | Triagem inteligente | Alta |
| P06 | PGE-Automa | Automação/RPA | Alta |
| P07 | PGE-Monitor | Monitoramento processual | Média |
| P08 | PGE-Parecer | Copiloto jurídico | Média |
| P09 | PGE-Analytics | BI e indicadores | Alta |
| P10 | PGE-Data | Plataforma de dados | Crítica |
| P11 | PGE-Agents | Agentes especializados | Futura |
| P12 | PGE-Portal | Integração das ferramentas | Futura |

---

# 5. P01 — PGE-DOCS

## Objetivo

Criar serviço corporativo de processamento inteligente de documentos.

### Entrada

PDF, DOCX, TXT, imagens e documentos digitalizados.

### Processamento

```text
Documento
   ↓
OCR
   ↓
Extração
   ↓
Classificação
   ↓
Metadados
   ↓
Anonimização, quando necessária
   ↓
Indexação
```

### Saída

Documento pesquisável e estruturado.

### API

Exemplos conceituais:

```text
POST /documents
GET  /documents/{id}
GET  /documents/{id}/text
GET  /documents/{id}/metadata
POST /documents/{id}/classify
```

### Tecnologias candidatas

Python, FastAPI, PostgreSQL, MinIO e ferramentas de extração documental/OCR.

---

# 6. P02 — PGE-SEARCH

Motor de pesquisa institucional.

Deverá pesquisar:

- documentos;
- pareceres;
- notas técnicas;
- legislação;
- processos autorizados;
- jurisprudência;
- manuais;
- orientações internas.

Deverá combinar pesquisa lexical e semântica.

---

# 7. P03 — PGE-RAG

Este será um dos componentes mais importantes.

O PGE-RAG será a camada responsável por fornecer conhecimento institucional para aplicações de IA.

```text
Pergunta
   ↓
Pesquisa híbrida
   ↓
Documentos relevantes
   ↓
Reranking
   ↓
Contexto
   ↓
LLM
   ↓
Resposta + fontes
```

O PGE-RAG deverá ser independente do chatbot.

Isso permitirá que futuramente seja utilizado por:

```text
PGE-Assistant ─┐
PGE-Triagem ───┤
PGE-Parecer ───┼── PGE-RAG
PGE-Agents ────┤
Outros sistemas┘
```

---

# 8. P04 — PGE-ASSISTANT

Interface conversacional corporativa.

Exemplos:

“Resuma este processo.”

“Localize pareceres relacionados ao assunto.”

“Compare estes dois documentos.”

“Quais fundamentos aparecem nos pareceres selecionados?”

“Prepare uma síntese para análise do procurador.”

Toda resposta baseada no acervo institucional deverá, sempre que tecnicamente possível, apresentar sua origem documental.

---

# 9. P05 — PGE-TRIAGEM

Serviço de inteligência processual.

Pipeline:

```text
PROCESSO
   ↓
PGE-DOCS
   ↓
Extração
   ↓
Classificação
   ↓
Resumo
   ↓
Entidades
   ↓
Assunto
   ↓
Prioridade
   ↓
Unidade sugerida
```

### IA/ML

Poderão ser empregados:

- classificação supervisionada;
- embeddings;
- NLP;
- LLM;
- modelos especializados.

A primeira versão deverá recomendar encaminhamentos, e não realizá-los autonomamente.

---

# 10. P06 — PGE-AUTOMA

Plataforma para automação de rotinas administrativas.

Exemplos:

- consultas repetitivas;
- obtenção de documentos;
- atualização de dados;
- geração de relatórios;
- captura de publicações;
- organização de arquivos;
- notificações;
- integração entre sistemas.

Regra arquitetural:

**API > integração de banco controlada > RPA.**

RPA deve ser utilizada principalmente quando o sistema de destino não disponibilizar interface adequada.

---

# 11. P07 — PGE-MONITOR

Monitoramento automatizado.

```text
Processos
Publicações
Prazos
Eventos
     │
     ↓
 PGE-Monitor
     │
     ↓
Mudança detectada
     │
     ↓
Classificação
     │
     ↓
Notificação
```

---

# 12. P08 — PGE-PARECER

Copiloto especializado para atividade jurídica.

Fluxo:

```text
Processo
   ↓
Resumo
   ↓
Questão jurídica
   ↓
PGE-RAG
   ↓
Pareceres anteriores
   ↓
Legislação
   ↓
Precedentes
   ↓
Estrutura sugerida
   ↓
Minuta
   ↓
Validação
   ↓
PROCURADOR
```

O sistema deverá ser concebido como ferramenta de apoio, e não como substituto da análise jurídica.

---

# 13. P09 — PGE-ANALYTICS

Camada gerencial.

Dashboards poderão acompanhar:

- estoque processual;
- processos recebidos;
- processos concluídos;
- tempo médio;
- assunto;
- unidade;
- valores;
- êxito;
- acordos;
- dívida ativa;
- saúde;
- precatórios;
- RPVs;
- produtividade;
- tendências.

---

# 14. P10 — PGE-DATA

Plataforma corporativa de dados.

Arquitetura:

```text
               SISTEMAS

        ┌─────────┼─────────┐
        ↓         ↓         ↓
       SEI       PJe     Sistemas PGE
        │         │         │
        └─────────┼─────────┘
                  ↓
              INGESTÃO
                  ↓
             DATA LAKE
                  ↓
         ┌────────┴────────┐
         ↓                 ↓
  DATA WAREHOUSE       IA / ML
         ↓                 ↓
       BI              Modelos
```

---

# 15. P11 — PGE-AGENTS

Projeto de maturidade avançada.

Não deverá ser implementado como primeira solução.

O agente deverá consumir os serviços anteriores:

```text
              Supervisor Agent

        ┌──────────┼──────────┐
        ↓          ↓          ↓
      Search      Docs       Legal
      Agent       Agent      Agent
        │          │          │
        └──────────┼──────────┘
                   ↓
               Risk Agent
                   ↓
             Drafting Agent
                   ↓
             Validator Agent
                   ↓
                HUMANO
```

---

# 16. P12 — PGE-PORTAL

Somente após amadurecimento dos módulos será necessário construir a experiência integrada.

O Portal não substituirá os serviços.

Será a camada de experiência do usuário.

```text
                   PGE-PORTAL

                        │
                   API Gateway
                        │
      ┌─────────┬───────┼───────┬─────────┐
      ↓         ↓       ↓       ↓         ↓
     Docs      RAG    Search  Triagem   Analytics
```

---

# 17. ARQUITETURA DE REFERÊNCIA

```text
                        USUÁRIOS
                            │
                   PGE-PA Portal
                            │
                       IAM / SSO
                            │
                       API Gateway
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
     Serviços            Serviços            Serviços
     Jurídicos              IA                Dados
        │                   │                    │
        │          ┌────────┼────────┐           │
        │          ↓        ↓        ↓           │
        │         RAG      LLM      ML           │
        │                                         │
        └───────────────────┬─────────────────────┘
                            │
                      Integration Layer
                            │
              ┌─────────────┼──────────────┐
              ↓             ↓              ↓
             SEI           PJe         Sistemas PGE
                            │
                     DATA PLATFORM
```

---

# 18. STACK TECNOLÓGICA DE REFERÊNCIA

A seleção definitiva dependerá da infraestrutura e contratos existentes, mas uma referência predominantemente baseada em tecnologias abertas seria:

### Backend

Python + FastAPI.

### Frontend

React/Next.js.

### Banco transacional

PostgreSQL.

### Vector Database

pgvector inicialmente.

Qdrant poderá ser avaliado para necessidades maiores.

### Cache

Redis.

### Object Storage

MinIO/S3.

### Mensageria

RabbitMQ inicialmente.

Kafka para cenários de maior escala/event streaming.

### IAM

Keycloak integrado ao diretório institucional.

### Containers

Docker.

### Orquestração futura

Kubernetes/K3s.

### Observabilidade

Prometheus + Grafana + Loki + OpenTelemetry.

### CI/CD

Git + CI + Registry + GitOps.

---

# 19. ARQUITETURA PARA IA

Não recomendo que cada aplicação se conecte diretamente a diferentes provedores de LLM.

Criar uma camada intermediária:

## AI Gateway

```text
Aplicações PGE
      │
      ↓
  AI Gateway
      │
 ┌────┼──────────────┐
 ↓    ↓              ↓
LLM  Modelo        Provedor
local especializado externo
```

O Gateway poderá controlar:

- autenticação;
- modelo utilizado;
- custo;
- tokens;
- logs;
- políticas;
- anonimização;
- rate limiting;
- fallback;
- auditoria.

Essa abstração reduz significativamente o vendor lock-in.

---

# 20. GOVERNANÇA DE IA

Criar um **Comitê de Governança de Dados, Automação e Inteligência Artificial**.

Participação recomendada:

- DTI;
- procuradores;
- segurança da informação;
- gestão;
- proteção de dados;
- unidades usuárias.

Classificar casos de uso por risco:

```text
BAIXO
Pesquisa e resumo interno

MODERADO
Classificação e recomendação

ALTO
Geração de conteúdo jurídico

CRÍTICO
Decisão ou ação automatizada
```

Quanto maior o risco, maior deverá ser a supervisão humana.

---

# 21. EQUIPE MÍNIMA DO PROGRAMA

Uma equipe inicial enxuta poderia possuir:

| Perfil | Quantidade inicial |
|---|---:|
| Líder/Arquiteto de Soluções | 1 |
| Backend Python/API | 2 |
| Frontend | 1 |
| DevOps/Infraestrutura | 1 |
| Engenheiro de Dados | 1 |
| IA/ML | 1 |
| Analista de Sistemas/Processos | 1 |
| Segurança | compartilhado |
| Especialistas jurídicos | representantes das áreas |

Total aproximado:

**8 profissionais técnicos dedicados + especialistas de negócio compartilhados.**

Não é necessário montar toda a equipe de 24 meses imediatamente.

---

# 22. ROADMAP DE 24 MESES

## ONDA 0 — Fundação
### Meses 1–2

Entregas:

- arquitetura de referência;
- Git institucional;
- Docker;
- CI/CD;
- homologação;
- IAM;
- padrão REST/OpenAPI;
- logging;
- observabilidade;
- padrões de segurança;
- inventário de sistemas;
- catálogo inicial de dados.

---

## ONDA 1 — Conhecimento
### Meses 3–5

Construir:

**PGE-Docs + PGE-RAG + PGE-Search.**

Primeiro grande resultado institucional:

**pesquisa inteligente sobre conhecimento autorizado da PGE.**

---

## ONDA 2 — IA Generativa
### Meses 5–7

Construir:

**PGE-Assistant.**

Integrar:

```text
Assistant
   ↓
RAG
   ↓
Search
   ↓
Docs
```

---

## ONDA 3 — Inteligência Processual
### Meses 7–10

Construir:

**PGE-Triagem.**

Realizar piloto inicialmente em uma única área.

Medir:

- acurácia;
- tempo economizado;
- erros;
- taxa de aceitação das recomendações.

---

## ONDA 4 — Automação
### Meses 9–13

Construir:

**PGE-Automa + PGE-Monitor.**

Selecionar aproximadamente cinco processos administrativos repetitivos de alto volume para pilotos.

---

## ONDA 5 — Dados
### Meses 10–16

Consolidar:

**PGE-Data + PGE-Analytics.**

Criar primeiros dashboards executivos.

---

## ONDA 6 — Copiloto Jurídico
### Meses 14–19

Construir:

**PGE-Parecer.**

Utilizar toda infraestrutura anterior:

```text
Docs
+
Search
+
RAG
+
LLM
+
Dados
```

---

## ONDA 7 — Integração
### Meses 18–22

Construir:

**PGE-Portal.**

O usuário passa a perceber os módulos como partes de um único ambiente.

---

## ONDA 8 — IA Agêntica
### Meses 21–24

Piloto:

**PGE-Agents.**

Somente processos controlados e com supervisão humana.

---

# 23. CRONOGRAMA CONSOLIDADO

```text
                     1  3  6  9  12  15  18  21  24 meses

Fundação             ███
Docs/RAG/Search          ████
Assistant                   ███
Triagem                       ████
Automação                       █████
Data/Analytics                   ███████
Copiloto                              █████
Portal                                      ████
Agents                                           ███
```

---

# 24. PRIORIDADE DE INVESTIMENTO

### PRIORIDADE 1

Infraestrutura, APIs, segurança e DevSecOps.

### PRIORIDADE 2

PGE-Docs.

### PRIORIDADE 3

PGE-RAG/Search.

### PRIORIDADE 4

Automação.

### PRIORIDADE 5

Dados/BI.

### PRIORIDADE 6

Copiloto jurídico.

### PRIORIDADE 7

Agentes autônomos.

A ordem é importante.

Não recomendo começar pelos agentes.

---

# 25. ESTIMATIVA PRELIMINAR DE CUSTOS

Sem levantamento da infraestrutura, contratos, licenças e quadro técnico atual da PGE-PA, qualquer número seria apenas uma estimativa de planejamento.

Para elaboração do orçamento definitivo deverá ser realizado diagnóstico próprio.

Como estrutura de custos, considerar:

| Categoria | Principais custos |
|---|---|
| Pessoas | desenvolvimento, dados, DevOps, IA |
| Computação | servidores/VMs/cloud |
| IA | GPU ou APIs de modelos |
| Storage | documentos, backups e Data Lake |
| Segurança | ferramentas e infraestrutura |
| Software | eventuais licenças |
| Capacitação | treinamento técnico e usuários |
| Integração | sistemas externos/legados |

A preferência por componentes open source reduz licenciamento, mas não elimina custos de operação, segurança, infraestrutura e pessoal especializado.

---

# 26. MATRIZ DE RISCOS

| Risco | Impacto | Mitigação |
|---|---|---|
| IA gerar informação incorreta | Alto | RAG + citações + validação humana |
| Vazamento de informação | Crítico | IAM + criptografia + segregação |
| Dependência de fornecedor | Alto | AI Gateway + APIs abertas |
| Sistema monolítico | Alto | microsserviços/modularidade |
| Falta de adesão | Alto | pilotos com usuários |
| Integrações frágeis | Alto | API Gateway |
| RPA quebrar | Médio | priorizar APIs |
| Dados ruins | Alto | governança de dados |
| Crescimento descontrolado | Médio | containers/orquestração |
| IA sem auditoria | Crítico | logs e trilhas completas |
| Projetos sem resultado | Alto | KPIs por MVP |

---

# 27. INDICADORES DE SUCESSO

Não avaliar o projeto apenas por "sistemas entregues".

Avaliar resultados.

Exemplos:

### Automação

Horas de trabalho manual eliminadas/mês.

### Documentos

Tempo médio para localização de informação.

### RAG

Recall@K e precisão das fontes recuperadas.

### IA

Taxa de respostas fundamentadas corretamente.

### Triagem

Precisão/F1 da classificação.

### Copiloto

Percentual de sugestões aproveitadas pelo procurador.

### Operação

Disponibilidade e latência dos serviços.

### Gestão

Percentual de indicadores estratégicos disponíveis automaticamente.

---

# 28. PRIMEIRO PROJETO PILOTO

O primeiro piloto não deve tentar resolver toda a PGE.

Sugestão:

## PGE Knowledge Assistant — MVP

Componentes:

```text
                  Interface Web
                       │
                  PGE-Assistant
                       │
                  AI Gateway
                       │
              ┌────────┴────────┐
              ↓                 ↓
            PGE-RAG            LLM
              │
        ┌─────┴─────┐
        ↓           ↓
     PGE-Docs     pgvector
        │
      MinIO
```

### Escopo inicial

Selecionar uma base controlada contendo, por exemplo:

- pareceres;
- notas técnicas;
- legislação;
- orientações internas;
- documentos públicos/institucionais autorizados.

### Funcionalidades

1. Upload de documentos.
2. Extração automática.
3. Indexação.
4. Pesquisa semântica.
5. Chat.
6. Resumo.
7. Comparação.
8. Respostas com fontes.
9. Controle de usuários.
10. Auditoria.

---

# 29. CRITÉRIO DE APROVAÇÃO DO MVP

Antes de avançar para produção ampla, executar avaliação objetiva.

Exemplo:

**200 perguntas jurídicas previamente validadas.**

Comparar:

```text
LLM puro

versus

LLM + RAG PGE
```

Medir:

- correção;
- fundamentação;
- recuperação documental;
- alucinação;
- latência;
- satisfação do usuário.

O MVP somente deverá avançar se demonstrar ganho mensurável.

---

# 30. VISÃO 2028

Ao final da transformação:

```text
                     PGE-PA INTELIGENTE
                              │
                       Portal Corporativo
                              │
                    ┌─────────┴─────────┐
                    │                   │
                Procurador          Servidor
                    │                   │
                    └─────────┬─────────┘
                              │
                         API Gateway
                              │
 ┌────────┬────────┬──────────┼──────────┬────────┬────────┐
 ↓        ↓        ↓          ↓          ↓        ↓        ↓
Docs    Search    RAG      Triagem    Automa   Parecer Analytics
 │        │        │          │          │        │        │
 └────────┴────────┴──────────┼──────────┴────────┴────────┘
                              │
                         AI Platform
                              │
                  ┌───────────┼───────────┐
                  ↓           ↓           ↓
                 LLM          ML        Agents
                              │
                         Data Platform
                              │
                  Integration Platform
                              │
                ┌─────────────┼─────────────┐
                ↓             ↓             ↓
               SEI           PJe       Sistemas PGE
```

---

# 31. RESULTADO ESPERADO

O objetivo do programa não será simplesmente colocar inteligência artificial na PGE-PA.

Será construir uma nova capacidade tecnológica institucional.

A DTI passará gradualmente de uma estrutura predominantemente responsável por sustentação de sistemas para uma estrutura capaz de oferecer:

**Infraestrutura + Sistemas + APIs + Dados + Automação + IA + Inteligência Institucional.**

O aspecto estratégico do modelo é que nenhuma das ferramentas propostas precisa aguardar a conclusão da plataforma completa.

Cada componente poderá nascer como projeto independente, resolver um problema concreto, ser avaliado objetivamente e posteriormente integrar-se aos demais.

Portanto:

**não se constrói primeiro uma grande plataforma para depois procurar problemas que ela resolva.**

**Resolvem-se problemas reais por meio de módulos independentes e, progressivamente, esses módulos formam a plataforma.**

Essa deverá ser a diretriz central do Programa de Modernização Tecnológica da DTI/PGE-PA 2026–2028.