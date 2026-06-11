-- Criação da tabela de telemetria dos inversores
CREATE TABLE IF NOT EXISTS telemetry_inverter (
    time TIMESTAMPTZ NOT NULL,
    inverter_id VARCHAR(50) NOT NULL,
    power_kw DOUBLE PRECISION,
    temperature_c DOUBLE PRECISION,
    efficiency_pct DOUBLE PRECISION,
    status VARCHAR(20)
);

-- O pulo do gato do TimescaleDB: Transforma a tabela em uma hypertable baseada na coluna 'time'
SELECT create_hypertable('telemetry_inverter', 'time', if_not_exists => TRUE);

-- Índice para acelerar as buscas do Grafana
CREATE INDEX IF NOT EXISTS idx_inverter_time ON telemetry_inverter (inverter_id, time DESC);