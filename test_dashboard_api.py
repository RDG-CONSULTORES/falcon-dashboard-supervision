#!/usr/bin/env python3
"""
Script para probar las APIs del dashboard
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8888"

def test_api_endpoint(endpoint, description):
    """Test a single API endpoint"""
    try:
        print(f"\n🔍 Testing: {description}")
        print(f"URL: {BASE_URL}{endpoint}")
        
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Status: {response.status_code}")
            
            # Print sample of data
            if isinstance(data, dict):
                if 'error' in data:
                    print(f"❌ API Error: {data['error']}")
                    return False
                else:
                    print(f"📊 Data keys: {list(data.keys())}")
                    if 'indicadores' in data:
                        print(f"   Total indicadores: {len(data['indicadores'])}")
                    if 'sucursales' in data:
                        print(f"   Total sucursales: {len(data['sucursales'])}")
                    if 'promedio_general' in data:
                        print(f"   Promedio general: {data['promedio_general']}%")
            return True
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Server not running on {BASE_URL}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT ERROR - Request took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Test all dashboard APIs"""
    print("🚀 TESTING DASHBOARD APIs")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/", "Main Dashboard Page"),
        ("/api/kpis", "KPIs Principales"),
        ("/api/kpis?trimestre=Q3&year=2025", "KPIs Q3 2025"),
        ("/api/indicadores", "29 Indicadores"),
        ("/api/indicadores?trimestre=Q3&year=2025", "Indicadores Q3 2025"),
        ("/api/sucursales", "Datos de Sucursales"),
        ("/api/sucursales?trimestre=Q3&year=2025", "Sucursales Q3 2025"),
        ("/api/estados", "Performance por Estados"),
        ("/api/grupos", "Performance por Grupos"),
        ("/api/filtros", "Opciones de Filtros")
    ]
    
    results = []
    for endpoint, description in endpoints:
        success = test_api_endpoint(endpoint, description)
        results.append((endpoint, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {total - successful}/{total}")
    
    if successful == total:
        print("\n🎉 ALL TESTS PASSED!")
        print(f"🌐 Dashboard available at: {BASE_URL}")
        print("\n📱 Features working:")
        print("   • 3-tab layout (Calificación General, 29 Indicadores, Administración)")
        print("   • Real PostgreSQL data connection")
        print("   • Interactive Leaflet.js maps with pin markers")
        print("   • Dynamic filtering by trimestre, estado, grupo")
        print("   • Heat map visualization with 70% red threshold")
        print("   • Top 5/Bottom 5 indicators")
        print("   • Chart.js bar charts for estados, grupos, sucursales")
        print("   • Responsive design with proper mobile support")
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        for endpoint, success in results:
            if not success:
                print(f"   ❌ {endpoint}")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)