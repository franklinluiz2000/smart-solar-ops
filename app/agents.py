"""
Agentes Autônomos de Monitoramento
Executa tarefas de análise, alertas e relatórios em background
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Callable, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import threading

logger = logging.getLogger(__name__)

class MonitoringAgent:
    """Agente autônomo que executa tarefas de monitoramento"""
    
    def __init__(self, name: str):
        self.name = name
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.last_execution = None
        self.execution_count = 0
        self.last_error = None
        self.lock = threading.Lock()
    
    def start(self):
        """Inicia o agente"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.is_running = True
                logger.info(f"✅ Agente {self.name} iniciado")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar agente {self.name}: {e}")
            self.last_error = str(e)
    
    def stop(self):
        """Para o agente"""
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info(f"⏹️ Agente {self.name} parado")
        except Exception as e:
            logger.error(f"❌ Erro ao parar agente {self.name}: {e}")
    
    def add_job(self, func: Callable, trigger_type: str = "interval", **kwargs) -> str:
        """
        Adiciona um job ao agente
        
        Args:
            func: Função a executar
            trigger_type: 'interval', 'cron', ou 'date'
            **kwargs: Argumentos do trigger
        
        Returns:
            str: ID do job
        """
        try:
            if trigger_type == "interval":
                trigger = IntervalTrigger(**kwargs)
            elif trigger_type == "cron":
                trigger = CronTrigger(**kwargs)
            else:
                trigger = IntervalTrigger(**kwargs)
            
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=f"{self.name}_{func.__name__}_{self.scheduler.get_jobs().__len__()}",
                name=f"Job: {func.__name__}",
                misfire_grace_time=60
            )
            
            logger.info(f"➕ Job adicionado ao agente {self.name}: {func.__name__}")
            return job.id
        
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar job: {e}")
            self.last_error = str(e)
            return None
    
    def get_status(self) -> Dict:
        """Retorna status do agente"""
        return {
            "name": self.name,
            "is_running": self.is_running,
            "jobs_count": len(self.scheduler.get_jobs()),
            "last_execution": self.last_execution,
            "execution_count": self.execution_count,
            "last_error": self.last_error
        }


class AnalysisAgent(MonitoringAgent):
    """Agente que executa análises contínuas"""
    
    def __init__(self, db_pool, ai_model):
        super().__init__("AnalysisAgent")
        self.db_pool = db_pool
        self.ai_model = ai_model
        self.analysis_history = []
    
    def run_anomaly_analysis(self):
        """Analisa anomalias em dados recentes"""
        try:
            with self.lock:
                conn = self.db_pool.getconn()
                cursor = conn.cursor()
                
                # Buscar dados dos últimos 10 minutos
                query = """
                    SELECT inverter_id, power_kw, temperature_c, efficiency_pct, status
                    FROM telemetry_inverter
                    WHERE time > now() - interval '10 minutes'
                    ORDER BY time DESC
                    LIMIT 100;
                """
                
                cursor.execute(query)
                data = cursor.fetchall()
                
                if not data:
                    logger.info("⏳ Nenhum dado recente para análise")
                    return
                
                anomalies_found = []
                for row in data:
                    inv_id, power, temp, eff, status = row
                    if "ANOMALY" in status or "FAULT" in status:
                        anomalies_found.append({
                            "inverter": inv_id,
                            "status": status,
                            "power": power,
                            "temperature": temp,
                            "efficiency": eff
                        })
                
                self.analysis_history.append({
                    "timestamp": datetime.now(timezone.utc),
                    "anomalies_count": len(anomalies_found),
                    "data_points_analyzed": len(data),
                    "anomalies": anomalies_found
                })
                
                # Manter apenas últimas 100 análises
                if len(self.analysis_history) > 100:
                    self.analysis_history.pop(0)
                
                if anomalies_found:
                    logger.warning(f"🔍 Análise: {len(anomalies_found)} anomalias detectadas")
                else:
                    logger.info(f"✅ Análise: Sistema normal ({len(data)} pontos analisados)")
                
                self.last_execution = datetime.now(timezone.utc)
                self.execution_count += 1
                
                cursor.close()
                self.db_pool.putconn(conn)
        
        except Exception as e:
            logger.error(f"❌ Erro na análise: {e}")
            self.last_error = str(e)


class PerformanceAgent(MonitoringAgent):
    """Agente que calcula KPIs de performance"""
    
    def __init__(self, db_pool):
        super().__init__("PerformanceAgent")
        self.db_pool = db_pool
        self.kpis_history = []
    
    def calculate_performance_metrics(self):
        """Calcula métricas de performance horária"""
        try:
            with self.lock:
                conn = self.db_pool.getconn()
                cursor = conn.cursor()
                
                # Dados da última hora
                query = """
                    SELECT 
                        inverter_id,
                        COUNT(*) as data_points,
                        AVG(power_kw) as avg_power,
                        MAX(power_kw) as max_power,
                        AVG(efficiency_pct) as avg_efficiency,
                        AVG(temperature_c) as avg_temperature,
                        STDDEV(power_kw) as power_stddev
                    FROM telemetry_inverter
                    WHERE time > now() - interval '1 hour'
                    GROUP BY inverter_id;
                """
                
                cursor.execute(query)
                metrics = cursor.fetchall()
                
                kpi_report = {
                    "timestamp": datetime.now(timezone.utc),
                    "period": "1h",
                    "inverters": []
                }
                
                total_power = 0
                for row in metrics:
                    inv_id, points, avg_pow, max_pow, avg_eff, avg_temp, stddev = row
                    
                    inverter_kpi = {
                        "inverter_id": inv_id,
                        "data_points": points,
                        "avg_power_kw": float(avg_pow) if avg_pow else 0,
                        "max_power_kw": float(max_pow) if max_pow else 0,
                        "avg_efficiency_pct": float(avg_eff) if avg_eff else 0,
                        "avg_temperature_c": float(avg_temp) if avg_temp else 0,
                        "power_variability": float(stddev) if stddev else 0
                    }
                    
                    kpi_report["inverters"].append(inverter_kpi)
                    total_power += inverter_kpi["avg_power_kw"]
                
                kpi_report["total_power_avg_kw"] = total_power
                kpi_report["system_efficiency_avg"] = sum([i["avg_efficiency_pct"] for i in kpi_report["inverters"]]) / len(kpi_report["inverters"]) if kpi_report["inverters"] else 0
                
                self.kpis_history.append(kpi_report)
                if len(self.kpis_history) > 24:  # 24 horas de histórico
                    self.kpis_history.pop(0)
                
                logger.info(f"📊 KPIs: Potência média {total_power:.2f}kW, Eficiência {kpi_report['system_efficiency_avg']:.1f}%")
                
                self.last_execution = datetime.now(timezone.utc)
                self.execution_count += 1
                
                cursor.close()
                self.db_pool.putconn(conn)
        
        except Exception as e:
            logger.error(f"❌ Erro ao calcular KPIs: {e}")
            self.last_error = str(e)
    
    def get_daily_report(self) -> Dict:
        """Retorna relatório do dia"""
        if not self.kpis_history:
            return {"error": "Sem dados disponíveis"}
        
        reports = [r for r in self.kpis_history if r["period"] == "1h"]
        
        if not reports:
            return {"error": "Sem dados de 1h disponível"}
        
        avg_power = sum([r["total_power_avg_kw"] for r in reports]) / len(reports)
        avg_efficiency = sum([r["system_efficiency_avg"] for r in reports]) / len(reports)
        
        return {
            "date": datetime.now(timezone.utc).date(),
            "reports_count": len(reports),
            "avg_power_kw": avg_power,
            "avg_efficiency_pct": avg_efficiency,
            "max_power_kw": max([r["total_power_avg_kw"] for r in reports]),
            "min_power_kw": min([r["total_power_avg_kw"] for r in reports])
        }


class PredictiveAgent(MonitoringAgent):
    """Agente que faz previsões de problemas futuros"""
    
    def __init__(self, db_pool, ai_model):
        super().__init__("PredictiveAgent")
        self.db_pool = db_pool
        self.ai_model = ai_model
        self.predictions = []
    
    def predict_failures(self):
        """Prediz possíveis falhas nos próximos dias"""
        try:
            with self.lock:
                conn = self.db_pool.getconn()
                cursor = conn.cursor()
                
                # Análise de tendências
                query = """
                    SELECT 
                        inverter_id,
                        time,
                        temperature_c,
                        efficiency_pct
                    FROM telemetry_inverter
                    WHERE time > now() - interval '24 hours'
                    ORDER BY inverter_id, time DESC
                    LIMIT 1000;
                """
                
                cursor.execute(query)
                data = cursor.fetchall()
                
                predictions = []
                
                # Agrupar por inversor
                inverters_data = {}
                for row in data:
                    inv_id, time, temp, eff = row
                    if inv_id not in inverters_data:
                        inverters_data[inv_id] = []
                    inverters_data[inv_id].append((time, temp, eff))
                
                # Analisar tendências
                for inv_id, inv_data in inverters_data.items():
                    temps = [t[1] for t in inv_data if t[1]]
                    effs = [t[2] for t in inv_data if t[2]]
                    
                    if len(temps) > 10:
                        # Tendência de temperatura
                        temp_trend = temps[0] - temps[-1]  # Últimas 24h
                        if temp_trend > 5:
                            predictions.append({
                                "inverter": inv_id,
                                "prediction": "OVERHEATING_RISK",
                                "confidence": min(100, temp_trend * 10),
                                "reason": f"Temperatura aumentando {temp_trend:.1f}°C em 24h"
                            })
                    
                    if len(effs) > 10:
                        # Tendência de eficiência
                        eff_trend = effs[-1] - effs[0]  # Últimas 24h
                        if eff_trend < -5:
                            predictions.append({
                                "inverter": inv_id,
                                "prediction": "DEGRADATION_RISK",
                                "confidence": min(100, abs(eff_trend) * 10),
                                "reason": f"Eficiência diminuindo {abs(eff_trend):.1f}% em 24h"
                            })
                
                self.predictions.append({
                    "timestamp": datetime.now(timezone.utc),
                    "predictions": predictions
                })
                
                if len(self.predictions) > 50:
                    self.predictions.pop(0)
                
                if predictions:
                    logger.warning(f"🔮 Previsões: {len(predictions)} riscos detectados")
                    for pred in predictions:
                        logger.warning(f"   - {pred['inverter']}: {pred['prediction']} ({pred['confidence']:.0f}%)")
                
                self.last_execution = datetime.now(timezone.utc)
                self.execution_count += 1
                
                cursor.close()
                self.db_pool.putconn(conn)
        
        except Exception as e:
            logger.error(f"❌ Erro na previsão: {e}")
            self.last_error = str(e)


class MonitoringAgentManager:
    """Gerenciador central de agentes"""
    
    def __init__(self, db_pool, ai_model):
        self.agents = {}
        self.db_pool = db_pool
        self.ai_model = ai_model
        self._setup_agents()
    
    def _setup_agents(self):
        """Configura todos os agentes"""
        try:
            # Agente de Análise
            self.agents["analysis"] = AnalysisAgent(self.db_pool, self.ai_model)
            self.agents["analysis"].add_job(
                self.agents["analysis"].run_anomaly_analysis,
                trigger_type="interval",
                seconds=60  # A cada minuto
            )
            
            # Agente de Performance
            self.agents["performance"] = PerformanceAgent(self.db_pool)
            self.agents["performance"].add_job(
                self.agents["performance"].calculate_performance_metrics,
                trigger_type="interval",
                minutes=5  # A cada 5 minutos
            )
            
            # Agente de Previsões
            self.agents["predictive"] = PredictiveAgent(self.db_pool, self.ai_model)
            self.agents["predictive"].add_job(
                self.agents["predictive"].predict_failures,
                trigger_type="interval",
                minutes=30  # A cada 30 minutos
            )
            
            logger.info(f"✅ {len(self.agents)} agentes configurados")
        
        except Exception as e:
            logger.error(f"❌ Erro ao configurar agentes: {e}")
    
    def start_all(self):
        """Inicia todos os agentes"""
        for agent in self.agents.values():
            agent.start()
        logger.info("🟢 Todos os agentes iniciados")
    
    def stop_all(self):
        """Para todos os agentes"""
        for agent in self.agents.values():
            agent.stop()
        logger.info("🔴 Todos os agentes parados")
    
    def get_status(self) -> Dict:
        """Retorna status de todos os agentes"""
        return {
            agent_name: agent.get_status()
            for agent_name, agent in self.agents.items()
        }
    
    def get_analysis_report(self) -> Dict:
        """Retorna relatório da análise"""
        if "analysis" not in self.agents:
            return {"error": "Agente não configurado"}
        
        agent = self.agents["analysis"]
        return {
            "agent_status": agent.get_status(),
            "recent_analyses": agent.analysis_history[-10:] if agent.analysis_history else []
        }
    
    def get_performance_report(self) -> Dict:
        """Retorna relatório de performance"""
        if "performance" not in self.agents:
            return {"error": "Agente não configurado"}
        
        agent = self.agents["performance"]
        return {
            "agent_status": agent.get_status(),
            "daily_report": agent.get_daily_report(),
            "recent_kpis": agent.kpis_history[-5:] if agent.kpis_history else []
        }
    
    def get_predictions(self) -> Dict:
        """Retorna previsões atuais"""
        if "predictive" not in self.agents:
            return {"error": "Agente não configurado"}
        
        agent = self.agents["predictive"]
        return {
            "agent_status": agent.get_status(),
            "current_predictions": agent.predictions[-1] if agent.predictions else {"predictions": []},
            "prediction_history": agent.predictions[-5:] if agent.predictions else []
        }
