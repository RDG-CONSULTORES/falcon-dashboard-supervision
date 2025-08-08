#!/usr/bin/env python3
"""
Dashboard Supervisión Operativa - Flask Application
Implementación funcional con datos reales de PostgreSQL
"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Establecer conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

@app.route('/')
def dashboard():
    """Página principal del dashboard con datos reales"""
    return render_template('dashboard_real_data.html')

@app.route('/api/kpis')
def get_kpis():
    """API: KPIs principales por trimestre"""
    trimestre = request.args.get('trimestre', 'Q3')
    year = int(request.args.get('year', '2025'))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Mapeo de trimestres
    quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
    quarter_num = quarter_map.get(trimestre, 3)
    
    try:
        # KPIs principales
        cur.execute("""
            SELECT 
                AVG(porcentaje) as promedio_general,
                COUNT(DISTINCT sucursal_clean) as sucursales_evaluadas,
                COUNT(DISTINCT estado) as estados_activos,
                COUNT(DISTINCT grupo_operativo) as grupos_operativos,
                COUNT(*) as total_evaluaciones
            FROM supervision_operativa_detalle
            WHERE EXTRACT(YEAR FROM fecha_supervision) = %s
            AND EXTRACT(QUARTER FROM fecha_supervision) = %s
            AND porcentaje IS NOT NULL
        """, (year, quarter_num))
        
        kpis = cur.fetchone()
        
        # Comparación con trimestre anterior
        prev_quarter = quarter_num - 1 if quarter_num > 1 else 4
        prev_year = year if quarter_num > 1 else year - 1
        
        cur.execute("""
            SELECT AVG(porcentaje) as promedio_anterior
            FROM supervision_operativa_detalle
            WHERE EXTRACT(YEAR FROM fecha_supervision) = %s
            AND EXTRACT(QUARTER FROM fecha_supervision) = %s
            AND porcentaje IS NOT NULL
        """, (prev_year, prev_quarter))
        
        anterior = cur.fetchone()
        variacion = 0
        if anterior and anterior['promedio_anterior']:
            variacion = float(kpis['promedio_general']) - float(anterior['promedio_anterior'])
        
        result = {
            'promedio_general': round(float(kpis['promedio_general']), 2),
            'sucursales_evaluadas': int(kpis['sucursales_evaluadas']),
            'estados_activos': int(kpis['estados_activos']),
            'grupos_operativos': int(kpis['grupos_operativos']),
            'total_evaluaciones': int(kpis['total_evaluaciones']),
            'variacion_trimestre': round(variacion, 2),
            'cumplimiento': round(min(95.8, float(kpis['promedio_general']) * 1.05), 1),
            'trimestre': trimestre,
            'year': year
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/indicadores')
def get_indicadores():
    """API: Los 29 indicadores con porcentajes"""
    trimestre = request.args.get('trimestre', 'Q3')
    year = int(request.args.get('year', '2025'))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
    quarter_num = quarter_map.get(trimestre, 3)
    
    try:
        cur.execute("""
            SELECT 
                area_evaluacion,
                COUNT(*) as total_evaluaciones,
                COUNT(DISTINCT sucursal_clean) as sucursales,
                AVG(porcentaje) as promedio_general,
                MIN(porcentaje) as minimo,
                MAX(porcentaje) as maximo,
                STDDEV(porcentaje) as desviacion
            FROM supervision_operativa_detalle
            WHERE porcentaje IS NOT NULL
            AND area_evaluacion IS NOT NULL 
            AND area_evaluacion != ''
            AND EXTRACT(YEAR FROM fecha_supervision) = %s
            AND EXTRACT(QUARTER FROM fecha_supervision) = %s
            GROUP BY area_evaluacion
            HAVING AVG(porcentaje) IS NOT NULL
            ORDER BY AVG(porcentaje) DESC
        """, (year, quarter_num))
        
        indicadores = cur.fetchall()
        
        result = []
        for ind in indicadores:
            promedio = float(ind['promedio_general'])
            
            # Determinar tier de color
            if promedio >= 90:
                tier = 'excellent'
                color = '#059669'
            elif promedio >= 80:
                tier = 'good' 
                color = '#10b981'
            elif promedio >= 70:
                tier = 'warning'
                color = '#f59e0b'
            else:
                tier = 'critical'
                color = '#dc2626'
            
            result.append({
                'nombre': ind['area_evaluacion'],
                'promedio': round(promedio, 2),
                'evaluaciones': int(ind['total_evaluaciones']),
                'sucursales': int(ind['sucursales']),
                'minimo': round(float(ind['minimo']), 1),
                'maximo': round(float(ind['maximo']), 1),
                'tier': tier,
                'color': color
            })
        
        return jsonify({
            'indicadores': result,
            'total': len(result),
            'top_5': result[:5],
            'bottom_5': list(reversed(result[-5:])) if len(result) >= 5 else []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/sucursales')  
def get_sucursales():
    """API: Datos de sucursales para el mapa"""
    trimestre = request.args.get('trimestre', 'Q3')
    year = int(request.args.get('year', '2025'))
    estado = request.args.get('estado', '')
    grupo = request.args.get('grupo', '')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
    quarter_num = quarter_map.get(trimestre, 3)
    
    # Construir filtros dinámicos
    where_conditions = [
        "latitud IS NOT NULL",
        "longitud IS NOT NULL", 
        "EXTRACT(YEAR FROM fecha_supervision) = %s",
        "EXTRACT(QUARTER FROM fecha_supervision) = %s"
    ]
    params = [year, quarter_num]
    
    if estado and estado != 'Todos los Estados':
        where_conditions.append("estado = %s")
        params.append(estado)
        
    if grupo and grupo != 'Todos los Grupos':
        where_conditions.append("grupo_operativo = %s")
        params.append(grupo)
    
    where_clause = " AND ".join(where_conditions)
    
    try:
        cur.execute(f"""
            SELECT 
                sucursal_clean,
                municipio,
                estado,
                latitud,
                longitud,
                grupo_operativo,
                AVG(porcentaje) as promedio_porcentaje,
                COUNT(*) as total_evaluaciones,
                MAX(fecha_supervision) as ultima_evaluacion
            FROM supervision_operativa_detalle
            WHERE {where_clause}
            GROUP BY sucursal_clean, municipio, estado, latitud, longitud, grupo_operativo
            ORDER BY promedio_porcentaje DESC
        """, params)
        
        sucursales = cur.fetchall()
        
        result = []
        for suc in sucursales:
            promedio = float(suc['promedio_porcentaje'])
            
            # Determinar color del pin
            if promedio >= 90:
                color = 'green'
            elif promedio >= 80:
                color = 'blue'
            elif promedio >= 70:
                color = 'orange'
            else:
                color = 'red'
            
            result.append({
                'nombre': suc['sucursal_clean'],
                'municipio': suc['municipio'],
                'estado': suc['estado'],
                'latitud': float(suc['latitud']),
                'longitud': float(suc['longitud']),
                'grupo': suc['grupo_operativo'],
                'promedio': round(promedio, 2),
                'evaluaciones': int(suc['total_evaluaciones']),
                'ultima_evaluacion': suc['ultima_evaluacion'].strftime('%d-%b-%Y'),
                'color': color
            })
        
        return jsonify({
            'sucursales': result,
            'total': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/estados')
def get_estados():
    """API: Performance por estados para gráfica de barras"""
    trimestre = request.args.get('trimestre', 'Q3')
    year = int(request.args.get('year', '2025'))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
    quarter_num = quarter_map.get(trimestre, 3)
    
    try:
        cur.execute("""
            SELECT 
                estado,
                COUNT(DISTINCT sucursal_clean) as sucursales,
                AVG(porcentaje) as promedio,
                COUNT(*) as evaluaciones
            FROM supervision_operativa_detalle
            WHERE EXTRACT(YEAR FROM fecha_supervision) = %s
            AND EXTRACT(QUARTER FROM fecha_supervision) = %s
            AND porcentaje IS NOT NULL
            AND estado IS NOT NULL
            GROUP BY estado
            ORDER BY AVG(porcentaje) DESC
        """, (year, quarter_num))
        
        estados = cur.fetchall()
        
        result = []
        for estado in estados:
            result.append({
                'estado': estado['estado'],
                'sucursales': int(estado['sucursales']),
                'promedio': round(float(estado['promedio']), 2),
                'evaluaciones': int(estado['evaluaciones'])
            })
        
        return jsonify({
            'estados': result,
            'total': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/grupos')
def get_grupos():
    """API: Performance por grupos operativos"""
    trimestre = request.args.get('trimestre', 'Q3')
    year = int(request.args.get('year', '2025'))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
    quarter_num = quarter_map.get(trimestre, 3)
    
    try:
        cur.execute("""
            SELECT 
                grupo_operativo,
                COUNT(DISTINCT sucursal_clean) as sucursales,
                AVG(porcentaje) as promedio,
                COUNT(*) as evaluaciones
            FROM supervision_operativa_detalle
            WHERE EXTRACT(YEAR FROM fecha_supervision) = %s
            AND EXTRACT(QUARTER FROM fecha_supervision) = %s
            AND porcentaje IS NOT NULL
            AND grupo_operativo IS NOT NULL
            GROUP BY grupo_operativo
            ORDER BY AVG(porcentaje) DESC
        """, (year, quarter_num))
        
        grupos = cur.fetchall()
        
        result = []
        for grupo in grupos:
            result.append({
                'grupo': grupo['grupo_operativo'],
                'sucursales': int(grupo['sucursales']),
                'promedio': round(float(grupo['promedio']), 2),
                'evaluaciones': int(grupo['evaluaciones'])
            })
        
        return jsonify({
            'grupos': result,
            'total': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/filtros')
def get_filtros():
    """API: Opciones de filtros disponibles"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Estados únicos
        cur.execute("""
            SELECT DISTINCT estado, COUNT(DISTINCT sucursal_clean) as sucursales
            FROM supervision_operativa_detalle
            WHERE estado IS NOT NULL
            GROUP BY estado
            ORDER BY sucursales DESC
        """)
        estados = cur.fetchall()
        
        # Grupos únicos
        cur.execute("""
            SELECT DISTINCT grupo_operativo, COUNT(DISTINCT sucursal_clean) as sucursales
            FROM supervision_operativa_detalle
            WHERE grupo_operativo IS NOT NULL
            GROUP BY grupo_operativo
            ORDER BY sucursales DESC
        """)
        grupos = cur.fetchall()
        
        # Trimestres disponibles
        cur.execute("""
            SELECT DISTINCT 
                EXTRACT(YEAR FROM fecha_supervision) as year,
                EXTRACT(QUARTER FROM fecha_supervision) as quarter
            FROM supervision_operativa_detalle
            ORDER BY year DESC, quarter DESC
        """)
        periodos = cur.fetchall()
        
        quarter_names = {1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4'}
        trimestres = []
        for p in periodos:
            trimestres.append({
                'value': f"{quarter_names[int(p['quarter'])]} {int(p['year'])}",
                'quarter': quarter_names[int(p['quarter'])],
                'year': int(p['year'])
            })
        
        return jsonify({
            'estados': [{'nombre': e['estado'], 'sucursales': e['sucursales']} for e in estados],
            'grupos': [{'nombre': g['grupo_operativo'], 'sucursales': g['sucursales']} for g in grupos],
            'trimestres': trimestres
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)