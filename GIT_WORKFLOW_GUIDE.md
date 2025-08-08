# 🔄 Metodología de Desarrollo - Control de Cambios

## 🎯 Metodología Recomendada: GitFlow Simplificado

### ⚠️ NUNCA hagas cambios directamente en Vercel
- Los cambios se sobrescriben en el próximo deploy
- No hay control de versiones
- No hay backup de código
- Problemas de colaboración

## 🌳 Estructura de Branches

```
main (producción)
├── develop (desarrollo)
├── feature/nueva-funcionalidad
├── hotfix/error-critico
└── release/v1.2.0
```

### 📋 Flujo de Trabajo

## 1. 🚀 Setup Inicial

### Crear repositorio Git
```bash
cd /Users/robertodavila/falcon-miniapp-bot
git init
git add .
git commit -m "🎉 Initial commit: Falcon Analytics Dashboard"
```

### Conectar con GitHub
```bash
# Crear repo en GitHub primero, luego:
git remote add origin https://github.com/tu-usuario/falcon-miniapp-bot.git
git branch -M main
git push -u origin main
```

### Crear branch de desarrollo
```bash
git checkout -b develop
git push -u origin develop
```

## 2. 🔧 Para Cambios Nuevos

### A. Crear Feature Branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature/nueva-funcionalidad
```

### B. Desarrollar y Testing Local
```bash
# Hacer cambios
# Probar localmente con ngrok
python app/app_v3.py
```

### C. Commit y Push
```bash
git add .
git commit -m "✨ feat: descripción del cambio"
git push origin feature/nueva-funcionalidad
```

### D. Pull Request a Develop
- Crear PR en GitHub
- Review del código
- Merge a develop

### E. Deploy a Staging (opcional)
```bash
git checkout develop
vercel --prod --target staging
```

### F. Release a Producción
```bash
git checkout main
git merge develop
git tag v1.2.0
git push origin main --tags
# Vercel auto-deploya main a producción
```

## 3. 🚨 Para Hotfixes Urgentes

### A. Crear Hotfix Branch desde Main
```bash
git checkout main
git pull origin main
git checkout -b hotfix/error-critico
```

### B. Fix y Test
```bash
# Arreglar el problema
# Probar localmente
git add .
git commit -m "🐛 hotfix: descripción del fix"
```

### C. Merge a Main y Develop
```bash
git checkout main
git merge hotfix/error-critico
git push origin main

git checkout develop  
git merge hotfix/error-critico
git push origin develop

git branch -d hotfix/error-critico
```

## 4. 🛠️ Setup de Vercel con GitHub

### Conectar Repositorio
1. En Vercel Dashboard → New Project
2. Import from GitHub
3. Seleccionar repositorio
4. Configurar:
   - Framework: Other
   - Build Command: (vacío)
   - Output Directory: (vacío)

### Configurar Auto-Deploy
```json
// vercel.json - ya configurado
{
  "git": {
    "deploymentEnabled": {
      "main": true,
      "develop": false
    }
  }
}
```

### Branches de Deploy
- **main** → Producción automática
- **develop** → Staging manual
- **feature/*** → Preview automático

## 5. 📝 Convenciones de Commits

### Formato
```
tipo(scope): descripción

feat: nueva funcionalidad
fix: corrección de bug  
docs: documentación
style: formato, espacios
refactor: refactoring
test: pruebas
chore: tareas de mantenimiento
```

### Ejemplos
```bash
git commit -m "✨ feat(dashboard): agregar filtro por trimestre"
git commit -m "🐛 fix(api): corregir error en endpoint de estados"
git commit -m "📝 docs: actualizar guía de deployment"
git commit -m "💄 style(ui): cambiar font a Arial en filtros"
```

## 6. 🔍 Testing Strategy

### Local Development
```bash
# Terminal 1: Flask app
python app/app_v3.py

# Terminal 2: ngrok tunnel
ngrok http 5000

# Terminal 3: Bot para testing
python bot_webapp.py
```

### Staging Environment
- Deploy develop a Vercel staging
- Probar con bot de testing
- Validar funcionalidades

### Production
- Solo deploy desde main
- Post-deploy verification
- Monitoring activo

## 7. 🚨 Rollback Strategy

### Rollback Rápido
```bash
# En Vercel Dashboard
# Deployments → Promote Previous

# O via CLI
vercel rollback
```

### Rollback con Git
```bash
git checkout main
git revert HEAD~1  # Revertir último commit
git push origin main
```

## 8. 📊 Herramientas Recomendadas

### Code Quality
```bash
# Pre-commit hooks
pip install pre-commit
pre-commit install
```

### Monitoring
- Vercel Analytics (automático)
- GitHub Actions para CI/CD
- Error tracking (Sentry opcional)

## 9. 🔐 Manejo de Secrets

### Desarrollo Local
```bash
# .env (gitignored)
DATABASE_URL=postgresql://...
BOT_TOKEN=123456:ABC...
```

### Producción
```bash
# Vercel environment variables
vercel env add DATABASE_URL production
vercel env add BOT_TOKEN production
```

### Staging
```bash
vercel env add DATABASE_URL_STAGING preview
vercel env add BOT_TOKEN_STAGING preview
```

## 10. 📋 Checklist de Deploy

### Pre-Deploy
- [ ] Tests pasando localmente
- [ ] Code review aprobado
- [ ] Documentación actualizada
- [ ] Variables de entorno configuradas

### Post-Deploy
- [ ] Health check endpoints
- [ ] Bot responde correctamente
- [ ] Dashboard carga sin errores
- [ ] Filtros funcionando
- [ ] Monitoreo activo

## 11. 🤝 Colaboración en Equipo

### Branch Protection Rules
- Require PR reviews
- Require status checks
- Restrict pushes to main
- Delete head branches

### Roles
- **Developer**: Feature branches, PRs
- **Reviewer**: Code review, approval
- **Maintainer**: Merge, deploy, hotfixes

## 💡 Beneficios de esta Metodología

1. **Control total** de cambios
2. **Backup automático** en GitHub
3. **Rollback rápido** si hay problemas
4. **Testing** antes de producción
5. **Colaboración** sin conflictos
6. **Historial completo** de cambios
7. **Deploy automático** desde main

## ⚡ Comandos Rápidos de Referencia

```bash
# Nuevo feature
git checkout -b feature/nombre && git push -u origin feature/nombre

# Sync con develop
git checkout develop && git pull && git checkout - && git merge develop

# Deploy staging
vercel --prod --target preview

# Emergency rollback
vercel rollback

# Ver logs
vercel logs --follow
```