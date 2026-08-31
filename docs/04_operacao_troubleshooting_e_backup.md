# Volume 04: Operação, Troubleshooting e Diagnósticos da Fase 2 (CA-RDL / MARL)

**Documento:** Volume Temático 04  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimento Operacional Padrão (SOP), Diagnóstico de Falhas, Streaming de Logs e Recuperação de Pods  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Procedimentos Operacionais e Diagnósticos

### 1.1. Verificar o Status dos Pods das xApps
```bash
make status-f2
# ou: kubectl get pods -n ricxapp -o wide
```

### 1.2. Inspecionar Logs do Motor MARL/MAPPO em Tempo Real
```bash
make logs-f2
# ou: kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -f
```

### 1.3. Validar Endpoints HTTP e Métricas Prometheus
```bash
make test-f2
```

### 1.4. Troubleshooting de Problemas Comuns
* **Pod em CrashLoopBackOff:** Verifique se as dependências PyTorch foram carregadas ou se a porta RMR está livre (`kubectl describe pod -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2`).
* **Timeout na Interface E2:** Certifique-se de que a porta SCTP `36422` está mapeada corretamente no cluster k3d.
