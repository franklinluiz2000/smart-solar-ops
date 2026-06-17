# 🚀 Guia de Uso - Smart Solar Ops com IA

## O que foi desenvolvido?

Você agora tem um **sistema inteligente de monitoramento solar com IA** que:

### 1️⃣ **Coleta Dados Meteorológicos em Tempo Real**
- Integração com API Open-Meteo (gratuita, sem autenticação)
- Dados de irradiância solar, cobertura de nuvens, temperatura, umidade
- Atualização a cada 50 segundos (1 ciclo a cada 10)

### 2️⃣ **IA com Machine Learning**
- **Isolation Forest**: Detecta anomalias em dados multidimensionais
- **Modelos Preditivos**: Prevê potência solar para próximas horas
- **Health Score**: Calcula saúde geral de cada inversor (0-100)
- Aprendizado contínuo com novos dados

### 3️⃣ **Sistema de Alertas Inteligente**
- Categorização de alertas por severidade (CRÍTICO, AVISO, INFO)
- Debouncing para evitar spam (mínimo 5 min entre alertas iguais)
- Tipos de anomalias: Hardware, Dirt, Thermal, Performance
- Ações recomendadas para cada tipo de falha

### 4️⃣ **API REST Completa**
- Endpoints para integração com sistemas terceiros
- Dashboard de métricas agregadas
- Histórico de dados e alertas
- Previsões de potência

### 5️⃣ **Banco de Dados Expandido**
- Tabelas para armazenar meteorologia
- Histórico de anomalias detectadas
- Registro de alertas com severidade
- Health scores históricos

---

## 📁 Arquivos Criados/Modificados

### Novos Módulos:
```
✅ app/weather_api.py       - Coleta de APIs meteorológicas
✅ app/ai_model.py          - Modelos de IA e ML
✅ app/alerts.py            - Sistema de alertas e notificações
✅ app/api.py               - API REST Flask
```

### Arquivos Modificados:
```
✅ app/main.py              - Integração completa com IA
✅ app/requirements.txt      - Novas dependências (scikit-learn, pandas, numpy, flask)
✅ database/init.sql        - Schema expandido com novas tabelas
✅ README.md                - Documentação completa
```

### Novos Documentos:
```
✅ API.md                   - Documentação da API REST
✅ .env.example             - Configurações de exemplo
✅ GUIA_USO.md              - Este arquivo
```

---

## 🎯 Como Usar

### Início Rápido (Docker)

```bash
# 1. Entrar no diretório
cd /home/franklinux/smart-solar-ops

# 2. Copiar configurações (se não existe .env)
cp .env.example .env

# 3. Iniciar containers
docker-compose up -d

# 4. Aguardar ~30 segundos para inicializar
docker-compose ps

# 5. Acessar interfaces:
# - Grafana: http://localhost:3000 (admin/admin)
# - API REST: http://localhost:5000
# - TimescaleDB: localhost:5432
```

### Ver Logs em Tempo Real

```bash
# Logs do processador
docker-compose logs -f app

# Logs do TimescaleDB
docker-compose logs timescaledb

# Logs do Grafana
docker-compose logs grafana
```

---

## 📊 Acessando a API

### 1. Listar Inversores com Dados Atuais
```bash
curl http://localhost:5000/api/inverters | jq
```

Resposta:
```json
[
  {
    "id": "INV-01",
    "power_kw": 45.2,
    "temperature_c": 52.3,
    "efficiency_pct": 98.5,
    "status": "NORMAL"
  }
]
```

### 2. Verificar Alertas Ativos
```bash
curl http://localhost:5000/api/alerts | jq
```

Resposta:
```json
{
  "alerts": [
    {
      "type": "ANOMALY_DIRT",
      "level": "WARNING",
      "inverter_id": "INV-02",
      "message": "Possível sujidade detectada: 72.3%"
    }
  ],
  "summary": {
    "critical": 0,
    "warning": 1,
    "total_active": 1
  }
}
```

### 3. Obter Health Score (Saúde do Inversor)
```bash
curl http://localhost:5000/api/inverter/INV-01/health | jq
```

Resposta:
```json
{
  "inverter_id": "INV-01",
  "health_score": 92.5,
  "status": "BOM",
  "anomaly_rate_pct": 2.3,
  "avg_temperature_c": 48.2,
  "avg_efficiency_pct": 96.8
}
```

### 4. Dashboard Agregado
```bash
curl http://localhost:5000/api/dashboard | jq
```

---

## 🤖 Como Funciona a IA

### Detecção de Anomalias (Isolation Forest)

O sistema analisa continuamente:
- **Potência (kW)** - Está dentro do esperado?
- **Temperatura (°C)** - Está super aquecido?
- **Umidade (%)** - Afeta resistência dos painéis?
- **Cobertura de Nuvens (%)** - Qual o impacto esperado?
- **Eficiência Relativa (%)** - Está produzindo o esperado?

Se uma combinação desses fatores sai do padrão, é uma anomalia!

### Health Score

Calculado a cada 10 ciclos (50 segundos):

```
Score = 100 - penalidades

Penalidades:
- Taxa de anomalias × 0.5 (até -50 pontos)
- Temperatura excessiva × 0.5 (até -X pontos)
- Baixa eficiência × 0.3 (até -30 pontos)

Resultado:
- 90-100: ✅ EXCELENTE
- 75-89:  ✅ BOM
- 50-74:  ⚠️  AVISO
- <50:    🔴 CRÍTICO
```

### Previsão de Potência

Para as próximas horas:
```
Potência Predita = Curva Solar × Atenuação de Nuvens × Fator de Temperatura

Curva Solar: Modelo matemático da irradiância ao longo do dia
Atenuação: (1 - cobertura_nuvens/100) × 0.85
Fator Temp: 1 - (temperatura - 25°C) × 0.004
```

---

## 🔔 Tipos de Alertas

### HARDWARE_FAULT (CRÍTICO 🔴)
- **Quando:** Temperatura > 65°C + Eficiência < 80%
- **Ação:** Verificar inversor, possível defeito
- **Exemplo:** INV-03 com 72°C e 75% de eficiência

### ANOMALY_DIRT (AVISO 🟡)
- **Quando:** Eficiência < 75% (sem sobrecarga térmica)
- **Ação:** Agendar limpeza de painéis
- **Exemplo:** INV-02 com 72% de eficiência

### OVERHEATING (CRÍTICO 🔴)
- **Quando:** Temperatura > 70°C
- **Ação:** Verificar ventilação
- **Exemplo:** INV-01 com 75°C

### HIGH_CLOUD_COVER (INFO 🔵)
- **Quando:** Cobertura > 80%
- **Ação:** Monitorar situação meteorológica
- **Exemplo:** Nublado em toda região

---

## 📊 Dados Armazenados no Banco

### Tabelas de Time-Series (HyperTables)
```sql
-- Telemetria de inversores (1 ponto a cada 5 segundos)
telemetry_inverter
├── time, inverter_id, power_kw, temperature_c
├── efficiency_pct, status

-- Dados meteorológicos (1 ponto a cada 50 segundos)
weather_data
├── time, location_id, temperature_c
├── humidity_pct, cloud_cover_pct, weather_code

-- Anomalias detectadas (quando IA encontra problema)
anomalies
├── time, inverter_id, anomaly_type, confidence
├── details, root_cause, recommended_action

-- Health scores (1 ponto a cada 50 segundos)
inverter_health
├── time, inverter_id, health_score, status
├── anomaly_rate_pct, avg_temperature_c, avg_efficiency_pct
```

### Tabelas Normais
```sql
-- Alertas do sistema
alerts
├── id, created_at, resolved_at, alert_type
├── severity, inverter_id, message, details

-- Previsões de potência
power_forecast
├── time, inverter_id, predicted_power_kw
├── confidence, weather_conditions
```

---

## ⚙️ Configuração e Customização

### Modificar Limiares de Detecção

Edite `app/main.py`:

```python
# Temperatura crítica para falha de hardware
TEMP_HARDWARE_FAULT_THRESHOLD = 65.0  # °C

# Eficiência mínima para falha de hardware
EFFICIENCY_HARDWARE_FAULT = 80  # %

# Eficiência mínima para anomalia de sujidade
EFFICIENCY_ANOMALY_DIRT = 75  # %
```

### Modificar Localização

Edite `.env`:

```env
# Para São Paulo:
SOLAR_LATITUDE=-23.5505
SOLAR_LONGITUDE=-46.6333
SOLAR_CITY=São Paulo

# Para Rio de Janeiro:
SOLAR_LATITUDE=-22.9068
SOLAR_LONGITUDE=-43.1729
SOLAR_CITY=Rio de Janeiro
```

---

## 📈 Queries Úteis no TimescaleDB

### Potência Total Atual (Todos Inversores)
```sql
SELECT COALESCE(SUM(power_kw), 0) as total_power
FROM (
  SELECT DISTINCT ON (inverter_id) power_kw
  FROM telemetry_inverter
  WHERE time > now() - interval '1 hour'
  ORDER BY inverter_id, time DESC
) t;
```

### Alertas Não Resolvidos
```sql
SELECT alert_type, severity, inverter_id, message, created_at
FROM alerts
WHERE is_active = true
ORDER BY created_at DESC;
```

### Anomalias da Última Hora
```sql
SELECT time, inverter_id, anomaly_type, confidence
FROM anomalies
WHERE time > now() - interval '1 hour'
ORDER BY time DESC;
```

### Health Score Histórico
```sql
SELECT time, inverter_id, health_score, status
FROM inverter_health
WHERE inverter_id = 'INV-01'
  AND time > now() - interval '24h'
ORDER BY time DESC;
```

---

## 🐛 Troubleshooting

### API não responde
```bash
# Verificar se está rodando
docker-compose logs app | grep "API REST"

# Reiniciar
docker-compose restart app
```

### Banco recusa conexão
```bash
# Aguardar inicialização (até 1 min)
docker-compose logs timescaledb | tail -20

# Ver se container está vivo
docker-compose ps timescaledb
```

### Sem dados no Grafana
```bash
# Verificar se telemetria está sendo inserida
docker-compose exec timescaledb psql -U admin -d solar_ops
solar_ops=# SELECT COUNT(*) FROM telemetry_inverter;

# Ver últimos dados
solar_ops=# SELECT * FROM telemetry_inverter ORDER BY time DESC LIMIT 5;
```

### IA não está funcionando
```bash
# Ver logs
docker-compose logs app | grep "AI\|Modelo\|anomaly"

# Verificar se scikit-learn está instalado
docker-compose exec app pip list | grep scikit
```

---

## 📚 Próximas Melhorias

- [ ] Integração com Kafka para streaming distribuído
- [ ] Deep Learning (LSTM) para previsões mais precisas
- [ ] Dashboard web customizado (React/Vue)
- [ ] Notificações via email/SMS
- [ ] Integração com EMS (Energy Management Systems)
- [ ] Regressão Linear com dados históricos
- [ ] AutoML com AutoGluon
- [ ] Análise de produção vs forecast

---

## 💡 Dicas Importantes

1. **Backup do Banco**: O docker-compose inclui volume para dados
2. **Performance**: O TimescaleDB é otimizado para séries temporais
3. **ML**: O modelo melhora com mais dados (> 1000 amostras)
4. **API**: Todos endpoints retornam JSON
5. **Alerts**: O debouncing evita spam (5 min entre iguais)

---

## 📞 Suporte

Para problemas:
1. Verificar logs: `docker-compose logs [serviço]`
2. Consultar API.md para endpoints
3. Consultar README.md para arquitetura

---

**Sistema desenvolvido com ❤️ para otimizar sua usina solar!**

Última atualização: 2026-06-16
