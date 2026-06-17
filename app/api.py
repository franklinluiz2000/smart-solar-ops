"""
API REST Flask para monitoramento solar
Endpoints para visualização de dados, alertas, previsões e relatórios
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import logging
import io

logger = logging.getLogger(__name__)

def create_api_app(db_pool=None, alert_manager=None, ai_model=None, agents_manager=None, report_generator=None):
    """
    Cria aplicação Flask com endpoints de monitoramento
    
    Args:
        db_pool: Pool de conexões do banco de dados
        alert_manager: Gerenciador de alertas
        ai_model: Modelo de IA
        agents_manager: Gerenciador de agentes
        report_generator: Gerador de relatórios
    
    Returns:
        Flask app
    """
    app = Flask(__name__)
    CORS(app)
    
    app.db_pool = db_pool
    app.alert_manager = alert_manager
    app.ai_model = ai_model
    app.agents_manager = agents_manager
    app.report_generator = report_generator
    
    # ==================== ENDPOINTS ====================
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Verificação de saúde da API"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
    
    @app.route('/api/inverters', methods=['GET'])
    def get_inverters():
        """Lista todos os inversores com dados recentes"""
        try:
            conn = app.db_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT inverter_id, 
                       MAX(time) as last_update,
                       FIRST(power_kw, time DESC) as power_kw,
                       FIRST(temperature_c, time DESC) as temperature_c,
                       FIRST(efficiency_pct, time DESC) as efficiency_pct,
                       FIRST(status, time DESC) as status
                FROM telemetry_inverter
                WHERE time > now() - interval '1 hour'
                GROUP BY inverter_id
                ORDER BY inverter_id;
            """
            
            cursor.execute(query)
            inverters = cursor.fetchall()
            
            result = []
            for inv in inverters:
                result.append({
                    "id": inv[0],
                    "last_update": inv[1].isoformat() if inv[1] else None,
                    "power_kw": float(inv[2]) if inv[2] else 0,
                    "temperature_c": float(inv[3]) if inv[3] else 0,
                    "efficiency_pct": float(inv[4]) if inv[4] else 0,
                    "status": inv[5]
                })
            
            cursor.close()
            app.db_pool.putconn(conn)
            
            return jsonify(result), 200
        
        except Exception as e:
            logger.error(f"Erro ao obter inversores: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/inverter/<inverter_id>/history', methods=['GET'])
    def get_inverter_history(inverter_id):
        """Obtém histórico de um inversor (últimas 24h)"""
        try:
            hours = request.args.get('hours', 24, type=int)
            
            conn = app.db_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                SELECT time, power_kw, temperature_c, efficiency_pct, status
                FROM telemetry_inverter
                WHERE inverter_id = %s 
                  AND time > now() - interval '%s hours'
                ORDER BY time DESC
                LIMIT 1000;
            """
            
            cursor.execute(query, (inverter_id, hours))
            data = cursor.fetchall()
            
            result = []
            for row in data:
                result.append({
                    "time": row[0].isoformat(),
                    "power_kw": float(row[1]) if row[1] else 0,
                    "temperature_c": float(row[2]) if row[2] else 0,
                    "efficiency_pct": float(row[3]) if row[3] else 0,
                    "status": row[4]
                })
            
            cursor.close()
            app.db_pool.putconn(conn)
            
            return jsonify(result), 200
        
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/alerts', methods=['GET'])
    def get_alerts():
        """Retorna alertas ativos"""
        try:
            inverter_id = request.args.get('inverter_id', None)
            
            if app.alert_manager:
                alerts = app.alert_manager.get_active_alerts(inverter_id)
                summary = app.alert_manager.get_alert_summary()
                
                return jsonify({
                    "alerts": alerts,
                    "summary": summary
                }), 200
            
            return jsonify({"alerts": [], "summary": {}}), 200
        
        except Exception as e:
            logger.error(f"Erro ao obter alertas: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/alerts/resolve', methods=['POST'])
    def resolve_alert():
        """Marca alerta como resolvido"""
        try:
            data = request.json
            inverter_id = data.get('inverter_id')
            alert_type = data.get('alert_type')
            
            if app.alert_manager:
                from alerts import AlertType
                app.alert_manager.resolve_alert(
                    inverter_id,
                    AlertType[alert_type]
                )
                
                return jsonify({"status": "resolved"}), 200
            
            return jsonify({"error": "Alert manager not available"}), 500
        
        except Exception as e:
            logger.error(f"Erro ao resolver alerta: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/inverter/<inverter_id>/health', methods=['GET'])
    def get_inverter_health(inverter_id):
        """Retorna health score de um inversor"""
        try:
            conn = app.db_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                SELECT time, health_score, status, anomaly_rate_pct, 
                       avg_temperature_c, avg_efficiency_pct
                FROM inverter_health
                WHERE inverter_id = %s
                ORDER BY time DESC
                LIMIT 1;
            """
            
            cursor.execute(query, (inverter_id,))
            row = cursor.fetchone()
            
            if row:
                result = {
                    "inverter_id": inverter_id,
                    "timestamp": row[0].isoformat(),
                    "health_score": float(row[1]),
                    "status": row[2],
                    "anomaly_rate_pct": float(row[3]),
                    "avg_temperature_c": float(row[4]),
                    "avg_efficiency_pct": float(row[5])
                }
            else:
                result = {"inverter_id": inverter_id, "status": "sem dados"}
            
            cursor.close()
            app.db_pool.putconn(conn)
            
            return jsonify(result), 200
        
        except Exception as e:
            logger.error(f"Erro ao obter health: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/forecast', methods=['GET'])
    def get_forecast():
        """Obtém previsão de potência para próximas horas"""
        try:
            inverter_id = request.args.get('inverter_id', 'INV-01')
            hours = request.args.get('hours', 24, type=int)
            
            conn = app.db_pool.getconn()
            cursor = conn.cursor()
            
            query = """
                SELECT time, predicted_power_kw, confidence, weather_conditions
                FROM power_forecast
                WHERE inverter_id = %s
                  AND time > now()
                  AND time < now() + interval '%s hours'
                ORDER BY time ASC;
            """
            
            cursor.execute(query, (inverter_id, hours))
            data = cursor.fetchall()
            
            result = []
            for row in data:
                result.append({
                    "time": row[0].isoformat(),
                    "predicted_power_kw": float(row[1]) if row[1] else 0,
                    "confidence": float(row[2]) if row[2] else 0,
                    "weather": row[3] if row[3] else {}
                })
            
            cursor.close()
            app.db_pool.putconn(conn)
            
            return jsonify(result), 200
        
        except Exception as e:
            logger.error(f"Erro ao obter previsão: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/dashboard', methods=['GET'])
    def get_dashboard():
        """Dashboard agregado com principais métricas"""
        try:
            conn = app.db_pool.getconn()
            cursor = conn.cursor()
            
            # Poder total atual
            query = """
                SELECT COALESCE(SUM(power_kw), 0) as total_power
                FROM (
                    SELECT DISTINCT ON (inverter_id) power_kw
                    FROM telemetry_inverter
                    WHERE time > now() - interval '1 hour'
                    ORDER BY inverter_id, time DESC
                ) t;
            """
            cursor.execute(query)
            total_power = cursor.fetchone()[0]
            
            # Alertas
            alerts_summary = app.alert_manager.get_alert_summary() if app.alert_manager else {}
            
            cursor.close()
            app.db_pool.putconn(conn)
            
            return jsonify({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_power_kw": float(total_power),
                "alerts": alerts_summary,
                "status": "operational"
            }), 200
        
        except Exception as e:
            logger.error(f"Erro ao obter dashboard: {e}")
            return jsonify({"error": str(e)}), 500
    
    # ==================== ERROR HANDLERS ====================
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint não encontrado"}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Erro interno do servidor"}), 500
    
    # ==================== NOVOS ENDPOINTS - AGENTES E RELATÓRIOS ====================
    
    @app.route('/api/agents/status', methods=['GET'])
    def get_agents_status():
        """Status de todos os agentes autônomos"""
        try:
            if app.agents_manager:
                return jsonify(app.agents_manager.get_status()), 200
            return jsonify({"error": "Agentes não disponíveis"}), 500
        except Exception as e:
            logger.error(f"Erro ao obter status de agentes: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/analysis/report', methods=['GET'])
    def get_analysis_report():
        """Relatório de análise de anomalias"""
        try:
            if app.agents_manager:
                return jsonify(app.agents_manager.get_analysis_report()), 200
            return jsonify({"error": "Agentes não disponíveis"}), 500
        except Exception as e:
            logger.error(f"Erro ao obter relatório de análise: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/performance/report', methods=['GET'])
    def get_performance_report():
        """Relatório de performance do sistema"""
        try:
            if app.agents_manager:
                return jsonify(app.agents_manager.get_performance_report()), 200
            return jsonify({"error": "Agentes não disponíveis"}), 500
        except Exception as e:
            logger.error(f"Erro ao obter relatório de performance: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/predictions', methods=['GET'])
    def get_predictions():
        """Previsões de problemas futuros"""
        try:
            if app.agents_manager:
                return jsonify(app.agents_manager.get_predictions()), 200
            return jsonify({"error": "Agentes não disponíveis"}), 500
        except Exception as e:
            logger.error(f"Erro ao obter previsões: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/report/daily', methods=['GET'])
    def generate_daily_report():
        """Gera relatório diário em PDF"""
        try:
            if not app.report_generator:
                return jsonify({"error": "Gerador de relatórios não disponível"}), 500
            
            if not app.agents_manager:
                return jsonify({"error": "Agentes não disponíveis"}), 500
            
            # Coletar dados
            performance_data = app.agents_manager.get_performance_report()
            alerts = app.alert_manager.get_active_alerts() if app.alert_manager else []
            predictions = app.agents_manager.get_predictions()
            
            # Gerar PDF
            pdf_bytes = app.report_generator.generate_daily_report(
                performance_data.get('daily_report', {}),
                alerts,
                predictions.get('current_predictions', {}).get('predictions', [])
            )
            
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"relatorio_diario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
        
        except Exception as e:
            logger.error(f"Erro ao gerar relatório PDF: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/report/monthly', methods=['GET'])
    def get_monthly_report():
        """Relatório mensal em HTML"""
        try:
            if not app.report_generator or not app.agents_manager:
                return jsonify({"error": "Recursos não disponíveis"}), 500
            
            # Coletar dados do mês
            performance_data = app.agents_manager.get_performance_report()
            monthly_data = performance_data.get('recent_kpis', [])
            
            # Gerar HTML
            html = app.report_generator.generate_monthly_summary(monthly_data)
            
            return app.response_class(
                response=html,
                status=200,
                mimetype='text/html'
            )
        
        except Exception as e:
            logger.error(f"Erro ao gerar relatório mensal: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/report/json', methods=['GET'])
    def get_json_report():
        """Exporta todos os dados em JSON"""
        try:
            report_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agents_status": app.agents_manager.get_status() if app.agents_manager else {},
                "analysis": app.agents_manager.get_analysis_report() if app.agents_manager else {},
                "performance": app.agents_manager.get_performance_report() if app.agents_manager else {},
                "predictions": app.agents_manager.get_predictions() if app.agents_manager else {},
                "alerts": {
                    "active": app.alert_manager.get_active_alerts() if app.alert_manager else [],
                    "summary": app.alert_manager.get_alert_summary() if app.alert_manager else {}
                }
            }
            
            return jsonify(report_data), 200
        
        except Exception as e:
            logger.error(f"Erro ao gerar relatório JSON: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/system/info', methods=['GET'])
    def get_system_info():
        """Informações gerais do sistema"""
        try:
            info = {
                "system_name": "Smart Solar Ops - Sistema Inteligente de Monitoramento",
                "version": "2.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "features": [
                    "Coleta de dados em tempo real",
                    "Detecção de anomalias com IA",
                    "Monitoramento autônomo com agentes",
                    "Alertas inteligentes",
                    "Previsões preditivas",
                    "Relatórios automáticos",
                    "API REST completa"
                ],
                "database": {
                    "type": "TimescaleDB",
                    "status": "connected" if app.db_pool else "disconnected"
                },
                "services": {
                    "ai_model": "active" if app.ai_model else "inactive",
                    "alert_manager": "active" if app.alert_manager else "inactive",
                    "agents": "active" if app.agents_manager else "inactive",
                    "report_generator": "active" if app.report_generator else "inactive"
                }
            }
            
            return jsonify(info), 200
        
        except Exception as e:
            logger.error(f"Erro ao obter informações do sistema: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app
