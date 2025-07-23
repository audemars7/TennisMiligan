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
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración CORS definitiva - permitir todo en desarrollo
CORS(app, 
     origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=False)

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
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tennis.db')
USE_POSTGRES = DATABASE_URL.startswith('postgresql')

# Configuración del rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_connection():
    """Crear conexión a la base de datos (SQLite o PostgreSQL)"""
    conn = None
    try:
        if USE_POSTGRES:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect('tennis.db')
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
    return conn

def init_db():
    """Inicializar la base de datos con las tablas necesarias"""
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            
            if USE_POSTGRES:
                # Crear tabla de clientes (PostgreSQL)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS clientes (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(255) NOT NULL,
                        telefono VARCHAR(50),
                        email VARCHAR(255)
                    )
                ''')
                
                # Crear tabla de reservas (PostgreSQL)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS reservas (
                        id SERIAL PRIMARY KEY,
                        cliente_id INTEGER,
                        nombre VARCHAR(255) NOT NULL,
                        cancha VARCHAR(100) NOT NULL,
                        horario VARCHAR(50) NOT NULL,
                        fecha VARCHAR(20) NOT NULL,
                        estado VARCHAR(50) DEFAULT 'activa',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                    )
                ''')
                
                # Crear tabla de productos (PostgreSQL)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS productos (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(255) NOT NULL,
                        precio DECIMAL(10,2) NOT NULL,
                        stock INTEGER DEFAULT 0
                    )
                ''')
                
                # Crear tabla de compras (PostgreSQL)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS compras (
                        id SERIAL PRIMARY KEY,
                        cliente_id INTEGER,
                        nombre_cliente VARCHAR(255),
                        producto VARCHAR(255) NOT NULL,
                        cantidad INTEGER NOT NULL,
                        precio_unitario DECIMAL(10,2) NOT NULL,
                        total DECIMAL(10,2) NOT NULL,
                        pagado INTEGER DEFAULT 0,
                        fecha VARCHAR(20) NOT NULL,
                        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                    )
                ''')
            else:
                # Crear tabla de clientes (SQLite)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        telefono TEXT,
                        email TEXT
                    )
                ''')
                
                # Crear tabla de reservas (SQLite)
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
                
                # Crear tabla de productos (SQLite)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS productos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        precio REAL NOT NULL,
                        stock INTEGER DEFAULT 0
                    )
                ''')
                
                # Crear tabla de compras (SQLite)
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
                        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                    )
                ''')
            
            conn.commit()
            conn.close()
            print(f"✅ Base de datos inicializada ({'PostgreSQL' if USE_POSTGRES else 'SQLite'})")
            
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
            conn.close()

# Inicializar la base de datos al arrancar
init_db()

# Configuración JWT
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu_jwt_secret_aqui')

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
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'mensaje': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'mensaje': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Credenciales hardcodeadas por ahora
    if username == "admin" and password == "admin123":
        token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET_KEY, algorithm="HS256")
        
        return jsonify({
            'token': token,
            'mensaje': 'Login exitoso'
        })
    else:
        return jsonify({'mensaje': 'Credenciales incorrectas'}), 401

@app.route("/")
def home():
    return jsonify({
        "mensaje": "API de Tennis Miligan funcionando",
        "database": "PostgreSQL" if USE_POSTGRES else "SQLite",
        "status": "online"
    })

@app.route("/test-cors")
def test_cors():
    return jsonify({"mensaje": "CORS funcionando correctamente"})

# Aquí continuarían todas las rutas existentes...
# Por ahora solo incluimos las funciones básicas de conexión

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000) 