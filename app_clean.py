"""
Aplicación principal de Tennis Miligan
Versión limpia y escalable
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os
import logging
from logging.handlers import RotatingFileHandler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Importar módulos propios
from config import get_config
from database import db
from models import Cliente, Reserva, Producto, Compra
from utils import (
    validar_cliente_data, validar_reserva_data, validar_producto_data,
    validar_compra_data, sanitizar_input, calcular_total,
    obtener_horarios_disponibles, obtener_canchas_disponibles
)

# Configuración
config = get_config()
app = Flask(__name__)
app.config.from_object(config)

# Configurar CORS
CORS(app, 
     origins=config.ALLOWED_ORIGINS,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=False)

# Configurar logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
handler = RotatingFileHandler(
    config.LOG_FILE, 
    maxBytes=config.LOG_MAX_BYTES, 
    backupCount=config.LOG_BACKUP_COUNT
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)

# Configurar rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[config.RATE_LIMIT_DAILY, config.RATE_LIMIT_HOURLY]
)

# Inicializar base de datos
db.init_database()

# Decorador para autenticación JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
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
            data = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'mensaje': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'mensaje': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Manejador de errores global
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled Exception: {str(e)}', exc_info=True)
    return jsonify({"mensaje": "Error interno del servidor"}), 500

# Rutas de autenticación
@app.route("/login", methods=["POST"])
def login():
    """Endpoint de login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Credenciales hardcodeadas (en producción usar base de datos)
    if username == "admin" and password == "admin123":
        token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        }, config.JWT_SECRET_KEY, algorithm="HS256")
        
        return jsonify({
            'token': token,
            'mensaje': 'Login exitoso'
        })
    else:
        return jsonify({'mensaje': 'Credenciales incorrectas'}), 401

# Rutas de información
@app.route("/")
def home():
    """Endpoint principal"""
    return jsonify({
        "mensaje": "API de Tennis Miligan funcionando",
        "database": "PostgreSQL" if config.USE_POSTGRES else "SQLite",
        "status": "online",
        "version": "2.0.0"
    })

@app.route("/config")
def get_config_info():
    """Obtener información de configuración"""
    return jsonify({
        "horarios_disponibles": obtener_horarios_disponibles(),
        "canchas_disponibles": obtener_canchas_disponibles(),
        "database_type": "PostgreSQL" if config.USE_POSTGRES else "SQLite"
    })

# Rutas de clientes
@app.route("/clientes", methods=["GET"])
@token_required
def listar_clientes(current_user):
    """Listar todos los clientes"""
    try:
        clientes = Cliente.get_all()
        return jsonify(clientes)
    except Exception as e:
        app.logger.error(f"Error listando clientes: {e}")
        return jsonify({"mensaje": "Error al obtener clientes"}), 500

@app.route("/clientes", methods=["POST"])
@token_required
def crear_cliente(current_user):
    """Crear nuevo cliente"""
    try:
        data = request.get_json()
        
        # Sanitizar datos
        data = {k: sanitizar_input(str(v)) for k, v in data.items()}
        
        # Validar datos
        validacion = validar_cliente_data(data)
        if not validacion['valido']:
            return jsonify({
                "mensaje": "Datos inválidos",
                "errores": validacion['errores']
            }), 400
        
        # Crear cliente
        resultado = Cliente.create(data)
        return jsonify(resultado)
    except Exception as e:
        app.logger.error(f"Error creando cliente: {e}")
        return jsonify({"mensaje": "Error al crear cliente"}), 500

@app.route("/clientes/<int:id>", methods=["PUT"])
@token_required
def actualizar_cliente(current_user, id):
    """Actualizar cliente existente"""
    try:
        data = request.get_json()
        
        # Sanitizar datos
        data = {k: sanitizar_input(str(v)) for k, v in data.items()}
        
        # Validar datos
        validacion = validar_cliente_data(data)
        if not validacion['valido']:
            return jsonify({
                "mensaje": "Datos inválidos",
                "errores": validacion['errores']
            }), 400
        
        # Actualizar cliente
        resultado = Cliente.update(id, data)
        return jsonify(resultado)
    except Exception as e:
        app.logger.error(f"Error actualizando cliente {id}: {e}")
        return jsonify({"mensaje": "Error al actualizar cliente"}), 500

@app.route("/clientes/<int:id>", methods=["DELETE"])
@token_required
def eliminar_cliente(current_user, id):
    """Eliminar cliente"""
    try:
        if Cliente.delete(id):
            return jsonify({"mensaje": "Cliente eliminado correctamente"})
        else:
            return jsonify({"mensaje": "Cliente no encontrado"}), 404
    except Exception as e:
        app.logger.error(f"Error eliminando cliente {id}: {e}")
        return jsonify({"mensaje": "Error al eliminar cliente"}), 500

# Rutas de reservas
@app.route("/reservas", methods=["GET"])
@token_required
def listar_reservas(current_user):
    """Listar todas las reservas"""
    try:
        reservas = Reserva.get_all()
        return jsonify(reservas)
    except Exception as e:
        app.logger.error(f"Error listando reservas: {e}")
        return jsonify({"mensaje": "Error al obtener reservas"}), 500

@app.route("/reservas", methods=["POST"])
@token_required
@limiter.limit(config.RATE_LIMIT_RESERVATIONS)
def crear_reserva(current_user):
    """Crear nueva reserva"""
    try:
        data = request.get_json()
        
        # Sanitizar datos
        data = {k: sanitizar_input(str(v)) for k, v in data.items()}
        
        # Validar datos
        validacion = validar_reserva_data(data)
        if not validacion['valido']:
            return jsonify({
                "mensaje": "Datos inválidos",
                "errores": validacion['errores']
            }), 400
        
        # Crear reserva
        resultado = Reserva.create(data)
        return jsonify(resultado)
    except Exception as e:
        app.logger.error(f"Error creando reserva: {e}")
        return jsonify({"mensaje": "Error al crear reserva"}), 500

@app.route("/reservas/<int:id>", methods=["PUT"])
@token_required
def actualizar_reserva(current_user, id):
    """Actualizar reserva existente"""
    try:
        data = request.get_json()
        
        # Sanitizar datos
        data = {k: sanitizar_input(str(v)) for k, v in data.items()}
        
        # Validar datos
        validacion = validar_reserva_data(data)
        if not validacion['valido']:
            return jsonify({
                "mensaje": "Datos inválidos",
                "errores": validacion['errores']
            }), 400
        
        # Actualizar reserva
        resultado = Reserva.update(id, data)
        return jsonify(resultado)
    except Exception as e:
        app.logger.error(f"Error actualizando reserva {id}: {e}")
        return jsonify({"mensaje": "Error al actualizar reserva"}), 500

@app.route("/reservas/<int:id>", methods=["DELETE"])
@token_required
def eliminar_reserva(current_user, id):
    """Eliminar reserva"""
    try:
        if Reserva.delete(id):
            return jsonify({"mensaje": "Reserva eliminada correctamente"})
        else:
            return jsonify({"mensaje": "Reserva no encontrada"}), 404
    except Exception as e:
        app.logger.error(f"Error eliminando reserva {id}: {e}")
        return jsonify({"mensaje": "Error al eliminar reserva"}), 500

# Rutas de productos
@app.route("/productos", methods=["GET"])
@token_required
def listar_productos(current_user):
    """Listar todos los productos"""
    try:
        productos = Producto.get_all()
        return jsonify(productos)
    except Exception as e:
        app.logger.error(f"Error listando productos: {e}")
        return jsonify({"mensaje": "Error al obtener productos"}), 500

@app.route("/productos", methods=["POST"])
@token_required
def crear_producto(current_user):
    """Crear nuevo producto"""
    try:
        data = request.get_json()
        
        # Sanitizar datos
        data = {k: sanitizar_input(str(v)) for k, v in data.items()}
        
        # Validar datos
        validacion = validar_producto_data(data)
        if not validacion['valido']:
            return jsonify({
                "mensaje": "Datos inválidos",
                "errores": validacion['errores']
            }), 400
        
        # Crear producto
        resultado = Producto.create(data)
        return jsonify(resultado)
    except Exception as e:
        app.logger.error(f"Error creando producto: {e}")
        return jsonify({"mensaje": "Error al crear producto"}), 500

# Rutas de compras
@app.route("/compras", methods=["GET"])
@token_required
def listar_compras(current_user):
    """Listar todas las compras"""
    try:
        compras = Compra.get_all()
        return jsonify(compras)
    except Exception as e:
        app.logger.error(f"Error listando compras: {e}")
        return jsonify({"mensaje": "Error al obtener compras"}), 500

@app.route("/compras", methods=["POST"])
@token_required
def crear_compra(current_user):
    """Crear nueva compra"""
    try:
        data = request.get_json()
        
        # Sanitizar datos
        data = {k: sanitizar_input(str(v)) for k, v in data.items()}
        
        # Calcular total si no se proporciona
        if 'total' not in data or not data['total']:
            data['total'] = calcular_total(
                int(data.get('cantidad', 0)), 
                float(data.get('precio_unitario', 0))
            )
        
        # Validar datos
        validacion = validar_compra_data(data)
        if not validacion['valido']:
            return jsonify({
                "mensaje": "Datos inválidos",
                "errores": validacion['errores']
            }), 400
        
        # Crear compra
        resultado = Compra.create(data)
        return jsonify(resultado)
    except Exception as e:
        app.logger.error(f"Error creando compra: {e}")
        return jsonify({"mensaje": "Error al crear compra"}), 500

if __name__ == "__main__":
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000) 