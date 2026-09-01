.PHONY: build build-no-cache test validate package onboard install status status-f2 logs logs-f2 smoke-test uninstall helm-deploy-f2 helm-upgrade-f2 helm-uninstall-f1 helm-uninstall-f2 uninstall-all-rdl helm-test-f2 test-f2 test-3xapps cluster-create cluster-delete cluster-recreate setup-ns3 run-baseline run-rdl run-scenario1 run-scenario2 run-experiments run-suite analyze-benchmarks view-results push-results sync auto-sync rollback rollback-push rollback-clean rollback-list

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 2.0.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
NAMESPACE_RIC ?= ricplt
NAMESPACE ?= ricxapp
RELEASE_NAME_F2 ?= ricxapp-iqos-xapp-rdl-f2
CLUSTER_NAME ?= rancher-lab
NS3_DIR ?= $(HOME)/ns3-oran-workspace/ns-3-oran

# -------------------------------------------------------------
# Build e Testes Locais da xApp RDL Fase 2
# -------------------------------------------------------------
build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

# -------------------------------------------------------------
# Deploy Helm Exclusivo para RDL Fase 2 (CA-RDL / MARL)
# Premissa: Near-RT RIC e as 3 Reference xApps ja estao rodando!
# -------------------------------------------------------------
helm-deploy-f2:
	@echo "Implantando/Atualizando exclusivamente a xApp RDL Fase 2 ($(RELEASE_NAME_F2))..."
	bash scripts/deploy_rdl_phase2.sh

helm-upgrade-f2:
	@echo "Executando Helm Upgrade da release $(RELEASE_NAME_F2)..."
	helm upgrade --install $(RELEASE_NAME_F2) $(CHART_DIR) \
	  --namespace $(NAMESPACE) \
	  --set image.repository=$(IMAGE_NAME) \
	  --set image.tag=$(IMAGE_TAG) \
	  --set image.pullPolicy=Never \
	  --set fullnameOverride=$(RELEASE_NAME_F2) \
	  --set env.useFakeSdl="false" \
	  --set env.rmrWaitForReady="false" \
	  --set env.enableTorch="true"

helm-uninstall-f1:
	@echo "Removendo a xApp RDL Fase 1 (ricxapp-iqos-xapp-rdl)..."
	helm uninstall ricxapp-iqos-xapp-rdl -n $(NAMESPACE) || echo "Release ricxapp-iqos-xapp-rdl nao encontrada."

helm-uninstall-f2:
	@echo "Removendo exclusivamente a xApp RDL Fase 2 ($(RELEASE_NAME_F2))..."
	helm uninstall $(RELEASE_NAME_F2) -n $(NAMESPACE) || echo "Release $(RELEASE_NAME_F2) nao encontrada."

uninstall-all-rdl:
	@echo "Removendo todas as versoes da xApp RDL (Fase 1 e Fase 2)..."
	helm uninstall ricxapp-iqos-xapp-rdl -n $(NAMESPACE) 2>/dev/null || true
	helm uninstall $(RELEASE_NAME_F2) -n $(NAMESPACE) 2>/dev/null || true

status-f2:
	@echo "=== Status das xApps no Namespace $(NAMESPACE) ==="
	@kubectl get pods -n $(NAMESPACE) -o wide
	@echo "\n=== Pod da xApp RDL Fase 2 ==="
	@kubectl get pods -n $(NAMESPACE) -l app=$(RELEASE_NAME_F2) -o wide

watch-pods-f2:
	@kubectl get pods -n $(NAMESPACE) -l app=$(RELEASE_NAME_F2) -w

logs-f2:
	kubectl logs -l app=$(RELEASE_NAME_F2) -n $(NAMESPACE) -f

test-f2:
	@echo "Testando endpoints da xApp RDL Fase 2 (CA-RDL / MARL)..."
	@curl -i http://localhost:8080/health || true
	@echo "\nMétricas Prometheus:"
	@curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_" || true

test-3xapps:
	@echo "Testando integridade das 3 Reference xApps no cluster..."
	bash scripts/verify_3_xapps.sh

# -------------------------------------------------------------
# Gestao do Cluster k3d (se necessario)
# -------------------------------------------------------------
cluster-create:
	@echo "Criando cluster k3d $(CLUSTER_NAME)..."
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 0 --port "36422:36422/SCTP@server:0" --port "8080:8080@server:0" --port "8081:8081@server:0" --port "4560:4560@server:0" --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config

cluster-delete:
	k3d cluster delete $(CLUSTER_NAME)

# -------------------------------------------------------------
# Simulações ns-3 e Pipelines Experimentais
# -------------------------------------------------------------
setup-ns3:
	bash scripts/setup_ns3.sh

run-scenario1:
	@echo "Executando Cenário 1: Energy Saving vs QoS (EEVS) com logs em tempo real..."
	@mkdir -p $(NS3_DIR)/scratch
	@cp simulations/ns3/scenario_rdl_energy_vs_qos.cc $(NS3_DIR)/scratch/
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdlEnergyVsQos=level_all" && ./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"

run-scenario2:
	@echo "Executando Cenário 2: Traffic Steering vs QoS (TVS) com logs em tempo real..."
	@mkdir -p $(NS3_DIR)/scratch
	@cp simulations/ns3/scenario_rdl_tvs_conflict.cc $(NS3_DIR)/scratch/
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdlTvsConflict=level_all" && ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"

run-baseline:
	bash scripts/run_baseline_experiment.sh

run-rdl:
	bash scripts/run_rdl_experiment.sh

run-experiments:
	bash scripts/run_full_experiment.sh

run-suite:
	python3 scripts/run_experiment_suite.py

analyze-benchmarks:
	python3 scripts/run_experiment_suite.py

view-results:
	@cat experiments/results/relatorio_comparativo.md

push-results:
	@echo "Sincronizando resultados com o GitHub..."
	git add experiments/results/ docs/ scripts/
	git commit -m "chore(experiments): upload latest ns-3 MARL benchmark results [skip ci]" || echo "Nenhum dado novo."
	git push origin main || echo "Aviso no push."

sync:
	@bash scripts/git_sync.sh "$(MSG)"

auto-sync:
	@bash scripts/git_auto_sync.sh $(INTERVAL)
