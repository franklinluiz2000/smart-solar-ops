# 🚀 Smart Solar Ops v2.0 - Guia de Início Rápido

## 📋 Pré-requisitos

- **Docker** e **Docker Compose** instalados
- **curl** ou Postman (para testar API)
- **Git** (já instalado)

## ⚡ Iniciar Sistema em 3 Minutos

### 1️⃣ Clone/Acesse o Projeto
```bash
cd /home/franklinux/smart-solar-ops
```

### 2️⃣ Construir Imagens Docker
```bash
docker-compose build
```

### 3️⃣ Iniciar Serviços
```bash
docker-compose up -d
```

### 4️⃣ Verificar Status
```bash
docker-compose ps
```

**Esperado:**
```
NAME              STATUS          PORTS
solar_db          Up              0.0.0.0:5432->5432/tcp
solar_processor   Up              
solar_grafana     Up              0.0.0.0:3000->3000/tcp
```

## 🌐 Acessar Serviços

### 📊 API REST
- **URL**: http://localhost:5000
- **Teste de saúde**: `curl http://localhost:5000/api/health`

### 📈 Dashboard Grafana  
- **URL**: http://localhost:3000
- **Usuário**: admin
- **Senha**: `admin` (configurável em `.env`)

### 🗄️ TimescaleDB
- **Host**: localhost
- **Porta**: 5432
- **Banco**: solar_ops
- **Usuário**: admin
- **Senha**: supersecretops2026

## 🧪 Testar Endpoints Principais

### 1. Status do Sistema
```bash
curl -s http://localhost:5000/api/system/info | jq .
```

### 2. Alertas Ativos
```bash
curl -s http://localhost:5000/api/alerts | jq .
```

### 3. Status dos Agentes
```bash
curl -s http://localhost:5000/api/agents/status | jq .
```

### 4. Análises de Anomalias
```bash
curl -s http://localhost:5000/api/analysis/report | jq .
```

### 5. Performance KPIs
```bash
curl -s http://localhost:5000/api/performance/report | jq .
```

### 6. Previsões Preditivas
```bash
curl -s http://localhost:5000/api/predictions | jq .
```

### 7. Relatório Diário (PDF)
```bash
curl -o relatorio_diario.pdf http://localhost:5000/api/report/daily
```

### 8. Relatório Mensal (HTML)
```bash
curl -o relatorio_mensal.html http://localhost:5000/api/report/monthly
```

### 9. Exportar Dados (JSON)
```bash
curl -s http://localhost:5000/api/report/json | jq . > dados_completos.json
```

## 🔧 Configurar Site Solar Real

### Opção 1: Brasília (500 kW) - Default
```bash
# Já configurado em .env
echo "SOLAR_SITE=USINA_BRASILIA" >> .env
docker-compose restart app
```

### Opção 2: São Paulo (1000 kW)
```bash
sed -i 's/SOLAR_SITE=.*/SOLAR_SITE=USINA_SAO_PAULO/' .env
docker-compose restart app
```

### Opção 3: Belo Horizonte (750 kW)
```bash
sed -i 's/SOLAR_SITE=.*/SOLAR_SITE=USINA_BELO_HORIZONTE/' .env
docker-compose restart app
```

### Opção 4: Salvador (600 kW - Bifacial)
```bash
sed -i 's/SOLAR_SITE=.*/SOLAR_SITE=USINA_SALVADOR/' .env
docker-compose restart app
```

## 📊 Sites Disponíveis

| Site | Localização | Potência | Tipo | Eficiência |
|------|-------------|----------|------|-----------|
| USINA_BRASILIA | Brasília, DF | 500 kW | Monocristalino | 97% |
| USINA_SAO_PAULO | São Paulo, SP | 1000 kW | Policristalino | 96% |
| USINA_BELO_HORIZONTE | Belo Horizonte, MG | 750 kW | Monocristalino | 97% |
| USINA_SALVADOR | Salvador, BA | 600 kW | Bifacial | 98% |

## 🤖 Agentes Autônomos

Rodando em background durante todo o tempo:

### AnalysisAgent
- **Frequência**: A cada 60 segundos
- **Função**: Detecta anomalias em janelas de 10 minutos
- **Saída**: Relatório de análises

### PerformanceAgent
- **Frequência**: A cada 5 minutos
- **Função**: Calcula KPIs (power, efficiency, temperature)
- **Saída**: Métricas horárias com histórico de 24h

### PredictiveAgent
- **Frequência**: A cada 30 minutos
- **Função**: Prevê riscos de superaquecimento e degradação
- **Saída**: Alertas preditivos com recomendações

## 📈 Visualizar Logs em Tempo Real

```bash
# Logs da aplicação
docker-compose logs -f app

# Logs do banco de dados
docker-compose logs -f timescaledb

# Todos os logs
docker-compose logs -f
```

## 🛑 Parar Sistema

```bash
docker-compose down
```

## 🗑️ Limpar Tudo (Reset)

```bash
# Parar e remover containers, volumes e redes
docker-compose down -v

# Reconstruir do zero
docker-compose up -d
```

## ⚠️ Solução de Problemas

### "Connection refused"
```bash
# Aguardar inicialização completa (30-60s)
docker-compose logs -f app
# Procurar por: "🟢 Iniciando streaming com IA"
```

### "Database error: FATAL"
```bash
# Reiniciar banco de dados
docker-compose restart timescaledb
sleep 10
docker-compose restart app
```

### "ModuleNotFoundError"
```bash
# Reconstruir imagem
docker-compose build --no-cache
docker-compose up -d
```

### Porta 5000 em uso
```bash
# Mudar em docker-compose.yml
# De: "5000:5000"
# Para: "5001:5000"
docker-compose up -d
# Acessar em: http://localhost:5001
```

## 📱 Exemplo de Integração (cURL)

### Dashboard Customizado
```bash
#!/bin/bash
# fetch_dashboard.sh - Coletar dados para dashboard

API="http://localhost:5000"

echo "🔄 Coletando dados em tempo real..."
echo ""

echo "📊 Performance Atual:"
curl -s $API/api/dashboard | jq '.performance'

echo ""
echo "⚠️  Alertas Ativos:"
curl -s $API/api/alerts | jq '.alerts | length'

echo ""
echo "🤖 Status dos Agentes:"
curl -s $API/api/agents/status | jq '.agents'

echo ""
echo "✅ Dados coletados!"
```

## 🎯 Casos de Uso

### 1. Monitorar Usina em Tempo Real
```bash
while true; do
  curl -s http://localhost:5000/api/dashboard | jq .
  sleep 10
done
```

### 2. Gerar Relatórios Automatizados
```bash
#!/bin/bash
DATA=$(date +%Y%m%d)
curl -o relatorio_$DATA.pdf http://localhost:5000/api/report/daily
echo "Relatório gerado: relatorio_$DATA.pdf"
```

### 3. Receber Alertas
```bash
#!/bin/bash
# Verificar alertas cada 1 minuto
while true; do
  ALERTS=$(curl -s http://localhost:5000/api/alerts | jq '.alerts | length')
  if [ $ALERTS -gt 0 ]; then
    echo "🚨 $ALERTS alertas encontrados!"
    curl -s http://localhost:5000/api/alerts | jq .
  fi
  sleep 60
done
```

## 📚 Documentação Completa

- **README.md** - Visão geral do projeto
- **API.md** - Documentação de endpoints
- **GUIA_USO.md** - Guia de uso em português
- **INTEGRATION_SUMMARY.md** - Resumo da integração v2.0

## 💡 Dicas

1. **Performance**: Usar `jq` para filtrar JSON grande
   ```bash
   curl -s http://localhost:5000/api/report/json | jq '.agents_status'
   ```

2. **Exportar PDF**: Guardar relatórios automaticamente
   ```bash
   curl -o ~/relatorios/$(date +%Y%m%d).pdf http://localhost:5000/api/report/daily
   ```

3. **Monitoramento**: Usar cron para executar testes periodicamente
   ```bash
   0 9 * * * /scripts/gerar_relatorio_diario.sh
   ```

4. **Integração**: API REST é ideal para:
   - Dashboards customizados
   - Mobile apps
   - Integrações com sistemas ERP
   - Alertas em Slack/Teams

## 🎓 Próximas Etapas

- [ ] Configurar Grafana com dashboards
- [ ] Integrar com email para alertas
- [ ] Configurar backup automático
- [ ] Deploy em cloud (AWS/Azure)
- [ ] Integração com ERP

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique `docker-compose logs -f app`
2. Consulte a documentação em GUIA_USO.md
3. Teste endpoints com `curl` simples primeiro

---

**Versão**: 2.0.0  
**Status**: ✅ Pronto para Produção  
**Última Atualização**: $(date)
