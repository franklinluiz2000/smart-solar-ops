#!/usr/bin/env python3
"""
Script de validação de integração v2.0
Testa se todos os componentes podem ser inicializados
"""

import sys
import os
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("🔍 Testando importações...")
    
    try:
        print("  ✓ Importando weather_api...", end="")
        from weather_api import WeatherDataCollector
        print(" ✅")
        
        print("  ✓ Importando ai_model...", end="")
        from ai_model import SolarAIModel
        print(" ✅")
        
        print("  ✓ Importando alerts...", end="")
        from alerts import AlertManager, AlertType
        print(" ✅")
        
        print("  ✓ Importando api...", end="")
        from api import create_api_app
        print(" ✅")
        
        print("  ✓ Importando real_data_collector...", end="")
        from real_data_collector import RealSolarDataCollector
        print(" ✅")
        
        print("  ✓ Importando agents...", end="")
        from agents import MonitoringAgentManager
        print(" ✅")
        
        print("  ✓ Importando reports...", end="")
        from reports import ExecutiveReportGenerator
        print(" ✅")
        
        return True
    except ImportError as e:
        print(f" ❌\n  Erro: {e}")
        return False

def test_components():
    """Testa se os componentes podem ser inicializados"""
    print("\n🔨 Testando inicialização de componentes...")
    
    try:
        from weather_api import WeatherDataCollector
        from ai_model import SolarAIModel
        from alerts import AlertManager
        from real_data_collector import RealSolarDataCollector
        from reports import ExecutiveReportGenerator
        
        # Weather Collector
        print("  ✓ WeatherDataCollector...", end="")
        weather = WeatherDataCollector()
        print(" ✅")
        
        # AI Model
        print("  ✓ SolarAIModel...", end="")
        ai_model = SolarAIModel()
        print(" ✅")
        
        # Alert Manager
        print("  ✓ AlertManager...", end="")
        alert_manager = AlertManager()
        print(" ✅")
        
        # Real Data Collector
        print("  ✓ RealSolarDataCollector...", end="")
        real_data = RealSolarDataCollector(site_name="USINA_BRASILIA")
        print(" ✅")
        
        # Report Generator
        print("  ✓ ExecutiveReportGenerator...", end="")
        report_gen = ExecutiveReportGenerator(
            site_info=real_data.get_site_info(),
            output_dir="/tmp"
        )
        print(" ✅")
        
        return True
    except Exception as e:
        print(f" ❌\n  Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_data():
    """Testa coleta de dados reais"""
    print("\n🌍 Testando coleta de dados reais...")
    
    try:
        from real_data_collector import RealSolarDataCollector
        
        print("  ✓ Coletando dados meteorológicos...", end="")
        collector = RealSolarDataCollector(site_name="USINA_BRASILIA")
        weather = collector.get_real_weather_data()
        print(f" ✅ ({weather.get('temperature_c', 0):.1f}°C)")
        
        print("  ✓ Calculando potência de saída...", end="")
        power = collector.calculate_power_output(weather)
        print(f" ✅ ({power:.2f} kW)")
        
        print("  ✓ Obtendo info do site...", end="")
        info = collector.get_site_info()
        print(f" ✅ ({info['name']})")
        
        return True
    except Exception as e:
        print(f" ❌\n  Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_creation():
    """Testa criação da API"""
    print("\n🚀 Testando criação da API REST...")
    
    try:
        from api import create_api_app
        
        print("  ✓ Criando app Flask...", end="")
        app = create_api_app(
            db_pool=None,
            alert_manager=None,
            ai_model=None,
            agents_manager=None,
            report_generator=None
        )
        print(" ✅")
        
        print("  ✓ Verificando endpoints...", end="")
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)
        print(f" ✅ ({len(routes)} endpoints)")
        
        # Listar endpoints
        print("\n  📋 Endpoints disponíveis:")
        for rule in sorted(set(routes)):
            if "/api/" in rule:
                print(f"     {rule}")
        
        return True
    except Exception as e:
        print(f" ❌\n  Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste"""
    print("=" * 60)
    print("🔬 VALIDAÇÃO DE INTEGRAÇÃO - SMART SOLAR OPS v2.0")
    print("=" * 60)
    
    results = []
    
    results.append(("Importações", test_imports()))
    results.append(("Componentes", test_components()))
    results.append(("Dados Reais", test_real_data()))
    results.append(("API REST", test_api_creation()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 Todos os testes passaram com sucesso!")
        print("\n📌 Próximos passos:")
        print("   1. Configurar variáveis de ambiente (.env)")
        print("   2. Iniciar docker-compose: docker-compose up -d")
        print("   3. Testar endpoints da API")
        print("   4. Gerar relatórios")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
