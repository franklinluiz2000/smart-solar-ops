"""
Gerador de Relatórios Executivos em PDF
Cria relatórios profissionais para apresentação
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from io import BytesIO
import json

logger = logging.getLogger(__name__)

# Para PDF, usaremos reportlab (será adicionado ao requirements.txt)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib.colors import HexColor, black, white, red, green, orange
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("⚠️ reportlab não instalado. PDF será gerado em formato texto.")


class ExecutiveReportGenerator:
    """Gera relatórios executivos para apresentação ao cliente"""
    
    def __init__(self, site_info: Dict, output_dir: str = "/tmp"):
        """
        Inicializa gerador de relatórios
        
        Args:
            site_info: Informações da usina
            output_dir: Diretório para salvar PDFs
        """
        self.site_info = site_info
        self.output_dir = output_dir
        self.styles = getSampleStyleSheet() if PDF_AVAILABLE else None
    
    def generate_daily_report(self, performance_data: Dict, alerts: List, predictions: List) -> bytes:
        """
        Gera relatório diário em PDF
        
        Args:
            performance_data: Dados de performance do dia
            alerts: Lista de alertas
            predictions: Previsões
        
        Returns:
            bytes: PDF em bytes
        """
        if not PDF_AVAILABLE:
            return self._generate_text_report(performance_data, alerts, predictions)
        
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=HexColor('#1f77b4'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            elements.append(Paragraph("☀️ RELATÓRIO DIÁRIO DE MONITORAMENTO", title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Informações da usina
            info_data = [
                ["USINA", self.site_info.get("site_name", "N/A")],
                ["LOCALIZAÇÃO", f"{self.site_info.get('latitude', 0):.4f}, {self.site_info.get('longitude', 0):.4f}"],
                ["CAPACIDADE", f"{self.site_info.get('capacity_kw', 0)} kW"],
                ["DATA", datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")],
                ["TECNOLOGIA", self.site_info.get("technology", "N/A")]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#e8f4f8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
            ]))
            
            elements.append(info_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Performance
            elements.append(Paragraph("📊 PERFORMANCE DO DIA", self.styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            perf_data = [
                ["MÉTRICA", "VALOR"],
                ["Potência Média", f"{performance_data.get('avg_power_kw', 0):.2f} kW"],
                ["Potência Máxima", f"{performance_data.get('max_power_kw', 0):.2f} kW"],
                ["Eficiência Média", f"{performance_data.get('avg_efficiency', 0):.1f} %"],
                ["Temperatura Média", f"{performance_data.get('avg_temperature', 0):.1f} °C"],
            ]
            
            perf_table = Table(perf_data, colWidths=[2.5*inch, 2.5*inch])
            perf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f0f0f0')])
            ]))
            
            elements.append(perf_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Alertas
            elements.append(Paragraph("🔔 ALERTAS DO PERÍODO", self.styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            if alerts:
                alert_data = [["TIPO", "INVERSOR", "SEVERIDADE", "MENSAGEM"]]
                for alert in alerts[:10]:
                    alert_data.append([
                        alert.get("type", ""),
                        alert.get("inverter_id", ""),
                        alert.get("level", ""),
                        alert.get("message", "")[:40] + "..."
                    ])
                
                alert_table = Table(alert_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.1*inch])
                alert_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#ff6b6b')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
                ]))
                elements.append(alert_table)
            else:
                elements.append(Paragraph("✅ Nenhum alerta registrado", self.styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
            
            # Previsões
            elements.append(Paragraph("🔮 PREVISÕES E RECOMENDAÇÕES", self.styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            if predictions:
                pred_text = "Baseado em análise de dados históricos, recomendamos:<br/>"
                for i, pred in enumerate(predictions[:5], 1):
                    pred_text += f"{i}. {pred.get('prediction', '')}: {pred.get('reason', '')}<br/>"
                elements.append(Paragraph(pred_text, self.styles['Normal']))
            else:
                elements.append(Paragraph("✅ Sistema operando dentro do esperado", self.styles['Normal']))
            
            elements.append(Spacer(1, 0.4*inch))
            
            # Rodapé
            footer_text = f"""
            <b>Relatório Gerado Automaticamente</b><br/>
            Sistema de Monitoramento Inteligente - Smart Solar Ops<br/>
            {datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")}
            """
            elements.append(Paragraph(footer_text, ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=HexColor('#666666'),
                alignment=TA_CENTER
            )))
            
            doc.build(elements)
            buffer.seek(0)
            return buffer.getvalue()
        
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF: {e}")
            return self._generate_text_report(performance_data, alerts, predictions)
    
    def _generate_text_report(self, performance_data: Dict, alerts: List, predictions: List) -> bytes:
        """Gera relatório em formato texto"""
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║        RELATÓRIO DIÁRIO DE MONITORAMENTO SOLAR                 ║
║              Smart Solar Ops - Sistema Inteligente             ║
╚════════════════════════════════════════════════════════════════╝

📍 INFORMAÇÕES DA USINA
├─ Nome: {self.site_info.get('site_name', 'N/A')}
├─ Localização: {self.site_info.get('latitude', 0):.4f}, {self.site_info.get('longitude', 0):.4f}
├─ Capacidade: {self.site_info.get('capacity_kw', 0)} kW
├─ Tecnologia: {self.site_info.get('technology', 'N/A')}
└─ Data do Relatório: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')}

📊 PERFORMANCE DO DIA
├─ Potência Média: {performance_data.get('avg_power_kw', 0):.2f} kW
├─ Potência Máxima: {performance_data.get('max_power_kw', 0):.2f} kW
├─ Eficiência Média: {performance_data.get('avg_efficiency', 0):.1f} %
└─ Temperatura Média: {performance_data.get('avg_temperature', 0):.1f} °C

🔔 ALERTAS ({len(alerts)} total)
"""
        for i, alert in enumerate(alerts[:10], 1):
            report += f"{i}. [{alert.get('level', '')}] {alert.get('type', '')}: {alert.get('message', '')}\n"
        
        report += f"""
🔮 PREVISÕES E RECOMENDAÇÕES
"""
        for i, pred in enumerate(predictions[:5], 1):
            report += f"{i}. {pred.get('prediction', '')}: {pred.get('reason', '')}\n"
        
        report += f"""
═══════════════════════════════════════════════════════════════════
Relatório gerado automaticamente em {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')}
"""
        return report.encode('utf-8')
    
    def generate_monthly_summary(self, monthly_data: List[Dict]) -> str:
        """
        Gera sumário mensal em HTML
        
        Args:
            monthly_data: Dados do mês
        
        Returns:
            str: HTML do relatório
        """
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Sumário Mensal - {self.site_info.get('site_name', 'Usina Solar')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #1f77b4; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background-color: #1f77b4; color: white; padding: 10px; }}
                td {{ border: 1px solid #ddd; padding: 10px; }}
                tr:nth-child(even) {{ background-color: #f0f0f0; }}
                .metric-box {{ background-color: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .status-good {{ color: green; font-weight: bold; }}
                .status-warning {{ color: orange; font-weight: bold; }}
                .status-critical {{ color: red; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>☀️ Sumário Mensal de Operação</h1>
            <h2>{self.site_info.get('site_name', 'Usina Solar')}</h2>
            
            <div class="metric-box">
                <h3>📊 Métricas do Mês</h3>
                <table>
                    <tr>
                        <th>Métrica</th>
                        <th>Valor</th>
                        <th>Status</th>
                    </tr>
        """
        
        if monthly_data:
            total_energy = sum([d.get('total_energy_kwh', 0) for d in monthly_data])
            avg_efficiency = sum([d.get('avg_efficiency', 0) for d in monthly_data]) / len(monthly_data)
            anomaly_count = sum([d.get('anomaly_count', 0) for d in monthly_data])
            
            html += f"""
                    <tr>
                        <td>Energia Total Gerada</td>
                        <td>{total_energy:,.0f} kWh</td>
                        <td><span class="status-good">✓</span></td>
                    </tr>
                    <tr>
                        <td>Eficiência Média</td>
                        <td>{avg_efficiency:.1f}%</td>
                        <td><span class="{'status-good' if avg_efficiency > 90 else 'status-warning'}">{'✓' if avg_efficiency > 90 else '⚠'}</span></td>
                    </tr>
                    <tr>
                        <td>Anomalias Detectadas</td>
                        <td>{anomaly_count}</td>
                        <td><span class="{'status-good' if anomaly_count < 10 else 'status-critical'}">{'✓' if anomaly_count < 10 else '✗'}</span></td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
            
            <h3>📈 Tendências</h3>
            <p>Sistema operando dentro dos parâmetros esperados para o período.</p>
            
            <footer>
                <hr>
                <p><small>Relatório gerado automaticamente pelo Smart Solar Ops</small></p>
                <p><small>Timestamp: """ + datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC") + """</small></p>
            </footer>
        </body>
        </html>
        """
        
        return html
    
    def export_json_report(self, data: Dict) -> str:
        """Exporta relatório em JSON"""
        return json.dumps(data, indent=2, default=str)
