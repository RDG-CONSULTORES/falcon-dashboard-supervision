#!/usr/bin/env python3
"""
Análisis detallado de la tabla supervision_operativa_detalle
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def analyze_supervision_table():
    """Analyze supervision_operativa_detalle table in detail"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("📊 ANÁLISIS DETALLADO: supervision_operativa_detalle")
    print("=" * 80)
    
    # 1. Estadísticas generales
    print("\n1️⃣ ESTADÍSTICAS GENERALES:")
    print("-" * 80)
    
    cur.execute("SELECT COUNT(*) as total FROM supervision_operativa_detalle")
    total = cur.fetchone()
    print(f"Total de registros: {total['total']:,}")
    
    # Registros con porcentaje
    cur.execute("SELECT COUNT(*) as total FROM supervision_operativa_detalle WHERE porcentaje IS NOT NULL")
    with_percentage = cur.fetchone()
    print(f"Registros con porcentaje: {with_percentage['total']:,}")
    
    # Rango de fechas
    cur.execute("""
        SELECT 
            MIN(fecha_supervision) as fecha_min,
            MAX(fecha_supervision) as fecha_max
        FROM supervision_operativa_detalle
        WHERE fecha_supervision IS NOT NULL
    """)
    dates = cur.fetchone()
    print(f"Rango de fechas: {dates['fecha_min']} a {dates['fecha_max']}")
    
    # 2. Análisis temporal
    print("\n2️⃣ ANÁLISIS TEMPORAL:")
    print("-" * 80)
    
    # Agregar columnas year y quarter si no existen
    cur.execute("""
        SELECT 
            EXTRACT(YEAR FROM fecha_supervision) as year,
            'Q' || EXTRACT(QUARTER FROM fecha_supervision) as quarter,
            COUNT(*) as total,
            COUNT(DISTINCT sucursal_clean) as sucursales,
            AVG(CASE WHEN porcentaje IS NOT NULL THEN porcentaje ELSE NULL END) as promedio
        FROM supervision_operativa_detalle
        WHERE fecha_supervision IS NOT NULL
        GROUP BY year, quarter
        ORDER BY year DESC, quarter DESC
        LIMIT 8
    """)
    
    quarters = cur.fetchall()
    print("\nDatos por Trimestre:")
    for q in quarters:
        year = int(q['year']) if q['year'] else 'N/A'
        avg = f"{q['promedio']:.2f}%" if q['promedio'] else 'N/A'
        print(f"  • {year} {q['quarter']}: {q['total']:,} registros, {q['sucursales']} sucursales, Promedio: {avg}")
    
    # 3. Análisis geográfico
    print("\n3️⃣ ANÁLISIS GEOGRÁFICO:")
    print("-" * 80)
    
    # Estados
    cur.execute("""
        SELECT 
            estado,
            COUNT(*) as total,
            COUNT(DISTINCT sucursal_clean) as sucursales,
            AVG(CASE WHEN porcentaje IS NOT NULL THEN porcentaje ELSE NULL END) as promedio
        FROM supervision_operativa_detalle
        WHERE estado IS NOT NULL
        GROUP BY estado
        ORDER BY total DESC
        LIMIT 10
    """)
    
    estados = cur.fetchall()
    print("\nTop 10 Estados:")
    for e in estados:
        avg = f"{e['promedio']:.2f}%" if e['promedio'] else 'N/A'
        print(f"  • {e['estado']}: {e['total']:,} evaluaciones, {e['sucursales']} sucursales, Promedio: {avg}")
    
    # 4. Grupos Operativos
    print("\n4️⃣ GRUPOS OPERATIVOS:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            grupo_operativo,
            COUNT(*) as total,
            COUNT(DISTINCT sucursal_clean) as sucursales,
            AVG(CASE WHEN porcentaje IS NOT NULL THEN porcentaje ELSE NULL END) as promedio
        FROM supervision_operativa_detalle
        WHERE grupo_operativo IS NOT NULL
        GROUP BY grupo_operativo
        ORDER BY total DESC
    """)
    
    grupos = cur.fetchall()
    print(f"\nTotal de Grupos Operativos: {len(grupos)}")
    print("\nPrimeros 10 Grupos:")
    for g in grupos[:10]:
        avg = f"{g['promedio']:.2f}%" if g['promedio'] else 'N/A'
        print(f"  • {g['grupo_operativo']}: {g['total']:,} evaluaciones, {g['sucursales']} sucursales, Promedio: {avg}")
    
    # 5. Áreas de Evaluación
    print("\n5️⃣ ÁREAS DE EVALUACIÓN:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            area_evaluacion,
            COUNT(*) as total,
            AVG(CASE WHEN porcentaje IS NOT NULL THEN porcentaje ELSE NULL END) as promedio,
            AVG(puntos_obtenidos::float / NULLIF(puntos_maximos, 0) * 100) as promedio_calc
        FROM supervision_operativa_detalle
        WHERE area_evaluacion IS NOT NULL
        GROUP BY area_evaluacion
        ORDER BY total DESC
        LIMIT 15
    """)
    
    areas = cur.fetchall()
    print(f"\nTotal de Áreas de Evaluación: {len(areas)}")
    print("\nTop 15 Áreas:")
    for a in areas:
        avg = f"{a['promedio']:.2f}%" if a['promedio'] else 'N/A'
        avg_calc = f"{a['promedio_calc']:.2f}%" if a['promedio_calc'] else 'N/A'
        print(f"  • {a['area_evaluacion']}: {a['total']:,} evaluaciones")
        print(f"    Promedio directo: {avg}, Promedio calculado: {avg_calc}")
    
    # 6. Análisis de datos para Q2 2025
    print("\n6️⃣ ANÁLISIS ESPECÍFICO Q2 2025:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT sucursal_clean) as sucursales,
            COUNT(DISTINCT estado) as estados,
            COUNT(DISTINCT grupo_operativo) as grupos,
            COUNT(DISTINCT area_evaluacion) as areas,
            AVG(CASE WHEN porcentaje IS NOT NULL THEN porcentaje ELSE NULL END) as promedio_general
        FROM supervision_operativa_detalle
        WHERE EXTRACT(YEAR FROM fecha_supervision) = 2025
        AND EXTRACT(QUARTER FROM fecha_supervision) = 2
    """)
    
    q2_2025 = cur.fetchone()
    if q2_2025 and q2_2025['total'] > 0:
        print(f"\nEstadísticas Q2 2025:")
        print(f"  • Total evaluaciones: {q2_2025['total']:,}")
        print(f"  • Sucursales evaluadas: {q2_2025['sucursales']}")
        print(f"  • Estados activos: {q2_2025['estados']}")
        print(f"  • Grupos operativos: {q2_2025['grupos']}")
        print(f"  • Áreas evaluadas: {q2_2025['areas']}")
        avg = f"{q2_2025['promedio_general']:.2f}%" if q2_2025['promedio_general'] else 'N/A'
        print(f"  • Promedio general: {avg}")
    else:
        print("\n⚠️ No hay datos para Q2 2025")
    
    # 7. Muestra de datos reales
    print("\n7️⃣ MUESTRA DE DATOS REALES:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            submission_id,
            fecha_supervision,
            sucursal_clean,
            municipio,
            estado,
            grupo_operativo,
            area_evaluacion,
            puntos_obtenidos,
            puntos_maximos,
            porcentaje,
            latitud,
            longitud
        FROM supervision_operativa_detalle
        WHERE fecha_supervision >= '2025-01-01'
        AND porcentaje IS NOT NULL
        ORDER BY fecha_supervision DESC
        LIMIT 3
    """)
    
    sample = cur.fetchall()
    for i, row in enumerate(sample, 1):
        print(f"\nEjemplo {i}:")
        print(f"  • Fecha: {row['fecha_supervision']}")
        print(f"  • Sucursal: {row['sucursal_clean']}")
        print(f"  • Ubicación: {row['municipio']}, {row['estado']}")
        print(f"  • Grupo: {row['grupo_operativo']}")
        print(f"  • Área: {row['area_evaluacion']}")
        print(f"  • Puntos: {row['puntos_obtenidos']}/{row['puntos_maximos']}")
        print(f"  • Porcentaje: {row['porcentaje']}%")
        print(f"  • Coordenadas: ({row['latitud']}, {row['longitud']})")
    
    # 8. Queries recomendadas
    print("\n8️⃣ QUERIES RECOMENDADAS PARA DASHBOARDS:")
    print("-" * 80)
    
    print("\n✅ Query 1 - KPIs Principales (con year/quarter calculados):")
    print("""
    SELECT 
        AVG(porcentaje) as promedio_general,
        COUNT(DISTINCT sucursal_clean) as sucursales_evaluadas,
        COUNT(DISTINCT estado) as estados_activos,
        COUNT(*) as total_evaluaciones
    FROM supervision_operativa_detalle
    WHERE EXTRACT(YEAR FROM fecha_supervision) = :year
    AND EXTRACT(QUARTER FROM fecha_supervision) = :quarter_num
    AND (:estado IS NULL OR estado = :estado)
    AND (:grupo IS NULL OR grupo_operativo = :grupo)
    """)
    
    print("\n✅ Query 2 - Datos para Mapa:")
    print("""
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
    WHERE latitud IS NOT NULL 
    AND longitud IS NOT NULL
    AND EXTRACT(YEAR FROM fecha_supervision) = :year
    AND EXTRACT(QUARTER FROM fecha_supervision) = :quarter_num
    GROUP BY sucursal_clean, municipio, estado, latitud, longitud, grupo_operativo
    """)
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_supervision_table()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()