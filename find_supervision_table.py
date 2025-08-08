#!/usr/bin/env python3
"""
Buscar la tabla correcta de supervisión en la base de datos
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def find_supervision_tables():
    """Find tables related to supervision"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("🔍 BUSCANDO TABLAS DE SUPERVISIÓN...")
    print("=" * 80)
    
    # Buscar tablas con 'supervision' en el nombre
    cur.execute("""
        SELECT 
            tablename,
            pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND (tablename LIKE '%supervision%' OR tablename LIKE '%supervisiones%')
        ORDER BY tablename;
    """)
    
    tables = cur.fetchall()
    print(f"\n📊 Tablas encontradas con 'supervision': {len(tables)}")
    for table in tables:
        print(f"\n• {table['tablename']} ({table['size']})")
        
        # Ver columnas de cada tabla
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table['tablename']}'
            ORDER BY ordinal_position
            LIMIT 10
        """)
        columns = cur.fetchall()
        print("  Columnas principales:")
        for col in columns:
            print(f"    - {col['column_name']} ({col['data_type']})")
        
        # Ver algunos registros
        try:
            cur.execute(f"SELECT COUNT(*) as total FROM {table['tablename']}")
            count = cur.fetchone()
            print(f"  Total registros: {count['total']:,}")
        except:
            print("  Total registros: Error al contar")
    
    # Buscar tabla con datos más recientes
    print("\n\n🔍 BUSCANDO TABLA CON DATOS MÁS RECIENTES...")
    print("=" * 80)
    
    # Revisar supervision_operativa_detalle que parece ser la más grande
    print("\n📋 Analizando: supervision_operativa_detalle (121 MB)")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'supervision_operativa_detalle'
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    print(f"\nTotal columnas: {len(columns)}")
    print("\nPrimeras 20 columnas:")
    for col in columns[:20]:
        print(f"  • {col['column_name']:30} ({col['data_type']})")
    
    # Ver muestra de datos
    print("\n📄 Muestra de datos:")
    cur.execute("""
        SELECT * FROM supervision_operativa_detalle 
        LIMIT 2
    """)
    
    sample = cur.fetchall()
    if sample:
        print("\nRegistro de ejemplo:")
        for key, value in sample[0].items():
            if key in ['year', 'quarter', 'estado', 'municipio', 'sucursal', 'porcentaje', 'grupo_operativo']:
                print(f"  {key}: {value}")
    
    conn.close()

if __name__ == "__main__":
    try:
        find_supervision_tables()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()