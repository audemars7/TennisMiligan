from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os
import sqlite3
from sqlite3 import Error
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Configuración completa de CORS
CORS(app, 
     origins=[
         "https://miligan-frontend.onrender.com",
         "http://localhost:5000",
         "http://127.0.0.1:5000",
         "http://localhost:3000",
         "http://localhost:3001"
     ],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

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

# Configuración de la base de datos
DATABASE = 'tennis.db'

# Configuración del rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        return conn
    except Error as e:
        print(e)
    return conn

def init_db():
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            # Crear tabla de reservas (ahora con cliente_id)
            c.execute('''
                CREATE TABLE IF NOT EXISTS reservas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    nombre TEXT NOT NULL,
                    cancha TEXT NOT NULL,
                    horario TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    estado TEXT DEFAULT 'activa',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            ''')
            # Crear tabla de clientes (opcional, pero recomendado)
            c.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT
                )
            ''')
            # Crear tabla de compras
            c.execute('''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    nombre_cliente TEXT,
                    producto TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    total REAL NOT NULL,
                    pagado INTEGER DEFAULT 0,
                    fecha TEXT NOT NULL,
                    reserva_id INTEGER,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            ''')
            # Crear tabla de productos
            c.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    precio REAL NOT NULL
                )
            ''')
            conn.commit()
        except Error as e:
            print(e)
        finally:
            conn.close()
    else:
        print("Error! No se pudo crear la conexión a la base de datos.")

# Inicializar la base de datos al arrancar
init_db()

# Clave secreta para JWT (usar variable de entorno en producción)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'miligan_secret_2025')

# Credenciales de administrador (usar variables de entorno en producción)
ADMIN_CREDENTIALS = {
    os.environ.get('ADMIN_USER', 'admin1'): os.environ.get('ADMIN_PASSWORD', 'pepito2025')
}

# Decorador para proteger rutas
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return '', 200  # Permitir preflight sin token
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
        if not token:
            return jsonify({'mensaje': 'Token no proporcionado'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except:
            return jsonify({'mensaje': 'Token inválido'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route("/login", methods=["POST"])
def login():
    auth = request.get_json()
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'mensaje': 'No se proporcionaron credenciales'}), 401
    
    if auth.get('username') in ADMIN_CREDENTIALS and \
       ADMIN_CREDENTIALS[auth.get('username')] == auth.get('password'):
        token = jwt.encode({
            'username': auth.get('username'),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({'token': token})
    
    return jsonify({'mensaje': 'Credenciales incorrectas'}), 401

# Cargar configuración
def cargar_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "whatsapp": "+51999999999",
            "ubicacion": {
                "direccion": "Av. Tennis 123, Lima",
                "coordenadas": {
                    "lat": "-12.045599",
                    "lng": "-77.031965"
                }
            }
        }

@app.route("/")
def home():
    return "¡Bienvenido a Miligan Tennis Academy API!"

@app.route("/config", methods=["GET"])
def obtener_config():
    return jsonify(cargar_config())

@app.route("/config", methods=["POST"])
@token_required
def actualizar_config(current_user):
    nueva_config = request.get_json()
    try:
        with open('config.json', 'w') as f:
            json.dump(nueva_config, f, indent=4)
        return jsonify({"mensaje": "Configuración actualizada correctamente"}), 200
    except:
        return jsonify({"mensaje": "Error al actualizar la configuración"}), 500

@app.route("/horarios", methods=["GET"])
@token_required
def obtener_horarios(current_user):
    horarios = [
        "06:00 - 07:00",
        "07:00 - 08:00",
        "08:00 - 09:00",
        "09:00 - 10:00",
        "10:00 - 11:00",
        "11:00 - 12:00",
        "12:00 - 13:00",
        "13:00 - 14:00",
        "14:00 - 15:00",
        "15:00 - 16:00",
        "16:00 - 17:00",
        "17:00 - 18:00"
    ]
    return jsonify(horarios)

# Validaciones
def validar_fecha(fecha):
    try:
        datetime.strptime(fecha, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validar_horario(horario):
    patron = r'^\d{2}:\d{2} - \d{2}:\d{2}$'
    return bool(re.match(patron, horario))

def validar_nombre(nombre):
    return bool(nombre and len(nombre) >= 3 and len(nombre) <= 50)

def sanitizar_input(texto):
    if not texto:
        return texto
    return re.sub(r'[<>"/\'%;()&+]', '', texto)

def extraer_numero_cancha(cancha):
    """Permite aceptar '1', '2', 'Cancha 1', 'Cancha 2', etc."""
    if not cancha:
        return None
    match = re.search(r'(\d+)', str(cancha))
    if match:
        num = int(match.group(1))
        if 1 <= num <= 4:
            return str(num)
    return None

@app.route("/reservar", methods=["POST"])
@token_required
@limiter.limit("20 per hour")
def hacer_reserva(current_user):
    data = request.get_json()
    cliente_id = data.get("cliente_id")
    nombre = sanitizar_input(data.get("nombre"))
    cancha = sanitizar_input(data.get("cancha"))
    horario = data.get("horario")
    fecha = data.get("fecha", datetime.now().strftime("%Y-%m-%d"))

    # Validaciones
    if cliente_id is not None:
        if not isinstance(cliente_id, int):
            return jsonify({"mensaje": "ID de cliente inválido"}), 400
    if not validar_nombre(nombre):
        return jsonify({"mensaje": "Nombre inválido"}), 400
    if not validar_horario(horario):
        return jsonify({"mensaje": "Formato de horario inválido"}), 400
    if not validar_fecha(fecha):
        return jsonify({"mensaje": "Formato de fecha inválido"}), 400
    numero_cancha = extraer_numero_cancha(cancha)
    if not numero_cancha:
        return jsonify({"mensaje": "Número de cancha inválido"}), 400

    conn = create_connection()
    if conn is not None:
        try:
            # Verificar si ya existe una reserva
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM reservas 
                WHERE cancha = ? AND horario = ? AND fecha = ? AND estado = 'activa'
            """, (numero_cancha, horario, fecha))
            if cursor.fetchone() is not None:
                return jsonify({"mensaje": "❌ Este horario ya está reservado para esta cancha"}), 400
            # Insertar nueva reserva
            cursor.execute("""
                INSERT INTO reservas (cliente_id, nombre, cancha, horario, fecha)
                VALUES (?, ?, ?, ?, ?)
            """, (cliente_id, nombre, numero_cancha, horario, fecha))
            conn.commit()
            return jsonify({"mensaje": "✅ Reserva guardada correctamente"}), 201
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al procesar la reserva"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/reservas", methods=["GET"])
@token_required
def obtener_reservas(current_user, *args, **kwargs):
    fecha_filtro = request.args.get('fecha')
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            if fecha_filtro:
                cursor.execute("""
                    SELECT id, nombre, cancha, horario, fecha, estado
                    FROM reservas 
                    WHERE fecha = ? AND estado = 'activa'
                    ORDER BY horario
                """, (fecha_filtro,))
            else:
                cursor.execute("""
                    SELECT id, nombre, cancha, horario, fecha, estado
                    FROM reservas 
                    WHERE estado = 'activa'
                    ORDER BY fecha, horario
                """)
            
            reservas = []
            for row in cursor.fetchall():
                reservas.append({
                    "id": row[0],
                    "nombre": row[1],
                    "cancha": row[2],
                    "horario": row[3],
                    "fecha": row[4],
                    "estado": row[5]
                })
            return jsonify(reservas)
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al obtener las reservas"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/admin/reservas", methods=["GET"])
@token_required
def obtener_reservas_admin(current_user):
    return obtener_reservas(current_user)

@app.route("/reservas/tabla", methods=["GET"])
@token_required
def obtener_tabla_reservas(current_user):
    fecha = request.args.get('fecha', datetime.now().strftime("%Y-%m-%d"))
    
    if not validar_fecha(fecha):
        return jsonify({"mensaje": "Formato de fecha inválido"}), 400

    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Obtener todas las reservas para la fecha específica
            cursor.execute("""
                SELECT horario, cancha, nombre, estado
                FROM reservas 
                WHERE fecha = ? AND estado = 'activa'
                ORDER BY horario, cancha
            """, (fecha,))
            
            reservas = cursor.fetchall()
            
            # Crear estructura de tabla
            tabla_reservas = {}
            horarios = obtener_horarios(current_user).get_json()
            
            for horario in horarios:
                tabla_reservas[horario] = {}
                for cancha in range(1, 11):  # 10 canchas
                    tabla_reservas[horario][str(cancha)] = None

            # Llenar la tabla con las reservas
            for reserva in reservas:
                horario, cancha, nombre, estado = reserva
                if horario in tabla_reservas and str(cancha) in tabla_reservas[horario]:
                    tabla_reservas[horario][str(cancha)] = {
                        "nombre": nombre,
                        "estado": estado
                    }

            return jsonify({
                "fecha": fecha,
                "tabla": tabla_reservas
            })
        except Error as e:
            app.logger.error(f"Error al obtener tabla de reservas: {str(e)}")
            return jsonify({"mensaje": "Error al obtener las reservas"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/admin/reservas/<int:id>", methods=["PUT"])
@token_required
def editar_reserva(current_user, id):
    data = request.get_json()
    nombre = sanitizar_input(data.get("nombre"))
    
    if not validar_nombre(nombre):
        return jsonify({"mensaje": "Nombre inválido"}), 400

    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reservas 
                SET nombre = ? 
                WHERE id = ? AND estado = 'activa'
            """, (nombre, id))
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({"mensaje": "✅ Reserva actualizada correctamente"}), 200
            return jsonify({"mensaje": "❌ Reserva no encontrada"}), 404
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al actualizar la reserva"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/admin/reservas/<int:id>", methods=["DELETE"])
@token_required
def eliminar_reserva_admin(current_user, id):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reservas 
                SET estado = 'cancelada' 
                WHERE id = ? AND estado = 'activa'
            """, (id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({"mensaje": "✅ Reserva eliminada correctamente"}), 200
            return jsonify({"mensaje": "❌ Reserva no encontrada"}), 404
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al eliminar la reserva"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

# --- ENDPOINTS PARA CLIENTES ---
@app.route("/clientes", methods=["POST"])
@token_required
def crear_cliente(current_user):
    data = request.get_json()
    nombre = sanitizar_input(data.get("nombre"))
    telefono = sanitizar_input(data.get("telefono"))
    email = sanitizar_input(data.get("email"))
    if not validar_nombre(nombre):
        return jsonify({"mensaje": "Nombre inválido"}), 400
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clientes (nombre, telefono, email)
                VALUES (?, ?, ?)
            """, (nombre, telefono, email))
            conn.commit()
            return jsonify({"mensaje": "Cliente creado correctamente"}), 201
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al crear cliente"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/clientes", methods=["GET"])
@token_required
def listar_clientes(current_user):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, telefono, email FROM clientes")
            clientes = [
                {"id": row[0], "nombre": row[1], "telefono": row[2], "email": row[3]}
                for row in cursor.fetchall()
            ]
            return jsonify(clientes)
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al obtener clientes"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/clientes/<int:id>", methods=["GET"])
@token_required
def obtener_cliente(current_user, id):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, telefono, email FROM clientes WHERE id = ?", (id,))
            row = cursor.fetchone()
            if row:
                return jsonify({"id": row[0], "nombre": row[1], "telefono": row[2], "email": row[3]})
            else:
                return jsonify({"mensaje": "Cliente no encontrado"}), 404
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al obtener cliente"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/clientes/<int:id>", methods=["PUT"])
@token_required
def actualizar_cliente(current_user, id):
    data = request.get_json()
    nombre = data.get("nombre")
    telefono = data.get("telefono")
    email = data.get("email")
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute(
                "UPDATE clientes SET nombre=?, telefono=?, email=? WHERE id=?",
                (nombre, telefono, email, id)
            )
            conn.commit()
            return jsonify({"mensaje": "Cliente actualizado"}), 200
        except Exception as e:
            return jsonify({"mensaje": "Error al actualizar cliente", "error": str(e)}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/clientes/<int:id>", methods=["DELETE"])
@token_required
def eliminar_cliente(current_user, id):
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("DELETE FROM clientes WHERE id=?", (id,))
            conn.commit()
            return jsonify({"mensaje": "Cliente eliminado"}), 200
        except Exception as e:
            return jsonify({"mensaje": "Error al eliminar cliente", "error": str(e)}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

# --- ENDPOINTS PARA COMPRAS ---
@app.route("/compras", methods=["POST"])
@token_required
def registrar_compra(current_user):
    data = request.get_json()
    cliente_id = data.get("cliente_id")
    producto_id = data.get("producto_id")
    cantidad = data.get("cantidad")
    pagado = int(data.get("pagado", 0))
    reserva_id = data.get("reserva_id")
    fecha = data.get("fecha", datetime.now().strftime("%Y-%m-%d"))
    # Validaciones básicas
    if not isinstance(producto_id, int) or not isinstance(cantidad, int) or cantidad <= 0:
        return jsonify({"mensaje": "Datos de compra inválidos"}), 400
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Buscar el producto en la tabla productos
            cursor.execute("SELECT nombre, precio FROM productos WHERE id = ?", (producto_id,))
            producto_row = cursor.fetchone()
            if not producto_row:
                return jsonify({"mensaje": "El producto no existe"}), 400
            nombre_producto, precio_unitario = producto_row
            total = cantidad * precio_unitario
            cursor.execute("""
                INSERT INTO compras (cliente_id, nombre_cliente, producto, cantidad, precio_unitario, total, pagado, fecha, reserva_id)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?)
            """, (cliente_id, nombre_producto, cantidad, precio_unitario, total, pagado, fecha, reserva_id))
            conn.commit()
            return jsonify({"mensaje": "Compra registrada correctamente"}), 201
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al registrar compra"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/compras", methods=["GET"])
@token_required
def listar_compras(current_user):
    cliente_id = request.args.get("cliente_id")
    pagado = request.args.get("pagado")
    fecha = request.args.get("fecha")
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            query = "SELECT id, cliente_id, nombre_cliente, producto, cantidad, precio_unitario, total, pagado, fecha, reserva_id FROM compras WHERE 1=1"
            params = []
            if cliente_id:
                query += " AND cliente_id = ?"
                params.append(cliente_id)
            if pagado is not None:
                query += " AND pagado = ?"
                params.append(pagado)
            if fecha:
                query += " AND fecha = ?"
                params.append(fecha)
            query += " ORDER BY fecha DESC, id DESC"
            cursor.execute(query, tuple(params))
            compras = [
                {
                    "id": row[0],
                    "cliente_id": row[1],
                    "nombre_cliente": row[2],
                    "producto": row[3],
                    "cantidad": row[4],
                    "precio_unitario": row[5],
                    "total": row[6],
                    "pagado": bool(row[7]),
                    "fecha": row[8],
                    "reserva_id": row[9]
                }
                for row in cursor.fetchall()
            ]
            return jsonify(compras)
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al obtener compras"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/compras/deuda", methods=["GET"])
@token_required
def listar_compras_deuda(current_user):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, cliente_id, nombre_cliente, producto, cantidad, precio_unitario, total, fecha, reserva_id
                FROM compras WHERE pagado = 0 ORDER BY fecha DESC, id DESC
            """)
            compras = [
                {
                    "id": row[0],
                    "cliente_id": row[1],
                    "nombre_cliente": row[2],
                    "producto": row[3],
                    "cantidad": row[4],
                    "precio_unitario": row[5],
                    "total": row[6],
                    "fecha": row[7],
                    "reserva_id": row[8]
                }
                for row in cursor.fetchall()
            ]
            return jsonify(compras)
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al obtener compras fiadas"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/compras/cliente/<int:cliente_id>", methods=["GET"])
@token_required
def listar_compras_cliente(current_user, cliente_id):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, producto, cantidad, precio_unitario, total, pagado, fecha, reserva_id
                FROM compras WHERE cliente_id = ? ORDER BY fecha DESC, id DESC
            """, (cliente_id,))
            compras = [
                {
                    "id": row[0],
                    "producto": row[1],
                    "cantidad": row[2],
                    "precio_unitario": row[3],
                    "total": row[4],
                    "pagado": bool(row[5]),
                    "fecha": row[6],
                    "reserva_id": row[7]
                }
                for row in cursor.fetchall()
            ]
            return jsonify(compras)
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al obtener compras del cliente"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

# --- ENDPOINTS PARA PRODUCTOS ---
@app.route("/productos", methods=["GET"])
@token_required
def listar_productos(current_user):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, tipo, precio FROM productos")
            productos = [
                {"id": row[0], "nombre": row[1], "tipo": row[2], "precio": row[3]}
                for row in cursor.fetchall()
            ]
            return jsonify(productos)
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al obtener productos"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

@app.route("/productos", methods=["POST"])
@token_required
def agregar_producto(current_user):
    data = request.get_json()
    nombre = sanitizar_input(data.get("nombre"))
    tipo = sanitizar_input(data.get("tipo"))
    precio = data.get("precio")
    if not nombre or tipo not in ["grip", "bebida"] or not isinstance(precio, (int, float)) or precio <= 0:
        return jsonify({"mensaje": "Datos de producto inválidos"}), 400
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO productos (nombre, tipo, precio) VALUES (?, ?, ?)", (nombre, tipo, precio))
            conn.commit()
            return jsonify({"mensaje": "Producto agregado correctamente"}), 201
        except Error as e:
            print(e)
            return jsonify({"mensaje": "Error al agregar producto"}), 500
        finally:
            conn.close()
    return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
