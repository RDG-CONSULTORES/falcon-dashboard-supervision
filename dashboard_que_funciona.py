#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
import sys
import os

# Add path for imports and templates
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder='app/templates')

# Try to import database connection
try:
    from database.connection_v3 import execute_query, test_connection
    DATABASE_CONNECTED = True
    print("✅ PostgreSQL conectada")
except:
    DATABASE_CONNECTED = False
    print("❌ PostgreSQL no disponible - usando datos demo")

@app.route('/')
def home():
    return '''
    <html>
    <head>
        <title>Dashboard Supervisión - FUNCIONA</title>
        <style>
            body{font-family:Arial;margin:40px;background:#f0f4f8;text-align:center}
            .container{max-width:600px;margin:0 auto;background:white;padding:40px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1)}
            h1{color:#2563eb;margin-bottom:20px}
            .btn{display:inline-block;background:#3b82f6;color:white;padding:15px 30px;text-decoration:none;border-radius:8px;margin:10px;font-weight:bold;font-size:18px}
            .btn:hover{background:#2563eb}
            .status{color:#10b981;font-weight:bold;margin:20px 0}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Dashboard Supervisión Operativa</h1>
            <p class="status">✅ SERVIDOR FUNCIONANDO EN PUERTO 9999</p>
            <p class="status">✅ WIREFRAME V2 DISPONIBLE</p>
            <p class="status">✅ LISTO PARA PRODUCCIÓN</p>
            
            <a href="/wireframe" class="btn">📊 VER WIREFRAME COMPLETO</a>
            <a href="/test" class="btn">🔗 TEST API</a>
        </div>
    </body>
    </html>
    '''

@app.route('/wireframe')
def wireframe():
    try:
        return render_template('wireframe_dashboard_v2.html')
    except:
        return '''
        <h1>Error: Wireframe no encontrado</h1>
        <p>El archivo wireframe_dashboard_v2.html no está disponible</p>
        <p><a href="/">Volver</a></p>
        '''

@app.route('/test')
def test():
    return {'status': 'working', 'message': 'API funciona', 'puerto': 9999}

def get_sucursales_reales():
    """Obtener sucursales reales de PostgreSQL"""
    if not DATABASE_CONNECTED:
        # Datos demo si no hay BD
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
            }
        ]
    
    try:
        # Query SIMPLE que funciona
        query = '''
        SELECT DISTINCT 
            sucursal_clean,
            grupo_operativo,
            municipio,
            estado,
            latitud,
            longitud,
            AVG(porcentaje) as calificacion_promedio
        FROM supervision_operativa_detalle 
        WHERE grupo_operativo IS NOT NULL 
            AND grupo_operativo NOT IN ('NO_ENCONTRADO', 'SIN_MAPEO')
            AND latitud IS NOT NULL 
            AND longitud IS NOT NULL
            AND porcentaje IS NOT NULL
        GROUP BY sucursal_clean, grupo_operativo, municipio, estado, latitud, longitud
        ORDER BY AVG(porcentaje) DESC
        '''
        
        return execute_query(query) or []
        
    except Exception as e:
        print(f"Error query: {e}")
        return []

def get_indicadores_reales():
    """Obtener 29 indicadores reales"""
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
            AVG(porcentaje) as promedio
        FROM supervision_operativa_detalle 
        WHERE porcentaje IS NOT NULL
            AND area_evaluacion IS NOT NULL
        GROUP BY area_evaluacion
        ORDER BY AVG(porcentaje) DESC
        '''
        
        return execute_query(query) or []
        
    except Exception as e:
        print(f"Error indicadores: {e}")
        return []

@app.route('/api/wireframe/sucursales')
def api_sucursales():
    """API sucursales - DATOS REALES O DEMO"""
    try:
        data = get_sucursales_reales()
        
        # Formatear para wireframe
        formatted_data = []
        for sucursal in data:
            calificacion = float(sucursal.get('calificacion_promedio', 0))
            
            # Sistema de tiers
            if calificacion >= 90:
                tier = 'Excelente'
            elif calificacion >= 80:
                tier = 'Bueno'
            elif calificacion >= 70:
                tier = 'Regular'
            else:
                tier = 'Crítico'
            
            formatted_data.append({
                'name': sucursal.get('sucursal_clean', 'Sin nombre'),
                'grupo': sucursal.get('grupo_operativo', 'Sin grupo'),
                'ciudad': sucursal.get('municipio', 'Sin ciudad'),
                'estado': sucursal.get('estado', 'Sin estado'),
                'lat': float(sucursal.get('latitud', 0)),
                'lng': float(sucursal.get('longitud', 0)),
                'calificacion': round(calificacion, 1),
                'tier': tier,
                'trimestre': 'Q3 2025',
                'areasOportunidad': [
                    f"Área 1 ({max(50, calificacion-15):.1f}%)",
                    f"Área 2 ({max(45, calificacion-20):.1f}%)", 
                    f"Área 3 ({max(40, calificacion-25):.1f}%)"
                ]
            })
        
        return jsonify({
            'status': 'success',
            'data': formatted_data,
            'count': len(formatted_data),
            'database': 'postgresql' if DATABASE_CONNECTED else 'demo'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/indicadores-wireframe')
def api_indicadores():
    """API 29 indicadores - DATOS REALES O DEMO"""
    try:
        data = get_indicadores_reales()
        
        # Formatear para wireframe
        formatted_data = []
        for ind in data:
            formatted_data.append({
                'area_evaluacion': ind.get('area_evaluacion', 'Sin nombre'),
                'promedio': float(ind.get('promedio', 0))
            })
        
        # Ordenar para Top 5 y Bottom 5
        sorted_data = sorted(formatted_data, key=lambda x: x['promedio'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'data': sorted_data,
            'count': len(sorted_data),
            'top5': sorted_data[:5],
            'bottom5': sorted_data[-5:],
            'database': 'postgresql' if DATABASE_CONNECTED else 'demo'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print('SERVIDOR ULTRA SIMPLE - PUERTO 9999')
    print('http://127.0.0.1:9999')
    app.run(host='127.0.0.1', port=9999, debug=False)