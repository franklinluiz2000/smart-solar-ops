-- Criação da tabela de telemetria dos inversores
CREATE TABLE IF NOT EXISTS telemetry_inverter (
    time TIMESTAMPTZ NOT NULL,
    inverter_id VARCHAR(50) NOT NULL,
    power_kw DOUBLE PRECISION,
    temperature_c DOUBLE PRECISION,
    efficiency_pct DOUBLE PRECISION,
    status VARCHAR(50)
);

-- O pulo do gato do TimescaleDB: Transforma a tabela em uma hypertable baseada na coluna 'time'
SELECT create_hypertable('telemetry_inverter', 'time', if_not_exists => TRUE);

-- Índice para acelerar as buscas do Grafana
CREATE INDEX IF NOT EXISTS idx_inverter_time ON telemetry_inverter (inverter_id, time DESC);

-- Tabela de dados meteorológicos (API)
CREATE TABLE IF NOT EXISTS weather_data (
    time TIMESTAMPTZ NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    temperature_c DOUBLE PRECISION,
    humidity_pct DOUBLE PRECISION,
    cloud_cover_pct DOUBLE PRECISION,
    weather_code INT,
    data_source VARCHAR(50)
);

SELECT create_hypertable('weather_data', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_data (location_id, time DESC);

-- Tabela de alertas
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    inverter_id VARCHAR(50) NOT NULL,
    message TEXT,
    details JSONB,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_alerts_inverter ON alerts (inverter_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts (alert_type, is_active);

-- Tabela de anomalias detectadas
CREATE TABLE IF NOT EXISTS anomalies (
    time TIMESTAMPTZ NOT NULL,
    inverter_id VARCHAR(50) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    confidence DOUBLE PRECISION,
    details JSONB,
    root_cause VARCHAR(200),
    recommended_action TEXT
);

SELECT create_hypertable('anomalies', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_anomalies_inverter ON anomalies (inverter_id, time DESC);

-- Tabela de health score dos inversores
CREATE TABLE IF NOT EXISTS inverter_health (
    time TIMESTAMPTZ NOT NULL,
    inverter_id VARCHAR(50) NOT NULL,
    health_score DOUBLE PRECISION,
    status VARCHAR(50),
    anomaly_rate_pct DOUBLE PRECISION,
    avg_temperature_c DOUBLE PRECISION,
    avg_efficiency_pct DOUBLE PRECISION
);

SELECT create_hypertable('inverter_health', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_health_inverter ON inverter_health (inverter_id, time DESC);

-- Tabela de previsões
CREATE TABLE IF NOT EXISTS power_forecast (
    time TIMESTAMPTZ NOT NULL,
    inverter_id VARCHAR(50) NOT NULL,
    predicted_power_kw DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    weather_conditions JSONB
);

SELECT create_hypertable('power_forecast', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_forecast_time ON power_forecast (inverter_id, time DESC);