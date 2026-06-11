import os
import time
import random
import math
from datetime import datetime, timezone
import psycopg2

DB_HOST = os.getenv("DB_HOST", "timescaledb")
DB_NAME = os.getenv("DB_NAME", "solar_ops")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASSWORD", "secretpass")

def connect_db():
    """Tenta ligar ao banco de dados com mecanismo de retry"""
    print("A aguardar ligação com o TimescaleDB...")
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
            )
            print("Ligação estabelecida com sucesso!")
            return conn
        except psycopg2.OperationalError:
            time.sleep(2)

def simulate_solar_physics(hour):
    """Simula a geração baseada na hora do dia (Curva Solar)"""
    # Geração só acontece entre as 06h e as 18h
    if 6 <= hour <= 18:
        # Curva de seno para simular o pico de sol ao meio-dia
        radianos = math.pi * (hour - 6) / 12
        base_power = math.sin(radianos) * 50.0  # Pico de 50kW por inversor
        return max(0.0, base_power)
    return 0.0

def detect_anomaly(power, temp, expected_power):
    """
    Algoritmo Preditivo de Detecção de Anomalias.
    Se a potência real for muito inferior à esperada para as condições meteorológicas,
    o sistema identifica uma falha ou sujidade.
    """
    if expected_power > 5.0:  # Só analisa se houver sol significativo
        efficiency = (power / expected_power) * 100
        
        # Anomalia Tipo 1: Temperatura altíssima e queda de performance (Falha de Hardware)
        if temp > 65.0 and efficiency < 80:
            return "HARDWARE_FAULT", efficiency
        # Anomalia Tipo 2: Temperatura normal mas eficiência baixa (Sujidade/Obstrução)
        elif efficiency < 75:
            return "ANOMALY_DIRT", efficiency
            
        return "NORMAL", efficiency
    return "NORMAL", 100.0

def main():
    conn = connect_db()
    cursor = conn.cursor()
    
    inverters = ["INV-01", "INV-02", "INV-03"]
    
    print("Iniciando streaming de telemetria em tempo real...")
    
    while True:
        # Usamos a hora atual do sistema para a curva solar
        current_time = datetime.now(timezone.utc)
        hour = current_time.hour + (current_time.minute / 60.0)
        
        for inv_id in inverters:
            base_power = simulate_solar_physics(hour)
            
            # Adiciona ruído natural (nuvens passando)
            cloud_effect = random.uniform(0.85, 1.0)
            power_kw = base_power * cloud_effect
            
            # Simula a temperatura do inversor (esquenta quando gera mais)
            temperature_c = 25.0 + (power_kw * 0.8) + random.uniform(-2, 2)
            
            # INJETAR UMA ANOMALIA FORÇADA NO INV-02 PARA MOSTRAR NO GRAFANA
            # Vamos simular que o inversor 2 está coberto de fezes de pássaros (sujo)
            if inv_id == "INV-02" and base_power > 0:
                power_kw = power_kw * 0.6  # Perda induzida de 40%
            
            # Executa o modelo analítico
            status, efficiency_pct = detect_anomaly(power_kw, temperature_c, base_power)
            
            # Insere os dados no TimescaleDB
            query = """
                INSERT INTO telemetry_inverter (time, inverter_id, power_kw, temperature_c, efficiency_pct, status)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (current_time, inv_id, power_kw, temperature_c, efficiency_pct, status))
            
        conn.commit()
        time.sleep(5)  # Envia dados a cada 5 segundos (Tempo Real)

if __name__ == "__main__":
    main()