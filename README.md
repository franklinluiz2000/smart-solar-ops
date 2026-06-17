# ☀️ Smart Solar Ops - Plataforma Inteligente de Monitoramento Solar

**Plataforma de IA e Telemetria em Tempo Real para Usinas Fotovoltaicas**

O **Smart Solar Ops** é uma solução completa para monitoramento, análise e otimização de usinas solares usando inteligência artificial. O sistema coleta dados em tempo real de seus inversores, integra dados meteorológicos de APIs públicas e executa modelos de IA para detectar anomalias, prever problemas e maximizar a eficiência energética.

---

## 🎯 Funcionalidades Principais

✅ **Coleta de Dados em Tempo Real** - Telemetria contínua de inversores solares  
✅ **APIs Meteorológicas** - Integração com dados de irradiância e condições climáticas  
✅ **IA/ML** - Detecção de anomalias com Isolation Forest e modelos preditivos  
✅ **Alertas Inteligentes** - Sistema de alertas com severidade e debouncing  
✅ **Health Score** - Score de saúde (0-100) para cada inversor  
✅ **Previsões** - Previsão de potência para próximas horas  
✅ **API REST** - Endpoints para integração com sistemas terceiros  
✅ **Dashboard** - Grafana com visualizações em tempo real  
✅ **TimescaleDB** - Banco otimizado para séries temporais  

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE INTERFACE                      │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Grafana        │  │   API REST   │  │  Dashboard   │  │
│  │  (Port 3000)     │  │  (Port 5000) │  │  (Métricas)  │  │
│  └──────────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────┐
│                 CAMADA DE PROCESSAMENTO (IA)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Detecção de │  │   Geração    │  │  Alertas &       │  │
│  │  Anomalias   │  │  de Health   │  │  Notificações    │  │
│  │  (ML Model)  │  │  Score       │  │  (Manager)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  Previsões   │  │  Dados API   │                         │
│  │  (Regressor) │  │  Meteorolog. │                         │
│  └──────────────┘  └──────────────┘                         │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────┐
│                  CAMADA DE ARMAZENAMENTO                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           TimescaleDB (PostgreSQL 15)                   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │ │
│  │  │ Telemetria   │  │ Meteorologia │  │ Alertas    │   │ │
│  │  │ (HyperTable) │  │ (HyperTable) │  │ (Tabela)   │   │ │
│  │  └──────────────┘  └──────────────┘  └────────────┘   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │ │
│  │  │ Anomalias    │  │ Health Score │  │ Previsões  │   │ │
│  │  │ (HyperTable) │  │ (HyperTable) │  │ (Tabela)   │   │ │
│  │  └──────────────┘  └──────────────┘  └────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

| Componente | Tecnologia | Versão |
|-----------|-----------|--------|
| **Linguagem** | Python | 3.11+ |
| **Banco de Dados** | TimescaleDB | Latest |
| **Web Framework** | Flask | 3.0.0 |
| **ML/IA** | scikit-learn | 1.3.2 |
| **Orquestração** | Docker & Docker Compose | Latest |
| **Visualização** | Grafana | Latest |
| **APIs** | Open-Meteo (Weather) | Public |

---

## 🚀 Início Rápido

### Pré-requisitos
- Docker & Docker Compose instalados
- Git

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/franklinluiz2000/smart-solar-ops.git
   cd smart-solar-ops
   ```

2. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env
   ```

3. **Inicie os containers:**
   ```bash
   docker-compose up -d
   ```

4. **Verifique o status:**
   ```bash
   docker-compose ps
   ```

---

## 📊 Acessando os Componentes

| Serviço | URL | Credenciais |
|---------|-----|-----------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **API REST** | http://localhost:5000 | - |
| **TimescaleDB** | localhost:5432 | admin / secretpass |

---

## 🤖 Sistema de IA

### Detecção de Anomalias

O sistema utiliza **Isolation Forest** para detectar anomalias em tempo real:

```python
- Monitoramento de potência (kW)
- Temperatura do inversor (°C)
- Umidade relativa (%)
- Cobertura de nuvens (%)
- Eficiência relativa (%)
```

**Tipos de Anomalias Detectadas:**
- 🔴 **HARDWARE_FAULT** - Falha detectada no inversor
- 🟡 **ANOMALY_DIRT** - Painéis sujos/obstruídos
- 🟠 **ANOMALY_THERMAL** - Temperatura anormal
- 🔵 **ANOMALY_PERFORMANCE** - Performance degradada

### Health Score

Cada inversor recebe um **Health Score (0-100)** baseado em:
- Taxa de anomalias recentes
- Temperatura média operacional
- Eficiência média
- Histórico de falhas

**Interpretação:**
- 90-100: ✅ EXCELENTE
- 75-89: ✅ BOM
- 50-74: ⚠️ AVISO
- <50: 🔴 CRÍTICO

---

## 📈 Previsões

O sistema prediz a potência solar para as próximas horas considerando:

```
Poder Predito = Curva Solar × Atenuação de Nuvens × Fator de Temperatura
```

---

## 🔔 Sistema de Alertas

### Tipos de Alertas

| Tipo | Severidade | Ação Recomendada |
|------|-----------|-----------------|
| HARDWARE_FAULT | CRÍTICA | Verificar inversor |
| ANOMALY_DIRT | AVISO | Agendar limpeza |
| OVERHEATING | CRÍTICA | Verificar ventilação |
| ANOMALY_PERFORMANCE | CRÍTICA | Analisar conexões |
| HIGH_CLOUD_COVER | INFO | Monitorar |

### Debouncing

O sistema implementa debouncing para evitar spam de alertas:
- Intervalo mínimo de 5 minutos entre alertas do mesmo tipo
- Evita notificações repetitivas

---

## 📡 API REST

### Endpoints Principais

```bash
# Status da API
GET /health

# Listar inversores
GET /api/inverters

# Histórico de um inversor
GET /api/inverter/{id}/history?hours=24

# Alertas ativos
GET /api/alerts

# Health score
GET /api/inverter/{id}/health

# Previsão de potência
GET /api/forecast?inverter_id=INV-01&hours=24

# Dashboard agregado
GET /api/dashboard
```

Para documentação completa, veja [API.md](API.md)

---

## 📝 Estrutura do Projeto

```
smart-solar-ops/
├── app/
│   ├── main.py                 # Loop principal com IA
│   ├── weather_api.py          # Coleta de dados meteorológicos
│   ├── ai_model.py             # Modelos de IA e ML
│   ├── alerts.py               # Sistema de alertas
│   ├── api.py                  # API REST Flask
│   ├── requirements.txt         # Dependências Python
│   └── Dockerfile
├── database/
│   └── init.sql                # Schema do banco com IA
├── docker-compose.yml          # Orquestração
├── .env.example                # Configurações
├── API.md                       # Documentação API
└── README.md                    # Este arquivo
```

---

## 🔧 Configuração Avançada

### Variáveis de Ambiente

```env
# Banco de Dados
DB_HOST=timescaledb
DB_PORT=5432
DB_NAME=solar_ops
DB_USER=admin
DB_PASSWORD=secretpass

# Localização da Usina
SOLAR_LATITUDE=-15.7959
SOLAR_LONGITUDE=-48.1604
SOLAR_CITY=Brasília

# Grafana
GRAFANA_PASSWORD=admin

# APIs (opcional)
WEATHER_API_KEY=seu_api_key_opcional
```

### Customização de Limiares

Edite `app/main.py`:
```python
TEMP_HARDWARE_FAULT_THRESHOLD = 65.0  # °C
EFFICIENCY_HARDWARE_FAULT = 80         # %
EFFICIENCY_ANOMALY_DIRT = 75           # %
```

---

## 📊 Integração com Grafana

### Dashboards Inclusos

1. **Real-Time Monitoring** - Potência, temperatura, eficiência ao vivo
2. **Health Score** - Histórico de saúde dos inversores
3. **Anomalies** - Detecção de problemas e tendências
4. **Weather Impact** - Correlação entre meteorologia e geração

### Criar Novo Dashboard

1. Acesse http://localhost:3000
2. Clique em "New Dashboard"
3. Adicione painéis com queries do TimescaleDB
4. Exemplo query:
   ```sql
   SELECT time, inverter_id, power_kw, efficiency_pct 
   FROM telemetry_inverter 
   WHERE time > now() - interval '24h'
   ORDER BY time DESC
   ```

---

## 🐛 Troubleshooting

### Conexão com banco recusada
```bash
# Verificar se containers estão rodando
docker-compose ps

# Ver logs
docker-compose logs timescaledb
```

### API não responde
```bash
# Verificar se Flask está rodando
docker-compose logs app | grep "API REST"
```

### Baixa performance
```bash
# Verificar índices
docker-compose exec timescaledb psql -U admin -d solar_ops
solar_ops=# \di
```

---

## 📚 Recursos e Documentação

- [API REST Completa](API.md)
- [TimescaleDB Docs](https://docs.timescale.com/)
- [scikit-learn ML Models](https://scikit-learn.org/)
- [Open-Meteo API](https://open-meteo.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo LICENSE para detalhes.

---

## 👨‍💼 Autor

**Franklin Luiz** - [@franklinluiz2000](https://github.com/franklinluiz2000)

---

## 📞 Suporte

Para questões e suporte:
- 📧 Email: [seu-email@exemplo.com]
- 🐛 Issues: [GitHub Issues](https://github.com/franklinluiz2000/smart-solar-ops/issues)
- 💬 Discussões: [GitHub Discussions](https://github.com/franklinluiz2000/smart-solar-ops/discussions)

---

**Desenvolvido com ❤️ para otimizar sua geração solar**