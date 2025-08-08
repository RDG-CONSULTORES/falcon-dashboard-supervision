#!/usr/bin/env python3
"""
Script para verificar datos disponibles y probar las funcionalidades del dashboard
"""

import os
import sys
from datetime import datetime
import json

# Add paths for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test basic database connection and data availability"""
    try:
        from database.connection_v3 import get_db_connection
        
        print("🔌 Conectando a la base de datos...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ Conexión exitosa - PostgreSQL {version[0].split()[1]}")
        
        # Check table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'supervision_operativa_detalle'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ Tabla 'supervision_operativa_detalle' no existe")
            return False
        
        # Check record count
        cursor.execute("SELECT COUNT(*) FROM supervision_operativa_detalle")
        total = cursor.fetchone()[0]
        print(f"📊 Total registros: {total:,}")
        
        if total == 0:
            print("⚠️  No hay datos en la tabla")
            return False
            
        # Check date range
        cursor.execute("""
            SELECT 
                MIN(fecha_supervision) as min_date,
                MAX(fecha_supervision) as max_date,
                COUNT(DISTINCT EXTRACT(YEAR FROM fecha_supervision)) as years,
                COUNT(DISTINCT sucursal) as sucursales,
                COUNT(DISTINCT estado) as estados
            FROM supervision_operativa_detalle 
            WHERE fecha_supervision IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        print(f"📅 Rango de fechas: {stats[0]} a {stats[1]}")
        print(f"📈 Años con datos: {stats[2]}")
        print(f"🏢 Sucursales: {stats[3]:,}")
        print(f"🗺️  Estados: {stats[4]:,}")
        
        # Check recent years
        cursor.execute("""
            SELECT 
                EXTRACT(YEAR FROM fecha_supervision)::int as year,
                COUNT(*) as records,
                AVG(porcentaje) as avg_pct,
                MIN(porcentaje) as min_pct,
                MAX(porcentaje) as max_pct
            FROM supervision_operativa_detalle 
            WHERE fecha_supervision IS NOT NULL 
            AND porcentaje IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM fecha_supervision)
            ORDER BY year DESC
            LIMIT 5
        """)
        
        print("\n📊 Datos por año:")
        print("Year | Records  | Avg%  | Min%  | Max%")
        print("-----|----------|-------|-------|------")
        
        years_with_data = []
        for row in cursor.fetchall():
            year, records, avg_pct, min_pct, max_pct = row
            years_with_data.append(year)
            print(f"{year} | {records:8,} | {avg_pct:5.1f} | {min_pct:5.1f} | {max_pct:5.1f}")
        
        cursor.close()
        conn.close()
        
        return years_with_data
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_api_endpoints(years_with_data):
    """Test API endpoints with actual data"""
    import requests
    
    if not years_with_data:
        print("⚠️  No hay años con datos para probar")
        return
        
    base_url = "http://localhost:5002"
    latest_year = years_with_data[0]
    
    print(f"\n🧪 Probando endpoints con datos del año {latest_year}...")
    
    # Test endpoints
    endpoints_to_test = [
        (f"/api/v1/analytics/kpis?year={latest_year}&quarter=Q1", "KPIs Q1"),
        (f"/api/v1/analytics/kpis?year={latest_year}&quarter=ALL", "KPIs todo el año"),
        (f"/api/v1/geo/coordinates?year={latest_year}&limit=5", "Coordenadas geográficas"),
        (f"/api/v1/analytics/performance/states?year={latest_year}", "Performance por estados"),
        ("/api/v1/health", "Health check"),
    ]
    
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {description}: OK")
                
                # Show sample data
                if 'data' in data and isinstance(data['data'], dict):
                    if 'promedio_general' in data['data'] and data['data']['promedio_general']:
                        print(f"   📊 Promedio: {data['data']['promedio_general']:.1f}%")
                elif isinstance(data, list) and len(data) > 0:
                    print(f"   📊 {len(data)} registros encontrados")
                elif 'status' in data:
                    print(f"   📊 Status: {data['status']}")
                    
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: Error de conexión - {e}")
        except Exception as e:
            print(f"❌ {description}: Error - {e}")

def create_test_dashboard():
    """Create a simple test dashboard HTML"""
    
    html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Falcon Miniapp - Test Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .metric { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .metric-label { color: #6c757d; margin-top: 5px; }
        .chart-container { position: relative; height: 400px; margin: 20px 0; }
        .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .loading { text-align: center; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Falcon Miniapp - Dashboard de Prueba</h1>
        
        <div class="card">
            <h2>📊 Estado del Sistema</h2>
            <div id="system-status" class="loading">Verificando estado del sistema...</div>
        </div>
        
        <div class="card">
            <h2>📈 Métricas Principales</h2>
            <div id="metrics-container" class="metrics">
                <div class="loading">Cargando métricas...</div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Gráfico de Performance</h2>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h2>🧪 Pruebas de API</h2>
            <button onclick="testAllEndpoints()">Probar Todos los Endpoints</button>
            <button onclick="loadDashboardData()">Recargar Datos</button>
            <div id="api-tests"></div>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:5002';
        let performanceChart = null;
        
        // Test system health
        async function checkSystemHealth() {
            try {
                const response = await fetch(`${API_BASE}/api/v1/health`);
                const data = await response.json();
                
                const statusDiv = document.getElementById('system-status');
                if (response.ok) {
                    statusDiv.innerHTML = `
                        <div class="status success">
                            ✅ Sistema funcionando correctamente<br>
                            Status: ${data.status}<br>
                            Timestamp: ${new Date(data.timestamp).toLocaleString()}
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `<div class="status error">❌ Error del sistema: ${data.error || 'Unknown'}</div>`;
                }
            } catch (error) {
                document.getElementById('system-status').innerHTML = 
                    `<div class="status error">❌ No se puede conectar al servidor: ${error.message}</div>`;
            }
        }
        
        // Load KPI metrics
        async function loadMetrics() {
            try {
                // Try current year first, then previous years  
                const currentYear = new Date().getFullYear();
                const yearsToTry = [currentYear, currentYear - 1, currentYear - 2, 2023, 2022];
                
                let data = null;
                let workingYear = null;
                
                for (const year of yearsToTry) {
                    try {
                        const response = await fetch(`${API_BASE}/api/v1/analytics/kpis?year=${year}&quarter=ALL`);
                        if (response.ok) {
                            const result = await response.json();
                            if (result.success && result.data && result.data.total_supervisiones > 0) {
                                data = result.data;
                                workingYear = year;
                                break;
                            }
                        }
                    } catch (e) {
                        continue;
                    }
                }
                
                const metricsContainer = document.getElementById('metrics-container');
                
                if (data && workingYear) {
                    metricsContainer.innerHTML = `
                        <div class="metric">
                            <div class="metric-value">${data.promedio_general ? data.promedio_general.toFixed(1) + '%' : 'N/A'}</div>
                            <div class="metric-label">Promedio General</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.total_supervisiones || 0}</div>
                            <div class="metric-label">Total Supervisiones</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.total_sucursales || 0}</div>
                            <div class="metric-label">Sucursales</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.total_estados || 0}</div>
                            <div class="metric-label">Estados</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${workingYear}</div>
                            <div class="metric-label">Año de Datos</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.cumplimiento_meta}%</div>
                            <div class="metric-label">Cumplimiento Meta</div>
                        </div>
                    `;
                    
                    // Load performance chart
                    loadPerformanceChart(workingYear);
                } else {
                    metricsContainer.innerHTML = `
                        <div class="status warning">
                            ⚠️ No se encontraron datos para los años ${yearsToTry.join(', ')}<br>
                            Verifica que existan datos en la base de datos.
                        </div>
                    `;
                }
                
            } catch (error) {
                document.getElementById('metrics-container').innerHTML = 
                    `<div class="status error">❌ Error cargando métricas: ${error.message}</div>`;
            }
        }
        
        // Load performance chart
        async function loadPerformanceChart(year) {
            try {
                const response = await fetch(`${API_BASE}/api/v1/analytics/performance/states?year=${year}&limit=10`);
                const data = await response.json();
                
                if (response.ok && data.success && data.data.length > 0) {
                    const ctx = document.getElementById('performanceChart').getContext('2d');
                    
                    if (performanceChart) {
                        performanceChart.destroy();
                    }
                    
                    performanceChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.data.map(item => item.estado),
                            datasets: [{
                                label: 'Promedio de Performance (%)',
                                data: data.data.map(item => item.promedio),
                                backgroundColor: 'rgba(0, 123, 255, 0.8)',
                                borderColor: 'rgba(0, 123, 255, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: `Performance por Estados - ${year}`
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 100,
                                    ticks: {
                                        callback: function(value) {
                                            return value + '%';
                                        }
                                    }
                                }
                            }
                        }
                    });
                }
            } catch (error) {
                console.error('Error loading performance chart:', error);
            }
        }
        
        // Test all endpoints
        async function testAllEndpoints() {
            const testsDiv = document.getElementById('api-tests');
            testsDiv.innerHTML = '<div class="loading">Probando endpoints...</div>';
            
            const endpoints = [
                { url: '/api/v1/health', name: 'Health Check' },
                { url: '/api/v1/analytics/kpis?year=2023&quarter=Q1', name: 'KPIs Q1 2023' },
                { url: '/api/v1/geo/coordinates?year=2023&limit=5', name: 'Coordenadas' },
                { url: '/api/v1/analytics/performance/states?year=2023', name: 'Performance Estados' },
            ];
            
            let results = '';
            
            for (const endpoint of endpoints) {
                try {
                    const response = await fetch(`${API_BASE}${endpoint.url}`);
                    const status = response.ok ? 'success' : 'error';
                    const statusText = response.ok ? '✅ OK' : `❌ ${response.status}`;
                    
                    results += `<div class="status ${status}">${endpoint.name}: ${statusText}</div>`;
                } catch (error) {
                    results += `<div class="status error">${endpoint.name}: ❌ Error de conexión</div>`;
                }
            }
            
            testsDiv.innerHTML = results;
        }
        
        // Load all dashboard data
        function loadDashboardData() {
            checkSystemHealth();
            loadMetrics();
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
        });
    </script>
</body>
</html>
    """
    
    with open('/Users/robertodavila/Falcon-miniapp-bot/test_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Dashboard de prueba creado: test_dashboard.html")

def main():
    """Main test function"""
    print("🧪 FALCON MINIAPP BOT - PRUEBA DE FUNCIONALIDAD")
    print("=" * 50)
    
    # Test database
    years_with_data = test_database_connection()
    
    if years_with_data:
        print(f"\n✅ Base de datos OK - Datos disponibles para: {years_with_data}")
        
        # Create test dashboard
        create_test_dashboard()
        
        print(f"\n🌐 Para probar el dashboard:")
        print(f"1. Asegúrate de que la aplicación v4 esté corriendo en puerto 5002")
        print(f"2. Abre: file:///Users/robertodavila/Falcon-miniapp-bot/test_dashboard.html")
        print(f"3. O ejecuta: open /Users/robertodavila/Falcon-miniapp-bot/test_dashboard.html")
        
    else:
        print("\n❌ Problemas con la base de datos")
        print("Verifica la configuración de DATABASE_URL en .env")

if __name__ == "__main__":
    main()