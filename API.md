# 📊 API REST - Smart Solar Ops

## Endpoints Disponíveis

### Status da API
```
GET /health
```
Verifica se a API está ativa.

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2026-06-16T12:00:00+00:00"
}
```

---

### Listar Inversores
```
GET /api/inverters
```
Retorna lista de todos os inversores com dados recentes.

**Resposta:**
```json
[
  {
    "id": "INV-01",
    "last_update": "2026-06-16T12:00:00+00:00",
    "power_kw": 45.2,
    "temperature_c": 52.3,
    "efficiency_pct": 98.5,
    "status": "NORMAL"
  }
]
```

---

### Histórico de Inversor
```
GET /api/inverter/{inverter_id}/history?hours=24
```
Obtém histórico de dados de um inversor.

**Parâmetros Query:**
- `hours` (opcional): Número de horas a retornar (padrão: 24)

**Resposta:**
```json
[
  {
    "time": "2026-06-16T11:55:00+00:00",
    "power_kw": 45.2,
    "temperature_c": 52.3,
    "efficiency_pct": 98.5,
    "status": "NORMAL"
  }
]
```

---

### Alertas Ativos
```
GET /api/alerts?inverter_id=INV-01
```
Retorna alertas ativos do sistema.

**Parâmetros Query:**
- `inverter_id` (opcional): Filtrar por inversor

**Resposta:**
```json
{
  "alerts": [
    {
      "type": "ANOMALY_DIRT",
      "level": "WARNING",
      "inverter_id": "INV-02",
      "message": "🔍 Possível sujidade detectada: 72.3% de eficiência",
      "details": {
        "power": 28.0,
        "efficiency": 72.3
      },
      "created_at": "2026-06-16T11:50:00+00:00",
      "is_active": true
    }
  ],
  "summary": {
    "critical": 0,
    "warning": 1,
    "info": 0,
    "total_active": 1,
    "by_inverter": {
      "INV-02": 1
    }
  }
}
```

---

### Resolver Alerta
```
POST /api/alerts/resolve
```
Marca um alerta como resolvido.

**Request Body:**
```json
{
  "inverter_id": "INV-02",
  "alert_type": "ANOMALY_DIRT"
}
```

**Resposta:**
```json
{
  "status": "resolved"
}
```

---

### Health Score do Inversor
```
GET /api/inverter/{inverter_id}/health
```
Retorna score de saúde do inversor (0-100).

**Resposta:**
```json
{
  "inverter_id": "INV-01",
  "timestamp": "2026-06-16T12:00:00+00:00",
  "health_score": 92.5,
  "status": "BOM",
  "anomaly_rate_pct": 2.3,
  "avg_temperature_c": 48.2,
  "avg_efficiency_pct": 96.8
}
```

**Status Possíveis:**
- `EXCELENTE` (90-100): Sistema funcionando perfeitamente
- `BOM` (75-89): Funcionamento normal com pequenas variações
- `AVISO` (50-74): Performance reduzida, verificação recomendada
- `CRÍTICO` (<50): Problema grave detectado

---

### Previsão de Potência
```
GET /api/forecast?inverter_id=INV-01&hours=24
```
Retorna previsão de potência para as próximas horas.

**Parâmetros Query:**
- `inverter_id` (opcional): ID do inversor (padrão: INV-01)
- `hours` (opcional): Horas a prever (padrão: 24)

**Resposta:**
```json
[
  {
    "time": "2026-06-16T13:00:00+00:00",
    "predicted_power_kw": 42.5,
    "confidence": 85.3,
    "weather": {
      "cloud_cover": 25.0,
      "temperature": 28.5
    }
  }
]
```

---

### Dashboard Principal
```
GET /api/dashboard
```
Retorna métricas agregadas do sistema.

**Resposta:**
```json
{
  "timestamp": "2026-06-16T12:00:00+00:00",
  "total_power_kw": 135.6,
  "alerts": {
    "critical": 0,
    "warning": 1,
    "info": 2,
    "total_active": 3,
    "by_inverter": {
      "INV-01": 0,
      "INV-02": 1,
      "INV-03": 2
    }
  },
  "status": "operational"
}
```

---

## Códigos de Status HTTP

| Código | Significado |
|--------|------------|
| 200 | OK - Sucesso |
| 404 | Recurso não encontrado |
| 500 | Erro interno do servidor |

---

## Tipos de Alertas

| Tipo | Severidade | Descrição |
|------|-----------|-----------|
| HARDWARE_FAULT | CRÍTICO | Falha detectada no hardware |
| ANOMALY_DIRT | AVISO | Sujidade/obstrução nos painéis |
| ANOMALY_THERMAL | CRÍTICO/AVISO | Temperatura anormal |
| ANOMALY_PERFORMANCE | CRÍTICO/AVISO | Performance degradada |
| LOW_POWER | AVISO | Geração baixa |
| OVERHEATING | CRÍTICO | Sobrecarga térmica |
| HIGH_CLOUD_COVER | INFO | Cobertura de nuvens alta |

---

## Exemplos com cURL

### Listar inversores
```bash
curl http://localhost:5000/api/inverters
```

### Obter alertas
```bash
curl http://localhost:5000/api/alerts
```

### Obter health score
```bash
curl http://localhost:5000/api/inverter/INV-01/health
```

### Dashboard
```bash
curl http://localhost:5000/api/dashboard
```

---

## Notas Importantes

- Todos os timestamps estão em UTC (ISO 8601)
- Poder em kW, temperatura em °C, eficiência em %
- Health Score de 0-100 (maior = melhor)
- Confidence de previsão de 0-100 (% de confiança)
