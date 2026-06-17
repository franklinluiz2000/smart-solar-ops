"""
Módulo de IA e Machine Learning para monitoramento solar
Detecta anomalias, faz previsões e otimiza performance
"""

import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from joblib import dump, load
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class SolarAIModel:
    """Sistema de IA para monitoramento e previsão solar"""
    
    def __init__(self, model_dir: str = "/app/models"):
        """
        Inicializa o sistema de IA
        
        Args:
            model_dir: Diretório para armazenar modelos treinados
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # Modelos
        self.anomaly_detector = None
        self.power_predictor = None
        self.scaler = StandardScaler()
        
        # Cache de dados para aprendizado
        self.training_buffer = []
        self.buffer_size = 1000
        
        self.load_models()
    
    def load_models(self):
        """Carrega modelos pré-treinados se existirem"""
        try:
            if (self.model_dir / "anomaly_model.pkl").exists():
                self.anomaly_detector = load(self.model_dir / "anomaly_model.pkl")
                logger.info("Modelo de anomalias carregado")
        except Exception as e:
            logger.warning(f"Não foi possível carregar modelos: {e}. Usando modelos padrão.")
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
    
    def detect_anomaly_ml(
        self,
        power_kw: float,
        temperature_c: float,
        humidity_pct: float,
        cloud_cover_pct: float,
        expected_power: float
    ) -> Tuple[str, float, Dict]:
        """
        Detecta anomalias usando ML
        
        Args:
            power_kw: Potência real
            temperature_c: Temperatura
            humidity_pct: Umidade relativa
            cloud_cover_pct: Cobertura de nuvens
            expected_power: Potência esperada
        
        Returns:
            Tuple: (status, anomaly_score, details)
        """
        try:
            # Preparar features
            features = np.array([[
                power_kw,
                temperature_c,
                humidity_pct,
                cloud_cover_pct,
                expected_power,
                power_kw / max(expected_power, 0.1)  # Eficiência relativa
            ]])
            
            # Normalizar
            features_scaled = self.scaler.fit_transform(features)
            
            # Detecção de anomalias
            anomaly_prediction = self.anomaly_detector.predict(features_scaled)[0]
            anomaly_score = abs(self.anomaly_detector.score_samples(features_scaled)[0])
            
            if anomaly_prediction == -1:  # Anomalia detectada
                if temperature_c > 65:
                    status = "ANOMALY_THERMAL"
                    confidence = min(anomaly_score * 100, 100.0)
                elif power_kw < expected_power * 0.7:
                    status = "ANOMALY_PERFORMANCE"
                    confidence = min(anomaly_score * 100, 100.0)
                else:
                    status = "ANOMALY_UNKNOWN"
                    confidence = min(anomaly_score * 100, 100.0)
            else:
                status = "NORMAL"
                confidence = 0.0
            
            details = {
                "confidence": confidence,
                "efficiency": (power_kw / max(expected_power, 0.1)) * 100,
                "cloud_impact": cloud_cover_pct,
                "thermal_stress": temperature_c - 25.0
            }
            
            return status, confidence, details
        
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias com ML: {e}")
            return "ERROR", 0.0, {}
    
    def predict_power(
        self,
        hour: float,
        cloud_cover_pct: float,
        temperature_c: float,
        historical_data: Optional[List[Dict]] = None
    ) -> float:
        """
        Prediz a potência solar para a próxima hora
        
        Args:
            hour: Hora atual do dia
            cloud_cover_pct: Cobertura de nuvens
            temperature_c: Temperatura
            historical_data: Dados históricos para melhor previsão
        
        Returns:
            float: Potência predita em kW
        """
        try:
            # Modelo básico com dados meteorológicos
            base_power = self._solar_curve(hour)
            cloud_factor = max(0.1, 1.0 - (cloud_cover_pct / 100.0) * 0.85)
            
            # Fator de temperatura (módulos FV perdem eficiência com calor)
            temp_factor = 1.0 - max(0, (temperature_c - 25.0) * 0.004)
            
            predicted_power = base_power * cloud_factor * temp_factor
            
            return max(0.0, predicted_power)
        
        except Exception as e:
            logger.error(f"Erro na previsão de potência: {e}")
            return 0.0
    
    def _solar_curve(self, hour: float) -> float:
        """Curva solar teórica"""
        if 6 <= hour <= 18:
            import math
            radianos = math.pi * (hour - 6) / 12
            return max(0.0, np.sin(radianos) * 50.0)
        return 0.0
    
    def add_training_sample(
        self,
        power: float,
        temp: float,
        humidity: float,
        clouds: float,
        expected: float,
        label: str
    ):
        """Adiciona amostra ao buffer de aprendizado"""
        self.training_buffer.append({
            "power": power,
            "temp": temp,
            "humidity": humidity,
            "clouds": clouds,
            "expected": expected,
            "label": label,
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Treina modelo a cada 1000 amostras
        if len(self.training_buffer) >= self.buffer_size:
            self.train_models()
    
    def train_models(self):
        """Treina modelos com dados acumulados"""
        try:
            if len(self.training_buffer) < 100:
                logger.warning("Buffer insuficiente para treinar. Necessário mínimo de 100 amostras.")
                return
            
            df = pd.DataFrame(self.training_buffer)
            
            # Preparar features
            X = df[["power", "temp", "humidity", "clouds", "expected"]].values
            X = np.column_stack([X, df["power"] / np.maximum(df["expected"], 0.1)])
            
            # Normalizar
            X_scaled = self.scaler.fit_transform(X)
            
            # Treinar detector de anomalias
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            self.anomaly_detector.fit(X_scaled)
            
            # Salvar modelos
            dump(self.anomaly_detector, self.model_dir / "anomaly_model.pkl")
            dump(self.scaler, self.model_dir / "scaler.pkl")
            
            logger.info(f"Modelos treinados com {len(self.training_buffer)} amostras")
            
            # Limpar buffer
            self.training_buffer = []
        
        except Exception as e:
            logger.error(f"Erro ao treinar modelos: {e}")
    
    def get_health_score(self, inverter_data: List[Dict]) -> Tuple[float, str]:
        """
        Calcula score de saúde geral do inversor (0-100)
        
        Args:
            inverter_data: Histórico recente de dados do inversor
        
        Returns:
            Tuple: (score 0-100, status textual)
        """
        try:
            if not inverter_data or len(inverter_data) < 10:
                return 100.0, "NOVO"
            
            recent = inverter_data[-100:]  # Últimas 100 amostras
            df = pd.DataFrame(recent)
            
            # Métricas
            anomaly_rate = (df["status"].str.contains("ANOMALY|FAULT", regex=True).sum() / len(df)) * 100
            avg_temp = df.get("temperature_c", pd.Series([25])).mean()
            avg_efficiency = df.get("efficiency_pct", pd.Series([100])).mean()
            
            # Calcular score
            score = 100.0
            score -= anomaly_rate * 0.5  # Até -50 pontos por anomalias
            score -= max(0, (avg_temp - 50) * 0.5)  # Penaliza calor excessivo
            score -= max(0, (100 - avg_efficiency) * 0.3)  # Penaliza baixa eficiência
            
            score = max(0, min(100, score))
            
            if score >= 90:
                status = "EXCELENTE"
            elif score >= 75:
                status = "BOM"
            elif score >= 50:
                status = "AVISO"
            else:
                status = "CRÍTICO"
            
            return score, status
        
        except Exception as e:
            logger.error(f"Erro ao calcular health score: {e}")
            return 50.0, "ERRO"
