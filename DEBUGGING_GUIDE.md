# 🔧 Guía de Debugging para Mini Web App

## 📱 **Opción 1: Panel de Debug Visible (Implementado)**

Agregué un panel amarillo en la parte superior del dashboard que muestra:
- ✅ Si Chart.js se carga correctamente
- 📊 Versión de Chart.js
- 🎯 Si las funciones se ejecutan
- ❌ Errores específicos
- 📋 Fallbacks cuando algo falla

## 🖥️ **Opción 2: Testing en Safari Mac**

### Para probar con DevTools:

1. **Abrir en Safari**:
   ```
   http://localhost:5002 
   ```

2. **Activar DevTools en Safari**:
   - Safari → Preferencias → Avanzado
   - ✅ "Mostrar menú Desarrollo"

3. **Abrir DevTools**:
   - Menú Desarrollo → Mostrar Inspector Web
   - O: `Cmd + Option + I`

4. **Ver Console**:
   - Tab "Console" en DevTools
   - Ver todos los mensajes de debug

## 🤖 **Opción 3: Testing en Telegram Desktop**

Si tienes Telegram Desktop:
1. Abrir el bot
2. Clic derecho en la Mini Web App
3. "Inspeccionar elemento" (si está disponible)

## 📋 **Qué buscar en el Panel de Debug:**

### ✅ **Mensajes Exitosos:**
```
[14:30:15] 📊 Chart.js disponible: true
[14:30:15] 📊 Chart.js version: 4.4.0
[14:30:16] 🎯 updateEstadosChart llamada con 7 estados
[14:30:16] ✅ Canvas encontrado: 300x300px
[14:30:16] ✅ Estados chart creado exitosamente
```

### ❌ **Posibles Errores:**
```
[14:30:15] ❌ Chart.js NO se cargó correctamente
[14:30:16] ❌ Canvas estados-chart no encontrado
[14:30:16] ⚠️ No hay datos de estados para mostrar
[14:30:16] ❌ Error creando chart de estados: [mensaje]
```

## 🎯 **Próximos Pasos:**

1. **Recarga la Mini Web App**
2. **Lee el panel amarillo de debug**
3. **Copia los mensajes que aparezcan**
4. **Reporta qué ves**

Si no aparecen las gráficas, verás automáticamente una lista simple con los datos como fallback.