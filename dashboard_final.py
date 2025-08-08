#!/usr/bin/env python3
"""
Dashboard Final - Supervisión Operativa con Sistema de Tiers
Conexión real a PostgreSQL con datos reales
"""

import os
import sys
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database.connection_v3 import execute_query, test_connection
    DATABASE_AVAILABLE = True
    print("✅ Conexión a base de datos disponible")
except ImportError as e:
    DATABASE_AVAILABLE = False
    print(f"❌ Error importando database: {e}")

app = Flask(__name__)
CORS(app)

class DashboardData:
    """Clase para manejar los datos del dashboard"""
    
    @staticmethod
    def get_sucursales_with_tiers():
        """Obtener sucursales con sistema de tiers desde la BD real"""
        if not DATABASE_AVAILABLE:
            return []
        
        try:
            query = '''
            WITH latest_supervision AS (
                SELECT DISTINCT 
                    sucursal_clean,
                    grupo_operativo,
                    municipio,
                    estado,
                    latitud,
                    longitud,
                    MAX(fecha_supervision) as ultima_fecha
                FROM supervision_operativa_detalle 
                WHERE grupo_operativo IS NOT NULL 
                    AND grupo_operativo NOT IN ('NO_ENCONTRADO', 'SIN_MAPEO')
                    AND latitud IS NOT NULL 
                    AND longitud IS NOT NULL
                    AND fecha_supervision >= NOW() - INTERVAL '90 days'
                GROUP BY sucursal_clean, grupo_operativo, municipio, estado, latitud, longitud
            ),
            sucursal_performance AS (
                SELECT 
                    ls.sucursal_clean,
                    ls.grupo_operativo,
                    ls.municipio,
                    ls.estado,
                    ls.latitud,
                    ls.longitud,
                    ls.ultima_fecha,
                    AVG(sod.porcentaje) as calificacion_promedio,
                    COUNT(DISTINCT sod.area_evaluacion) as areas_evaluadas,
                    COUNT(*) as total_evaluaciones
                FROM latest_supervision ls
                LEFT JOIN supervision_operativa_detalle sod ON ls.sucursal_clean = sod.sucursal_clean 
                    AND sod.fecha_supervision >= ls.ultima_fecha - INTERVAL '7 days'
                GROUP BY ls.sucursal_clean, ls.grupo_operativo, ls.municipio, ls.estado, 
                         ls.latitud, ls.longitud, ls.ultima_fecha
                HAVING AVG(sod.porcentaje) IS NOT NULL
            ),
            areas_oportunidad AS (
                SELECT 
                    sucursal_clean,
                    area_evaluacion,
                    AVG(porcentaje) as promedio_area,
                    ROW_NUMBER() OVER (PARTITION BY sucursal_clean ORDER BY AVG(porcentaje) ASC) as rank_bajo
                FROM supervision_operativa_detalle 
                WHERE fecha_supervision >= NOW() - INTERVAL '30 days'
                GROUP BY sucursal_clean, area_evaluacion
            )
            SELECT 
                sp.*,
                -- Sistema de Tiers
                CASE 
                    WHEN sp.calificacion_promedio >= 90 THEN 'Tier 1 - Excelente'
                    WHEN sp.calificacion_promedio >= 80 THEN 'Tier 2 - Bueno'
                    WHEN sp.calificacion_promedio >= 70 THEN 'Tier 3 - Regular'
                    ELSE 'Tier 4 - Crítico'
                END as tier,
                -- Trimestre
                CASE 
                    WHEN EXTRACT(QUARTER FROM sp.ultima_fecha) = 1 THEN 'Q1'
                    WHEN EXTRACT(QUARTER FROM sp.ultima_fecha) = 2 THEN 'Q2'  
                    WHEN EXTRACT(QUARTER FROM sp.ultima_fecha) = 3 THEN 'Q3'
                    ELSE 'Q4'
                END || ' ' || EXTRACT(YEAR FROM sp.ultima_fecha) as trimestre,
                -- Top 3 áreas de oportunidad
                STRING_AGG(
                    ao.area_evaluacion || ' (' || ROUND(ao.promedio_area, 1) || '%)', 
                    ', ' ORDER BY ao.promedio_area ASC
                ) as areas_oportunidad
            FROM sucursal_performance sp
            LEFT JOIN areas_oportunidad ao ON sp.sucursal_clean = ao.sucursal_clean 
                AND ao.rank_bajo <= 3
            GROUP BY sp.sucursal_clean, sp.grupo_operativo, sp.municipio, sp.estado, 
                     sp.latitud, sp.longitud, sp.ultima_fecha, sp.calificacion_promedio, 
                     sp.areas_evaluadas, sp.total_evaluaciones
            ORDER BY sp.calificacion_promedio DESC
            LIMIT 100
            '''
            
            return execute_query(query) or []
            
        except Exception as e:
            print(f"Error obteniendo sucursales: {e}")
            return []
    
    @staticmethod
    def get_indicadores_performance():
        """Obtener performance de los 29 indicadores reales"""
        if not DATABASE_AVAILABLE:
            return []
        
        try:
            query = '''
            SELECT 
                area_evaluacion,
                AVG(porcentaje) as promedio,
                COUNT(*) as total_evaluaciones,
                MIN(porcentaje) as minimo,
                MAX(porcentaje) as maximo,
                STDDEV(porcentaje) as desviacion_std
            FROM supervision_operativa_detalle 
            WHERE fecha_supervision >= NOW() - INTERVAL '90 days'
                AND porcentaje IS NOT NULL
            GROUP BY area_evaluacion
            HAVING COUNT(*) >= 5  -- Al menos 5 evaluaciones
            ORDER BY AVG(porcentaje) DESC
            '''
            
            return execute_query(query) or []
            
        except Exception as e:
            print(f"Error obteniendo indicadores: {e}")
            return []
    
    @staticmethod
    def get_grupos_operativos():
        """Obtener lista de grupos operativos únicos"""
        if not DATABASE_AVAILABLE:
            return []
        
        try:
            query = '''
            SELECT DISTINCT grupo_operativo
            FROM supervision_operativa_detalle 
            WHERE grupo_operativo IS NOT NULL 
                AND grupo_operativo NOT IN ('NO_ENCONTRADO', 'SIN_MAPEO')
            ORDER BY grupo_operativo
            '''
            
            result = execute_query(query)
            return [row['grupo_operativo'] for row in result] if result else []
            
        except Exception as e:
            print(f"Error obteniendo grupos: {e}")
            return []

@app.route('/')
def home():
    """Página principal del dashboard"""
    db_status = test_connection() if DATABASE_AVAILABLE else False
    
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚀 Dashboard Final - Supervisión Operativa</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #f8fafc; }}
            .container {{ max-width: 1000px; margin: 0 auto; padding: 2rem; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 1rem; margin-bottom: 2rem; text-align: center; }}
            .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: 2rem 0; }}
            .status-card {{ background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .status-success {{ border-left: 4px solid #10b981; }}
            .status-error {{ border-left: 4px solid #ef4444; }}
            .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 0.5rem; margin: 0.5rem; font-weight: 500; transition: background-color 0.2s; }}
            .btn:hover {{ background: #2563eb; }}
            .btn-success {{ background: #10b981; }}
            .btn-success:hover {{ background: #059669; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Dashboard Final - Supervisión Operativa</h1>
                <p>Sistema completo de tiers con conexión real a PostgreSQL</p>
            </div>
            
            <div class="status-grid">
                <div class="status-card {'status-success' if DATABASE_AVAILABLE else 'status-error'}">
                    <h3>🗄️ Base de Datos</h3>
                    <p><strong>Estado:</strong> {'✅ Conectada' if db_status else '❌ Desconectada'}</p>
                    <p><strong>Tipo:</strong> {'PostgreSQL Real' if DATABASE_AVAILABLE else 'No disponible'}</p>
                </div>
                
                <div class="status-card status-success">
                    <h3>🏆 Sistema de Tiers</h3>
                    <p><strong>Tier 1:</strong> 90%+ Excelente</p>
                    <p><strong>Tier 2:</strong> 80-90% Bueno</p>
                    <p><strong>Tier 3:</strong> 70-80% Regular</p>
                    <p><strong>Tier 4:</strong> <70% Crítico</p>
                </div>
                
                <div class="status-card status-success">
                    <h3>📊 Funcionalidades</h3>
                    <p>✅ Mapas interactivos con tiers</p>
                    <p>✅ 29 Indicadores reales</p>
                    <p>✅ Filtros dinámicos</p>
                    <p>✅ Áreas de oportunidad</p>
                </div>
                
                <div class="status-card status-success">
                    <h3>🔧 APIs</h3>
                    <p>✅ /api/sucursales-tiers</p>
                    <p>✅ /api/indicadores-reales</p>
                    <p>✅ /api/grupos-operativos</p>
                    <p>✅ /api/health</p>
                </div>
            </div>
            
            <div style="text-align: center; margin: 3rem 0;">
                <a href="/dashboard" class="btn btn-success">🎯 ABRIR DASHBOARD COMPLETO</a>
                <a href="/api/health" class="btn">🏥 Health Check</a>
                <a href="/api/sucursales-tiers" class="btn">🔗 API Sucursales</a>
                <a href="/api/indicadores-reales" class="btn">📈 API Indicadores</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/dashboard')
def dashboard():
    """Dashboard principal con tiers"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Supervisión - Sistema de Tiers</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Leaflet Maps -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
        .tier-1 { background: linear-gradient(135deg, #059669, #10b981); color: white; }
        .tier-2 { background: linear-gradient(135deg, #10b981, #34d399); color: white; }
        .tier-3 { background: linear-gradient(135deg, #f59e0b, #fbbf24); color: white; }
        .tier-4 { background: linear-gradient(135deg, #dc2626, #ef4444); color: white; }
        .map-container { height: 450px; border-radius: 0.75rem; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .loading { display: inline-block; width: 24px; height: 24px; border: 3px solid #f3f3f3; border-top: 3px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .tier-badge { font-size: 0.75rem; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 600; }
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <div class="gradient-bg text-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <h1 class="text-3xl font-bold">🚀 Dashboard Supervisión Operativa</h1>
            <p class="text-blue-100 mt-2">Sistema de Tiers con datos reales en tiempo real</p>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        <!-- Loading State -->
        <div id="loading" class="text-center py-12">
            <div class="loading mx-auto mb-4"></div>
            <p class="text-gray-600">Cargando datos desde PostgreSQL...</p>
        </div>

        <!-- Error State -->
        <div id="error" class="hidden bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Error de Conexión</h3>
                    <div class="mt-2 text-sm text-red-700">
                        <p id="error-message">No se pudo conectar con la base de datos.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div id="content" class="hidden space-y-8">
            
            <!-- KPIs Tiers -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6" id="kpis-container">
                <!-- Populated by JavaScript -->
            </div>

            <!-- Filters -->
            <div class="bg-white rounded-xl shadow-sm p-6">
                <h3 class="text-lg font-semibold mb-4 flex items-center">
                    <svg class="w-5 h-5 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"></path>
                    </svg>
                    Filtros Dinámicos
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <select id="filter-tier" class="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        <option value="">Todos los Tiers</option>
                        <option value="Tier 1">🏆 Tier 1 - Excelente</option>
                        <option value="Tier 2">⭐ Tier 2 - Bueno</option>
                        <option value="Tier 3">⚠️ Tier 3 - Regular</option>
                        <option value="Tier 4">🚨 Tier 4 - Crítico</option>
                    </select>
                    
                    <select id="filter-estado" class="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        <option value="">Todos los Estados</option>
                    </select>
                    
                    <select id="filter-grupo" class="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        <option value="">Todos los Grupos</option>
                    </select>
                    
                    <button onclick="aplicarFiltros()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                        Aplicar Filtros
                    </button>
                    
                    <button onclick="resetearFiltros()" class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                        Resetear
                    </button>
                </div>
            </div>

            <!-- Dashboard Grid -->
            <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
                
                <!-- Mapa -->
                <div class="xl:col-span-2 bg-white rounded-xl shadow-sm p-6">
                    <h3 class="text-lg font-semibold mb-4 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3"></path>
                        </svg>
                        Mapa de Sucursales por Tiers
                    </h3>
                    <div id="map" class="map-container"></div>
                    
                    <!-- Legend -->
                    <div class="mt-4 flex flex-wrap gap-2">
                        <span class="tier-badge tier-1">🏆 Tier 1 (90%+)</span>
                        <span class="tier-badge tier-2">⭐ Tier 2 (80-90%)</span>
                        <span class="tier-badge tier-3">⚠️ Tier 3 (70-80%)</span>
                        <span class="tier-badge tier-4">🚨 Tier 4 (<70%)</span>
                    </div>
                </div>

                <!-- Indicadores -->
                <div class="bg-white rounded-xl shadow-sm p-6">
                    <h3 class="text-lg font-semibold mb-4 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                        Top 5 y Áreas de Oportunidad
                    </h3>
                    <div id="indicadores-container" class="space-y-4">
                        <!-- Populated by JavaScript -->
                    </div>
                </div>
            </div>

            <!-- Tabla de Sucursales -->
            <div class="bg-white rounded-xl shadow-sm p-6">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-lg font-semibold flex items-center">
                        <svg class="w-5 h-5 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                        </svg>
                        Lista de Sucursales por Performance
                    </h3>
                    <span id="sucursales-count" class="text-sm text-gray-500 font-medium"></span>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sucursal</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tier</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Calificación</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grupo Operativo</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ubicación</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Áreas de Oportunidad</th>
                            </tr>
                        </thead>
                        <tbody id="sucursales-table" class="bg-white divide-y divide-gray-200">
                            <!-- Populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    </div>

    <script>
        // Variables globales
        let todasSucursales = [];
        let todosIndicadores = [];
        let mapa = null;
        let capaMarcadores = null;

        // Inicializar dashboard
        document.addEventListener('DOMContentLoaded', cargarDashboard);

        async function cargarDashboard() {
            try {
                console.log('Cargando datos del dashboard...');
                
                // Cargar datos de sucursales con tiers
                const respuestaSucursales = await fetch('/api/sucursales-tiers');
                const datosSucursales = await respuestaSucursales.json();
                
                // Cargar indicadores
                const respuestaIndicadores = await fetch('/api/indicadores-reales');
                const datosIndicadores = await respuestaIndicadores.json();
                
                if (datosSucursales.status === 'success' && datosIndicadores.status === 'success') {
                    todasSucursales = datosSucursales.data;
                    todosIndicadores = datosIndicadores.data;
                    
                    // Ocultar loading, mostrar contenido
                    document.getElementById('loading').classList.add('hidden');
                    document.getElementById('content').classList.remove('hidden');
                    
                    // Inicializar componentes
                    inicializarKPIs();
                    inicializarFiltros();
                    inicializarMapa();
                    cargarIndicadores();
                    cargarTablaSucursales();
                    
                    console.log(`Dashboard cargado: ${todasSucursales.length} sucursales, ${todosIndicadores.length} indicadores`);
                    
                } else {
                    throw new Error('Error en las APIs: ' + (datosSucursales.message || datosIndicadores.message));
                }
                
            } catch (error) {
                console.error('Error cargando dashboard:', error);
                mostrarError(error.message);
            }
        }

        function mostrarError(mensaje) {
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('error').classList.remove('hidden');
            document.getElementById('error-message').textContent = mensaje;
        }

        function inicializarKPIs() {
            const tiers = {
                tier1: todasSucursales.filter(s => s.tier && s.tier.includes('Tier 1')).length,
                tier2: todasSucursales.filter(s => s.tier && s.tier.includes('Tier 2')).length,
                tier3: todasSucursales.filter(s => s.tier && s.tier.includes('Tier 3')).length,
                tier4: todasSucursales.filter(s => s.tier && s.tier.includes('Tier 4')).length
            };

            const kpisContainer = document.getElementById('kpis-container');
            const kpis = [
                { label: 'Tier 1 - Excelente', value: tiers.tier1, clase: 'tier-1', icono: '🏆' },
                { label: 'Tier 2 - Bueno', value: tiers.tier2, clase: 'tier-2', icono: '⭐' },
                { label: 'Tier 3 - Regular', value: tiers.tier3, clase: 'tier-3', icono: '⚠️' },
                { label: 'Tier 4 - Crítico', value: tiers.tier4, clase: 'tier-4', icono: '🚨' }
            ];

            kpisContainer.innerHTML = kpis.map(kpi => `
                <div class="${kpi.clase} rounded-xl shadow-sm p-6 text-center transition-transform hover:scale-105">
                    <div class="text-3xl mb-2">${kpi.icono}</div>
                    <div class="text-3xl font-bold">${kpi.value}</div>
                    <div class="text-sm opacity-90 mt-1">${kpi.label}</div>
                </div>
            `).join('');
        }

        function inicializarFiltros() {
            // Obtener valores únicos para filtros
            const estados = [...new Set(todasSucursales.map(s => s.estado).filter(Boolean))].sort();
            const grupos = [...new Set(todasSucursales.map(s => s.grupo_operativo).filter(Boolean))].sort();

            // Poblar filtro de estados
            const selectEstado = document.getElementById('filter-estado');
            selectEstado.innerHTML = '<option value="">Todos los Estados</option>' +
                estados.map(estado => `<option value="${estado}">${estado}</option>`).join('');

            // Poblar filtro de grupos
            const selectGrupo = document.getElementById('filter-grupo');
            selectGrupo.innerHTML = '<option value="">Todos los Grupos</option>' +
                grupos.map(grupo => `<option value="${grupo}">${grupo}</option>`).join('');
        }

        function inicializarMapa() {
            // Crear mapa centrado en México
            mapa = L.map('map').setView([23.6345, -102.5528], 5);

            // Agregar tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            }).addTo(mapa);

            actualizarMarcadoresMapa();
        }

        function actualizarMarcadoresMapa() {
            // Limpiar marcadores existentes
            if (capaMarcadores) {
                mapa.removeLayer(capaMarcadores);
            }

            capaMarcadores = L.layerGroup();

            todasSucursales.forEach(sucursal => {
                if (sucursal.latitud && sucursal.longitud) {
                    // Determinar color por tier
                    let color = '#dc2626'; // Tier 4 - Rojo
                    if (sucursal.tier && sucursal.tier.includes('Tier 1')) color = '#059669'; // Verde
                    else if (sucursal.tier && sucursal.tier.includes('Tier 2')) color = '#10b981'; // Verde claro
                    else if (sucursal.tier && sucursal.tier.includes('Tier 3')) color = '#f59e0b'; // Naranja

                    // Crear marcador
                    const marcador = L.circleMarker([sucursal.latitud, sucursal.longitud], {
                        radius: 8,
                        fillColor: color,
                        color: '#fff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.8
                    });

                    // Tooltip
                    const areasOportunidad = sucursal.areas_oportunidad ? 
                        sucursal.areas_oportunidad.split(', ').slice(0, 3) : ['Sin datos'];

                    marcador.bindPopup(`
                        <div class="p-3 min-w-64">
                            <h4 class="font-bold text-lg mb-2">${sucursal.sucursal_clean || 'Sin nombre'}</h4>
                            <div class="space-y-1 text-sm">
                                <p><strong>Tier:</strong> <span class="font-semibold">${sucursal.tier || 'Sin tier'}</span></p>
                                <p><strong>Calificación:</strong> <span class="font-bold text-lg">${sucursal.calificacion_promedio ? Math.round(sucursal.calificacion_promedio * 10) / 10 + '%' : 'N/A'}</span></p>
                                <p><strong>Grupo:</strong> ${sucursal.grupo_operativo || 'Sin grupo'}</p>
                                <p><strong>Ubicación:</strong> ${sucursal.municipio || 'Sin ciudad'}, ${sucursal.estado || 'Sin estado'}</p>
                                <p><strong>Último trimestre:</strong> ${sucursal.trimestre || 'Sin fecha'}</p>
                                <div class="mt-2">
                                    <p><strong>Áreas de Oportunidad:</strong></p>
                                    <ul class="list-disc list-inside text-xs mt-1 space-y-1">
                                        ${areasOportunidad.map(area => `<li>${area}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    `);

                    capaMarcadores.addLayer(marcador);
                }
            });

            mapa.addLayer(capaMarcadores);
        }

        function cargarIndicadores() {
            if (todosIndicadores.length === 0) {
                document.getElementById('indicadores-container').innerHTML = 
                    '<p class="text-gray-500 text-center">No hay datos de indicadores disponibles</p>';
                return;
            }

            // Ordenar indicadores por promedio
            const indicadoresOrdenados = [...todosIndicadores].sort((a, b) => 
                (b.promedio || 0) - (a.promedio || 0)
            );
            
            const top5 = indicadoresOrdenados.slice(0, 5);
            const bottom5 = indicadoresOrdenados.slice(-5).reverse();

            const container = document.getElementById('indicadores-container');
            container.innerHTML = `
                <!-- Top 5 Indicadores -->
                <div>
                    <h4 class="font-medium text-green-700 mb-3 flex items-center">
                        <span class="text-lg mr-2">🏆</span>
                        Top 5 Indicadores
                    </h4>
                    <div class="space-y-2">
                        ${top5.map((indicator, index) => `
                            <div class="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                                <div>
                                    <span class="text-sm font-medium text-gray-900">${index + 1}. ${indicator.area_evaluacion || 'Sin nombre'}</span>
                                    <div class="text-xs text-gray-500">${indicator.total_evaluaciones || 0} evaluaciones</div>
                                </div>
                                <span class="text-sm font-bold text-green-700">${(indicator.promedio || 0).toFixed(1)}%</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Áreas de Oportunidad (Bottom 5) -->
                <div>
                    <h4 class="font-medium text-red-700 mb-3 flex items-center">
                        <span class="text-lg mr-2">🎯</span>
                        Áreas de Oportunidad
                    </h4>
                    <div class="space-y-2">
                        ${bottom5.map((indicator, index) => `
                            <div class="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                                <div>
                                    <span class="text-sm font-medium text-gray-900">${index + 1}. ${indicator.area_evaluacion || 'Sin nombre'}</span>
                                    <div class="text-xs text-gray-500">${indicator.total_evaluaciones || 0} evaluaciones</div>
                                </div>
                                <span class="text-sm font-bold text-red-700">${(indicator.promedio || 0).toFixed(1)}%</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        function cargarTablaSucursales() {
            const tbody = document.getElementById('sucursales-table');
            const countSpan = document.getElementById('sucursales-count');

            // Ordenar sucursales por calificación (descendente)
            const sucursalesOrdenadas = [...todasSucursales].sort((a, b) => 
                (b.calificacion_promedio || 0) - (a.calificacion_promedio || 0)
            );

            countSpan.textContent = `${sucursalesOrdenadas.length} sucursales encontradas`;

            tbody.innerHTML = sucursalesOrdenadas.map(sucursal => {
                // Determinar clase CSS del tier
                let tierClass = 'tier-4';
                if (sucursal.tier && sucursal.tier.includes('Tier 1')) tierClass = 'tier-1';
                else if (sucursal.tier && sucursal.tier.includes('Tier 2')) tierClass = 'tier-2';
                else if (sucursal.tier && sucursal.tier.includes('Tier 3')) tierClass = 'tier-3';

                const areasOportunidad = sucursal.areas_oportunidad ? 
                    sucursal.areas_oportunidad.split(', ').slice(0, 3).join(', ') : 
                    'Sin datos disponibles';

                return `
                    <tr class="hover:bg-gray-50 transition-colors">
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="font-medium text-gray-900">${sucursal.sucursal_clean || 'Sin nombre'}</div>
                            <div class="text-sm text-gray-500">${sucursal.trimestre || 'Sin fecha'}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="tier-badge ${tierClass}">${sucursal.tier || 'Sin tier'}</span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-lg font-bold text-gray-900">
                                ${sucursal.calificacion_promedio ? Math.round(sucursal.calificacion_promedio * 10) / 10 + '%' : 'N/A'}
                            </div>
                            <div class="text-xs text-gray-500">
                                ${sucursal.areas_evaluadas || 0} áreas evaluadas
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ${sucursal.grupo_operativo || 'Sin grupo'}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <div>${sucursal.municipio || 'Sin ciudad'}</div>
                            <div class="text-xs">${sucursal.estado || 'Sin estado'}</div>
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-500">
                            <div class="max-w-xs truncate" title="${areasOportunidad}">
                                ${areasOportunidad}
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function aplicarFiltros() {
            const filtroTier = document.getElementById('filter-tier').value;
            const filtroEstado = document.getElementById('filter-estado').value;
            const filtroGrupo = document.getElementById('filter-grupo').value;

            console.log('Aplicando filtros:', { filtroTier, filtroEstado, filtroGrupo });

            // Filtrar sucursales
            let sucursalesFiltradas = todasSucursales;

            if (filtroTier) {
                sucursalesFiltradas = sucursalesFiltradas.filter(s => 
                    s.tier && s.tier.includes(filtroTier)
                );
            }

            if (filtroEstado) {
                sucursalesFiltradas = sucursalesFiltradas.filter(s => 
                    s.estado === filtroEstado
                );
            }

            if (filtroGrupo) {
                sucursalesFiltradas = sucursalesFiltradas.filter(s => 
                    s.grupo_operativo === filtroGrupo
                );
            }

            // Actualizar datos temporalmente para mostrar filtros
            const sucursalesOriginales = [...todasSucursales];
            todasSucursales = sucursalesFiltradas;

            // Actualizar componentes
            inicializarKPIs();
            cargarTablaSucursales();
            actualizarMarcadoresMapa();

            console.log(`Filtros aplicados: ${sucursalesFiltradas.length}/${sucursalesOriginales.length} sucursales mostradas`);

            // Restaurar datos originales
            todasSucursales = sucursalesOriginales;
        }

        function resetearFiltros() {
            // Limpiar filtros
            document.getElementById('filter-tier').value = '';
            document.getElementById('filter-estado').value = '';
            document.getElementById('filter-grupo').value = '';

            // Recargar datos originales
            inicializarKPIs();
            cargarTablaSucursales();
            actualizarMarcadoresMapa();

            console.log('Filtros reseteados');
        }

        // Manejar errores de red
        window.addEventListener('unhandledrejection', function(event) {
            console.error('Error no manejado:', event.reason);
            mostrarError('Error de conexión: ' + event.reason.message);
        });

    </script>
</body>
</html>
    ''')

@app.route('/api/sucursales-tiers')
def api_sucursales_tiers():
    """API endpoint para sucursales con sistema de tiers"""
    try:
        sucursales = DashboardData.get_sucursales_with_tiers()
        
        if not sucursales:
            return jsonify({
                'status': 'error',
                'message': 'No se encontraron datos de sucursales',
                'data': []
            }), 404

        # Calcular estadísticas de tiers
        tiers_stats = {
            'tier1': len([s for s in sucursales if s.get('tier', '').startswith('Tier 1')]),
            'tier2': len([s for s in sucursales if s.get('tier', '').startswith('Tier 2')]),
            'tier3': len([s for s in sucursales if s.get('tier', '').startswith('Tier 3')]),
            'tier4': len([s for s in sucursales if s.get('tier', '').startswith('Tier 4')])
        }

        return jsonify({
            'status': 'success',
            'data': sucursales,
            'count': len(sucursales),
            'tiers': tiers_stats,
            'database': 'postgresql_real' if DATABASE_AVAILABLE else 'mock',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Error en API sucursales-tiers: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error interno del servidor: {str(e)}',
            'data': []
        }), 500

@app.route('/api/indicadores-reales')
def api_indicadores_reales():
    """API endpoint para los 29 indicadores reales"""
    try:
        indicadores = DashboardData.get_indicadores_performance()
        
        if not indicadores:
            return jsonify({
                'status': 'error',
                'message': 'No se encontraron datos de indicadores',
                'data': []
            }), 404

        # Ordenar por promedio descendente
        indicadores_ordenados = sorted(indicadores, key=lambda x: x.get('promedio', 0), reverse=True)
        
        return jsonify({
            'status': 'success',
            'data': indicadores_ordenados,
            'count': len(indicadores_ordenados),
            'top5': indicadores_ordenados[:5],
            'bottom5': indicadores_ordenados[-5:],
            'database': 'postgresql_real' if DATABASE_AVAILABLE else 'mock',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Error en API indicadores-reales: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error interno del servidor: {str(e)}',
            'data': []
        }), 500

@app.route('/api/grupos-operativos')
def api_grupos_operativos():
    """API endpoint para grupos operativos"""
    try:
        grupos = DashboardData.get_grupos_operativos()
        
        return jsonify({
            'status': 'success',
            'data': grupos,
            'count': len(grupos),
            'database': 'postgresql_real' if DATABASE_AVAILABLE else 'mock',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Error en API grupos-operativos: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error interno del servidor: {str(e)}',
            'data': []
        }), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    db_connected = False
    
    if DATABASE_AVAILABLE:
        try:
            db_connected = test_connection()
        except:
            db_connected = False
    
    return jsonify({
        'status': 'healthy',
        'database': {
            'available': DATABASE_AVAILABLE,
            'connected': db_connected,
            'type': 'postgresql' if DATABASE_AVAILABLE else 'none'
        },
        'apis': {
            'sucursales_tiers': '/api/sucursales-tiers',
            'indicadores_reales': '/api/indicadores-reales', 
            'grupos_operativos': '/api/grupos-operativos'
        },
        'dashboard_url': '/dashboard',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint no encontrado'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Error interno del servidor'
    }), 500

if __name__ == '__main__':
    port = 3030
    
    print('\n' + '='*60)
    print('🚀 DASHBOARD FINAL - SUPERVISIÓN OPERATIVA')
    print('='*60)
    print(f'📊 Dashboard Principal: http://127.0.0.1:{port}/dashboard')
    print(f'🏠 Página de Inicio: http://127.0.0.1:{port}/')
    print(f'🔗 API Sucursales Tiers: http://127.0.0.1:{port}/api/sucursales-tiers')
    print(f'📈 API Indicadores Reales: http://127.0.0.1:{port}/api/indicadores-reales')
    print(f'👥 API Grupos Operativos: http://127.0.0.1:{port}/api/grupos-operativos')
    print(f'🏥 Health Check: http://127.0.0.1:{port}/api/health')
    print('='*60)
    print(f'🗄️ Base de Datos: {"✅ PostgreSQL Conectada" if DATABASE_AVAILABLE and test_connection() else "❌ Sin conexión"}')
    print(f'🏆 Sistema de Tiers: ✅ Implementado')
    print(f'🗺️ Mapas Interactivos: ✅ Leaflet con markers por tier')
    print(f'🔍 Filtros Dinámicos: ✅ Estado, Grupo, Tier')
    print('='*60)
    
    app.run(host='127.0.0.1', port=port, debug=False)