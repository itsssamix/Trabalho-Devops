# Pedidos Veloz - Plataforma de Pedidos em Microsserviços

Este projeto implementa uma plataforma de pedidos para e-commerce "Pedidos Veloz" usando arquitetura de microsserviços, seguindo práticas DevOps modernas.

## Arquitetura

- **API Gateway**: Ponto de entrada único, roteia requisições para serviços internos.
- **Order Service**: Gerencia criação e consulta de pedidos.
- **Payment Service**: Processa pagamentos.
- **Inventory Service**: Controla reserva e liberação de estoque.
- **Database**: PostgreSQL para persistência.
- **Messaging**: RabbitMQ para eventos assíncronos.

## Tecnologias

- **Contêineres**: Docker e Docker Compose para desenvolvimento local.
- **Orquestração**: Kubernetes com Deployments, Services, ConfigMaps, Secrets, HPA.
- **CI/CD**: GitHub Actions para build, test e deploy.
- **IaC**: Terraform para provisionamento de infraestrutura (esqueleto).
- **Observabilidade**: Prometheus, Grafana, Jaeger.

## Desenvolvimento Local

1. Clone o repositório.
2. Execute `docker-compose up --build` para subir todos os serviços.
3. Acesse o API Gateway em http://localhost:8080.

## Deploy no Kubernetes

1. Configure kubectl para o cluster.
2. Aplique os manifests: `kubectl apply -f k8s/manifests/`.
3. Para observabilidade: `kubectl apply -f observability/`.

## CI/CD

O pipeline GitHub Actions constrói imagens Docker, executa testes básicos e faz deploy no K8s.

## IaC

Use Terraform na pasta `terraform/` para criar um cluster GKE.

## Exemplo de Uso

Criar um pedido:
```bash
curl -X POST http://localhost:8080/orders -H "Content-Type: application/json" -d '{"product_id": 1, "quantity": 2}'
```

## Baseado em

Este projeto é inspirado no Google Cloud Platform Microservices Demo (Online Boutique), adaptado para o cenário brasileiro de e-commerce.