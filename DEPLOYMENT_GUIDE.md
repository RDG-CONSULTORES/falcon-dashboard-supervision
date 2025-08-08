# 🚀 Guía de Deployment - Falcon Analytics Dashboard

## 📋 Preparación

### 1. Verificar archivos necesarios
- ✅ `vercel.json` - Configuración de Vercel
- ✅ `api/index.py` - Entry point para serverless
- ✅ `.vercelignore` - Archivos a ignorar
- ✅ `requirements.txt` - Dependencias Python

### 2. Variables de entorno necesarias
```
DATABASE_URL=postgresql://user:password@host:port/database
BOT_TOKEN=your_telegram_bot_token
SECRET_KEY=your_secret_key
WEBAPP_URL=https://your-vercel-app.vercel.app
```

## 🔧 Deployment en Vercel

### Opción A: Vercel CLI (Recomendado)

1. **Instalar Vercel CLI**
```bash
npm i -g vercel
```

2. **Login a Vercel**
```bash
vercel login
```

3. **Deploy desde la carpeta del proyecto**
```bash
cd /Users/robertodavila/falcon-miniapp-bot
vercel
```

4. **Configurar variables de entorno**
```bash
vercel env add DATABASE_URL
vercel env add BOT_TOKEN
vercel env add SECRET_KEY
vercel env add WEBAPP_URL
```

### Opción B: GitHub + Vercel Dashboard

1. **Subir a GitHub**
```bash
git init
git add .
git commit -m "Initial commit - Falcon Analytics Dashboard"
git remote add origin https://github.com/tu-usuario/falcon-miniapp-bot.git
git push -u origin main
```

2. **Conectar en Vercel Dashboard**
   - Ir a https://vercel.com/dashboard
   - Click "New Project"
   - Importar desde GitHub
   - Seleccionar el repositorio

3. **Configurar en Dashboard**
   - Framework: `Other`
   - Build Command: (dejar vacío)
   - Output Directory: (dejar vacío)
   - Install Command: `pip install -r requirements.txt`

## 🤖 Configurar Telegram Bot

### 1. Obtener URL de Vercel
Después del deploy, obtendrás una URL como:
```
https://falcon-miniapp-bot.vercel.app
```

### 2. Actualizar webhook del bot
```bash
curl -X POST https://api.telegram.org/bot{BOT_TOKEN}/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tu-app.vercel.app/webhook"}'
```

### 3. Configurar Mini Web App
En BotFather:
```
/newapp
/myapps
# Seleccionar tu bot
# URL: https://tu-app.vercel.app
```

## 🔍 Verificación

### 1. Probar endpoints
```bash
curl https://tu-app.vercel.app/api/health
curl https://tu-app.vercel.app/
```

### 2. Probar bot
- Enviar `/start` al bot
- Verificar que aparezca el Mini Web App
- Probar dashboard y filtros

## 🛠️ Troubleshooting

### Error: "Module not found"
- Verificar que `api/index.py` esté en el root
- Revisar imports en `vercel.json`

### Error: "Database connection failed"
- Verificar `DATABASE_URL` en variables de entorno
- Asegurar que la base de datos sea accesible desde Vercel

### Error: "Bot webhook failed"
- Verificar `BOT_TOKEN`
- Confirmar que la URL esté configurada correctamente
- Revisar logs en Vercel Dashboard

## 📊 Monitoreo

### Logs en Vercel
```bash
vercel logs
```

### Performance
- Vercel Analytics automático
- Métricas en Dashboard

## 🔄 Updates

### Redeployment automático
- Push a GitHub redeploya automáticamente
- O usar `vercel --prod` para deploy manual

### Variables de entorno
```bash
vercel env add NUEVA_VARIABLE
vercel env rm VARIABLE_VIEJA
```

## 💡 Optimizaciones

### 1. Cold starts
- Vercel maneja automáticamente
- Primera carga puede ser lenta (~2-3 segundos)

### 2. Caché
- Archivos estáticos se cachean automáticamente
- Considerar Redis para datos frecuentes

### 3. Escalabilidad
- Vercel escala automáticamente
- Considerar rate limiting para API calls

## ⚠️ Consideraciones importantes

1. **Costos**: Vercel tiene límites en plan gratuito
2. **Timeouts**: 10 segundos máximo por request
3. **Memoria**: 1024MB por función
4. **Concurrencia**: 1000 ejecuciones concurrentes

## 🎯 Próximos pasos

1. Deploy inicial
2. Configurar dominio personalizado (opcional)
3. Configurar analytics
4. Monitoring y alertas
5. Backup de base de datos