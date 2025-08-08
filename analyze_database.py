#!/usr/bin/env python3
"""
Análisis completo de la base de datos Neon
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Create database connection"""
    return psycopg2.connect(DATABASE_URL)

def analyze_database():
    """Analyze complete database structure"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("🗄️  ANÁLISIS COMPLETO DE BASE DE DATOS NEON")
    print("=" * 80)
    print(f"📅 Fecha: {datetime.now()}")
    print(f"🔗 Conectado a: {DATABASE_URL.split('@')[1].split('/')[0]}")
    print()
    
    # 1. Obtener todas las tablas
    print("📊 1. TABLAS EN LA BASE DE DATOS:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename;
    """)
    
    tables = cur.fetchall()
    for table in tables:
        print(f"   • {table['schemaname']}.{table['tablename']} - Tamaño: {table['size']}")
    
    # 2. Obtener estructura de la tabla principal
    print("\n📋 2. ESTRUCTURA DE LA TABLA PRINCIPAL (supervision_sucursales):")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'supervision_sucursales'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    print(f"\n   Total de columnas: {len(columns)}")
    print("\n   Columnas:")
    for col in columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        print(f"   • {col['column_name']:30} {col['data_type']:15} {nullable}")
    
    # 3. Estadísticas de datos
    print("\n📈 3. ESTADÍSTICAS DE DATOS:")
    print("-" * 80)
    
    # Total de registros
    cur.execute("SELECT COUNT(*) as total FROM supervision_sucursales")
    total = cur.fetchone()
    print(f"\n   Total de registros: {total['total']:,}")
    
    # Registros por año
    cur.execute("""
        SELECT year, COUNT(*) as total 
        FROM supervision_sucursales 
        GROUP BY year 
        ORDER BY year DESC
    """)
    years = cur.fetchall()
    print("\n   Registros por año:")
    for year in years:
        print(f"   • {year['year']}: {year['total']:,} registros")
    
    # Registros por trimestre
    cur.execute("""
        SELECT year, quarter, COUNT(*) as total 
        FROM supervision_sucursales 
        WHERE year >= 2024
        GROUP BY year, quarter 
        ORDER BY year DESC, quarter DESC
        LIMIT 8
    """)
    quarters = cur.fetchall()
    print("\n   Últimos trimestres:")
    for q in quarters:
        print(f"   • {q['year']} {q['quarter']}: {q['total']:,} registros")
    
    # 4. Análisis de campos importantes
    print("\n🔍 4. ANÁLISIS DE CAMPOS CLAVE:")
    print("-" * 80)
    
    # Estados únicos
    cur.execute("SELECT COUNT(DISTINCT estado) as total FROM supervision_sucursales")
    estados = cur.fetchone()
    print(f"\n   Estados únicos: {estados['total']}")
    
    # Grupos operativos
    cur.execute("SELECT COUNT(DISTINCT grupo_operativo) as total FROM supervision_sucursales WHERE grupo_operativo IS NOT NULL")
    grupos = cur.fetchone()
    print(f"   Grupos operativos: {grupos['total']}")
    
    # Sucursales únicas
    cur.execute("SELECT COUNT(DISTINCT sucursal_clean) as total FROM supervision_sucursales")
    sucursales = cur.fetchone()
    print(f"   Sucursales únicas: {sucursales['total']}")
    
    # Áreas de evaluación únicas
    cur.execute("SELECT COUNT(DISTINCT area_evaluacion) as total FROM supervision_sucursales WHERE area_evaluacion IS NOT NULL")
    areas = cur.fetchone()
    print(f"   Áreas de evaluación: {areas['total']}")
    
    # 5. Muestra de datos reales
    print("\n📄 5. MUESTRA DE DATOS REALES (Últimos 5 registros):")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            year,
            quarter,
            estado,
            municipio,
            sucursal_clean,
            grupo_operativo,
            area_evaluacion,
            porcentaje,
            latitud,
            longitud
        FROM supervision_sucursales 
        WHERE year = 2025 AND quarter = 'Q2'
        LIMIT 5
    """)
    
    sample = cur.fetchall()
    for i, row in enumerate(sample, 1):
        print(f"\n   Registro {i}:")
        print(f"   • Periodo: {row['year']} {row['quarter']}")
        print(f"   • Ubicación: {row['sucursal_clean']}, {row['municipio']}, {row['estado']}")
        print(f"   • Grupo: {row['grupo_operativo']}")
        print(f"   • Área: {row['area_evaluacion']}")
        print(f"   • Calificación: {row['porcentaje']}%")
        print(f"   • Coordenadas: ({row['latitud']}, {row['longitud']})")
    
    # 6. KPIs principales
    print("\n💡 6. KPIs PRINCIPALES IDENTIFICADOS:")
    print("-" * 80)
    
    # Promedio general
    cur.execute("""
        SELECT 
            AVG(porcentaje) as promedio_general,
            COUNT(DISTINCT sucursal_clean) as sucursales_evaluadas,
            COUNT(DISTINCT estado) as estados_activos
        FROM supervision_sucursales 
        WHERE year = 2025 AND quarter = 'Q2'
    """)
    
    kpis = cur.fetchone()
    print(f"\n   Q2 2025:")
    print(f"   • Promedio General: {kpis['promedio_general']:.2f}%")
    print(f"   • Sucursales Evaluadas: {kpis['sucursales_evaluadas']}")
    print(f"   • Estados Activos: {kpis['estados_activos']}")
    
    # Top 5 áreas de evaluación
    print("\n   Top 5 Áreas de Evaluación (por frecuencia):")
    cur.execute("""
        SELECT area_evaluacion, COUNT(*) as total
        FROM supervision_sucursales
        WHERE area_evaluacion IS NOT NULL
        GROUP BY area_evaluacion
        ORDER BY total DESC
        LIMIT 5
    """)
    
    areas = cur.fetchall()
    for area in areas:
        print(f"   • {area['area_evaluacion']}: {area['total']:,} evaluaciones")
    
    # 7. Análisis de filtros necesarios
    print("\n🔧 7. FILTROS DISPONIBLES PARA DASHBOARDS:")
    print("-" * 80)
    
    # Estados disponibles
    cur.execute("""
        SELECT DISTINCT estado 
        FROM supervision_sucursales 
        WHERE year = 2025 
        ORDER BY estado
    """)
    estados = cur.fetchall()
    print(f"\n   Estados ({len(estados)}):")
    estados_list = [e['estado'] for e in estados[:10]]  # Primeros 10
    print(f"   {', '.join(estados_list)}...")
    
    # Grupos operativos
    cur.execute("""
        SELECT DISTINCT grupo_operativo 
        FROM supervision_sucursales 
        WHERE grupo_operativo IS NOT NULL AND year = 2025
        ORDER BY grupo_operativo
    """)
    grupos = cur.fetchall()
    print(f"\n   Grupos Operativos ({len(grupos)}):")
    for grupo in grupos[:5]:  # Primeros 5
        print(f"   • {grupo['grupo_operativo']}")
    
    # 8. Consultas SQL optimizadas para dashboards
    print("\n📝 8. CONSULTAS SQL RECOMENDADAS PARA DASHBOARDS:")
    print("-" * 80)
    
    print("\n   Query 1 - KPIs Generales:")
    print("""
    SELECT 
        AVG(porcentaje) as promedio_general,
        COUNT(DISTINCT sucursal_clean) as sucursales_evaluadas,
        COUNT(DISTINCT estado) as estados_activos,
        COUNT(*) as total_evaluaciones
    FROM supervision_sucursales 
    WHERE year = :year AND quarter = :quarter
        AND (:estado IS NULL OR estado = :estado)
        AND (:grupo IS NULL OR grupo_operativo = :grupo)
    """)
    
    print("\n   Query 2 - Performance por Estado:")
    print("""
    SELECT 
        estado,
        AVG(porcentaje) as promedio,
        COUNT(DISTINCT sucursal_clean) as sucursales,
        COUNT(*) as evaluaciones
    FROM supervision_sucursales 
    WHERE year = :year AND quarter = :quarter
    GROUP BY estado
    ORDER BY promedio DESC
    """)
    
    print("\n   Query 3 - Mapa de Sucursales:")
    print("""
    SELECT 
        sucursal_clean,
        municipio,
        estado,
        latitud,
        longitud,
        AVG(porcentaje) as promedio,
        COUNT(*) as total_evaluaciones
    FROM supervision_sucursales 
    WHERE year = :year AND quarter = :quarter
        AND latitud IS NOT NULL 
        AND longitud IS NOT NULL
    GROUP BY sucursal_clean, municipio, estado, latitud, longitud
    """)
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_database()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()