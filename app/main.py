import os
import time
import random
import math
import logging
import sys
from datetime import datetime, timezone
from contextlib import contextmanager
from threading import Thread
import psycopg2
from psycopg2 import pool, Error as PgError

# Importar módulos customizados
try:
    from weather_api import WeatherDataCollector
    from ai_model import SolarAIModel
    from alerts import AlertManager, AlertType
    from api import create_api_app
    from real_data_collector import RealSolarDataCollector
    from agents import MonitoringAgentManager
    from reports import ExecutiveReportGenerator
except ImportError as e:
    print(f"Aviso: Módulo não encontrado: {e}")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações
DB_HOST = os.getenv("DB_HOST", "timescaledb")
DB_NAME = os.getenv("DB_NAME", "solar_ops")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASSWORD", "secretpass")
DB_PORT = int(os.getenv("DB_PORT", 5432))

# Constantes para robustez
MAX_RETRY_ATTEMPTS = 5
RETRY_BACKOFF_FACTOR = 2  # Exponencial backoff
INITIAL_RETRY_DELAY = 2
QUERY_TIMEOUT = 10
CONNECTION_POOL_SIZE = 5

# Constantes do algoritmo
TEMP_HARDWARE_FAULT_THRESHOLD = 65.0
EFFICIENCY_HARDWARE_FAULT = 80
EFFICIENCY_ANOMALY_DIRT = 75
MIN_POWER_FOR_ANALYSIS = 5.0
TEMP_BASE = 25.0
TEMP_COEFF = 0.8
CLOUD_EFFECT_MIN = 0.85
CLOUD_EFFECT_MAX = 1.0

# Pool de conexões global
db_pool = None
weather_collector = None
ai_model = None
alert_manager = None
real_data_collector = None
agents_manager = None
report_generator = None
api_app = None

def init_db_pool():
    """Inicializa o pool de conexões para o banco de dados"""
    global db_pool
    try:
        db_pool = pool.SimpleConnectionPool(
            1, CONNECTION_POOL_SIZE,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=10
        )
        logger.info("Pool de conexões inicializado com sucesso")
        return True
    except PgError as e:
        logger.error(f"Erro ao inicializar pool de conexões: {e}")
        return False

def connect_db():
    """Tenta ligar ao banco de dados com retry exponencial"""
    logger.info("A aguardar ligação com o TimescaleDB...")
    
    attempt = 0
    delay = INITIAL_RETRY_DELAY
    
    while attempt < MAX_RETRY_ATTEMPTS:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                connect_timeout=10
            )
            logger.info("Ligação estabelecida com sucesso!")
            return conn
        except (PgError, Exception) as e:
            attempt += 1
            if attempt >= MAX_RETRY_ATTEMPTS:
                logger.error(f"Falha ao conectar após {MAX_RETRY_ATTEMPTS} tentativas: {e}")
                sys.exit(1)
            
            logger.warning(f"Tentativa {attempt}/{MAX_RETRY_ATTEMPTS} falhou. Aguardando {delay}s... Erro: {e}")
            time.sleep(delay)
            delay *= RETRY_BACKOFF_FACTOR

@contextmanager
def get_cursor(conn):
    """Context manager para garantir fechamento seguro do cursor"""
    cursor = None
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        logger.error(f"Erro ao executar query: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()


def init_components():
    """Inicializa componentes do sistema (IA, API, Alertas, Agentes, Relatórios)"""
    global weather_collector, ai_model, alert_manager, real_data_collector, agents_manager, report_generator
    
    try:
        # Inicializar coletor de dados meteorológicos
        weather_collector = WeatherDataCollector(
            latitude=float(os.getenv("SOLAR_LATITUDE", "-15.7959")),
            longitude=float(os.getenv("SOLAR_LONGITUDE", "-48.1604")),
            city=os.getenv("SOLAR_CITY", "Brasília")
        )
        logger.info("✅ Coletor de dados meteorológicos inicializado")
        
        # Inicializar coletor de dados reais
        site_name = os.getenv("SOLAR_SITE", "USINA_BRASILIA")
        real_data_collector = RealSolarDataCollector(site_name=site_name)
        logger.info(f"✅ Coletor de dados reais inicializado: {site_name}")
        
        # Inicializar modelo de IA
        ai_model = SolarAIModel()
        logger.info("✅ Modelo de IA inicializado")
        
        # Inicializar gerenciador de alertas
        alert_manager = AlertManager()
        logger.info("✅ Gerenciador de alertas inicializado")
        
        # Inicializar gerenciador de agentes autônomos
        agents_manager = MonitoringAgentManager(db_pool, ai_model)
        logger.info("✅ Gerenciador de agentes inicializado")
        
        # Inicializar gerador de relatórios
        report_generator = ExecutiveReportGenerator(
            site_info=real_data_collector.get_site_info(),
            output_dir="/tmp"
        )
        logger.info("✅ Gerador de relatórios inicializado")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar componentes: {e}")
        return False


def insert_weather_data(cursor, timestamp, weather_data):
    """Insere dados meteorológicos no banco"""
    try:
        query = """
            INSERT INTO weather_data 
            (time, location_id, temperature_c, humidity_pct, cloud_cover_pct, weather_code, data_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        
        cursor.execute(query, (
            timestamp,
            "solar_plant_01",
            weather_data.get("temperature_c", 25.0),
            weather_data.get("humidity_pct", 50.0),
            weather_data.get("cloud_cover_pct", 30.0),
            weather_data.get("weather_code", 1),
            weather_data.get("source", "api")
        ))
        return True
    except Exception as e:
        logger.warning(f"Erro ao inserir dados meteorológicos: {e}")
        return False


def insert_alert(cursor, alert):
    """Insere alerta no banco de dados"""
    try:
        query = """
            INSERT INTO alerts (alert_type, severity, inverter_id, message, details, is_active)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        cursor.execute(query, (
            alert.alert_type.value,
            alert.level.name,
            alert.inverter_id,
            alert.message,
            str(alert.details),
            alert.is_active
        ))
        return True
    except Exception as e:
        logger.warning(f"Erro ao inserir alerta: {e}")
        return False


def insert_anomaly(cursor, timestamp, inverter_id, status, confidence, details):
    """Insere anomalia detectada no banco"""
    try:
        # Mapear tipo de anomalia
        anomaly_map = {
            "HARDWARE_FAULT": "Hardware Fault",
            "ANOMALY_DIRT": "Dirt/Obstruction",
            "ANOMALY_THERMAL": "Thermal Anomaly",
            "ANOMALY_PERFORMANCE": "Performance Degradation",
            "NORMAL": None
        }
        
        anomaly_type = anomaly_map.get(status)
        if not anomaly_type or status == "NORMAL":
            return True
        
        query = """
            INSERT INTO anomalies 
            (time, inverter_id, anomaly_type, confidence, details, recommended_action)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        recommended_action = {
            "Hardware Fault": "Verificar inversor - possível defeito eletrônico",
            "Dirt/Obstruction": "Agendar limpeza de painéis solares",
            "Thermal Anomaly": "Verificar ventilação e sistema de dissipação",
            "Performance Degradation": "Analisar conexões e condutores"
        }
        
        cursor.execute(query, (
            timestamp,
            inverter_id,
            anomaly_type,
            confidence,
            str(details),
            recommended_action.get(anomaly_type, "")
        ))
        return True
    except Exception as e:
        logger.warning(f"Erro ao inserir anomalia: {e}")
        return False


def insert_health_score(cursor, timestamp, inverter_id, health_score, status, recent_data):
    """Insere health score do inversor"""
    try:
        import statistics
        
        temperatures = [d.get("temperature_c", 25) for d in recent_data if "temperature_c" in d]
        efficiencies = [d.get("efficiency_pct", 100) for d in recent_data if "efficiency_pct" in d]
        statuses = [d.get("status", "NORMAL") for d in recent_data if "status" in d]
        
        query = """
            INSERT INTO inverter_health 
            (time, inverter_id, health_score, status, anomaly_rate_pct, avg_temperature_c, avg_efficiency_pct)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        
        anomaly_rate = (len([s for s in statuses if "ANOMALY" in s or "FAULT" in s]) / len(statuses) * 100) if statuses else 0
        avg_temp = statistics.mean(temperatures) if temperatures else 25
        avg_eff = statistics.mean(efficiencies) if efficiencies else 100
        
        cursor.execute(query, (
            timestamp,
            inverter_id,
            health_score,
            status,
            anomaly_rate,
            avg_temp,
            avg_eff
        ))
        return True
    except Exception as e:
        logger.warning(f"Erro ao inserir health score: {e}")
        return False


def simulate_solar_physics(hour):
    """
    Simula a geração baseada na hora do dia (Curva Solar)
    
    Args:
        hour: Hora do dia em float (0-23)
    
    Returns:
        float: Potência gerada em kW, sempre >= 0
    """
    try:
        hour = float(hour)
        
        # Geração só acontece entre as 06h e as 18h
        if 6 <= hour <= 18:
            # Curva de seno para simular o pico de sol ao meio-dia
            radianos = math.pi * (hour - 6) / 12
            base_power = math.sin(radianos) * 50.0  # Pico de 50kW por inversor
            return max(0.0, base_power)
        return 0.0
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao calcular potência solar para hora {hour}: {e}")
        return 0.0

def detect_anomaly(power, temp, expected_power):
    """
    Algoritmo Preditivo de Detecção de Anomalias.
    Se a potência real for muito inferior à esperada para as condições meteorológicas,
    o sistema identifica uma falha ou sujidade.
    
    Args:
        power: Potência real em kW
        temp: Temperatura do inversor em °C
        expected_power: Potência esperada em kW
    
    Returns:
        tuple: (status, efficiency_pct) - status da anomalia e eficiência percentual
    """
    try:
        power = float(power)
        temp = float(temp)
        expected_power = float(expected_power)
        
        # Validar valores
        if power < 0 or temp < -50 or temp > 100 or expected_power < 0:
            logger.warning(f"Valores inválidos detectados: power={power}, temp={temp}, expected={expected_power}")
            return "INVALID_DATA", 0.0
        
        if expected_power > MIN_POWER_FOR_ANALYSIS:  # Só analisa se houver sol significativo
            efficiency = (power / expected_power) * 100
            
            # Anomalia Tipo 1: Temperatura altíssima e queda de performance (Falha de Hardware)
            if temp > TEMP_HARDWARE_FAULT_THRESHOLD and efficiency < EFFICIENCY_HARDWARE_FAULT:
                return "HARDWARE_FAULT", efficiency
            # Anomalia Tipo 2: Temperatura normal mas eficiência baixa (Sujidade/Obstrução)
            elif efficiency < EFFICIENCY_ANOMALY_DIRT:
                return "ANOMALY_DIRT", efficiency
                
            return "NORMAL", efficiency
        return "NORMAL", 100.0
    except (ValueError, TypeError, ZeroDivisionError) as e:
        logger.error(f"Erro ao detectar anomalia: {e}")
        return "ERROR", 0.0



def insert_telemetry(cursor, current_time, inv_id, power_kw, temperature_c, efficiency_pct, status):
    """
    Insere dados de telemetria no banco de dados com validação
    
    Args:
        cursor: Cursor da conexão
        current_time: Timestamp
        inv_id: ID do inversor
        power_kw: Potência em kW
        temperature_c: Temperatura em °C
        efficiency_pct: Eficiência em %
        status: Status da anomalia
    
    Returns:
        bool: True se bem-sucedido, False caso contrário
    """
    try:
        # Validar dados antes de inserir
        if power_kw < 0:
            logger.warning(f"Potência negativa detectada para {inv_id}: {power_kw}. Ajustando para 0.")
            power_kw = 0
        
        if temperature_c < -50 or temperature_c > 100:
            logger.warning(f"Temperatura inválida para {inv_id}: {temperature_c}°C")
            return False
        
        if efficiency_pct < 0 or efficiency_pct > 100:
            logger.warning(f"Eficiência inválida para {inv_id}: {efficiency_pct}%")
            return False
        
        # TimescaleDB hypertable não suporta ON CONFLICT com constraint implícita
        query = """
            INSERT INTO telemetry_inverter 
            (time, inverter_id, power_kw, temperature_c, efficiency_pct, status)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        cursor.execute(query, (current_time, inv_id, power_kw, temperature_c, efficiency_pct, status))
        return True
    except PgError as e:
        logger.error(f"Erro ao inserir telemetria para {inv_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao inserir telemetria: {e}")
        return False

def main():
    """Função principal de streaming de telemetria em tempo real com IA"""
    conn = None
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 10
    inverter_history = {}
    weather_update_counter = 0
    iteration_count = 0
    
    try:
        conn = connect_db()
        inverters = ["INV-01", "INV-02", "INV-03"]
        logger.info("🟢 Iniciando streaming com IA e monitoramento...")
        logger.info(f"📍 Site de monitoramento: {real_data_collector.site_name if real_data_collector else 'Simulação'}")
        
        while True:
            try:
                iteration_count += 1
                current_time = datetime.now(timezone.utc)
                hour = current_time.hour + (current_time.minute / 60.0)
                
                # Atualizar dados meteorológicos (real ou simulado)
                weather_data = None
                if weather_update_counter % 10 == 0:
                    if real_data_collector:
                        # Usar dados reais do site
                        try:
                            weather_data = real_data_collector.get_real_weather_data()
                        except Exception as e:
                            logger.warning(f"Erro ao obter dados reais: {e}, usando API fallback...")
                            if weather_collector:
                                weather_data = weather_collector.get_irradiance_data()
                    else:
                        # Fallback para dados simulados
                        if weather_collector:
                            weather_data = weather_collector.get_irradiance_data()
                weather_update_counter += 1
                
                with get_cursor(conn) as cursor:
                    successful_inserts = 0
                    
                    if weather_data:
                        insert_weather_data(cursor, current_time, weather_data)
                    
                    for inv_id in inverters:
                        try:
                            # Calcular potência com dados reais ou simulados
                            if real_data_collector:
                                try:
                                    # Usar potência calculada do site real
                                    real_weather = weather_data or real_data_collector.get_real_weather_data()
                                    power_kw = real_data_collector.calculate_power_output(real_weather)
                                except Exception as e:
                                    # Fallback para simulação
                                    logger.debug(f"Erro ao calcular potência real: {e}")
                                    base_power = simulate_solar_physics(hour)
                                    power_kw = base_power * random.uniform(0.85, 1.0)
                            else:
                                # Modo simulado
                                base_power = simulate_solar_physics(hour)
                                power_kw = base_power * random.uniform(0.85, 1.0)
                            
                            # Obter dados meteorológicos
                            if weather_data:
                                cloud_factor = weather_collector.calculate_cloud_attenuation(
                                    weather_data.get("cloud_cover_pct", 30.0)
                                ) if weather_collector else 1.0
                                power_kw = power_kw * cloud_factor
                                api_humidity = weather_data.get("humidity_pct", 50.0)
                                cloud_cover = weather_data.get("cloud_cover_pct", 30.0)
                                base_power = power_kw / cloud_factor if cloud_factor > 0 else power_kw
                            else:
                                api_humidity = 50.0
                                cloud_cover = 30.0
                                base_power = power_kw
                            
                            # Simular temperatura
                            temperature_c = TEMP_BASE + (power_kw * TEMP_COEFF) + random.uniform(-2, 2)
                            
                            # Simular falha no INV-02 quando há sol
                            if inv_id == "INV-02" and base_power > 10:
                                power_kw = power_kw * 0.6  # 40% de redução
                            
                            # Detecção de anomalias (regras)
                            status, efficiency_pct = detect_anomaly(power_kw, temperature_c, base_power)
                            
                            # Detecção de anomalias com ML
                            if ai_model:
                                status_ml, confidence_ml, details_ml = ai_model.detect_anomaly_ml(
                                    power_kw, temperature_c, api_humidity, cloud_cover, base_power
                                )
                                if status_ml != "NORMAL" and confidence_ml > 0.6:
                                    status = status_ml
                                    efficiency_pct = details_ml.get("efficiency", efficiency_pct)
                            
                            # Inserir telemetria
                            if insert_telemetry(cursor, current_time, inv_id, power_kw, temperature_c, efficiency_pct, status):
                                successful_inserts += 1
                                
                                # Manter histórico
                                if inv_id not in inverter_history:
                                    inverter_history[inv_id] = []
                                inverter_history[inv_id].append({
                                    "time": current_time,
                                    "power_kw": power_kw,
                                    "temperature_c": temperature_c,
                                    "efficiency_pct": efficiency_pct,
                                    "status": status,
                                    "humidity_pct": api_humidity,
                                    "cloud_cover_pct": cloud_cover,
                                    "expected_power": base_power
                                })
                                if len(inverter_history[inv_id]) > 100:
                                    inverter_history[inv_id].pop(0)
                                
                                # Alertas
                                if alert_manager:
                                    alerts = alert_manager.check_and_create_alerts(
                                        inv_id, power_kw, temperature_c, efficiency_pct, status, cloud_cover
                                    )
                                    for alert in alerts:
                                        insert_alert(cursor, alert)
                                
                                # Health score
                                if len(inverter_history[inv_id]) >= 10 and ai_model:
                                    health_score, health_status = ai_model.get_health_score(inverter_history[inv_id])
                                    insert_health_score(cursor, current_time, inv_id, health_score, health_status, inverter_history[inv_id])
                                
                                logger.info(f"📊 {inv_id}: {power_kw:.2f}kW | {temperature_c:.1f}°C | {efficiency_pct:.1f}% | {status}")
                        
                        except Exception as e:
                            logger.error(f"❌ Erro ao processar {inv_id}: {e}")
                            continue
                    
                    # Treinar modelo periodicamente (a cada 20 iterações)
                    if iteration_count % 20 == 0 and ai_model:
                        try:
                            ai_model.train_models()
                            logger.debug("🤖 Modelo de IA retrainado")
                        except Exception as e:
                            logger.debug(f"Erro ao retreinar modelo: {e}")
                    
                    if successful_inserts > 0:
                        consecutive_errors = 0
                    else:
                        consecutive_errors += 1
                        logger.warning(f"⚠️ Nenhuma inserção ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})")
                    
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logger.critical("❌ Máximo de erros atingido!")
                        sys.exit(1)
                
                time.sleep(5)
            
            except PgError as e:
                consecutive_errors += 1
                logger.error(f"❌ Erro BD: {e}")
                
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    if conn:
                        try:
                            conn.close()
                        except:
                            pass
                    time.sleep(5)
                    conn = connect_db()
                    consecutive_errors = 0
                else:
                    time.sleep(2)
            
            except Exception as e:
                logger.error(f"❌ Erro: {e}")
                time.sleep(5)
    
    except KeyboardInterrupt:
        logger.info("⏹️ Interrupção por utilizador")
    except Exception as e:
        logger.critical(f"❌ Erro crítico: {e}")
        sys.exit(1)
    finally:
        if conn:
            try:
                conn.close()
                logger.info("✅ Conexão fechada")
            except Exception as e:
                logger.error(f"❌ Erro ao fechar: {e}")


def start_api_server():
    """Inicia API Flask em thread separada"""
    try:
        app = create_api_app(
            db_pool=db_pool,
            alert_manager=alert_manager,
            ai_model=ai_model,
            agents_manager=agents_manager,
            report_generator=report_generator
        )
        logger.info("🚀 API REST iniciada na porta 5000...")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        logger.error(f"❌ Erro na API: {e}")


if __name__ == "__main__":
    try:
        if not init_db_pool():
            sys.exit(1)
        
        if not init_components():
            logger.warning("⚠️ Alguns componentes não inicializaram")
        
        # Iniciar agentes autônomos se disponível
        if agents_manager:
            try:
                agents_manager.start_all()
                logger.info("✅ Agentes autônomos iniciados")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao iniciar agentes: {e}")
        
        # Iniciar API em thread separada
        api_thread = Thread(target=start_api_server, daemon=True)
        api_thread.start()
        time.sleep(2)
        
        # Iniciar streaming principal
        logger.info("=" * 60)
        logger.info("🌞 SMART SOLAR OPS - SISTEMA DE MONITORAMENTO INTELIGENTE 🌞")
        logger.info("=" * 60)
        main()
    
    except Exception as e:
        logger.critical(f"❌ Erro fatal: {e}")
        sys.exit(1)
