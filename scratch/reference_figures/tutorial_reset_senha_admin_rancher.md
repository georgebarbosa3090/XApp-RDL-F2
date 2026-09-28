# Tutorial --- Reset da Senha do Administrador no Rancher

## Objetivo

Este procedimento mostra como recuperar o acesso administrativo ao
Rancher Manager instalado no cluster k3d/K3s, redefinindo a senha do
usuário local `admin`.

> **Importante:** na tela normal de login, o usuário é `admin`.
> `bootstrap` não é o nome de usuário administrativo.

## 1. Bootstrap Password x senha do admin

A **Bootstrap Password** é usada somente durante a configuração inicial
do Rancher. Para consultá-la:

``` bash
kubectl get secret bootstrap-secret \
  -n cattle-system \
  -o go-template='{{.data.bootstrapPassword|base64decode}}{{"\n"}}'
```

Depois do primeiro setup, o login normal é:

``` text
Username: admin
Password: <senha administrativa>
```

## 2. Confirmar que o Rancher está funcionando

``` bash
kubectl get pods -n cattle-system -l app=rancher
```

O pod deve estar `1/1 Running`.

Confira também:

``` bash
kubectl get deployment rancher -n cattle-system
```

## 3. Resetar a senha do admin

A forma mais prática é localizar automaticamente o pod Rancher e
executar `reset-password`:

``` bash
kubectl exec -it -n cattle-system \
  $(kubectl get pods -n cattle-system \
  -l app=rancher \
  -o jsonpath='{.items[0].metadata.name}') \
  -- reset-password
```

O Rancher deverá retornar uma nova senha administrativa. Guarde-a
temporariamente.

## 4. Fazer login

No laboratório configurado, acesse:

``` text
https://rancher.localhost:8443
```

Use:

``` text
Username: admin
Password: <senha retornada pelo reset-password>
```

Não use:

``` text
Username: bootstrap
```

## 5. Alternativa usando o nome explícito do pod

Descubra o pod:

``` bash
kubectl get pods -n cattle-system -l app=rancher
```

Exemplo:

``` text
rancher-566679bf4c-hbx9g
```

Execute:

``` bash
kubectl exec -it -n cattle-system \
  rancher-566679bf4c-hbx9g \
  -- reset-password
```

## 6. Se o reset falhar

Verifique todos os pods:

``` bash
kubectl get pods -n cattle-system -o wide
```

Veja os logs:

``` bash
kubectl logs -n cattle-system deployment/rancher --tail=200
```

Acompanhe em tempo real:

``` bash
kubectl logs -n cattle-system deployment/rancher -f
```

Consulte eventos:

``` bash
kubectl get events -n cattle-system \
  --sort-by=.metadata.creationTimestamp
```

## 7. Testar a API

``` bash
curl -k https://rancher.localhost:8443/ping
```

Esperado:

``` text
pong
```

## 8. Verificar Ingress

``` bash
kubectl get ingress -n cattle-system
kubectl describe ingress rancher -n cattle-system
kubectl get ingressclass
```

No laboratório com ingress-nginx, a classe esperada é `nginx`.

## 9. Verificar rancher-webhook

``` bash
kubectl get deployment rancher-webhook -n cattle-system
kubectl get pods -n cattle-system -l app=rancher-webhook -o wide
kubectl get svc rancher-webhook -n cattle-system
kubectl get endpointslices -n cattle-system
```

O pod `rancher-webhook` deve estar `Running`.

## 10. Reiniciar o Rancher sem destruir o cluster

``` bash
kubectl rollout restart deployment/rancher -n cattle-system
```

Acompanhe:

``` bash
kubectl rollout status deployment/rancher -n cattle-system
kubectl get pods -n cattle-system
```

Quando o Rancher voltar para `1/1 Running`, tente novamente:

``` bash
kubectl exec -it -n cattle-system \
  $(kubectl get pods -n cattle-system \
  -l app=rancher \
  -o jsonpath='{.items[0].metadata.name}') \
  -- reset-password
```

## 11. Diagnóstico completo

``` bash
echo "===== NODES ====="
kubectl get nodes -o wide

echo
echo "===== RANCHER PODS ====="
kubectl get pods -n cattle-system -o wide

echo
echo "===== DEPLOYMENT ====="
kubectl get deployment rancher -n cattle-system

echo
echo "===== SERVICE ====="
kubectl get svc rancher -n cattle-system

echo
echo "===== INGRESS ====="
kubectl get ingress rancher -n cattle-system

echo
echo "===== WEBHOOK ====="
kubectl get pods -n cattle-system -l app=rancher-webhook

echo
echo "===== HELM ====="
helm list -A

echo
echo "===== API ====="
curl -k https://rancher.localhost:8443/ping

echo
echo "===== LOGS ====="
kubectl logs -n cattle-system deployment/rancher --tail=100
```

## 12. Resumo rápido

Na maioria dos casos:

``` bash
kubectl exec -it -n cattle-system \
  $(kubectl get pods -n cattle-system \
  -l app=rancher \
  -o jsonpath='{.items[0].metadata.name}') \
  -- reset-password
```

Depois:

``` text
URL:      https://rancher.localhost:8443
Username: admin
Password: <nova senha retornada>
```

## Fluxo das credenciais

``` text
Instalação
    |
    v
Bootstrap Password
    |
    | usada no primeiro setup
    v
Configuração inicial
    |
    v
Usuário admin + senha definitiva
    |
    v
Login normal
    |
    +-- senha esquecida
            |
            v
       reset-password
            |
            v
       nova senha admin
```

## Boas práticas

-   Não reutilize a Bootstrap Password como senha permanente.
-   Não compartilhe a senha exibida pelo `reset-password`.
-   Não grave senhas em Git, scripts ou documentação.
-   Para ambientes compartilhados/produção, utilize TLS confiável e
    política apropriada de autenticação.
