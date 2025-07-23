# 🎾 Tennis Miligan - Backend Limpio y Escalable

## 📋 Resumen
Sistema de gestión para Tennis Miligan completamente refactorizado con arquitectura modular, soporte para múltiples bases de datos y código escalable.

## 🏗️ Arquitectura

### **Estructura de archivos:**
```
Miligan-Tennis/
├── app_clean.py          # 🚀 Aplicación principal (NUEVA)
├── config.py             # ⚙️ Configuración centralizada
├── database.py           # 🗄️ Gestor de base de datos
├── models.py             # 📊 Modelos de datos
├── utils.py              # 🛠️ Utilidades y validaciones
├── requirements.txt      # 📦 Dependencias
├── env.example           # 🔧 Variables de entorno
├── Procfile              # 🚀 Configuración Render
└── logs/                 # 📝 Logs de la aplicación
```

### **Módulos principales:**

#### **1. config.py** - Configuración centralizada
- ✅ Configuración por entorno (desarrollo/producción)
- ✅ Variables de entorno
- ✅ Configuración de base de datos
- ✅ Configuración de CORS, rate limiting, logging

#### **2. database.py** - Gestor de base de datos
- ✅ Soporte SQLite y PostgreSQL
- ✅ Conexiones seguras con context managers
- ✅ Creación automática de tablas
- ✅ Manejo de errores centralizado

#### **3. models.py** - Modelos de datos
- ✅ Clases para Cliente, Reserva, Producto, Compra
- ✅ Métodos CRUD estandarizados
- ✅ Validaciones de datos
- ✅ Manejo de errores consistente

#### **4. utils.py** - Utilidades comunes
- ✅ Validaciones de entrada
- ✅ Sanitización de datos
- ✅ Funciones de formateo
- ✅ Cálculos de negocio

#### **5. app_clean.py** - Aplicación principal
- ✅ Rutas RESTful organizadas
- ✅ Autenticación JWT
- ✅ Rate limiting
- ✅ Logging estructurado
- ✅ Manejo de errores global

## 🚀 Características principales

### **✅ Escalabilidad:**
- **Arquitectura modular:** Fácil agregar nuevas funcionalidades
- **Soporte múltiples DB:** SQLite para desarrollo, PostgreSQL para producción
- **Rate limiting:** Protección contra abuso
- **Logging estructurado:** Monitoreo y debugging

### **✅ Seguridad:**
- **Validación de entrada:** Todos los datos se validan y sanitizan
- **Autenticación JWT:** Tokens seguros con expiración
- **CORS configurado:** Control de acceso por origen
- **SQL injection protection:** Consultas parametrizadas

### **✅ Mantenibilidad:**
- **Código limpio:** Sin duplicados, bien documentado
- **Separación de responsabilidades:** Cada módulo tiene una función específica
- **Configuración centralizada:** Fácil cambiar configuraciones
- **Manejo de errores consistente:** Respuestas uniformes

### **✅ Funcionalidades:**
- **Gestión de clientes:** CRUD completo
- **Gestión de reservas:** CRUD con validaciones de horarios
- **Gestión de productos:** CRUD con control de stock
- **Gestión de compras:** CRUD con cálculos automáticos

## 🔧 Configuración

### **1. Variables de entorno (.env):**
```env
# Base de datos
DATABASE_URL=sqlite:///tennis.db                    # Desarrollo
DATABASE_URL=postgresql://user:pass@host/db        # Producción

# Seguridad
SECRET_KEY=tu_clave_secreta_aqui
JWT_SECRET_KEY=tu_jwt_secret_aqui

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3002

# Entorno
FLASK_ENV=development
LOG_LEVEL=INFO
```

### **2. Instalación:**
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp env.example .env
# Editar .env con tus configuraciones

# Ejecutar aplicación
python app_clean.py
```

## 📊 Endpoints disponibles

### **Autenticación:**
- `POST /login` - Iniciar sesión

### **Información:**
- `GET /` - Estado de la API
- `GET /config` - Configuración del sistema

### **Clientes:**
- `GET /clientes` - Listar clientes
- `POST /clientes` - Crear cliente
- `PUT /clientes/<id>` - Actualizar cliente
- `DELETE /clientes/<id>` - Eliminar cliente

### **Reservas:**
- `GET /reservas` - Listar reservas
- `POST /reservas` - Crear reserva
- `PUT /reservas/<id>` - Actualizar reserva
- `DELETE /reservas/<id>` - Eliminar reserva

### **Productos:**
- `GET /productos` - Listar productos
- `POST /productos` - Crear producto

### **Compras:**
- `GET /compras` - Listar compras
- `POST /compras` - Crear compra

## 🔄 Migración desde versión anterior

### **Opción 1: Migración gradual (Recomendado)**
1. Mantener `app.py` para desarrollo
2. Usar `app_clean.py` para producción
3. Migrar gradualmente funcionalidades

### **Opción 2: Migración completa**
1. Reemplazar `app.py` con `app_clean.py`
2. Actualizar todas las referencias
3. Probar exhaustivamente

## 🧪 Testing

### **Verificar instalación:**
```bash
# Verificar que la API responde
curl http://localhost:5000/

# Verificar login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### **Verificar funcionalidades:**
```bash
# Crear cliente
curl -X POST http://localhost:5000/clientes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN" \
  -d '{"nombre":"Juan Pérez","telefono":"999888777"}'

# Listar clientes
curl -X GET http://localhost:5000/clientes \
  -H "Authorization: Bearer TU_TOKEN"
```

## 🚀 Despliegue en Render

### **1. Configurar variables de entorno:**
- `DATABASE_URL`: URL de PostgreSQL
- `SECRET_KEY`: Clave secreta para Flask
- `JWT_SECRET_KEY`: Clave para JWT
- `FLASK_ENV`: production

### **2. Configurar comando de inicio:**
```bash
gunicorn app_clean:app
```

### **3. Configurar build command:**
```bash
pip install -r requirements.txt
```

## 📈 Beneficios de la nueva arquitectura

### **Para desarrolladores:**
- ✅ Código más fácil de entender y mantener
- ✅ Fácil agregar nuevas funcionalidades
- ✅ Testing más sencillo
- ✅ Debugging mejorado

### **Para el negocio:**
- ✅ Sistema más estable y confiable
- ✅ Mejor rendimiento con múltiples usuarios
- ✅ Fácil escalar según el crecimiento
- ✅ Menos tiempo de inactividad

### **Para usuarios:**
- ✅ Respuestas más rápidas
- ✅ Mejor manejo de errores
- ✅ Funcionalidades más robustas
- ✅ Experiencia más fluida

## 🔮 Próximos pasos

### **Corto plazo:**
1. ✅ Migrar a PostgreSQL en producción
2. ✅ Implementar testing automatizado
3. ✅ Agregar documentación de API (Swagger)

### **Mediano plazo:**
1. 🔄 Implementar roles de usuario
2. 🔄 Agregar notificaciones (email/SMS)
3. 🔄 Dashboard con estadísticas

### **Largo plazo:**
1. 🔄 API para aplicación móvil
2. 🔄 Integración con sistemas de pago
3. 🔄 Análisis avanzado de datos

---

**¡La nueva arquitectura está lista para escalar con tu negocio de tenis!** 🎾 