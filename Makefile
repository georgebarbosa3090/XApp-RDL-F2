.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall helm-deploy helm-deploy-baseline helm-package helm-test helm-uninstall k8s-deploy k8s-deploy-baseline k8s-uninstall k8s-test test-3xapps kiali-install kiali-dashboard inject-traffic start-traffic stop-traffic cluster-create cluster-delete cluster-recreate rancher-start rancher-stop rancher-logs rancher-password rancher-connect setup-ns3 deploy-rdl deploy-baseline run-baseline run-rdl run-experiments run-suite analyze-benchmarks view-results push-results sync auto-sync rollback rollback-push rollback-clean rollback-list

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 2.0.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
K8S_DIR ?= deploy/kubernetes
NAMESPACE_RIC ?= ricplt
NAMESPACE ?= ricxapp
RELEASE_NAME ?= ricxapp-iqos-xapp-rdl
CLUSTER_NAME ?= rancher-lab

build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

# Gestão do Cluster k3d
cluster-create:
	@echo "Criando cluster k3d $(CLUSTER_NAME)..."
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 0 --port "36422:36422/SCTP@server:0" --port "8080:8080@server:0" --port "8081:8081@server:0" --port "4560:4560@server:0" --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config

cluster-delete:
	k3d cluster delete $(CLUSTER_NAME)

# Deploy Helm / K8s
helm-deploy:
	bash scripts/deploy_helm.sh --with-rdl

helm-deploy-baseline:
	bash scripts/deploy_helm.sh --baseline

test-3xapps:
	bash scripts/verify_3_xapps.sh

# Simulações ns-3 e Pipelines Experimentais
setup-ns3:
	bash scripts/setup_ns3.sh

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
