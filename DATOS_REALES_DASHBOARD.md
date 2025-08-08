# 📊 DATOS REALES PARA DASHBOARD SUPERVISIÓN OPERATIVA

## 🎯 RESUMEN EJECUTIVO

### KPIs PRINCIPALES - Q3 2025 (Trimestre Actual)
- **Sucursales Evaluadas**: 26 sucursales
- **Promedio General**: 91.39%
- **Total Evaluaciones**: 45,790
- **Estados Activos**: 9 estados
- **Grupos Operativos**: 20 grupos

### KPIs PRINCIPALES - Q2 2025 (Comparación)
- **Sucursales Evaluadas**: 63 sucursales  
- **Promedio General**: 88.91%
- **Total Evaluaciones**: 284,311
- **Estados Activos**: 9 estados
- **Grupos Operativos**: 19 grupos

### TOTALES EN EL SISTEMA
- **Total de Registros**: 423,746
- **Rango de Fechas**: Marzo 2025 - Agosto 2025
- **Total de Áreas de Evaluación**: 39 (no solo 29)

---

## 📍 DISTRIBUCIÓN GEOGRÁFICA

### Top Estados por Número de Sucursales:
1. **Nuevo León**: 42 sucursales (268,015 evaluaciones) - Promedio: 91.48%
2. **Tamaulipas**: 19 sucursales (78,848 evaluaciones) - Promedio: 84.56%
3. **Coahuila de Zaragoza**: 8 sucursales (24,839 evaluaciones) - Promedio: 84.49%
4. **Querétaro**: 4 sucursales (18,444 evaluaciones) - Promedio: 96.97%
5. **Michoacán de Ocampo**: 3 sucursales (10,032 evaluaciones) - Promedio: 87.80%
6. **Durango**: 2 sucursales (9,744 evaluaciones) - Promedio: 90.06%
7. **Coahuila**: 6 sucursales (6,804 evaluaciones) - Promedio: 86.16%
8. **Sinaloa**: 1 sucursal (3,828 evaluaciones) - Promedio: 91.10%
9. **Michoacán**: 3 sucursales (3,192 evaluaciones) - Promedio: 87.80%

---

## 👥 GRUPOS OPERATIVOS (20 TOTALES)

### Top 10 Grupos por Evaluaciones:
1. **EXPO**: 11 sucursales - Promedio: 87.49%
2. **OGAS**: 8 sucursales - Promedio: 97.37%
3. **PLOG NUEVO LEON**: 6 sucursales - Promedio: 89.01%
4. **TEPEYAC**: 10 sucursales - Promedio: 92.50%
5. **PLOG LAGUNA**: 6 sucursales - Promedio: 89.80%
6. **TEC**: 4 sucursales - Promedio: 93.22%
7. **EFM**: 3 sucursales - Promedio: 89.27%
8. **PLOG QUERETARO**: 4 sucursales - Promedio: 96.97%
9. **OCHTER TAMPICO**: 4 sucursales - Promedio: 87.20%
10. **GRUPO MATAMOROS**: 4 sucursales - Promedio: 90.57%

Otros grupos: CRR, EPL SO, GRUPO CANTERA ROSA (MORELIA), GRUPO CENTRITO, GRUPO NUEVO LAREDO (RUELAS), GRUPO PIEDRAS NEGRAS, GRUPO RIO BRAVO, GRUPO SABINAS HIDALGO, GRUPO SALTILLO, RAP

---

## 📊 INDICADORES DE EVALUACIÓN (39 ÁREAS)

### 🏆 TOP 10 - MEJORES INDICADORES (Q3 2025):
1. **TIEMPOS DE SERVICIO**: 100.00%
2. **ALMACEN QUÍMICOS**: 100.00%
3. **CAJAS DE TOTOPO EMPACADO**: 100.00%
4. **LAVADO DE UTENSILIOS**: 100.00%
5. **BARRA DE SALSAS**: 99.30%
6. **COMEDOR AREA COMEDOR**: 99.27%
7. **PROCESO MARINADO CALIFICACION**: 97.87%
8. **REFRIGERADORES DE SERVICIO**: 96.04%
9. **BARRA DE SERVICIO**: 95.56%
10. **ALMACEN JARABES**: 95.52%

### 🚨 BOTTOM 10 - ÁREAS CRÍTICAS (Q3 2025):
1. **FREIDORA DE PAPA**: 76.45% ⚠️
2. **EXTERIOR SUCURSAL**: 81.17%
3. **ASADORES**: 83.19%
4. **CONGELADOR PAPA**: 84.23%
5. **HORNOS**: 84.58%
6. **CONSERVADOR PAPA FRITA**: 86.21%
7. **FREIDORAS**: 86.98%
8. **MAQUINA DE HIELO**: 87.34%
9. **AVISO DE FUNCIONAMIENTO, BITACORAS, CARPETA DE FUMIGACION CONTROL**: 87.96%
10. **BAÑO EMPLEADOS**: 88.28%

### 📈 INDICADORES CON MAYOR MEJORA (Q2 vs Q3):
1. **FREIDORAS**: +25.79% (61.19% → 86.98%)
2. **AVISO DE FUNCIONAMIENTO**: +18.31% (69.65% → 87.96%)
3. **EXTERIOR SUCURSAL**: +13.48% (67.69% → 81.17%)
4. **FREIDORA DE PAPA**: +7.47% (68.98% → 76.45%)
5. **ESTACION DE LAVADO DE MANOS**: +6.59% (86.84% → 93.43%)

---

## 🎨 SISTEMA DE COLORES - HEAT MAP (70% LÍMITE ROJO)

- 🟢 **EXCELENTE** (≥90%): Verde oscuro (#059669)
- 🟢 **BUENO** (80-89%): Verde claro (#10b981)
- 🟡 **REGULAR** (70-79%): Amarillo/Naranja (#f59e0b)
- 🔴 **CRÍTICO** (<70%): ROJO (#dc2626)

---

## 📋 QUERIES SQL CORRECTAS

### Query para KPIs principales:
```sql
SELECT 
    AVG(porcentaje) as promedio_general,
    COUNT(DISTINCT sucursal_clean) as sucursales_evaluadas,
    COUNT(DISTINCT estado) as estados_activos,
    COUNT(DISTINCT grupo_operativo) as grupos_operativos,
    COUNT(*) as total_evaluaciones
FROM supervision_operativa_detalle
WHERE EXTRACT(YEAR FROM fecha_supervision) = 2025
AND EXTRACT(QUARTER FROM fecha_supervision) = 3;
```

### Query para datos del mapa:
```sql
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
AND EXTRACT(YEAR FROM fecha_supervision) = 2025
AND EXTRACT(QUARTER FROM fecha_supervision) = 3
GROUP BY sucursal_clean, municipio, estado, latitud, longitud, grupo_operativo;
```

### Query para indicadores:
```sql
SELECT 
    area_evaluacion,
    COUNT(*) as total_evaluaciones,
    AVG(porcentaje) as promedio_general,
    COUNT(DISTINCT sucursal_clean) as sucursales
FROM supervision_operativa_detalle
WHERE area_evaluacion IS NOT NULL 
AND area_evaluacion != ''
AND EXTRACT(YEAR FROM fecha_supervision) = 2025
AND EXTRACT(QUARTER FROM fecha_supervision) = 3
GROUP BY area_evaluacion
ORDER BY AVG(porcentaje) DESC;
```

---

## 🗺️ NOTAS IMPORTANTES PARA EL MAPA

1. **Coordenadas**: Todas las sucursales tienen latitud y longitud en la BD
2. **GeoJSON de México**: Necesitamos el archivo GeoJSON de estados de México para el heat map por estados
3. **Pin Map**: Usar las coordenadas de cada sucursal para mostrar marcadores
4. **Auto-zoom**: El mapa debe hacer zoom automático para mostrar todas las sucursales

---

## ✅ RESUMEN DE CORRECCIONES NECESARIAS

1. **NO son 1,234 sucursales** - Son 26 en Q3 2025 y 63 en Q2 2025
2. **NO son solo 29 indicadores** - Son 39 áreas de evaluación
3. **El límite rojo es 70%** - Todo debajo de 70% es crítico
4. **Q3 2025 es el trimestre actual** - No Q4 2024
5. **20 grupos operativos** - No 19
6. **9 estados activos** - Con Nuevo León liderando con 42 sucursales totales