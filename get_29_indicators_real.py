#!/usr/bin/env python3
"""
Obtener los 29 indicadores REALES - solo los que tienen porcentaje
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def get_real_29_indicators():
    """Obtener solo las áreas que tienen valores de porcentaje"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("📊 OBTENIENDO LOS 29 INDICADORES REALES (CON PORCENTAJE)")
    print("=" * 80)
    
    # Query para obtener SOLO las áreas que tienen porcentaje
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
        AND EXTRACT(YEAR FROM fecha_supervision) = 2025
        GROUP BY area_evaluacion
        HAVING AVG(porcentaje) IS NOT NULL
        ORDER BY AVG(porcentaje) DESC
    """)
    
    indicadores = cur.fetchall()
    
    print(f"\n✅ TOTAL DE INDICADORES CON PORCENTAJE: {len(indicadores)}")
    print("\n" + "=" * 80)
    
    # Mostrar todos los indicadores ordenados por promedio
    print("\n📊 LISTA COMPLETA DE INDICADORES (ORDENADOS POR CALIFICACIÓN):")
    print("-" * 80)
    
    for i, ind in enumerate(indicadores, 1):
        print(f"\n{i:2}. {ind['area_evaluacion']}")
        print(f"    Promedio: {ind['promedio_general']:.2f}%")
        print(f"    Evaluaciones: {ind['total_evaluaciones']:,} | Sucursales: {ind['sucursales']}")
        print(f"    Rango: {ind['minimo']:.1f}% - {ind['maximo']:.1f}%")
    
    # Separar Top 5 y Bottom 5
    print("\n" + "=" * 80)
    print("\n🏆 TOP 5 - MEJORES INDICADORES:")
    print("-" * 80)
    
    for i, ind in enumerate(indicadores[:5], 1):
        print(f"{i}. {ind['area_evaluacion']}: {ind['promedio_general']:.2f}%")
    
    print("\n" + "=" * 80)
    print("\n🚨 BOTTOM 5 - ÁREAS DE OPORTUNIDAD:")
    print("-" * 80)
    
    bottom_5 = indicadores[-5:] if len(indicadores) >= 5 else indicadores
    for i, ind in enumerate(reversed(bottom_5), 1):
        print(f"{i}. {ind['area_evaluacion']}: {ind['promedio_general']:.2f}%")
    
    # Análisis específico para Q3 2025
    print("\n" + "=" * 80)
    print("\n📈 ANÁLISIS ESPECÍFICO Q3 2025:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            area_evaluacion,
            COUNT(*) as evaluaciones_q3,
            AVG(porcentaje) as promedio_q3,
            COUNT(DISTINCT sucursal_clean) as sucursales_q3
        FROM supervision_operativa_detalle
        WHERE porcentaje IS NOT NULL
        AND area_evaluacion IS NOT NULL 
        AND area_evaluacion != ''
        AND EXTRACT(YEAR FROM fecha_supervision) = 2025
        AND EXTRACT(QUARTER FROM fecha_supervision) = 3
        GROUP BY area_evaluacion
        HAVING AVG(porcentaje) IS NOT NULL
        ORDER BY AVG(porcentaje) DESC
    """)
    
    indicadores_q3 = cur.fetchall()
    
    print(f"\nIndicadores en Q3 2025: {len(indicadores_q3)}")
    
    if indicadores_q3:
        print("\nTop 5 Q3:")
        for ind in indicadores_q3[:5]:
            print(f"  • {ind['area_evaluacion']}: {ind['promedio_q3']:.2f}%")
        
        print("\nBottom 5 Q3:")
        for ind in indicadores_q3[-5:]:
            print(f"  • {ind['area_evaluacion']}: {ind['promedio_q3']:.2f}%")
    
    # Verificar cuáles son exactamente los que tienen porcentaje
    print("\n" + "=" * 80)
    print("\n🔍 VERIFICACIÓN - ÁREAS CON PALABRA 'CALIFICACION' O '%':")
    print("-" * 80)
    
    cur.execute("""
        SELECT DISTINCT area_evaluacion
        FROM supervision_operativa_detalle
        WHERE porcentaje IS NOT NULL
        AND area_evaluacion IS NOT NULL
        AND (
            UPPER(area_evaluacion) LIKE '%CALIFICACION%'
            OR area_evaluacion LIKE '%\\%%' ESCAPE '\\'
        )
        ORDER BY area_evaluacion
    """)
    
    areas_calificacion = cur.fetchall()
    print(f"\nÁreas con 'CALIFICACION' o '%': {len(areas_calificacion)}")
    for area in areas_calificacion:
        print(f"  • {area['area_evaluacion']}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 80)
    
    return indicadores

if __name__ == "__main__":
    try:
        get_real_29_indicators()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()