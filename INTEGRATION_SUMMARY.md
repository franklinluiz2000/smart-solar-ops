# Integração Completa: Sistema de Monitoramento Solar Inteligente v2.0

## 📋 Resumo das Mudanças

### ✅ 1. Atualizado `requirements.txt`
- Adicionadas dependências necessárias para agentes autônomos e relatórios:
  - `apscheduler==3.10.4` - Agendamento de tarefas em background
  - `reportlab==4.0.4` - Geração de relatórios PDF/HTML

### ✅ 2. Expandida API REST (`api.py`)
**Novos Endpoints Adicionados:**

1. **Agentes Autônomos:**
   - `GET /api/agents/status` - Status de todos os agentes
   - `GET /api/analysis/report` - Relatório de análises de anomalias
   - `GET /api/performance/report` - Relatório de performance

2. **Previsões:**
   - `GET /api/predictions` - Previsões de problemas futuros

3. **Relatórios:**
   - `GET /api/report/daily` - PDF com análise diária
   - `GET /api/report/monthly` - HTML com resumo mensal
   - `GET /api/report/json` - Exportação completa em JSON

4. **Sistema:**
   - `GET /api/system/info` - Informações gerais e status dos serviços

**Mudanças Internas:**
- `create_api_app()` agora aceita 5 parâmetros: `db_pool`, `alert_manager`, `ai_model`, `agents_manager`, `report_generator`
- Novos endpoints com tratamento de erros robusto

### ✅ 3. Integrado `main.py` com Componentes Empresariais

**Novos Componentes Importados:**
```python
from real_data_collector import RealSolarDataCollector
from agents import MonitoringAgentManager
from reports import ExecutiveReportGenerator
```

**Mudanças em `init_components()`:**
- Instancia `RealSolarDataCollector` com site configurável via `SOLAR_SITE` env var
- Cria `MonitoringAgentManager` com pool de BD e modelo de IA
- Inicializa `ExecutiveReportGenerator` com informações do site

**Mudanças em `main()`:**
- Coleta dados reais via `real_data_collector.get_real_weather_data()` ao invés de simulação
- Calcula potência com modelo PVWatts real: `real_data_collector.calculate_power_output()`
- Treina modelo de IA periodicamente (a cada 20 iterações)
- Mantém histórico expandido com `humidity_pct`, `cloud_cover_pct`, `expected_power`
- Log melhorado com nome do site de monitoramento

**Mudanças em `start_api_server()`:**
- Passa novos componentes para API: `agents_manager` e `report_generator`

**Mudanças no `if __name__ == "__main__"`:**
- Inicia agentes autônomos com `agents_manager.start_all()`
- Agentes rodam em background durante todo o streaming
- Log melhorado com banners informativos

## 🌍 Dados Reais Configuráveis

Sites solares reais pré-configurados via `SOLAR_SITE` env var:
- `USINA_BRASILIA` (default) - 500 kW, -15.7942°, -48.1504°
- `USINA_SAO_PAULO` - 1000 kW, -23.5505°, -46.6333°
- `USINA_BELO_HORIZONTE` - 750 kW, -19.9191°, -43.9386°
- `USINA_SALVADOR` - 600 kW, -12.9714°, -38.5014°

## 🤖 Agentes Autônomos em Execução

3 agentes rodando em background:

1. **AnalysisAgent** (a cada 60s)
   - Detecta anomalias em janelas de 10 minutos
   - Identifica padrões de falha

2. **PerformanceAgent** (a cada 5 min)
   - Calcula KPIs horários
   - Mantém histórico de 24h

3. **PredictiveAgent** (a cada 30 min)
   - Prevê riscos de superaquecimento
   - Detecta degradação

## 📊 Relatórios Executivos Automáticos

Gerados via API ou agentes:

1. **PDF Diário** (`/api/report/daily`)
   - Logo da usina
   - Métricas de performance
   - Tabela de alertas
   - Previsões e recomendações

2. **HTML Mensal** (`/api/report/monthly`)
   - Gráficos de performance
   - Tendências de eficiência
   - Comparativas mes-a-mes

3. **JSON Export** (`/api/report/json`)
   - Todos os dados estruturados
   - Pronto para integração externa

## 🚀 Como Usar

### Iniciar Sistema:
```bash
cd /home/franklinux/smart-solar-ops
docker-compose up -d
# ou
python app/main.py
```

### Configurar Site Real:
```bash
export SOLAR_SITE=USINA_SAO_PAULO  # Ou outro site
python app/main.py
```

### Acessar API:
```bash
# Status dos agentes
curl http://localhost:5000/api/agents/status

# Análises de anomalias
curl http://localhost:5000/api/analysis/report

# Previsões preditivas
curl http://localhost:5000/api/predictions

# Download PDF diário
curl -o relatorio.pdf http://localhost:5000/api/report/daily

# Exportar JSON
curl http://localhost:5000/api/report/json | jq .
```

## 📈 Arquitetura Atual

```
┌─────────────────────────────────────────────────┐
│         Main Streaming Loop (5s)                 │
│  - Coleta dados reais do site solar              │
│  - Detecta anomalias (regras + ML)               │
│  - Treina modelo (a cada 20 iterações)           │
│  - Insere telemetria, alertas, health scores     │
└──────────────┬──────────────────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌──────────────┐  ┌──────────────────────────────┐
│  Agentes     │  │  API REST (porta 5000)       │
│  (Background)│  │  - 8 endpoints de dados      │
│  - Analysis  │  │  - 7 endpoints novos agents  │
│  - Performance│ │  - 3 endpoints relatórios    │
│  - Predictive│  │  - 1 endpoint sistema        │
└──────────────┘  └──────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  TimescaleDB (5 HyperTables)        │
│  - telemetry_inverter              │
│  - weather_data (real)              │
│  - anomalies (ML results)           │
│  - inverter_health (scores)         │
│  - alerts (events)                  │
└─────────────────────────────────────┘
```

## ✨ Diferenças v1.0 → v2.0

| Aspecto | v1.0 | v2.0 |
|---------|------|------|
| Dados | Simulação | Dados reais de 4 sites |
| Alertas | Apenas regras | Regras + ML |
| Monitoramento | Manual | Agentes autônomos |
| Relatórios | Não | PDF/HTML/JSON automáticos |
| Endpoints API | 8 | 18 (8 + 10 novos) |
| IA | Detecção de anomalias | Detecção + previsão + recomendações |

## 🎯 Próximos Passos (Opcional)

1. **Grafana Dashboard** - Visualizar dados em tempo real
2. **Email Alerts** - Notificar via email para alertas críticos
3. **Integração AWS/Azure** - Deploy em nuvem
4. **Mobile App** - Aplicativo para acompanhar remotamente
5. **Database Backup** - Rotina automática de backup

---

**Versão**: 2.0.0  
**Status**: ✅ Pronto para Apresentação Empresarial  
**Última Atualização**: $(date)
