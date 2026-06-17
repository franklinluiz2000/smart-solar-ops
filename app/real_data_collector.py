"""
Módulo de Dados Reais - Coleta de Usinas Solares Públicas
Integra dados reais de APIs públicas (NREL, OpenWeather) e datasets de usinas
"""

import requests
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class RealSolarDataCollector:
    """Coleta dados reais de usinas solares públicas e APIs"""
    
    # APIs e fontes públicas
    NREL_API = "https://developer.nrel.gov/api/pvwatts/v6.json"
    OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
    SOLAR_SITES = {
        "USINA_BRASILIA": {
            "latitude": -15.7942,
            "longitude": -48.1504,
            "capacity_kw": 500,  # 500 kW (realista para POC)
            "technology": "monocrystalline",
            "inverter_efficiency": 0.97
        },
        "USINA_SAO_PAULO": {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "capacity_kw": 1000,  # 1 MWp
            "technology": "polycrystalline",
            "inverter_efficiency": 0.96
        },
        "USINA_BELO_HORIZONTE": {
            "latitude": -19.9191,
            "longitude": -43.9386,
            "capacity_kw": 750,
            "technology": "monocrystalline",
            "inverter_efficiency": 0.97
        },
        "USINA_SALVADOR": {
            "latitude": -12.9714,
            "longitude": -38.5014,
            "capacity_kw": 600,
            "technology": "bifacial",
            "inverter_efficiency": 0.98
        }
    }
    
    def __init__(self, site_name: str = "USINA_BRASILIA"):
        """
        Inicializa coletor com uma usina específica
        
        Args:
            site_name: Nome da usina pré-configurada
        """
        self.site_name = site_name
        if site_name not in self.SOLAR_SITES:
            logger.warning(f"Site {site_name} não encontrado. Usando USINA_BRASILIA")
            site_name = "USINA_BRASILIA"
        
        self.site = self.SOLAR_SITES[site_name]
        self.latitude = self.site["latitude"]
        self.longitude = self.site["longitude"]
        self.capacity_kw = self.site["capacity_kw"]
        self.cache = {}
        
    def get_real_weather_data(self) -> Dict:
        """
        Obtém dados meteorológicos reais em tempo real
        Usa Open-Meteo (API pública, 10000 chamadas/dia grátis)
        
        Returns:
            Dict: Dados meteorológicos reais
        """
        try:
            # Cache para evitar múltiplas requisições
            cache_key = "weather_data"
            if cache_key in self.cache:
                cached_time, cached_data = self.cache[cache_key]
                if (datetime.now(timezone.utc) - cached_time).total_seconds() < 300:
                    return cached_data
            
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "current": "temperature_2m,relative_humidity_2m,weather_code,cloud_cover,solar_radiation",
                "timezone": "America/Sao_Paulo",
                "forecast_days": 1
            }
            
            response = requests.get(self.OPEN_METEO_API, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()["current"]
            
            weather_data = {
                "timestamp": datetime.now(timezone.utc),
                "temperature_c": float(data.get("temperature_2m", 25)),
                "humidity_pct": float(data.get("relative_humidity_2m", 50)),
                "cloud_cover_pct": float(data.get("cloud_cover", 20)),
                "solar_radiation_w_m2": float(data.get("solar_radiation", 500)),
                "weather_code": int(data.get("weather_code", 1)),
                "source": "open-meteo-real"
            }
            
            self.cache[cache_key] = (datetime.now(timezone.utc), weather_data)
            logger.info(f"✅ Dados reais obtidos para {self.site_name}: {weather_data['temperature_c']}°C, "
                       f"{weather_data['cloud_cover_pct']}% nuvens, {weather_data['solar_radiation_w_m2']}W/m²")
            
            return weather_data
        
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados meteorológicos reais: {e}")
            return self._generate_realistic_simulation()
    
    def _generate_realistic_simulation(self) -> Dict:
        """
        Gera simulação realista baseada em curva solar
        Quando API falha, mantém o sistema funcionando com dados realistas
        """
        from datetime import datetime
        import math
        
        now = datetime.now(timezone.utc)
        # Converter para hora local de Brasília
        local_hour = now.hour + (now.minute / 60)
        
        # Curva solar realista (mais potência ao meio-dia)
        if 6 <= local_hour <= 18:
            solar_angle = (local_hour - 6) * 15  # 15° por hora
            radiation = 800 * math.sin(math.radians(solar_angle))
        else:
            radiation = 0
        
        # Simulação com variações naturais
        import random
        radiation = max(0, radiation + random.gauss(0, 50))
        temp = 20 + (radiation / 100) + random.gauss(0, 2)
        humidity = 50 + random.gauss(0, 10)
        clouds = min(100, max(0, 30 + random.gauss(0, 15)))
        
        return {
            "timestamp": now,
            "temperature_c": temp,
            "humidity_pct": humidity,
            "cloud_cover_pct": clouds,
            "solar_radiation_w_m2": radiation,
            "weather_code": 1,
            "source": "realistic-simulation"
        }
    
    def calculate_power_output(self, weather_data: Dict) -> Dict:
        """
        Calcula potência realista usando modelo PVWatts simplificado
        
        Args:
            weather_data: Dados meteorológicos
        
        Returns:
            Dict: Potência calculada e eficiência
        """
        try:
            # Potência incidente
            ghi = weather_data.get("solar_radiation_w_m2", 500)  # W/m²
            
            # Fator de temperatura (-0.4%/°C acima de 25°C)
            temp = weather_data.get("temperature_c", 25)
            temp_factor = 1.0 - max(0, (temp - 25) * 0.004)
            
            # Fator de nuvens
            cloud_cover = weather_data.get("cloud_cover_pct", 20)
            cloud_factor = 1.0 - (cloud_cover / 100 * 0.85)
            
            # Fator de umidade (afeta vidro dos módulos)
            humidity = weather_data.get("humidity_pct", 50)
            humidity_factor = 0.98 if humidity < 80 else 0.95
            
            # Modelo de potência (similar ao PVWatts)
            # POA (Plane of Array) = GHI × cos(incidence_angle) × albedo
            # Simplificado para inclinação ótima
            effective_ghi = ghi * 0.9  # Perdas por reflexão e ângulo
            
            # Potência AC = DC × Eficiência do inversor × Eficiência dos cabeamentos
            dc_power = effective_ghi * (self.capacity_kw * 1000 / 1000)  # W/m² × capacidade
            ac_power = dc_power * temp_factor * cloud_factor * humidity_factor * self.site["inverter_efficiency"]
            
            # Converter para kW e normalizar pela capacidade
            ac_power_kw = ac_power / 1000
            efficiency_pct = (ac_power_kw / self.capacity_kw) * 100 if self.capacity_kw > 0 else 0
            
            # Adicionar ruído realista (variações de nuvens passando, etc)
            import random
            noise = random.gauss(0, ac_power_kw * 0.02)  # ±2% de ruído
            ac_power_kw = max(0, ac_power_kw + noise)
            efficiency_pct = (ac_power_kw / self.capacity_kw) * 100
            
            return {
                "power_kw": ac_power_kw,
                "efficiency_pct": min(100, efficiency_pct),
                "ghi_w_m2": ghi,
                "temperature_factor": temp_factor,
                "cloud_factor": cloud_factor,
                "humidity_factor": humidity_factor
            }
        
        except Exception as e:
            logger.error(f"❌ Erro ao calcular potência: {e}")
            return {"power_kw": 0, "efficiency_pct": 0}
    
    def get_site_info(self) -> Dict:
        """Retorna informações da usina"""
        return {
            "site_name": self.site_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "capacity_kw": self.capacity_kw,
            "technology": self.site["technology"],
            "inverter_efficiency": self.site["inverter_efficiency"]
        }
    
    def get_available_sites(self) -> List[str]:
        """Retorna lista de usinas disponíveis"""
        return list(self.SOLAR_SITES.keys())
    
    @staticmethod
    def get_historical_reference(month: int, latitude: float, longitude: float) -> Dict:
        """
        Retorna valores de referência históricos para um mês/localização
        Baseado em dados climatológicos
        
        Args:
            month: Mês (1-12)
            latitude: Latitude
            longitude: Longitude
        
        Returns:
            Dict: Dados históricos médios
        """
        # Dados climatológicos médios (simplificado)
        # Em produção, integraria com PVGIS ou NREL Datasets
        monthly_data = {
            1: {"avg_ghi": 450, "avg_temp": 28, "avg_humidity": 70},  # Jan - verão
            2: {"avg_ghi": 450, "avg_temp": 28, "avg_humidity": 72},
            3: {"avg_ghi": 420, "avg_temp": 26, "avg_humidity": 68},
            4: {"avg_ghi": 380, "avg_temp": 24, "avg_humidity": 65},  # Outono
            5: {"avg_ghi": 320, "avg_temp": 21, "avg_humidity": 60},
            6: {"avg_ghi": 280, "avg_temp": 20, "avg_humidity": 55},  # Inverno
            7: {"avg_ghi": 300, "avg_temp": 21, "avg_humidity": 54},
            8: {"avg_ghi": 360, "avg_temp": 23, "avg_humidity": 58},
            9: {"avg_ghi": 420, "avg_temp": 25, "avg_humidity": 65},  # Primavera
            10: {"avg_ghi": 480, "avg_temp": 27, "avg_humidity": 68},
            11: {"avg_ghi": 500, "avg_temp": 28, "avg_humidity": 70},
            12: {"avg_ghi": 480, "avg_temp": 28, "avg_humidity": 72}
        }
        
        return monthly_data.get(month, monthly_data[1])
