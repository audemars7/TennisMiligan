from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os
import psycopg
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración CORS
CORS(app, 
     origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

# Configuración de logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)

# Log all errors
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled Exception: {str(e)}', exc_info=True)
    return jsonify({"mensaje": "Error interno del servidor"}), 500

# Importar configuración centralizada
from config import get_config

# Configuración centralizada
config = get_config()
DATABASE_URL = config.DATABASE_URL

# Configuración del rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[config.RATE_LIMIT_DAILY, config.RATE_LIMIT_HOURLY]
)

# Configuración JWT
app.config['SECRET_KEY'] = config.SECRET_KEY
JWT_SECRET_KEY = config.JWT_SECRET_KEY

# Credenciales de administrador
ADMIN_CREDENTIALS = {
    os.environ.get('ADMIN_USER', 'admin1'): os.environ.get('ADMIN_PASSWORD', 'pepito2025')
}

def create_connection():
    """Crear conexión a PostgreSQL"""
    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        app.logger.error(f"Error conectando a la base de datos: {e}")
        return None

def init_db():
    """Inicializar base de datos con todas las tablas"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Tabla clientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    apellido VARCHAR(255),
                    telefono VARCHAR(50),
                    email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla reservas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservas (
                    id SERIAL PRIMARY KEY,
                    cliente_id INTEGER REFERENCES clientes(id),
                    nombre VARCHAR(255) NOT NULL,
                    cancha VARCHAR(100) NOT NULL,
                    horario VARCHAR(50) NOT NULL,
                    fecha VARCHAR(20) NOT NULL,
                    estado VARCHAR(50) DEFAULT 'activa',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla productos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    stock INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla compras
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compras (
                    id SERIAL PRIMARY KEY,
                    cliente_id INTEGER REFERENCES clientes(id),
                    nombre_cliente VARCHAR(255),
                    producto VARCHAR(255) NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    total DECIMAL(10,2) NOT NULL,
                    pagado INTEGER DEFAULT 0,
                    fecha VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            app.logger.info("Base de datos PostgreSQL inicializada correctamente")
        except Exception as e:
            app.logger.error(f"Error creando tablas: {e}")
        finally:
            conn.close()

# Inicializar la base de datos al arrancar
init_db()

def token_required(f):
    """Decorador para proteger rutas con JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Permitir requests OPTIONS para CORS
        if request.method == 'OPTIONS':
            return f(None, *args, **kwargs)
            
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'mensaje': 'Token inválido'}), 401
        
        if not token:
            return jsonify({'mensaje': 'Token requerido'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'mensaje': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'mensaje': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route("/login", methods=["POST"])
def login():
    """Login de administrador"""
    auth = request.get_json()
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'mensaje': 'No se proporcionaron credenciales'}), 401
    
    if auth.get('username') in ADMIN_CREDENTIALS and \
       ADMIN_CREDENTIALS[auth.get('username')] == auth.get('password'):
        token = jwt.encode({
            'username': auth.get('username'),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET_KEY, algorithm="HS256")
        
        return jsonify({'token': token})
    
    return jsonify({'mensaje': 'Credenciales incorrectas'}), 401

# ==================== RUTAS BÁSICAS ====================

@app.route("/")
def home():
    """Ruta principal"""
    return jsonify({
        "mensaje": "API de Tennis Miligan funcionando",
        "database": "PostgreSQL",
        "status": "online"
    })

@app.route("/test-cors")
def test_cors():
    """Prueba de CORS"""
    return jsonify({"mensaje": "CORS funcionando correctamente"})

# ==================== RUTAS DE CLIENTES ====================

@app.route("/clientes", methods=["POST"])
@token_required
def crear_cliente(current_user):
    """Crear nuevo cliente"""
    data = request.get_json()
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    telefono = data.get("telefono")
    email = data.get("email")
    
    if not nombre:
        return jsonify({"mensaje": "El nombre es obligatorio"}), 400
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clientes (nombre, apellido, telefono, email)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (nombre, apellido, telefono, email))
            cliente_id = cursor.fetchone()[0]
            conn.commit()
            return jsonify({"id": cliente_id, "mensaje": "Cliente creado correctamente"}), 201
        except Exception as e:
            app.logger.error(f"Error al crear cliente: {e}")
            return jsonify({"mensaje": "Error al crear cliente"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/clientes", methods=["GET"])
@token_required
def listar_clientes(current_user):
    """Listar todos los clientes"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, apellido, telefono, email FROM clientes ORDER BY nombre")
            clientes = [
                {"id": row[0], "nombre": row[1], "apellido": row[2], "telefono": row[3], "email": row[4]}
                for row in cursor.fetchall()
            ]
            return jsonify(clientes)
        except Exception as e:
            app.logger.error(f"Error al obtener clientes: {e}")
            return jsonify({"mensaje": "Error al obtener clientes"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/clientes/<int:id>", methods=["GET"])
@token_required
def obtener_cliente(current_user, id):
    """Obtener cliente por ID"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, apellido, telefono, email FROM clientes WHERE id = %s", (id,))
            row = cursor.fetchone()
            if row:
                return jsonify({"id": row[0], "nombre": row[1], "apellido": row[2], "telefono": row[3], "email": row[4]})
            else:
                return jsonify({"mensaje": "Cliente no encontrado"}), 404
        except Exception as e:
            app.logger.error(f"Error al obtener cliente: {e}")
            return jsonify({"mensaje": "Error al obtener cliente"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/clientes/<int:id>", methods=["PUT"])
@token_required
def actualizar_cliente(current_user, id):
    """Actualizar cliente"""
    data = request.get_json()
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    telefono = data.get("telefono")
    email = data.get("email")
    
    if not nombre:
        return jsonify({"mensaje": "El nombre es obligatorio"}), 400
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clientes SET nombre=%s, apellido=%s, telefono=%s, email=%s WHERE id=%s",
                (nombre, apellido, telefono, email, id)
            )
            conn.commit()
            return jsonify({"mensaje": "Cliente actualizado correctamente"}), 200
        except Exception as e:
            app.logger.error(f"Error al actualizar cliente: {e}")
            return jsonify({"mensaje": "Error al actualizar cliente"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/clientes/<int:id>", methods=["DELETE"])
@token_required
def eliminar_cliente(current_user, id):
    """Eliminar cliente"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clientes WHERE id=%s", (id,))
            conn.commit()
            return jsonify({"mensaje": "Cliente eliminado correctamente"}), 200
        except Exception as e:
            app.logger.error(f"Error al eliminar cliente: {e}")
            return jsonify({"mensaje": "Error al eliminar cliente"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

# ==================== RUTAS DE RESERVAS ====================

@app.route("/reservar", methods=["POST"])
@token_required
@limiter.limit("20 per hour")
def hacer_reserva(current_user):
    """Crear nueva reserva con verificación de disponibilidad"""
    data = request.get_json()
    cliente_id = data.get("cliente_id")
    nombre = data.get("nombre")
    cancha = data.get("cancha")
    horario = data.get("horario")
    fecha = data.get("fecha")
    
    if not all([nombre, cancha, horario, fecha]):
        return jsonify({"mensaje": "Todos los campos son obligatorios"}), 400
    
    # Validar que la fecha no sea pasada
    try:
        fecha_reserva = datetime.strptime(fecha, "%Y-%m-%d").date()
        fecha_actual = datetime.now().date()
        
        if fecha_reserva < fecha_actual:
            return jsonify({
                "mensaje": "No se pueden hacer reservas para fechas pasadas",
                "fecha_valida": False
            }), 400
    except ValueError:
        return jsonify({"mensaje": "Formato de fecha inválido"}), 400
    
    # Verificar disponibilidad del horario
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Verificar si ya existe una reserva para esa cancha, fecha y horario
            cursor.execute("""
                SELECT id, nombre FROM reservas 
                WHERE cancha = %s AND fecha = %s AND horario = %s AND estado = 'activa'
            """, (cancha, fecha, horario))
            
            reserva_existente = cursor.fetchone()
            if reserva_existente:
                return jsonify({
                    "mensaje": f"Horario no disponible. Ya existe una reserva para {reserva_existente[1]} en cancha {cancha} a las {horario} el {fecha}",
                    "disponible": False
                }), 409
            
            # Si está disponible, crear la reserva
            cursor.execute("""
                INSERT INTO reservas (cliente_id, nombre, cancha, horario, fecha)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (cliente_id, nombre, cancha, horario, fecha))
            reserva_id = cursor.fetchone()[0]
            conn.commit()
            
            return jsonify({
                "id": reserva_id, 
                "mensaje": f"Reserva creada correctamente para {nombre} en cancha {cancha} a las {horario} el {fecha}",
                "disponible": True,
                "fecha_valida": True
            }), 201
            
        except Exception as e:
            app.logger.error(f"Error al crear reserva: {e}")
            return jsonify({"mensaje": "Error al crear reserva"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/reservas", methods=["GET"])
@token_required
def obtener_reservas(current_user):
    """Obtener todas las reservas"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.id, r.cliente_id, r.nombre, r.cancha, r.horario, r.fecha, r.estado,
                       c.nombre as cliente_nombre, c.apellido as cliente_apellido
                FROM reservas r
                LEFT JOIN clientes c ON r.cliente_id = c.id
                ORDER BY r.fecha DESC, r.horario
            """)
            reservas = [
                {
                    "id": row[0], "cliente_id": row[1], "nombre": row[2], 
                    "cancha": row[3], "horario": row[4], "fecha": row[5], 
                    "estado": row[6], "cliente_nombre": row[7], "cliente_apellido": row[8]
                }
                for row in cursor.fetchall()
            ]
            return jsonify(reservas)
        except Exception as e:
            app.logger.error(f"Error al obtener reservas: {e}")
            return jsonify({"mensaje": "Error al obtener reservas"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/horarios-disponibles", methods=["GET"])
@token_required
def obtener_horarios_disponibles(current_user):
    """Obtener horarios disponibles para una fecha y cancha específica"""
    fecha = request.args.get("fecha")
    cancha = request.args.get("cancha")
    
    if not fecha or not cancha:
        return jsonify({"mensaje": "Fecha y cancha son obligatorios"}), 400
    
    # Validar que la fecha no sea pasada
    try:
        fecha_reserva = datetime.strptime(fecha, "%Y-%m-%d").date()
        fecha_actual = datetime.now().date()
        
        if fecha_reserva < fecha_actual:
            return jsonify({
                "mensaje": "No se pueden consultar horarios para fechas pasadas",
                "fecha_valida": False,
                "horarios_disponibles": []
            }), 400
    except ValueError:
        return jsonify({"mensaje": "Formato de fecha inválido", "horarios_disponibles": []}), 400
    
    # Horarios disponibles desde configuración centralizada
    horarios_totales = config.HORARIOS_DISPONIBLES
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Obtener horarios ocupados para esa fecha y cancha
            cursor.execute("""
                SELECT horario FROM reservas 
                WHERE fecha = %s AND cancha = %s AND estado = 'activa'
            """, (fecha, cancha))
            
            horarios_ocupados = [row[0] for row in cursor.fetchall()]
            
            # Filtrar horarios disponibles
            horarios_disponibles = [h for h in horarios_totales if h not in horarios_ocupados]
            
            return jsonify({
                "fecha": fecha,
                "cancha": cancha,
                "horarios_disponibles": horarios_disponibles,
                "horarios_ocupados": horarios_ocupados,
                "total_disponibles": len(horarios_disponibles),
                "fecha_valida": True
            })
            
        except Exception as e:
            app.logger.error(f"Error al obtener horarios disponibles: {e}")
            return jsonify({"mensaje": "Error al obtener horarios disponibles"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/verificar-disponibilidad", methods=["GET"])
@token_required
def verificar_disponibilidad(current_user):
    """Verificar si un horario específico está disponible"""
    fecha = request.args.get("fecha")
    cancha = request.args.get("cancha")
    horario = request.args.get("horario")
    
    if not all([fecha, cancha, horario]):
        return jsonify({"mensaje": "Fecha, cancha y horario son obligatorios"}), 400
    
    # Validar que la fecha no sea pasada
    try:
        fecha_reserva = datetime.strptime(fecha, "%Y-%m-%d").date()
        fecha_actual = datetime.now().date()
        
        if fecha_reserva < fecha_actual:
            return jsonify({
                "disponible": False,
                "mensaje": "No se pueden verificar horarios para fechas pasadas",
                "fecha_valida": False
            })
    except ValueError:
        return jsonify({
            "disponible": False,
            "mensaje": "Formato de fecha inválido",
            "fecha_valida": False
        })
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Verificar si existe una reserva para ese horario
            cursor.execute("""
                SELECT id, nombre FROM reservas 
                WHERE fecha = %s AND cancha = %s AND horario = %s AND estado = 'activa'
            """, (fecha, cancha, horario))
            
            reserva_existente = cursor.fetchone()
            
            if reserva_existente:
                return jsonify({
                    "disponible": False,
                    "mensaje": f"Horario ocupado por {reserva_existente[1]}",
                    "reserva_id": reserva_existente[0],
                    "fecha_valida": True
                })
            else:
                return jsonify({
                    "disponible": True,
                    "mensaje": "Horario disponible",
                    "fecha_valida": True
                })
            
        except Exception as e:
            app.logger.error(f"Error al verificar disponibilidad: {e}")
            return jsonify({"mensaje": "Error al verificar disponibilidad"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/admin/reservas/<int:id>", methods=["PUT"])
@token_required
def editar_reserva(current_user, id):
    """Editar reserva"""
    data = request.get_json()
    nombre = data.get("nombre")
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE reservas SET nombre=%s WHERE id=%s", (nombre, id))
            conn.commit()
            return jsonify({"mensaje": "Reserva actualizada correctamente"}), 200
        except Exception as e:
            app.logger.error(f"Error al actualizar reserva: {e}")
            return jsonify({"mensaje": "Error al actualizar reserva"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/admin/reservas/<int:id>", methods=["DELETE"])
@token_required
def eliminar_reserva_admin(current_user, id):
    """Eliminar reserva"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reservas WHERE id=%s", (id,))
            conn.commit()
            return jsonify({"mensaje": "Reserva eliminada correctamente"}), 200
        except Exception as e:
            app.logger.error(f"Error al eliminar reserva: {e}")
            return jsonify({"mensaje": "Error al eliminar reserva"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

# ==================== RUTAS DE PRODUCTOS ====================

@app.route("/productos", methods=["GET"])
@token_required
def listar_productos(current_user):
    """Listar todos los productos"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, precio, stock FROM productos ORDER BY nombre")
            productos = [
                {"id": row[0], "nombre": row[1], "precio": float(row[2]), "stock": row[3]}
                for row in cursor.fetchall()
            ]
            return jsonify(productos)
        except Exception as e:
            app.logger.error(f"Error al obtener productos: {e}")
            return jsonify({"mensaje": "Error al obtener productos"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/productos", methods=["POST"])
@token_required
def agregar_producto(current_user):
    """Agregar nuevo producto"""
    data = request.get_json()
    nombre = data.get("nombre")
    precio = data.get("precio")
    stock = data.get("stock", 0)
    
    if not nombre or not precio:
        return jsonify({"mensaje": "Nombre y precio son obligatorios"}), 400
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO productos (nombre, precio, stock)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (nombre, precio, stock))
            producto_id = cursor.fetchone()[0]
            conn.commit()
            return jsonify({"id": producto_id, "mensaje": "Producto agregado correctamente"}), 201
        except Exception as e:
            app.logger.error(f"Error al agregar producto: {e}")
            return jsonify({"mensaje": "Error al agregar producto"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/productos/<int:id>", methods=["PUT"])
@token_required
def actualizar_producto(current_user, id):
    """Actualizar producto existente"""
    data = request.get_json()
    nombre = data.get("nombre")
    precio = data.get("precio")
    stock = data.get("stock")
    
    if not nombre or not precio or stock is None:
        return jsonify({"mensaje": "Todos los campos son obligatorios"}), 400
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Verificar que el producto existe
            cursor.execute("SELECT id FROM productos WHERE id = %s", (id,))
            if not cursor.fetchone():
                return jsonify({"mensaje": "Producto no encontrado"}), 404
            
            # Actualizar producto
            cursor.execute("""
                UPDATE productos 
                SET nombre = %s, precio = %s, stock = %s
                WHERE id = %s
            """, (nombre, precio, stock, id))
            conn.commit()
            return jsonify({"mensaje": "Producto actualizado correctamente"})
        except Exception as e:
            app.logger.error(f"Error al actualizar producto: {e}")
            return jsonify({"mensaje": "Error al actualizar producto"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/productos/<int:id>", methods=["DELETE"])
@token_required
def eliminar_producto(current_user, id):
    """Eliminar producto"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Verificar que el producto existe
            cursor.execute("SELECT nombre FROM productos WHERE id = %s", (id,))
            resultado = cursor.fetchone()
            if not resultado:
                return jsonify({"mensaje": "Producto no encontrado"}), 404
            
            nombre_producto = resultado[0]
            
            # Eliminar producto
            cursor.execute("DELETE FROM productos WHERE id = %s", (id,))
            conn.commit()
            return jsonify({"mensaje": f"Producto '{nombre_producto}' eliminado correctamente"})
        except Exception as e:
            app.logger.error(f"Error al eliminar producto: {e}")
            return jsonify({"mensaje": "Error al eliminar producto"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

# ==================== RUTAS DE COMPRAS ====================

@app.route("/compras", methods=["POST"])
@token_required
def registrar_compra(current_user):
    """Registrar nueva compra"""
    data = request.get_json()
    cliente_id = data.get("cliente_id")
    nombre_cliente = data.get("nombre_cliente")
    producto = data.get("producto")
    cantidad = data.get("cantidad")
    precio_unitario = data.get("precio_unitario")
    total = data.get("total")
    fecha = data.get("fecha")
    
    if not all([nombre_cliente, producto, cantidad, precio_unitario, total, fecha]):
        return jsonify({"mensaje": "Todos los campos son obligatorios"}), 400
    
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compras (cliente_id, nombre_cliente, producto, cantidad, precio_unitario, total, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (cliente_id, nombre_cliente, producto, cantidad, precio_unitario, total, fecha))
            compra_id = cursor.fetchone()[0]
            conn.commit()
            return jsonify({"id": compra_id, "mensaje": "Compra registrada correctamente"}), 201
        except Exception as e:
            app.logger.error(f"Error al registrar compra: {e}")
            return jsonify({"mensaje": "Error al registrar compra"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/compras", methods=["GET"])
@token_required
def listar_compras(current_user):
    """Listar todas las compras"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.cliente_id, c.nombre_cliente, c.producto, c.cantidad, 
                       c.precio_unitario, c.total, c.pagado, c.fecha,
                       cl.nombre as cliente_nombre
                FROM compras c
                LEFT JOIN clientes cl ON c.cliente_id = cl.id
                ORDER BY c.fecha DESC
            """)
            compras = [
                {
                    "id": row[0], "cliente_id": row[1], "nombre_cliente": row[2],
                    "producto": row[3], "cantidad": row[4], "precio_unitario": float(row[5]),
                    "total": float(row[6]), "pagado": bool(row[7]), "fecha": row[8],
                    "cliente_nombre": row[9]
                }
                for row in cursor.fetchall()
            ]
            return jsonify(compras)
        except Exception as e:
            app.logger.error(f"Error al obtener compras: {e}")
            return jsonify({"mensaje": "Error al obtener compras"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/compras/deuda", methods=["GET"])
@token_required
def listar_compras_deuda(current_user):
    """Listar compras con deuda (no pagadas)"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.cliente_id, c.nombre_cliente, c.producto, c.cantidad, 
                       c.precio_unitario, c.total, c.pagado, c.fecha,
                       cl.nombre as cliente_nombre
                FROM compras c
                LEFT JOIN clientes cl ON c.cliente_id = cl.id
                WHERE c.pagado = 0
                ORDER BY c.fecha DESC
            """)
            compras = [
                {
                    "id": row[0], "cliente_id": row[1], "nombre_cliente": row[2],
                    "producto": row[3], "cantidad": row[4], "precio_unitario": float(row[5]),
                    "total": float(row[6]), "pagado": bool(row[7]), "fecha": row[8],
                    "cliente_nombre": row[9]
                }
                for row in cursor.fetchall()
            ]
            return jsonify(compras)
        except Exception as e:
            app.logger.error(f"Error al obtener compras con deuda: {e}")
            return jsonify({"mensaje": "Error al obtener compras con deuda"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/compras/cliente/<int:cliente_id>", methods=["GET"])
@token_required
def listar_compras_cliente(current_user, cliente_id):
    """Listar compras de un cliente específico"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.cliente_id, c.nombre_cliente, c.producto, c.cantidad, 
                       c.precio_unitario, c.total, c.pagado, c.fecha
                FROM compras c
                WHERE c.cliente_id = %s
                ORDER BY c.fecha DESC
            """, (cliente_id,))
            compras = [
                {
                    "id": row[0], "cliente_id": row[1], "nombre_cliente": row[2],
                    "producto": row[3], "cantidad": row[4], "precio_unitario": float(row[5]),
                    "total": float(row[6]), "pagado": bool(row[7]), "fecha": row[8]
                }
                for row in cursor.fetchall()
            ]
            return jsonify(compras)
        except Exception as e:
            app.logger.error(f"Error al obtener compras del cliente: {e}")
            return jsonify({"mensaje": "Error al obtener compras del cliente"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/compras/<int:id>/pagar", methods=["PUT"])
@token_required
def marcar_compra_pagada(current_user, id):
    """Marcar compra como pagada"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Verificar que la compra existe y no está pagada
            cursor.execute("SELECT id, nombre_cliente, producto, total, pagado FROM compras WHERE id = %s", (id,))
            compra = cursor.fetchone()
            
            if not compra:
                return jsonify({"mensaje": "Compra no encontrada"}), 404
            
            if compra[4]:  # ya está pagada
                return jsonify({"mensaje": "Esta compra ya está pagada"}), 400
            
            # Marcar como pagada
            cursor.execute("UPDATE compras SET pagado = 1 WHERE id = %s", (id,))
            conn.commit()
            
            return jsonify({
                "mensaje": f"Compra de {compra[1]} ({compra[2]}) marcada como pagada",
                "total_pagado": float(compra[3])
            })
        except Exception as e:
            app.logger.error(f"Error al marcar compra como pagada: {e}")
            return jsonify({"mensaje": "Error al marcar compra como pagada"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000) 