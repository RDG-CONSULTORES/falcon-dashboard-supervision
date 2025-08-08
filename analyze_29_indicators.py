#!/usr/bin/env python3
"""
Identificar los 29 indicadores exactos de la base de datos
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def analyze_indicators():
    """Get the exact 29 indicators from the database"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("📊 IDENTIFICANDO LOS 29 INDICADORES (ÁREAS DE EVALUACIÓN)")
    print("=" * 80)
    
    # Obtener todas las áreas únicas con sus estadísticas
    cur.execute("""
        SELECT 
            area_evaluacion,
            COUNT(*) as total_evaluaciones,
            COUNT(DISTINCT sucursal_clean) as sucursales,
            AVG(porcentaje) as promedio_general,
            MIN(fecha_supervision) as primera_evaluacion,
            MAX(fecha_supervision) as ultima_evaluacion
        FROM supervision_operativa_detalle
        WHERE area_evaluacion IS NOT NULL 
        AND area_evaluacion != ''
        AND EXTRACT(YEAR FROM fecha_supervision) = 2025
        GROUP BY area_evaluacion
        ORDER BY total_evaluaciones DESC
    """)
    
    areas = cur.fetchall()
    
    print(f"\nTotal de áreas encontradas: {len(areas)}")
    print("\n📋 LISTA DE INDICADORES:")
    print("-" * 80)
    
    for i, area in enumerate(areas, 1):
        avg = f"{area['promedio_general']:.2f}%" if area['promedio_general'] else 'N/A'
        print(f"{i:2}. {area['area_evaluacion']}")
        print(f"    Evaluaciones: {area['total_evaluaciones']:,} | Promedio: {avg}")
    
    # Análisis por trimestre Q3 2025
    print("\n📊 ANÁLISIS Q3 2025 (TRIMESTRE ACTUAL):")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            area_evaluacion,
            COUNT(*) as evaluaciones_q3,
            AVG(porcentaje) as promedio_q3,
            COUNT(DISTINCT sucursal_clean) as sucursales_q3
        FROM supervision_operativa_detalle
        WHERE area_evaluacion IS NOT NULL 
        AND area_evaluacion != ''
        AND EXTRACT(YEAR FROM fecha_supervision) = 2025
        AND EXTRACT(QUARTER FROM fecha_supervision) = 3
        GROUP BY area_evaluacion
        HAVING COUNT(*) > 10
        ORDER BY AVG(porcentaje) ASC
        LIMIT 10
    """)
    
    areas_q3 = cur.fetchall()
    
    print("\nTop 10 Indicadores con MENOR calificación en Q3:")
    for area in areas_q3:
        avg = f"{area['promedio_q3']:.2f}%" if area['promedio_q3'] else 'N/A'
        print(f"  • {area['area_evaluacion']}: {avg}")
        print(f"    ({area['evaluaciones_q3']} evaluaciones en {area['sucursales_q3']} sucursales)")
    
    # Comparativa Q2 vs Q3
    print("\n📈 COMPARATIVA Q2 vs Q3 2025:")
    print("-" * 80)
    
    cur.execute("""
        WITH q2_data AS (
            SELECT 
                area_evaluacion,
                AVG(porcentaje) as promedio_q2
            FROM supervision_operativa_detalle
            WHERE EXTRACT(YEAR FROM fecha_supervision) = 2025
            AND EXTRACT(QUARTER FROM fecha_supervision) = 2
            AND area_evaluacion IS NOT NULL
            GROUP BY area_evaluacion
        ),
        q3_data AS (
            SELECT 
                area_evaluacion,
                AVG(porcentaje) as promedio_q3
            FROM supervision_operativa_detalle
            WHERE EXTRACT(YEAR FROM fecha_supervision) = 2025
            AND EXTRACT(QUARTER FROM fecha_supervision) = 3
            AND area_evaluacion IS NOT NULL
            GROUP BY area_evaluacion
        )
        SELECT 
            COALESCE(q2.area_evaluacion, q3.area_evaluacion) as area,
            q2.promedio_q2,
            q3.promedio_q3,
            q3.promedio_q3 - q2.promedio_q2 as diferencia
        FROM q2_data q2
        FULL OUTER JOIN q3_data q3 ON q2.area_evaluacion = q3.area_evaluacion
        WHERE q2.promedio_q2 IS NOT NULL AND q3.promedio_q3 IS NOT NULL
        ORDER BY diferencia DESC
        LIMIT 5
    """)
    
    mejoras = cur.fetchall()
    
    print("\nTop 5 Indicadores con MAYOR MEJORA:")
    for area in mejoras:
        print(f"  • {area['area']}")
        print(f"    Q2: {area['promedio_q2']:.2f}% → Q3: {area['promedio_q3']:.2f}% (↑ +{area['diferencia']:.2f}%)")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_indicators()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()