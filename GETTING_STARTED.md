# 🚀 Guia de Início Rápido - PayFlow

Este guia te ajudará a executar o **PayFlow - Sistema de Automação Financeira** em sua máquina local.

## 📋 Pré-requisitos

Certifique-se de ter instalado:

- **Docker** (versão 20.10+)
- **Docker Compose** (versão 2.0+)
- **Make** (opcional, mas recomendado)
- **Git**

### Verificar instalação:
```bash
docker --version
docker-compose --version
make --version
```

## 🛠️ Configuração Inicial

### 1. Clonar o repositório
```bash
git clone <seu-repositorio>
cd payflow
```

### 2. Configurar ambiente
```bash
# Usando Make (recomendado)
make setup

# Ou manualmente
cp env.example .env
```

### 3. Construir as imagens Docker
```bash
# Usando Make
make build

# Ou usando Docker Compose diretamente
docker-compose build
```

## 🚀 Executando o Sistema

### Opção 1: Ambiente Completo (Recomendado)
```bash
# Iniciar todos os serviços
make dev

# Ou usando Docker Compose
docker-compose up -d
```

### Opção 2: Desenvolvimento Individual
```bash
# Apenas Core API + dependências
make dev-core

# Apenas Frontend + dependências
make dev-frontend
```

## 🌐 Acessando os Serviços

Após iniciar o sistema, você pode acessar:

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **PayFlow API Docs** | http://localhost:8000/docs | - |
| **PayFlow Frontend** | http://localhost:3000 | - |
| **RabbitMQ UI** | http://localhost:15672 | (configuradas no .env) |
| **MinIO UI** | http://localhost:9001 | (configuradas no .env) |

## 📊 Verificando o Status

```bash
# Ver status dos containers
make status

# Ver logs em tempo real
make logs

# Ver logs de um serviço específico
make logs-core
make logs-db
make logs-queue
```

## 🧪 Testando a API

### 1. Verificar Health Check
```bash
curl http://localhost:8000/health
```

### 2. Acessar Dashboard Stats
```bash
curl http://localhost:8000/api/v1/dashboard/stats
```

### 3. Usar a documentação interativa
Acesse http://localhost:8000/docs para testar todos os endpoints.

## 🗄️ Banco de Dados

### Conectar ao PostgreSQL
```bash
# Via Make
make db-shell

# Via Docker diretamente
docker-compose exec postgres psql -U dev_user -d financial_automation
```

### Resetar banco de dados
```bash
make db-reset
```

## 🛠️ Comandos Úteis

```bash
# Ver todos os comandos disponíveis
make help

# Parar todos os serviços
make down

# Reiniciar todos os serviços
make restart

# Limpeza completa
make clean-all

# Fazer backup do banco
make backup-db
```

## 🐛 Solução de Problemas

### Problema: Porta já em uso
```bash
# Verificar quais portas estão em uso
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000
netstat -tulpn | grep :5432

# Parar outros serviços ou alterar portas no docker-compose.yml
```

### Problema: Containers não iniciam
```bash
# Ver logs detalhados
docker-compose logs

# Reconstruir imagens
make clean
make build
```

### Problema: Banco de dados não conecta
```bash
# Verificar se o PostgreSQL está rodando
docker-compose ps postgres

# Resetar banco
make db-reset
```

### Problema: RabbitMQ não conecta
```bash
# Verificar logs do RabbitMQ
make logs-queue

# Reiniciar apenas o RabbitMQ
docker-compose restart rabbitmq
```

## 📁 Estrutura do Projeto PayFlow

```
payflow/
├── services/                 # PayFlow Microsserviços
│   ├── core-api/            # PayFlow Core API
│   ├── document-ingestion/  # PayFlow Document Ingestion
│   ├── ocr-nlp/            # PayFlow OCR/NLP Service
│   ├── ap-workflow/        # PayFlow AP Workflow
│   ├── ar-workflow/        # PayFlow AR Workflow
│   └── reconciliation/     # PayFlow Reconciliation Service
├── frontend/               # PayFlow Frontend
├── infrastructure/         # Scripts de banco
├── docker-compose.yml     # Orquestração Docker
├── Makefile              # Comandos de desenvolvimento
└── README.md            # Documentação principal
```

## 🎯 Próximos Passos

1. **Explore a PayFlow API**: Acesse http://localhost:8000/docs
2. **Teste o upload**: Use o endpoint `/api/v1/documents/upload`
3. **Monitore as filas**: Acesse http://localhost:15672
4. **Desenvolva**: Modifique os serviços PayFlow e veja as mudanças em tempo real

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs: `make logs`
2. Consulte a documentação da PayFlow API: http://localhost:8000/docs
3. Verifique se todas as dependências estão instaladas
4. Tente uma limpeza completa: `make clean-all && make build && make dev`

---

**Dica**: Use `make help` para ver todos os comandos disponíveis!
