"""
Módulo de coleta de dados meteorológicos de APIs opensource
Integra dados de irradiância solar e condições climáticas
"""

import os
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class WeatherDataCollector:
    """Coleta dados meteorológicos de APIs opensource"""
    
    # Configurações - use APIs públicas/free (sem API key obrigatória)
    OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
    WEATHER_API = "https://api.weatherapi.com/v1/current.json"
    
    def __init__(self, latitude: float = -15.7959, longitude: float = -48.1604, city: str = "Brasília"):
        """
        Inicializa o coletor de dados meteorológicos
        
        Args:
            latitude: Latitude da usina solar
            longitude: Longitude da usina solar
            city: Nome da cidade
        """
        self.latitude = latitude
        self.longitude = longitude
        self.city = city
        self.api_key = os.getenv("WEATHER_API_KEY", "")  # Opcional
        
    def get_irradiance_data(self) -> Dict:
        """
        Obtém dados de irradiância solar e condições climáticas
        Usa Open-Meteo (API pública, sem autenticação)
        
        Returns:
            Dict: Dados meteorológicos
        """
        try:
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "current": "temperature_2m,relative_humidity_2m,weather_code,cloud_cover",
                "hourly": "radiation,direct_radiation,diffuse_radiation",
                "timezone": "America/Sao_Paulo"
            }
            
            response = requests.get(
                self.OPEN_METEO_API,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            current = data.get("current", {})
            
            return {
                "temperature_c": float(current.get("temperature_2m", 25.0)),
                "humidity_pct": float(current.get("relative_humidity_2m", 50.0)),
                "cloud_cover_pct": float(current.get("cloud_cover", 30.0)),
                "weather_code": int(current.get("weather_code", 1)),
                "timestamp": datetime.now(timezone.utc),
                "source": "open-meteo"
            }
        except requests.RequestException as e:
            logger.warning(f"Erro ao obter dados do Open-Meteo: {e}")
            return self._get_fallback_data()
        except Exception as e:
            logger.error(f"Erro inesperado ao coletar irradiância: {e}")
            return self._get_fallback_data()
    
    def get_forecast(self) -> Dict:
        """
        Obtém previsão de 7 dias para melhor planejamento
        
        Returns:
            Dict: Dados de previsão
        """
        try:
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,cloud_cover_max,precipitation_sum",
                "timezone": "America/Sao_Paulo",
                "forecast_days": 7
            }
            
            response = requests.get(
                self.OPEN_METEO_API,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            daily = data.get("daily", {})
            
            return {
                "forecast_days": 7,
                "max_temps": daily.get("temperature_2m_max", []),
                "min_temps": daily.get("temperature_2m_min", []),
                "cloud_cover": daily.get("cloud_cover_max", []),
                "precipitation": daily.get("precipitation_sum", []),
                "timestamp": datetime.now(timezone.utc)
            }
        except Exception as e:
            logger.error(f"Erro ao obter previsão: {e}")
            return {}
    
    def _get_fallback_data(self) -> Dict:
        """Retorna dados padrão quando API falha"""
        return {
            "temperature_c": 25.0,
            "humidity_pct": 50.0,
            "cloud_cover_pct": 30.0,
            "weather_code": 1,
            "timestamp": datetime.now(timezone.utc),
            "source": "fallback"
        }
    
    def calculate_cloud_attenuation(self, cloud_cover_pct: float) -> float:
        """
        Calcula atenuação da radiação solar devido às nuvens
        
        Args:
            cloud_cover_pct: Percentual de cobertura de nuvens (0-100)
        
        Returns:
            float: Fator de atenuação (0.0-1.0)
        """
        # Modelo simplificado: cada 10% de nuvem reduz ~8% de irradiância
        if cloud_cover_pct >= 100:
            return 0.0
        if cloud_cover_pct <= 0:
            return 1.0
        
        attenuation = 1.0 - (cloud_cover_pct / 100.0) * 0.85
        return max(0.0, min(1.0, attenuation))
