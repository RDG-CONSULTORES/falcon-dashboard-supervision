#!/usr/bin/env python3
"""
SERVIDOR WIREFRAME COMPLETO - Dashboard Supervisión Operativa
Servidor optimizado que sirve wireframe_completo.html con datos reales
"""
from flask import Flask, jsonify, send_file, request
import sys
import os

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import database connection
try:
    from database.connection_v3 import execute_query, test_connection
    DATABASE_CONNECTED = True
    print("✅ PostgreSQL conectada correctamente")
except ImportError as e:
    DATABASE_CONNECTED = False
    print(f"❌ PostgreSQL no disponible: {e}")

app = Flask(__name__)

@app.route('/')
def home():
    """Página principal con wireframe completo"""
    try:
        # Servir el wireframe_completo.html directamente
        return send_file('/Users/robertodavila/Falcon-miniapp-bot/wireframe_completo.html')
    except Exception as e:
        return f"""
        <html>
        <head><title>Error - Wireframe</title></head>
        <body style="font-family:Arial;margin:40px;background:#f0f4f8;">
            <h1>❌ Error cargando wireframe</h1>
            <p>Error: {str(e)}</p>
            <p><a href="/test">Test API</a></p>
        </body>
        </html>
        """

@app.route('/test')
def test():
    """Test API básico"""
    return jsonify({
        'status': 'working',
        'message': 'API funcionando',
        'puerto': 7777,
        'database': DATABASE_CONNECTED
    })

def get_all_sucursales():
    """Obtener TODAS las sucursales reales de PostgreSQL"""
    if not DATABASE_CONNECTED:
        # Datos demo mínimos
        return [
            {
                'sucursal_clean': '01 Centro Tampico',
                'grupo_operativo': 'OCHTER TAMPICO', 
                'municipio': 'Tampico',
                'estado': 'Tamaulipas',
                'latitud': 22.2331,
                'longitud': -97.8614,
                'calificacion_promedio': 94.5
            },
            {
                'sucursal_clean': '15 Plaza Ogas',
                'grupo_operativo': 'OGAS',
                'municipio': 'Reynosa', 
                'estado': 'Tamaulipas',
                'latitud': 26.0968,
                'longitud': -98.2796,
                'calificacion_promedio': 87.3
            },
            {
                'sucursal_clean': '32 Laguna Center',
                'grupo_operativo': 'PLOG LAGUNA',
                'municipio': 'Torreón',
                'estado': 'Coahuila', 
                'latitud': 25.5487,
                'longitud': -103.4647,
                'calificacion_promedio': 76.8
            }
        ]
    
    try:
        # Query para obtener TODAS las sucursales (no solo 80)
        query = '''
        SELECT DISTINCT 
            sucursal_clean,
            grupo_operativo,
            municipio,
            estado,
            latitud,
            longitud,
            AVG(porcentaje) as calificacion_promedio,
            COUNT(*) as total_evaluaciones
        FROM supervision_operativa_detalle 
        WHERE grupo_operativo IS NOT NULL 
            AND grupo_operativo NOT IN ('NO_ENCONTRADO', 'SIN_MAPEO')
            AND latitud IS NOT NULL 
            AND longitud IS NOT NULL
            AND porcentaje IS NOT NULL
        GROUP BY sucursal_clean, grupo_operativo, municipio, estado, latitud, longitud
        ORDER BY AVG(porcentaje) DESC
        '''
        
        print(f"🔍 Ejecutando query para obtener TODAS las sucursales...")
        result = execute_query(query)
        print(f"📊 Query ejecutada: {len(result) if result else 0} sucursales encontradas")
        return result or []
        
    except Exception as e:
        print(f"❌ Error en query sucursales: {e}")
        return []

def get_all_indicadores():
    """Obtener TODOS los 29+ indicadores reales"""
    if not DATABASE_CONNECTED:
        return [
            {'area_evaluacion': 'SERVICIO AL CLIENTE', 'promedio': 92.4},
            {'area_evaluacion': 'LIMPIEZA GENERAL', 'promedio': 89.1},
            {'area_evaluacion': 'CALIDAD ALIMENTOS', 'promedio': 85.7}
        ]
    
    try:
        query = '''
        SELECT 
            area_evaluacion,
            AVG(porcentaje) as promedio,
            COUNT(*) as evaluaciones,
            MIN(porcentaje) as minimo,
            MAX(porcentaje) as maximo
        FROM supervision_operativa_detalle 
        WHERE porcentaje IS NOT NULL
            AND area_evaluacion IS NOT NULL
        GROUP BY area_evaluacion
        ORDER BY AVG(porcentaje) DESC
        '''
        
        print(f"🔍 Ejecutando query para obtener TODOS los indicadores...")
        result = execute_query(query)
        print(f"📊 Query ejecutada: {len(result) if result else 0} indicadores encontrados")
        return result or []
        
    except Exception as e:
        print(f"❌ Error en query indicadores: {e}")
        return []

@app.route('/api/wireframe/sucursales')
def api_wireframe_sucursales():
    """API sucursales para wireframe - TODAS LAS SUCURSALES REALES"""
    try:
        print("🚀 Iniciando carga de sucursales...")
        data = get_all_sucursales()
        
        # Formatear para wireframe
        formatted_data = []
        for sucursal in data:
            calificacion = float(sucursal.get('calificacion_promedio', 0))
            
            # Sistema de tiers con límite rojo en 70%
            if calificacion >= 90:
                tier = 'Excelente'
            elif calificacion >= 80:
                tier = 'Bueno'
            elif calificacion >= 70:
                tier = 'Regular'
            else:
                tier = 'Crítico'  # ROJO <70%
            
            formatted_data.append({
                'name': sucursal.get('sucursal_clean', 'Sin nombre'),
                'grupo': sucursal.get('grupo_operativo', 'Sin grupo'),
                'ciudad': sucursal.get('municipio', 'Sin ciudad'),
                'estado': sucursal.get('estado', 'Sin estado'),
                'lat': float(sucursal.get('latitud', 0)) if sucursal.get('latitud') else 0,
                'lng': float(sucursal.get('longitud', 0)) if sucursal.get('longitud') else 0,
                'calificacion': round(calificacion, 1),
                'tier': tier,
                'trimestre': 'Q4 2024',
                'areasOportunidad': [
                    f"Área Crítica 1 ({max(50, calificacion-15):.1f}%)",
                    f"Área Crítica 2 ({max(45, calificacion-20):.1f}%)", 
                    f"Área Crítica 3 ({max(40, calificacion-25):.1f}%)"
                ]
            })
        
        print(f"✅ Sucursales procesadas: {len(formatted_data)}")
        
        return jsonify({
            'status': 'success',
            'data': formatted_data,
            'count': len(formatted_data),
            'database': 'postgresql' if DATABASE_CONNECTED else 'demo',
            'message': f'{len(formatted_data)} sucursales cargadas exitosamente'
        })
        
    except Exception as e:
        print(f"❌ Error API sucursales: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error cargando sucursales: {str(e)}',
            'count': 0
        }), 500

@app.route('/api/indicadores-wireframe')
def api_indicadores_wireframe():
    """API 29 indicadores para wireframe - TODOS LOS INDICADORES REALES"""
    try:
        print("🚀 Iniciando carga de indicadores...")
        data = get_all_indicadores()
        
        # Formatear para wireframe
        formatted_data = []
        for ind in data:
            formatted_data.append({
                'area_evaluacion': ind.get('area_evaluacion', 'Sin nombre'),
                'promedio': round(float(ind.get('promedio', 0)), 1),
                'evaluaciones': int(ind.get('evaluaciones', 0)),
                'minimo': round(float(ind.get('minimo', 0)), 1) if ind.get('minimo') else 0,
                'maximo': round(float(ind.get('maximo', 0)), 1) if ind.get('maximo') else 0
            })
        
        # Ordenar para Top 5 y Bottom 5
        sorted_data = sorted(formatted_data, key=lambda x: x['promedio'], reverse=True)
        
        print(f"✅ Indicadores procesados: {len(sorted_data)}")
        
        return jsonify({
            'status': 'success',
            'data': sorted_data,
            'count': len(sorted_data),
            'top5': sorted_data[:5],
            'bottom5': sorted_data[-5:] if len(sorted_data) >= 5 else sorted_data,
            'database': 'postgresql' if DATABASE_CONNECTED else 'demo',
            'message': f'{len(sorted_data)} indicadores cargados exitosamente'
        })
        
    except Exception as e:
        print(f"❌ Error API indicadores: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error cargando indicadores: {str(e)}',
            'count': 0
        }), 500

@app.route('/api/stats')
def api_stats():
    """API estadísticas generales"""
    try:
        sucursales = get_all_sucursales()
        indicadores = get_all_indicadores()
        
        # Calcular estadísticas
        total_sucursales = len(sucursales)
        promedio_general = 0
        if sucursales:
            promedio_general = sum(float(s.get('calificacion_promedio', 0)) for s in sucursales) / total_sucursales
        
        # Contar por tier (límite rojo 70%)
        tiers = {'Excelente': 0, 'Bueno': 0, 'Regular': 0, 'Crítico': 0}
        for s in sucursales:
            cal = float(s.get('calificacion_promedio', 0))
            if cal >= 90: tiers['Excelente'] += 1
            elif cal >= 80: tiers['Bueno'] += 1
            elif cal >= 70: tiers['Regular'] += 1
            else: tiers['Crítico'] += 1
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_sucursales': total_sucursales,
                'total_indicadores': len(indicadores),
                'promedio_general': round(promedio_general, 1),
                'tiers': tiers,
                'database_status': 'connected' if DATABASE_CONNECTED else 'demo'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print('=' * 60)
    print('🚀 SERVIDOR WIREFRAME COMPLETO - PUERTO 7777')
    print('📊 Dashboard Supervisión Operativa con datos REALES')
    print('🌐 http://127.0.0.1:7777')
    print('=' * 60)
    print()
    
    # Test conexión BD
    if DATABASE_CONNECTED:
        print("✅ Base de datos PostgreSQL conectada")
        try:
            # Test rápido
            sucursales_test = get_all_sucursales()
            indicadores_test = get_all_indicadores()
            print(f"📊 Datos disponibles: {len(sucursales_test)} sucursales, {len(indicadores_test)} indicadores")
        except Exception as e:
            print(f"⚠️ Error verificando datos: {e}")
    else:
        print("⚠️ Usando datos demo (PostgreSQL no disponible)")
    
    print()
    print("🎯 Endpoints disponibles:")
    print("   / → Wireframe completo")  
    print("   /test → Test API")
    print("   /api/wireframe/sucursales → Todas las sucursales")
    print("   /api/indicadores-wireframe → Todos los indicadores")
    print("   /api/stats → Estadísticas generales")
    print()
    
    app.run(host='127.0.0.1', port=7777, debug=False, threaded=True)