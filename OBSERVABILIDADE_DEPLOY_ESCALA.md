# Observabilidade, Deploy e Escala - Pedidos Veloz

Este documento descreve como o projeto **Pedidos Veloz** aborda os três pilares solicitados no trabalho acadêmico: Observabilidade, Estratégia de Deploy e Escalabilidade.

---

## 1. OBSERVABILIDADE

A observabilidade é implementada com foco em **métricas, logs e traces distribuídos**.

### 1.1 Proposta de Métricas, Logs e Traces

#### **Métricas**
- **Local**: [observability/prometheus.yaml](observability/prometheus.yaml)
- **Solução**: **Prometheus**
  - Coleta métricas em tempo real de todos os serviços
  - Armazena séries temporais para análise histórica
  - Expõe interface web em `http://localhost:9090` (dentro do cluster)
  - Scrapa endpoints `/metrics` dos serviços (padrão Prometheus)

#### **Logs**
- **Abordagem**: Logs estruturados em stdout (12-factor app)
- **Acesso**: Via `kubectl logs <pod>` no Kubernetes
- **Potencial**: Integração com ELK Stack ou Cloud Logging (não implementada, conceitual)
- **Vantagem**: Facilita correlação com traces distribuídos

#### **Traces Distribuídos**
- **Local**: [observability/jaeger.yaml](observability/jaeger.yaml)
- **Solução**: **Jaeger (Uber)**
  - Rastreia requisições entre serviços microserviços
  - Coleta spans para cada operação (API Gateway → Order Service → Database)
  - Interface web em `http://localhost:16686` para visualização
  - Suporta sampling para high-throughput (configurável)

### 1.2 Estratégia de Tracing Distribuído (Conceitual e Instrumentada)

#### **Arquitetura de Traces**

```
Cliente HTTP
    ↓ (trace-id: xyz)
API Gateway [span: "POST /orders"]
    ↓ (propaga trace-id)
Order Service [span: "create_order", span: "db_insert"]
    ↓ (propaga trace-id)
Payment Service [span: "validate_payment"]
    ↓ (propaga trace-id)
Inventory Service [span: "reserve_stock"]
    ↓ (propaga trace-id)
RabbitMQ [span: "publish_event"]
```

#### **Implementação**

**Componentes Instrumentados:**

1. **Serviços Flask**: Cada serviço pode ser instrumentado com `jaeger-client` Python:
   ```python
   from jaeger_client import Config
   from opentracing_instrumentation.local_span import LocalSpan
   
   # Inicializar tracer
   config = Config(
       config={'sampler': {'type': 'const', 'param': 1}},
       service_name='order-service'
   )
   tracer = config.initialize_tracer()
   ```

2. **Propagação de Contexto**: Via headers HTTP padrão (W3C Trace Context ou Jaeger):
   - `traceparent` ou `uber-trace-id` é propagado entre serviços
   - Cada chamada HTTP cria um novo span filho

3. **Banco de Dados e RabbitMQ**: Spans adicionais para operações de I/O:
   - `db_query`, `db_insert`, `publish_message`

#### **Justificativa**

- **Jaeger** é escolha padrão em clusters Kubernetes (CNCF)
- **Tracing distribuído** permite:
  - Identificar gargalos de latência
  - Detectar falhas em cascata entre serviços
  - Correlacionar logs e métricas via trace-id único
  - Validar SLA de ponta-a-ponta

---

## 2. ESTRATÉGIA DE DEPLOY

### 2.1 Abordagem Selecionada: **Rolling Deployment** com suporte a **Blue-Green**

#### **Estratégia Principal: Rolling Deployment**

**Definição**: Substitui gradualmente réplicas antigas por novas, com zero downtime.

**Implementação no Kubernetes:**

- **Local**: [k8s/manifests/api-gateway.yaml](k8s/manifests/api-gateway.yaml) (e serviços similares)
- **Configuração**:
  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: api-gateway
  spec:
    replicas: 2
    strategy:
      type: RollingUpdate
      rollingUpdate:
        maxSurge: 1        # 1 pod adicional durante update
        maxUnavailable: 0  # 0 pods indisponíveis (zero downtime)
  ```

**Fluxo:**
1. Novo pod com v2 é criado
2. Tráfego é gradualmente roteado para v2 via Service
3. Pod v1 antigo é removido após health check passar
4. Repetir até todas as réplicas estarem em v2

**Vantagens:**
- Sem downtime
- Rollback automático se health checks falharem
- Economia de recursos (máx 3 pods simultâneos para 2 réplicas)

#### **Estratégia Complementar: Blue-Green (Conceitual)**

**Definição**: Manter dois ambientes (Blue/atual, Green/novo) e fazer switch instantâneo.

**Como implementar** (não está ativo, mas conceitual):
```yaml
# Blue (atual)
labels:
  version: v1
  slot: blue

---
# Green (novo)
labels:
  version: v2
  slot: green

---
# Service aponta para "slot: blue"
selector:
  slot: blue
  
# Após validar Green, mudar para:
selector:
  slot: green
```

**Vantagens:**
- Rollback instantâneo (switchar label)
- Ambos ambientes disponíveis para validação
- Ideal para hotfixes críticos

### 2.2 Justificativa da Escolha

| Critério | Rolling | Blue-Green | Canary |
|----------|---------|-----------|--------|
| **Downtime** | Zero | Zero | Zero |
| **Recursos** | Baixo | Alto (2x) | Médio |
| **Complexidade** | Baixa | Baixa | Alta |
| **Rollback** | Automático (lento) | Instantâneo | Graduado |
| **Validação** | Health checks | Ambiente completo | % tráfego real |

**Decisão**: **Rolling como padrão** (simples, eficiente) + **Blue-Green como opção** para produção crítica.

### 2.3 Integração com CI/CD

- **Pipeline GitHub Actions**: [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)
  - Build imagens Docker
  - Testes unitários e integração
  - Security scan (Trivy)
  - Deploy: `kubectl apply -f k8s/manifests/`

---

## 3. ESCALABILIDADE

### 3.1 Estratégia de Auto-Scaling: HPA (Horizontal Pod Autoscaler)

**Local**: [k8s/manifests/hpa.yaml](k8s/manifests/hpa.yaml)

#### **Configuração**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### **Comportamento**

- **Métrica monitorada**: CPU média dos pods
- **Threshold**: 70% utilização
- **Scaling Up**: Se CPU > 70% → adiciona pods (até máx 10)
- **Scaling Down**: Se CPU < 70% por 5 min → remove pods (até mín 2)
- **Período de reconciliação**: 15 segundos (padrão)

#### **Fluxo**

```
Cliente 1 → CPU 60% (2 pods) → Normal
Client 2 → CPU 75% (2 pods) → CPU > 70%
           ↓ HPA decision → Escala para 3 pods
           CPU 50% (3 pods) → Reduz novo escalonamento
```

### 3.2 Possível Extensão: VPA (Vertical Pod Autoscaler)

**Não implementado**, mas conceitual:
- Ajusta `requests` e `limits` de CPU/Memory dinamicamente
- Útil quando workload tem picos previsíveis
- Requer restart dos pods (downtime)
- **Quando usar**: Workloads com tamanho imprevisível

### 3.3 Alinhamento com Outros Pilares

#### **Observabilidade → Escalabilidade**
- Prometheus fornece métricas de CPU/Memory
- HPA usa essas métricas para decisões de scale
- Jaeger ajuda a identificar gargalos (P95 latência)

#### **Deploy → Escalabilidade**
- Rolling deployment respeita HPA:
  - Novo pod é criado com mesmo tamanho (resources)
  - HPA ajusta réplicas totais se necessário
- Blue-Green simplifica rollback de scaling issues

#### **Containers → Escalabilidade**
- **Requests/Limits** em [k8s/manifests/api-gateway.yaml](k8s/manifests/api-gateway.yaml):
  ```yaml
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  ```
  - Permitem scheduler Kubernetes posicionar pods corretamente
  - HPA usa `requests` como baseline para cálculo de percentual

### 3.4 Estratégia de Escalabilidade por Componente

| Serviço | Min | Max | Métrica | Justificativa |
|---------|-----|-----|---------|---------------|
| **API Gateway** | 2 | 10 | CPU 70% | Ponto de entrada, alto throughput |
| **Order Service** | 2 | 8 | CPU 70% | Operações síncronas, DB-bound |
| **Payment Service** | 1 | 5 | CPU 70% | Serviço crítico, pouca concorrência |
| **Inventory Service** | 2 | 8 | CPU 70% | Leitura frequente (reservas) |

---

## 4. COMO DEMONSTRAR NO TRABALHO

### 4.1 Observabilidade
```bash
# 1. Subir observabilidade
kubectl apply -f observability/

# 2. Abrir Prometheus
kubectl port-forward svc/prometheus 9090:9090
# Acessar: http://localhost:9090/graph
# Query: rate(http_requests_total[5m])

# 3. Abrir Jaeger
kubectl port-forward svc/jaeger 16686:16686
# Acessar: http://localhost:16686
# Procurar traces de uma requisição end-to-end
```

### 4.2 Deploy com Rolling Update
```bash
# 1. Verificar versão atual
kubectl get deployment api-gateway -o wide

# 2. Fazer update (simular novo código)
kubectl set image deployment/api-gateway \
  api-gateway=pedidos-veloz/api-gateway:v2

# 3. Monitorar rolling update
kubectl rollout status deployment/api-gateway

# 4. Rollback se necessário
kubectl rollout undo deployment/api-gateway
```

### 4.3 Escalabilidade com HPA
```bash
# 1. Subir HPA
kubectl apply -f k8s/manifests/hpa.yaml

# 2. Monitorar estado
kubectl get hpa api-gateway-hpa --watch

# 3. Gerar carga para testar
kubectl run -it --rm load-generator \
  --image=busybox /bin/sh
# Dentro do pod: while true; do wget -O- http://api-gateway:8080; done

# 4. Observar scaling
kubectl get pods -l app=api-gateway --watch
```

---

## 5. ARQUIVOS RELEVANTES

| Arquivo | Propósito |
|---------|-----------|
| [observability/prometheus.yaml](observability/prometheus.yaml) | Stack de métricas |
| [observability/grafana.yaml](observability/grafana.yaml) | Dashboard de visualização |
| [observability/jaeger.yaml](observability/jaeger.yaml) | Tracing distribuído |
| [k8s/manifests/hpa.yaml](k8s/manifests/hpa.yaml) | Auto-scaling horizontal |
| [k8s/manifests/api-gateway.yaml](k8s/manifests/api-gateway.yaml) | Deployment com estratégia |
| [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) | Deploy via CI/CD |
| [terraform/main.tf](terraform/main.tf) | Provisionamento de infraestrutura |

---

## 6. CONCLUSÃO

O projeto **Pedidos Veloz** implementa uma solução completa de DevOps moderno:

✅ **Observabilidade**: Métricas (Prometheus), Logs (stdout), Traces (Jaeger)  
✅ **Deploy**: Rolling Update com suporte Blue-Green  
✅ **Escalabilidade**: HPA baseado em CPU, escalável de 2 a 10 pods  
✅ **Integração**: GitHub Actions → Kubernetes → Observabilidade  

Todos os componentes trabalham em conjunto para garantir **confiabilidade, visibilidade e performance** em produção.
