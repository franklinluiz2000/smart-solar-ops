"""
Módulo de Alertas e Notificações
Sistema inteligente de alertas para anomalias
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Níveis de severidade de alerta"""
    INFO = 0
    WARNING = 1
    CRITICAL = 2

class AlertType(Enum):
    """Tipos de alertas"""
    HARDWARE_FAULT = "HARDWARE_FAULT"
    ANOMALY_DIRT = "ANOMALY_DIRT"
    ANOMALY_THERMAL = "ANOMALY_THERMAL"
    ANOMALY_PERFORMANCE = "ANOMALY_PERFORMANCE"
    LOW_POWER = "LOW_POWER"
    OVERHEATING = "OVERHEATING"
    COMMUNICATION_LOSS = "COMMUNICATION_LOSS"
    HIGH_CLOUD_COVER = "HIGH_CLOUD_COVER"
    MAINTENANCE_DUE = "MAINTENANCE_DUE"

class Alert:
    """Representa um alerta no sistema"""
    
    def __init__(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        inverter_id: str,
        message: str,
        details: Dict = None
    ):
        self.id = None
        self.alert_type = alert_type
        self.level = level
        self.inverter_id = inverter_id
        self.message = message
        self.details = details or {}
        self.created_at = datetime.now(timezone.utc)
        self.resolved_at = None
        self.is_active = True
    
    def to_dict(self) -> Dict:
        """Converte alerta para dicionário"""
        return {
            "type": self.alert_type.value,
            "level": self.level.name,
            "inverter_id": self.inverter_id,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }

class AlertManager:
    """Gerencia alertas e notificações do sistema"""
    
    def __init__(self, db_cursor_provider=None):
        """
        Inicializa o gerenciador de alertas
        
        Args:
            db_cursor_provider: Função para obter cursor do banco
        """
        self.active_alerts: Dict[str, List[Alert]] = {}
        self.alert_history: List[Alert] = []
        self.db_cursor = db_cursor_provider
        
        # Configurações de alerta
        self.alert_thresholds = {
            "temp_warning": 55.0,
            "temp_critical": 70.0,
            "efficiency_warning": 80.0,
            "efficiency_critical": 60.0,
            "power_warning": 10.0,
            "cloud_cover_high": 80.0,
        }
        
        # Supressão de alertas duplicados (debounce)
        self.last_alert_time: Dict[str, datetime] = {}
        self.alert_cooldown_seconds = 300  # 5 minutos
    
    def check_and_create_alerts(
        self,
        inverter_id: str,
        power_kw: float,
        temperature_c: float,
        efficiency_pct: float,
        status: str,
        cloud_cover_pct: float = 0
    ) -> List[Alert]:
        """
        Verifica condições e cria alertas apropriados
        
        Returns:
            List[Alert]: Lista de novos alertas criados
        """
        new_alerts = []
        current_time = datetime.now(timezone.utc)
        
        try:
            # Alerta 1: Falha de Hardware
            if status == "HARDWARE_FAULT":
                alert = Alert(
                    AlertType.HARDWARE_FAULT,
                    AlertLevel.CRITICAL,
                    inverter_id,
                    f"⚠️ FALHA DE HARDWARE detectada: {efficiency_pct:.1f}% eficiência a {temperature_c:.1f}°C",
                    {
                        "power": power_kw,
                        "temperature": temperature_c,
                        "efficiency": efficiency_pct,
                        "recommended_action": "Verificar inversor - possível defeito"
                    }
                )
                new_alerts.append(alert)
            
            # Alerta 2: Sujidade/Obstrução
            elif status == "ANOMALY_DIRT":
                alert = Alert(
                    AlertType.ANOMALY_DIRT,
                    AlertLevel.WARNING,
                    inverter_id,
                    f"🔍 Possível sujidade detectada: {efficiency_pct:.1f}% de eficiência",
                    {
                        "power": power_kw,
                        "efficiency": efficiency_pct,
                        "recommended_action": "Programar limpeza de painéis"
                    }
                )
                new_alerts.append(alert)
            
            # Alerta 3: Sobrecarga térmica
            if temperature_c > self.alert_thresholds["temp_critical"]:
                alert = Alert(
                    AlertType.OVERHEATING,
                    AlertLevel.CRITICAL,
                    inverter_id,
                    f"🔥 Sobrecarga térmica CRÍTICA: {temperature_c:.1f}°C",
                    {
                        "temperature": temperature_c,
                        "threshold": self.alert_thresholds["temp_critical"],
                        "recommended_action": "Verificar ventilação e radiadores"
                    }
                )
                new_alerts.append(alert)
            elif temperature_c > self.alert_thresholds["temp_warning"]:
                alert = Alert(
                    AlertType.OVERHEATING,
                    AlertLevel.WARNING,
                    inverter_id,
                    f"⚠️ Temperatura elevada: {temperature_c:.1f}°C",
                    {
                        "temperature": temperature_c,
                        "threshold": self.alert_thresholds["temp_warning"]
                    }
                )
                new_alerts.append(alert)
            
            # Alerta 4: Baixa eficiência
            if efficiency_pct < self.alert_thresholds["efficiency_critical"]:
                alert = Alert(
                    AlertType.ANOMALY_PERFORMANCE,
                    AlertLevel.CRITICAL,
                    inverter_id,
                    f"📉 Performance crítica: {efficiency_pct:.1f}% de eficiência",
                    {
                        "efficiency": efficiency_pct,
                        "power": power_kw,
                        "threshold": self.alert_thresholds["efficiency_critical"]
                    }
                )
                new_alerts.append(alert)
            
            # Alerta 5: Cobertura de nuvens alta
            if cloud_cover_pct > self.alert_thresholds["cloud_cover_high"]:
                alert = Alert(
                    AlertType.HIGH_CLOUD_COVER,
                    AlertLevel.INFO,
                    inverter_id,
                    f"☁️ Cobertura de nuvens alta: {cloud_cover_pct:.1f}%",
                    {
                        "cloud_cover": cloud_cover_pct,
                        "expected_power_reduction": f"{(100 - efficiency_pct):.1f}%"
                    }
                )
                new_alerts.append(alert)
            
            # Armazenar alertas
            if inverter_id not in self.active_alerts:
                self.active_alerts[inverter_id] = []
            
            for alert in new_alerts:
                # Verificar cooldown para evitar spam
                alert_key = f"{inverter_id}_{alert.alert_type.value}"
                last_time = self.last_alert_time.get(alert_key)
                
                if last_time is None or (current_time - last_time).total_seconds() > self.alert_cooldown_seconds:
                    self.active_alerts[inverter_id].append(alert)
                    self.alert_history.append(alert)
                    self.last_alert_time[alert_key] = current_time
                    logger.warning(f"ALERTA [{alert.level.name}] {alert.message}")
            
            return new_alerts
        
        except Exception as e:
            logger.error(f"Erro ao criar alertas: {e}")
            return []
    
    def get_active_alerts(self, inverter_id: Optional[str] = None) -> List[Dict]:
        """Retorna alertas ativos"""
        if inverter_id:
            alerts = self.active_alerts.get(inverter_id, [])
        else:
            alerts = []
            for alert_list in self.active_alerts.values():
                alerts.extend(alert_list)
        
        return [a.to_dict() for a in alerts if a.is_active]
    
    def get_alert_summary(self) -> Dict:
        """Retorna resumo de alertas por severidade"""
        summary = {
            "critical": 0,
            "warning": 0,
            "info": 0,
            "total_active": 0,
            "by_inverter": {}
        }
        
        for inv_id, alerts in self.active_alerts.items():
            active = [a for a in alerts if a.is_active]
            summary["total_active"] += len(active)
            summary["by_inverter"][inv_id] = len(active)
            
            for alert in active:
                if alert.level == AlertLevel.CRITICAL:
                    summary["critical"] += 1
                elif alert.level == AlertLevel.WARNING:
                    summary["warning"] += 1
                else:
                    summary["info"] += 1
        
        return summary
    
    def resolve_alert(self, inverter_id: str, alert_type: AlertType):
        """Marca um alerta como resolvido"""
        if inverter_id in self.active_alerts:
            for alert in self.active_alerts[inverter_id]:
                if alert.alert_type == alert_type and alert.is_active:
                    alert.is_active = False
                    alert.resolved_at = datetime.now(timezone.utc)
                    logger.info(f"Alerta resolvido: {alert_type.value} em {inverter_id}")
