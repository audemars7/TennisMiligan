# 🚀 Migración de SQLite a PostgreSQL

## 📋 Resumen
Este documento explica cómo migrar el sistema de Tennis Miligan de SQLite a PostgreSQL para soportar múltiples usuarios simultáneos (6-8 usuarios).

## 🎯 ¿Por qué migrar?
- **SQLite:** Solo 1 escritura a la vez (problema con 6-8 usuarios)
- **PostgreSQL:** Múltiples escrituras simultáneas (solución para tu negocio)

## 📦 Archivos creados/modificados

### Nuevos archivos:
- `app_postgres.py` - Versión del backend con soporte PostgreSQL
- `migrate_to_postgres.py` - Script para migrar datos
- `env.example` - Ejemplo de variables de entorno
- `MIGRATION_README.md` - Este archivo

### Modificados:
- `requirements.txt` - Agregadas dependencias PostgreSQL

## 🔧 Pasos para la migración

### Paso 1: Configurar PostgreSQL en Render

1. **Ir a Render Dashboard**
2. **Crear nueva base de datos PostgreSQL:**
   - Click en "New" → "PostgreSQL"
   - Nombre: `tennis-miligan-db`
   - Plan: Free (suficiente para empezar)
   - Click "Create Database"

3. **Copiar la URL de conexión:**
   - En la base de datos creada, click en "Connect"
   - Copiar "External Database URL"
   - Formato: `postgresql://user:password@host:port/database`

### Paso 2: Configurar variables de entorno

1. **En tu proyecto local:**
   ```bash
   # Crear archivo .env en Miligan-Tennis/
   cp env.example .env
   ```

2. **Editar .env:**
   ```env
   # Para desarrollo (SQLite)
   DATABASE_URL=sqlite:///tennis.db
   
   # Para producción (PostgreSQL en Render)
   DATABASE_URL=postgresql://user:password@host:port/database
   
   SECRET_KEY=tu_clave_secreta_aqui
   JWT_SECRET_KEY=tu_jwt_secret_aqui
   ```

### Paso 3: Instalar dependencias

```bash
cd Miligan-Tennis
pip install -r requirements.txt
```

### Paso 4: Migrar datos existentes

```bash
# Configurar DATABASE_URL para PostgreSQL en .env
python migrate_to_postgres.py
```

### Paso 5: Probar la migración

```bash
# Usar la nueva versión del backend
python app_postgres.py
```

### Paso 6: Configurar Render para producción

1. **En Render Dashboard:**
   - Ir a tu servicio web
   - Click en "Environment"
   - Agregar variables:
     ```
     DATABASE_URL=postgresql://user:password@host:port/database
     SECRET_KEY=tu_clave_secreta_aqui
     JWT_SECRET_KEY=tu_jwt_secret_aqui
     ```

2. **Cambiar el comando de inicio:**
   - En "Settings" → "Build Command"
   - Cambiar a: `gunicorn app_postgres:app`

## 🔄 Migración gradual (Recomendado)

### Opción A: Desarrollo con SQLite, Producción con PostgreSQL
- **Desarrollo:** Mantener `DATABASE_URL=sqlite:///tennis.db`
- **Producción:** Usar `DATABASE_URL=postgresql://...`
- **Ventaja:** Desarrollo rápido, producción robusta

### Opción B: Todo PostgreSQL
- **Desarrollo y producción:** Usar PostgreSQL
- **Ventaja:** Entorno idéntico
- **Desventaja:** Requiere conexión a internet para desarrollo

## 🧪 Verificar la migración

### 1. Verificar conexión:
```bash
curl http://localhost:5000/
# Debe mostrar: {"database": "PostgreSQL", "status": "online"}
```

### 2. Verificar login:
```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 3. Verificar datos migrados:
- Crear un cliente
- Crear una reserva
- Verificar que aparezcan en la lista

## 🚨 Solución de problemas

### Error: "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Error: "Connection refused"
- Verificar que la URL de PostgreSQL sea correcta
- Verificar que la base de datos esté activa en Render

### Error: "Database is locked" (SQLite)
- Este error desaparece con PostgreSQL
- Si persiste, reiniciar el servidor

### Datos no aparecen después de la migración
- Verificar que el script de migración se ejecutó correctamente
- Verificar que las tablas se crearon en PostgreSQL

## 📊 Beneficios después de la migración

### ✅ Concurrencia:
- 6-8 usuarios simultáneos sin problemas
- Múltiples reservas al mismo tiempo
- Actualizaciones de deudas simultáneas

### ✅ Escalabilidad:
- Base de datos crece con tu negocio
- Backups automáticos en Render
- Mejor rendimiento con muchos datos

### ✅ Confiabilidad:
- Transacciones seguras
- No se pierden datos
- Sistema más robusto

## 🔮 Próximos pasos

1. **Migrar completamente:** Reemplazar `app.py` con `app_postgres.py`
2. **Agregar todas las rutas:** Copiar las rutas del `app.py` original
3. **Optimizar consultas:** Usar características específicas de PostgreSQL
4. **Monitoreo:** Configurar logs y métricas

## 📞 Soporte

Si tienes problemas durante la migración:
1. Verificar los logs en `logs/app.log`
2. Revisar la configuración de variables de entorno
3. Probar la conexión a PostgreSQL manualmente

---

**¡La migración a PostgreSQL te permitirá escalar tu negocio de tenis sin problemas de concurrencia!** 🎾 