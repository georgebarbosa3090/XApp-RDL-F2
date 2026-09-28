# Prompt Mestre — Vídeo Científico dos Dois Cenários do XApp-RDL

Crie um **vídeo-resumo científico, técnico e visualmente didático** sobre os experimentos do projeto **XApp-RDL**, apresentando e simulando conceitualmente os **dois cenários experimentais implementados**.

O vídeo deve ser baseado **exclusivamente nos documentos, códigos, resultados, gráficos e informações fornecidos nas fontes do NotebookLM**. Não invente componentes, métricas, resultados, topologias ou tecnologias que não estejam presentes nas fontes.

## Objetivo do vídeo

Explicar visualmente:

1. **Cenário 1 — RDL: Energy vs QoS**
2. **Cenário 2 — RDL: TVS Conflict**

O vídeo deve mostrar como o mecanismo **RDL (Resource/Radio Decision Logic, conforme definido nas fontes)** toma decisões sobre recursos da rede e como essas decisões afetam simultaneamente **QoS, consumo de energia e conflitos entre objetivos**, de acordo com a implementação real do projeto.

---

# Estrutura narrativa

## 1. Introdução — O problema

Comece apresentando o problema científico:

> Como realizar decisões de alocação/controle de recursos em uma rede Open RAN de forma determinística, segura e explicável, equilibrando requisitos de QoS e eficiência energética?

Apresente brevemente:

- Open RAN;
- Near-RT RIC, somente se estiver presente nas fontes;
- RDL;
- recursos de rádio;
- QoS;
- energia;
- decisões de controle;
- necessidade de evitar decisões conflitantes.

Não apresente inteligência artificial generativa como parte do mecanismo experimental se isso não estiver implementado nos cenários.

---

# 2. Arquitetura experimental

Mostre uma representação visual simplificada da arquitetura efetivamente utilizada.

A representação deve deixar claro:

**UEs/usuários → células/antenas → RAN → mecanismo RDL → métricas/resultados**

Se o código indicar exatamente duas antenas/células, represente **exatamente duas antenas/células**, sem adicionar antenas fictícias.

Mostre que os experimentos são controlados por parâmetros definidos nos scripts de simulação.

Destaque visualmente:

- entradas;
- decisões do RDL;
- recursos disponíveis;
- métricas observadas;
- saída da decisão.

Não introduza elementos como AMF, SMF, UPF, PGW, EPC, Free5GC ou OAI caso eles não façam parte efetivamente dos dois cenários simulados.

---

# 3. Simulação do Cenário 1 — Energy vs QoS

Título visual:

**Cenário 1 — Energy vs QoS**

Explique que o objetivo do experimento é investigar o compromisso entre:

**Eficiência energética ↔ Qualidade de Serviço**

Faça uma simulação visual passo a passo.

### Etapa A — Estado inicial

Mostrar:

- duas antenas/células, caso confirmado pelo código;
- usuários distribuídos entre as células;
- recursos de rádio disponíveis;
- demandas de tráfego;
- estado inicial da rede.

### Etapa B — Coleta das métricas

Mostrar o RDL recebendo informações como:

- demanda;
- utilização dos recursos;
- QoS;
- consumo/estimativa de energia;

somente para as métricas efetivamente utilizadas pelo código.

### Etapa C — Decisão RDL

Mostrar visualmente o RDL avaliando alternativas.

Representar:

**Estado da rede → regras/decisão RDL → nova configuração de recursos**

Explique que a decisão deve ser apresentada de maneira **determinística e interpretável**, conforme a implementação.

### Etapa D — Resultado

Mostrar a alteração dos recursos e seus efeitos sobre:

- QoS;
- energia;
- utilização dos recursos.

Apresente os gráficos/resultados reais disponíveis nas fontes.

Se houver múltiplos pontos experimentais, mostre a evolução progressiva:

**baixa carga → carga intermediária → alta carga**

somente se isso estiver efetivamente presente nos dados.

### Interpretação

Explique:

- quando economizar energia;
- quando preservar QoS;
- quando existe trade-off;
- como o RDL resolve esse compromisso.

Não invente valores numéricos.

---

# 4. Simulação do Cenário 2 — TVS Conflict

Título visual:

**Cenário 2 — TVS Conflict**

Explique o problema de conflito entre decisões/requisitos.

Apresente visualmente uma situação em que diferentes objetivos ou condições da rede podem levar a decisões conflitantes.

Mostrar:

**Estado da rede → condições/objetivos conflitantes → decisão RDL → configuração resultante**

Explique o significado de **TVS** exatamente conforme definido nos documentos e no código.

Não expanda a sigla por hipótese.

---

## Simulação passo a passo

### Estado inicial

Mostrar as duas células/antenas e os usuários, caso sejam exatamente os elementos presentes na implementação.

### Condição de conflito

Visualizar claramente:

**Objetivo/Regra A ↔ Objetivo/Regra B**

Mostrar que uma decisão que favorece um requisito pode prejudicar outro.

### Atuação do RDL

Mostrar o RDL avaliando as condições e aplicando sua lógica de decisão.

O espectador deve conseguir visualizar:

**Entrada → regra RDL → decisão → consequência**

### Resultado

Mostrar o estado da rede após a decisão.

Comparar:

**antes da decisão × depois da decisão**

Utilizar os resultados reais disponíveis no projeto.

---

# 5. Comparação dos dois cenários

Criar uma seção visual chamada:

**Comparação Experimental**

Apresentar uma tabela ou quadro visual:

| Aspecto | Cenário 1 | Cenário 2 |
|---|---|---|
| Objetivo | Energy vs QoS | TVS Conflict |
| Problema | Trade-off energia/QoS | Conflito entre decisões/requisitos |
| Entrada | Métricas da rede | Condições de conflito |
| Mecanismo | RDL | RDL |
| Decisão | Ajuste de recursos | Resolução do conflito |
| Resultado | QoS × energia | Decisão consistente |

Preencher somente informações confirmadas pelas fontes.

---

# 6. Visualização dos resultados

Utilize os gráficos reais disponíveis nos documentos/repositórios.

Para cada gráfico:

1. explique o eixo X;
2. explique o eixo Y;
3. explique cada curva/barra;
4. indique o comportamento observado;
5. explique o significado científico;
6. não altere os valores originais.

Não invente resultados para preencher gráficos ausentes.

---

# 7. Mensagem científica principal

Finalizar mostrando que os dois experimentos avaliam diferentes propriedades da mesma abordagem RDL:

**Cenário 1**
→ capacidade de lidar com o compromisso **energia × QoS**

**Cenário 2**
→ capacidade de lidar com **conflitos de decisão**

Concluir explicando quais evidências experimentais sustentam a proposta e quais limitações permanecem.

---

# Estilo visual do vídeo

Utilize estilo:

**artigo científico / laboratório de telecomunicações / Open RAN**

Características:

- visual acadêmico;
- diagramas técnicos;
- gráficos científicos;
- animações discretas;
- arquitetura de rede limpa;
- duas células/antenas quando aplicável;
- fluxo de dados claramente indicado;
- sem estética futurista exagerada;
- sem robôs;
- sem avatares;
- sem elementos de ficção científica;
- sem aparência de propaganda comercial;
- sem "IA generativa" visual.

O vídeo deve parecer uma **demonstração experimental de um artigo científico**, e não um vídeo publicitário.

---

# Narração

A narração deve ser feita em linguagem científica, porém compreensível.

Evite frases vagas como:

"o sistema utiliza inteligência artificial avançada para otimizar a rede".

Prefira:

"Neste experimento, o mecanismo RDL recebe as condições observadas da rede e aplica a lógica de decisão definida no modelo experimental."

Explique sempre:

**o que entra → o que é decidido → o que muda → qual métrica é afetada.**

---

# Regra de fidelidade científica

IMPORTANTE:

O vídeo deve distinguir claramente entre:

**IMPLEMENTADO**
e
**CONCEITUAL/FUTURO**.

Não apresentar funcionalidades futuras como se já estivessem implementadas.

Se houver diferença entre a arquitetura conceitual do projeto e o código efetivamente executado, priorize **o código e os resultados experimentais** para descrever os cenários.

Não invente:

- número de antenas;
- número de UEs;
- protocolos;
- componentes 5G;
- métricas;
- valores;
- resultados;
- algoritmos;
- módulos;
- interfaces;
- entidades de rede.

Quando uma informação não estiver disponível nas fontes, simplesmente indique:

**"Não especificado nos dados experimentais fornecidos."**

---

# Encerramento

Finalizar com uma síntese visual:

**XApp-RDL**

**Cenário 1**
Energy ↔ QoS

+

**Cenário 2**
TVS Conflict

↓

**Avaliação experimental da lógica RDL**

Encerrar destacando que os experimentos permitem avaliar a capacidade da abordagem RDL de produzir decisões **determinísticas, consistentes e explicáveis**, dentro das condições definidas pelos cenários experimentais.