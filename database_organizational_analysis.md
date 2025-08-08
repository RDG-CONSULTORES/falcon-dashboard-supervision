# Neon PostgreSQL Database - Real Organizational Structure Analysis

## 🏢 Executive Summary

**Database Analysis Complete**: The real organizational structure has been mapped from the `sucursales_master` table, which contains complete and accurate data with 100% coordinate coverage for pin map functionality.

### Key Findings
- **18 Grupos Operativos** (not the sample 9 from limited sucursales table)
- **86 Active Sucursales** across **7 Mexican States**
- **100% Coordinate Coverage** for all locations
- **Complete Hierarchy**: Grupo → Estado → Ciudad → Sucursal

---

## 📊 Real Organizational Structure

### Complete Grupos Operativos List (18 Total)
```
✓ CANTERA ROSA (MORELIA)    - 3 sucursales (Michoacán)
✓ CRR                       - 7 sucursales (Tamaulipas) 
✓ EFM                       - 1 sucursales (Sinaloa)
✓ EXPO                      - 16 sucursales (Nuevo León)
✓ GRUPO MATAMOROS           - 5 sucursales (Tamaulipas)
✓ GRUPO NUEVO LAREDO        - 2 sucursales (Tamaulipas)
✓ GRUPO PIEDRAS NEGRAS      - 1 sucursales (Coahuila)
✓ GRUPO RIO BRAVO           - 1 sucursales (Tamaulipas)
✓ GRUPO SABINAS             - 1 sucursales (Coahuila)
✓ GRUPO SALTILLO            - 6 sucursales (Coahuila)
✓ OCHTER                    - 4 sucursales (Coahuila/Durango)
✓ OGAS                      - 5 sucursales (Nuevo León)
✓ PLOG                      - 7 sucursales (Nuevo León)
✓ PLOG QUERETARO            - 4 sucursales (Querétaro)
✓ PLOG TORREON              - 6 sucursales (Coahuila)
✓ RAP                       - 3 sucursales (Tamaulipas)
✓ TEC                       - 4 sucursales (Nuevo León)
✓ TEPEYAC                   - 10 sucursales (Nuevo León)
```

### Geographic Distribution by State

| Estado | Total Sucursales | Grupos Operativos |
|--------|------------------|-------------------|
| **Nuevo León** | 42 | EXPO (16), TEPEYAC (10), PLOG (7), OGAS (5), TEC (4) |
| **Tamaulipas** | 18 | CRR (7), GRUPO MATAMOROS (5), RAP (3), GRUPO NUEVO LAREDO (2), GRUPO RIO BRAVO (1) |
| **Coahuila** | 16 | GRUPO SALTILLO (6), PLOG TORREON (6), OCHTER (2), GRUPO PIEDRAS NEGRAS (1), GRUPO SABINAS (1) |
| **Querétaro** | 4 | PLOG QUERETARO (4) |
| **Michoacán** | 3 | CANTERA ROSA (MORELIA) (3) |
| **Durango** | 2 | OCHTER (2) |
| **Sinaloa** | 1 | EFM (1) |

---

## 🗺️ Pin Map Implementation Data

### Complete Coordinate Coverage
- **✅ 86/86 sucursales** have valid coordinates (100% coverage)
- **Map Bounds**: 
  - Latitude: 19.7069° to 28.7000° North
  - Longitude: -108.4688° to -97.5047° West
  - **Center Point**: (24.2035°N, -102.9868°W)

### Sample Coordinate Data
```javascript
[
  {
    name: "Morelia Centro",
    grupo: "CANTERA ROSA (MORELIA)", 
    estado: "Michoacán",
    ciudad: "Morelia",
    lat: 19.7069,
    lng: -101.1956
  },
  {
    name: "Pino Suarez",
    grupo: "TEPEYAC",
    estado: "Nuevo León", 
    ciudad: "Monterrey",
    lat: 25.6694,
    lng: -100.3095
  }
  // ... 84 more locations
]
```

---

## 🔧 Dashboard Implementation Guide

### 1. Data Source Configuration
```sql
-- PRIMARY TABLE: Use sucursales_master (NOT sucursales)
SELECT 
    nombre_sucursal,
    ciudad_normalizada,
    estado_normalizado,
    grupo_operativo,
    latitud,
    longitud,
    gerente_operaciones
FROM sucursales_master 
WHERE activa = true
ORDER BY grupo_operativo, estado_normalizado;
```

### 2. Filter System Structure

#### Grupo Operativo Filter (18 options)
```javascript
const gruposOperativos = [
    "CANTERA ROSA (MORELIA)",
    "CRR", 
    "EFM",
    "EXPO",
    "GRUPO MATAMOROS",
    "GRUPO NUEVO LAREDO",
    "GRUPO PIEDRAS NEGRAS", 
    "GRUPO RIO BRAVO",
    "GRUPO SABINAS",
    "GRUPO SALTILLO",
    "OCHTER",
    "OGAS",
    "PLOG",
    "PLOG QUERETARO", 
    "PLOG TORREON",
    "RAP",
    "TEC",
    "TEPEYAC"
];
```

#### Estado Filter (7 options)
```javascript
const estados = [
    "Coahuila",    // 16 sucursales
    "Durango",     // 2 sucursales  
    "Michoacán",   // 3 sucursales
    "Nuevo León",  // 42 sucursales
    "Querétaro",   // 4 sucursales
    "Sinaloa",     // 1 sucursales
    "Tamaulipas"   // 18 sucursales
];
```

### 3. Pin Map Auto-Zoom Logic
```javascript
// When filters applied, calculate bounds and auto-zoom
function autoZoomToFiltered(filteredSucursales) {
    const lats = filteredSucursales.map(s => s.lat);
    const lngs = filteredSucursales.map(s => s.lng);
    
    const bounds = {
        north: Math.max(...lats),
        south: Math.min(...lats), 
        east: Math.max(...lngs),
        west: Math.min(...lngs)
    };
    
    map.fitBounds(bounds);
}
```

### 4. Business Data Integration
```sql
-- Link with supervision data for performance metrics
SELECT 
    sm.nombre_sucursal,
    sm.grupo_operativo,
    AVG(soc.calificacion_general_pct) as avg_supervision_score
FROM sucursales_master sm
LEFT JOIN supervision_operativa_cas soc ON sm.nombre_sucursal LIKE '%' || TRIM(soc.location_name) || '%'  
WHERE sm.activa = true
GROUP BY sm.nombre_sucursal, sm.grupo_operativo;
```

---

## ⚠️ Critical Implementation Notes

### ❌ Avoid These Issues
1. **Don't use `sucursales` table** - Missing coordinates and incomplete data
2. **Don't hard-code grupo names** - Use database values exactly as stored
3. **Don't assume uniform distribution** - Nuevo León has 49% of all sucursales

### ✅ Best Practices  
1. **Use `sucursales_master` table** - Complete, accurate, 100% coordinates
2. **Match location names carefully** - Use fuzzy matching for business data joins
3. **Handle state name variations** - "Coahuila" vs "Coahuila de Zaragoza" 
4. **Implement progressive loading** - 86 pins may need clustering for performance

---

## 🚀 Next Steps for Development

1. **Update Dashboard Queries**: Switch from `sucursales` to `sucursales_master`
2. **Implement Filter System**: Use the 18 real grupos operativos
3. **Add Pin Map**: All coordinates ready for immediate implementation  
4. **Business Metrics**: Link supervision scores and complaint data
5. **Performance Optimization**: Consider pin clustering for 86+ locations

---

## 📈 Business Intelligence Opportunities

- **Geographic Analysis**: Nuevo León concentration (49% of sucursales)
- **Operational Comparison**: EXPO vs TEPEYAC performance in same region
- **Growth Planning**: Estado coverage gaps and expansion opportunities  
- **Supervision Integration**: 117 inspection records available for overlay
