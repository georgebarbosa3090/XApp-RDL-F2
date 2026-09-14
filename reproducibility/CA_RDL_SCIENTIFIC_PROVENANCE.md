# CA-RDL Scientific Provenance Contract

Resultados de `MAPPO_SMOKE_ENV`, mocks, demos, geradores locais e replay
não causal são **NON_PUBLICATION**.

Um treinamento MAPPO publicável deve registrar, no mínimo:

- SHA do commit do CA-RDL;
- backend e ambiente causal RAN;
- seeds de treinamento e avaliação, sem sobreposição;
- versão exata de Python, PyTorch, CUDA/cuDNN e device;
- hash do schema de observação;
- hash do schema de ações;
- hash da definição de reward/cost;
- hiperparâmetros completos;
- hash SHA-256 de actor/critic/optimizer checkpoints;
- manifesto do ambiente experimental;
- referências aos raw KPM/RC/ACK usados para construir transições;
- separação explícita entre training e unseen evaluation.

`TraceReplayEnvironment` é permitido para avaliação/replay offline, mas não
prova causalidade `action -> RAN state transition`.
