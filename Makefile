# Makefile para PayFlow - Sistema de Automação Financeira

.PHONY: help build up down logs clean test

# Variáveis
COMPOSE_FILE = docker-compose.yml
PROJECT_NAME = payflow

help: ## Mostrar ajuda
	@echo "PayFlow - Sistema de Automação Financeira - Comandos Disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Configurar ambiente inicial
	@echo "🚀 Configurando ambiente de desenvolvimento..."
	@cp env.example .env
	@echo "✅ Arquivo .env criado. Ajuste as configurações se necessário."

build: ## Construir todas as imagens Docker
	@echo "🔨 Construindo imagens Docker..."
	docker-compose -f $(COMPOSE_FILE) build

up: ## Subir todos os serviços
	@echo "🚀 Iniciando todos os serviços..."
	docker-compose -f $(COMPOSE_FILE) up -d

up-logs: ## Subir todos os serviços com logs
	@echo "🚀 Iniciando todos os serviços com logs..."
	docker-compose -f $(COMPOSE_FILE) up

down: ## Parar todos os serviços
	@echo "🛑 Parando todos os serviços..."
	docker-compose -f $(COMPOSE_FILE) down

restart: down up ## Reiniciar todos os serviços

logs: ## Ver logs de todos os serviços
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-core: ## Ver logs do Core API
	docker-compose -f $(COMPOSE_FILE) logs -f core-api

logs-db: ## Ver logs do PostgreSQL
	docker-compose -f $(COMPOSE_FILE) logs -f postgres

logs-queue: ## Ver logs do RabbitMQ
	docker-compose -f $(COMPOSE_FILE) logs -f rabbitmq

status: ## Ver status dos serviços
	docker-compose -f $(COMPOSE_FILE) ps

clean: ## Limpar containers, volumes e imagens
	@echo "🧹 Limpando ambiente Docker..."
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

clean-all: ## Limpar tudo incluindo imagens
	@echo "🧹 Limpeza completa do ambiente Docker..."
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -af

db-shell: ## Conectar ao shell do PostgreSQL
	docker-compose -f $(COMPOSE_FILE) exec postgres psql -U dev_user -d financial_automation

db-reset: ## Resetar banco de dados
	@echo "🔄 Resetando banco de dados..."
	docker-compose -f $(COMPOSE_FILE) down postgres
	docker volume rm financial-automation_postgres_data || true
	docker-compose -f $(COMPOSE_FILE) up -d postgres
	@echo "⏳ Aguardando banco inicializar..."
	sleep 10
	@echo "✅ Banco de dados resetado!"

queue-ui: ## Abrir interface do RabbitMQ
	@echo "🐰 Interface do RabbitMQ: http://localhost:15672"
	@echo "   Usuário: $(shell grep RABBITMQ_USER .env 2>/dev/null | cut -d'=' -f2 || echo 'dev_user')"
	@echo "   Senha: [configurada no arquivo .env]"

storage-ui: ## Abrir interface do MinIO
	@echo "📦 Interface do MinIO: http://localhost:9001"
	@echo "   Usuário: $(shell grep MINIO_USER .env 2>/dev/null | cut -d'=' -f2 || echo 'dev_user')"
	@echo "   Senha: [configurada no arquivo .env]"

api-docs: ## Abrir documentação da API
	@echo "📚 Documentação da API: http://localhost:8000/docs"

frontend: ## Abrir frontend
	@echo "🌐 Frontend: http://localhost:3000"

dev: up ## Iniciar ambiente de desenvolvimento
	@echo "🎯 Ambiente de desenvolvimento iniciado!"
	@echo ""
	@echo "📚 API Docs: http://localhost:8000/docs"
	@echo "🌐 Frontend: http://localhost:3000"
	@echo "🐰 RabbitMQ: http://localhost:15672 (use 'make queue-ui' para credenciais)"
	@echo "📦 MinIO: http://localhost:9001 (use 'make storage-ui' para credenciais)"
	@echo ""
	@echo "Use 'make logs' para ver os logs em tempo real"

test: ## Executar testes
	@echo "🧪 Executando testes..."
	# TODO: Implementar testes
	@echo "⚠️  Testes ainda não implementados"

install-deps: ## Instalar dependências localmente (para desenvolvimento)
	@echo "📦 Instalando dependências do Core API..."
	cd services/core-api && pip install -r requirements.txt
	@echo "📦 Instalando dependências do Frontend..."
	cd frontend && npm install

format: ## Formatar código Python
	@echo "🎨 Formatando código Python..."
	find services -name "*.py" -exec black {} \;
	find services -name "*.py" -exec isort {} \;

lint: ## Verificar qualidade do código
	@echo "🔍 Verificando qualidade do código..."
	find services -name "*.py" -exec flake8 {} \;

backup-db: ## Fazer backup do banco de dados
	@echo "💾 Fazendo backup do banco de dados..."
	docker-compose -f $(COMPOSE_FILE) exec postgres pg_dump -U dev_user financial_automation > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup salvo como backup_$(shell date +%Y%m%d_%H%M%S).sql"

# Comandos de desenvolvimento individual por serviço
dev-core: ## Desenvolver apenas Core API
	docker-compose -f $(COMPOSE_FILE) up -d postgres redis rabbitmq minio
	docker-compose -f $(COMPOSE_FILE) up core-api

dev-frontend: ## Desenvolver apenas Frontend
	docker-compose -f $(COMPOSE_FILE) up -d core-api
	docker-compose -f $(COMPOSE_FILE) up frontend

# Informações do projeto
info: ## Mostrar informações do projeto
	@echo "📊 PayFlow - Sistema de Automação Financeira"
	@echo "============================================="
	@echo "🏗️  Arquitetura: Microsserviços"
	@echo "🐍 Backend: Python/FastAPI"
	@echo "⚛️  Frontend: React/TypeScript"
	@echo "🗄️  Database: PostgreSQL"
	@echo "🐰 Queue: RabbitMQ"
	@echo "📦 Storage: MinIO (S3-compatible)"
	@echo "🤖 IA: OCR + NLP"
	@echo ""
	@echo "Use 'make help' para ver todos os comandos disponíveis"
