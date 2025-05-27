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
     origins=["https://miligan-frontend.onrender.com", "http://localhost:5000", "http://127.0.0.1:5000"],
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
            # Crear tabla de reservas
            c.execute('''
                CREATE TABLE IF NOT EXISTS reservas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cancha TEXT NOT NULL,
                    horario TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    estado TEXT DEFAULT 'activa',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        token = None
        
        # Verificar si el token está en los headers
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')

        if not token:
            return jsonify({'mensaje': 'Token no proporcionado'}), 401

        try:
            # Verificar el token
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
    nombre = sanitizar_input(data.get("nombre"))
    cancha = sanitizar_input(data.get("cancha"))
    horario = data.get("horario")
    fecha = data.get("fecha", datetime.now().strftime("%Y-%m-%d"))

    # Validaciones
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
                INSERT INTO reservas (nombre, cancha, horario, fecha)
                VALUES (?, ?, ?, ?)
            """, (nombre, numero_cancha, horario, fecha))
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
def obtener_reservas(current_user):
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

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
