# Plano de Demonstração (Showcase da RDL xApp)

Este guia prático foi desenhado para maximizar o impacto da sua apresentação, estruturando a demonstração do seu orquestrador cognitivo em cima do cluster **K8s (k3d)** que você possui, utilizando o Rancher para visualização e Helm para deploy.

O plano é dividido em duas partes estratégicas: uma voltada à arquitetura cognitiva (sem NS-3) e outra focada na validação em rede simulada (com NS-3 O-RAN).

---

## 🏗️ 0. Preparação do Ambiente (O Palco)

*Dica: Deixe tudo pré-carregado no cluster antes de projetar a tela.*
1. **Rancher Dashboard Aberto:** Mostre o cluster k3d rodando de forma saudável. Isso evidencia que a aplicação não é um script Python de laboratório, mas um microsserviço *Cloud Native*.
2. **Terminal em Tela Dividida (Split Screen):** 
   - Lado esquerdo: Logs dinâmicos da RDL xApp (usando `kubectl logs -f -l app=ricxapp-iqos-xapp-rdl`).
   - Lado direito: Terminal livre para disparar os *Control Requests* falsos ou disparar scripts.
3. **Métricas (Opcional):** Se o Prometheus/Grafana estiver no cluster, deixe um painel aberto monitorando `rdl_kpm_indications_total` e `rdl_active_xapps`.

---

## ⚡ Parte 1: Arquitetura e Decisão (Sem NS-3)
*Objetivo: Provar que o "cérebro" da xApp (Batching, SLA, APER e Resiliência) funciona perfeitamente, focando na Teoria da Computação e Engenharia de Software.*

Neste cenário, rodaremos a RDL xApp utilizando a variável `USE_FAKE_SDL=True` (acionando o nosso `MemoryModule` de fallback) e enviaremos ações artificiais via RMR ou injeção de script.

### Passo 1: O "Graceful Fallback" e APER Nativo
- **Ação:** Mostre a inicialização da xApp. 
- **O que falar:** *"Nós reescrevemos o núcleo para suportar mensagens **O-RAN APER nativas via ASN.1**, aderente às especificações (RF-08, 09 e 17). No entanto, para fins de demonstração, como não estou gerando APER bruto no terminal agora, o sistema reconhece falhas de decodificação e aciona o **MOCK fallback gracioso**, garantindo que a IA nunca trave."*

### Passo 2: O Poder do Decision Windowing (200ms)
- **Ação:** Envie 3 propostas RMR concorrentes quase simultaneamente (você pode rodar o `scripts/test_batching.py` adaptado ou injetar dados).
- **O que focar nos logs:** Mostre o log `Decision Window Expired. Processing batch of 3 actions`.
- **O que falar:** *"Diferente de xApps legadas que resolvem conflitos em First-Come-First-Served, a nossa RDL acumula propostas por 200ms. Isso aglutina pedidos assíncronos e evita que um conflito indireto passe despercebido."*

### Passo 3: Avaliação Combinatória (O Espaço de Estado)
- **Ação:** Acompanhe a resolução desse lote (onde a xApp A pede Potência e a xApp B pede Escalonador).
- **O que focar nos logs:** Mostre o log de resolução do `ReasoningAgent`. 
- **O que falar:** *"O nosso motor não apenas escolhe um vencedor, ele avalia matematicamente o espaço combinatório inteiro ($2^N$). A política de TVS (Throughput Violation Selection) determina se é vantajoso atender ambas simultaneamente (Ações Complementares) ou vetar uma delas com base no Acordo de SLA."*

---

## 📡 Parte 2: O Loop de Controle (Com NS-3 O-RAN)
*Objetivo: Demonstrar o impacto físico na rede e evidenciar o Loop Fechado.*

Aqui a complexidade aumenta. O NS-3 com O-RAN module servirá como o *E2 Node (gNB/UEs)*.

### Passo 1: O Fluxo de Percepção KPM
- **Ação:** Inicie a simulação NS-3 apontando para o seu E2 Term. Mostre que a RDL xApp está recebendo relatórios contínuos.
- **O que focar nos logs:** Os logs estruturados do `PerceptionAgent` atualizando o estado atual (Vazão do UE, Uso de PRB).
- **O que falar:** *"Neste cenário, estamos integrados ao NS-3. A RDL está monitorando passivamente as telemetrias via subscrições E2SM-KPM. Este é o pilar de Percepção do nosso Agente Cognitivo."*

### Passo 2: A Geração de Conflito Indireto
- **Ação:** Inicie duas xApps satélites (ou simule o tráfego delas):
  - *xApp 1:* Pede aumento extremo de potência TX para otimizar *Handover*.
  - *xApp 2:* Pede aumento de cota de PRB para maximizar *Throughput*.
- **O que focar nos logs:** O sistema acusando **"Conflito Indireto"** (já que afetam parâmetros distintos, mas impactam métricas de energia cruzadas).
- **O que falar:** *"Observe que as xApps querem coisas diferentes, não colidem diretamente no parâmetro. Porém, nossa topologia de grafos percebe a correlação de dependência indireta. E a RDL entra em ação."*

### Passo 3: A Atuação e a Física (E2SM-RC)
- **Ação:** A RDL processará o lote, penalizará a ação de Potência devido à violação extrema de Eficiência Energética (Política EEVS) e emitirá o `RICcontrolRequest`.
- **Visão do NS-3:** Mostre no terminal do NS-3 ou em gráficos de plotagem que a potência da antena foi barrada/reduzida, mas os PRBs do usuário foram alocados conforme solicitado.
- **O que falar:** *"O orquestrador tomou a decisão determinística e enviou um payload APER Nativo E2SM-RC em tempo real para o simulador NS-3. Em loop fechado, salvamos o mundo 5G de um colapso energético, ao mesmo tempo em que agradamos o SLA do usuário, preservando a harmonia da rede O-RAN."*

---

## 💡 Argumentos "Coringas" para Dúvidas da Banca

- **"Por que não ML/MARL puro o tempo todo?"**
  *Resposta:* Redes de Telecom exigem SLA garantido e latência < 10ms para o loop interno. Nosso modelo cognitivo tenta a resolução híbrida: usamos regras matemáticas rápidas (TVS) para urgência, guardando o MARL para aprendizado de dinâmicas indiretas lentas.
- **"O que acontece se o Redis (SDL) cair?"**
  *Resposta:* A xApp possui a variável `USE_FAKE_SDL`. Se o banco principal ficar indisponível, a aplicação migra graciosamente para estruturas de memória locais (MemoryModule), o que mantém o sistema de telecom sobrevivendo a desastres na infraestrutura de TI.
