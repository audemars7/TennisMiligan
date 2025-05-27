from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os

app = Flask(__name__)
CORS(app, 
     origins=["https://miligan-frontend.onrender.com", "http://localhost:5000", "http://127.0.0.1:5000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

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

# Lista temporal de reservas (por ahora en memoria)
reservas = []

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

@app.route("/reservar", methods=["POST"])
@token_required
def hacer_reserva(current_user):
    data = request.get_json()
    
    nombre = data.get("nombre")
    cancha = data.get("cancha")
    horario = data.get("horario")
    fecha = data.get("fecha", datetime.now().strftime("%Y-%m-%d"))
    
    # Validar que no exista una reserva para la misma cancha y horario en la misma fecha
    for reserva in reservas:
        if (reserva["cancha"] == cancha and 
            reserva["horario"] == horario and 
            reserva["fecha"] == fecha):
            return jsonify({"mensaje": "❌ Este horario ya está reservado para esta cancha"}), 400
    
    nueva_reserva = {
        "id": len(reservas),
        "nombre": nombre,
        "cancha": cancha,
        "horario": horario,
        "fecha": fecha,
        "estado": "activa"
    }
    
    reservas.append(nueva_reserva)
    return jsonify({"mensaje": "✅ Reserva guardada correctamente"}), 201

@app.route("/reservas", methods=["GET"])
@token_required
def obtener_reservas(current_user):
    fecha_filtro = request.args.get('fecha')
    if fecha_filtro:
        return jsonify([r for r in reservas if r["fecha"] == fecha_filtro])
    return jsonify(reservas)

@app.route("/reservas/<int:id>", methods=["DELETE"])
@token_required
def eliminar_reserva(current_user, id):
    for i, reserva in enumerate(reservas):
        if reserva["id"] == id:
            reservas.pop(i)
            return jsonify({"mensaje": "✅ Reserva eliminada correctamente"}), 200
    return jsonify({"mensaje": "❌ Reserva no encontrada"}), 404

@app.route("/admin/reservas", methods=["GET"])
@token_required
def obtener_reservas_admin(current_user):
    return jsonify(reservas)

@app.errorhandler(404)
def not_found(e):
    response = jsonify({'mensaje': 'No encontrado'})
    response.status_code = 404
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
