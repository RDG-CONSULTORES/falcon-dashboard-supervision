# Falcon Miniapp Bot - Analytics de Supervisión Operativa

Bot de Telegram con Mini Web App para visualización y análisis de datos de supervisión operativa. Conecta con la base de datos existente de `supervision_operativa_detalle` para mostrar gráficas interactivas y métricas en tiempo real.

## 🚀 Características

- 🤖 **Bot de Telegram** con comandos útiles y botón de Mini Web App
- 📊 **Dashboard interactivo** con múltiples tipos de visualizaciones
- 🔍 **Filtros avanzados** por sucursal, grupo operativo, área y fechas
- 📈 **Gráficas en tiempo real** con Chart.js
- 📱 **Diseño responsivo** adaptado al tema de Telegram
- 🗄️ **Conexión optimizada** a PostgreSQL (Neon)
- 📤 **Exportación de datos** en CSV y JSON
- 🔄 **Actualización automática** cada 5 minutos

## 🏗️ Estructura del Proyecto

```
falcon-miniapp-bot/
├── app/                    # Flask Web Application
│   ├── static/
│   │   ├── css/           # Estilos CSS
│   │   └── js/            # JavaScript del dashboard
│   ├── templates/         # Plantillas HTML
│   └── app.py            # Aplicación Flask principal
├── bot/                   # Telegram Bot
│   └── telegram_bot.py   # Bot con comandos y Mini Web App
├── database/              # Conexión y consultas BD
│   ├── connection.py     # Pool de conexiones PostgreSQL
│   └── queries.py        # Consultas específicas para los datos
├── config/               # Configuración
├── utils/                # Utilidades
├── main.py              # Punto de entrada principal
├── requirements.txt     # Dependencias Python
├── .env                 # Variables de entorno (configurado)
└── README.md           # Este archivo
```

## 📋 Datos de la Base de Datos

El proyecto utiliza la tabla `supervision_operativa_detalle` con la siguiente estructura:

- **submission_id** (VARCHAR) - ID único de la evaluación
- **sucursal_clean** (VARCHAR) - Nombre de la sucursal
- **grupo_operativo** (VARCHAR) - Grupo operativo al que pertenece
- **area_evaluacion** (VARCHAR) - Área específica evaluada
- **fecha_supervision** (DATE) - Fecha de la supervisión
- **porcentaje** (DECIMAL) - Calificación obtenida (0-100)

## 🛠️ Instalación

### 1. Clonar y configurar el entorno

```bash
# Ya estás en el directorio correcto
cd falcon-miniapp-bot

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración (Ya realizada)

El archivo `.env` ya está configurado con:
- ✅ **BOT_TOKEN**: `8057006268:AAEOGaQu-FbeEYYuNrFUbB0jDZObGyQzMO8`
- ✅ **DATABASE_URL**: Conexión a Neon PostgreSQL
- ✅ **Configuración Flask**: Puerto 5000, modo desarrollo

### 3. Ejecutar el proyecto

```bash
# Ejecutar tanto el bot como la web app
python main.py
```

Esto iniciará:
- 🤖 Bot de Telegram (escuchando mensajes)
- 🌐 Servidor Flask en http://localhost:5000

## 🎯 Uso

### Comandos del Bot

- `/start` - Muestra botón para abrir el dashboard
- `/help` - Ayuda y comandos disponibles
- `/status` - Estado del sistema y conexión BD
- `/sucursales` - Lista todas las sucursales
- `/resumen` - Resumen rápido de estadísticas

### Dashboard Web

1. **Filtros**: Sucursal, grupo operativo, área, rango de fechas
2. **Métricas**: Resumen con KPIs principales
3. **Gráficas**:
   - Rendimiento por sucursal (barras)
   - Distribución por grupo operativo (donut)
   - Rendimiento por área (barras horizontales)
   - Tendencias temporales (líneas)
4. **Tabla de datos**: Detalles paginados
5. **Exportación**: CSV y JSON

## 🔌 API Endpoints

### Datos principales
- `GET /api/health` - Estado del sistema
- `GET /api/summary` - Estadísticas generales
- `GET /api/sucursales` - Lista de sucursales
- `GET /api/grupos` - Lista de grupos operativos
- `GET /api/areas` - Lista de áreas de evaluación

### Análisis de rendimiento
- `GET /api/performance/sucursal` - Rendimiento por sucursal
- `GET /api/performance/grupo` - Rendimiento por grupo
- `GET /api/performance/area` - Rendimiento por área

### Datos filtrados
- `GET /api/metrics` - Métricas con filtros
- `GET /api/trends` - Tendencias temporales
- `GET /api/export` - Exportación de datos

### Parámetros de filtrado
- `sucursal` - Filtrar por sucursal específica
- `grupo` - Filtrar por grupo operativo
- `area` - Filtrar por área de evaluación
- `fecha_inicio` - Fecha inicial (YYYY-MM-DD)
- `fecha_fin` - Fecha final (YYYY-MM-DD)

## 📊 Visualizaciones

### 1. Rendimiento por Sucursal
- **Tipo**: Gráfica de barras
- **Datos**: Promedio de calificaciones por sucursal
- **Orden**: Descendente por rendimiento

### 2. Distribución por Grupo Operativo
- **Tipo**: Gráfica de donut
- **Datos**: Promedio por grupo operativo
- **Colores**: Paleta diferenciada

### 3. Rendimiento por Área
- **Tipo**: Barras horizontales
- **Datos**: Promedio por área de evaluación
- **Orden**: Ascendente por rendimiento

### 4. Tendencias Temporales
- **Tipo**: Gráfica de líneas
- **Datos**: Promedio diario en el tiempo
- **Filtros**: Por sucursal específica

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Telegram Bot
BOT_TOKEN=tu_token_aqui
WEBAPP_URL=https://tu-dominio.com

# Flask
SECRET_KEY=tu_secret_key_aqui
PORT=5000
DEBUG=True

# Database
DATABASE_URL=postgresql://usuario:password@host/database?sslmode=require
```

### Personalización

1. **Colores y tema**: Modificar `app/static/css/style.css`
2. **Gráficas**: Ajustar configuración en `app/static/js/dashboard.js`
3. **Consultas**: Modificar `database/queries.py`
4. **Comandos bot**: Agregar en `bot/telegram_bot.py`

## 🚀 Despliegue

### Heroku
```bash
# Crear app
heroku create falcon-miniapp-bot

# Configurar variables
heroku config:set BOT_TOKEN=tu_token
heroku config:set DATABASE_URL=tu_database_url
heroku config:set WEBAPP_URL=https://falcon-miniapp-bot.herokuapp.com

# Desplegar
git push heroku main
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 📈 Métricas y Monitoreo

El sistema incluye:
- **Logs detallados** en `logs/app.log`
- **Health check** en `/api/health`
- **Monitoreo de conexión** a base de datos
- **Manejo de errores** con alertas

## 🔒 Seguridad

- **Variables de entorno** para credenciales
- **Validación del hash** de Telegram Web App
- **Conexión SSL** a PostgreSQL
- **Manejo seguro** de consultas SQL

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Notas Importantes

- El bot usa el token real proporcionado
- La base de datos está configurada para Neon
- Los datos se actualizan cada 5 minutos
- Filtros por defecto: últimos 30 días
- Máximo 100 registros en tabla de datos
- Exportación incluye todos los datos filtrados

## 🐛 Solución de Problemas

### Bot no responde
- Verificar BOT_TOKEN en .env
- Comprobar conexión a internet
- Revisar logs en `logs/app.log`

### Error de base de datos
- Verificar DATABASE_URL
- Comprobar certificados SSL
- Revisar permisos de tabla

### Web App no carga
- Verificar WEBAPP_URL (debe ser HTTPS)
- Comprobar puerto Flask
- Revisar consola del navegador

¡El proyecto está listo para usar! 🎉