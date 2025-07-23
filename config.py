"""
Configuración centralizada para Tennis Miligan
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Base de datos
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tennis.db')
    USE_POSTGRES = DATABASE_URL.startswith('postgresql')
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 
                               'http://localhost:3000,http://localhost:3001,http://localhost:3002').split(',')
    
    # Rate limiting
    RATE_LIMIT_DAILY = "200 per day"
    RATE_LIMIT_HOURLY = "50 per hour"
    RATE_LIMIT_RESERVATIONS = "20 per hour"
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/app.log'
    LOG_MAX_BYTES = 10000
    LOG_BACKUP_COUNT = 3
    
    # JWT
    JWT_EXPIRATION_HOURS = 24
    
    # Validaciones
    MAX_NOMBRE_LENGTH = 255
    MAX_TELEFONO_LENGTH = 50
    MAX_EMAIL_LENGTH = 255
    MAX_CANCHA_LENGTH = 100
    MAX_HORARIO_LENGTH = 50
    MAX_FECHA_LENGTH = 20
    MAX_PRODUCTO_LENGTH = 255
    
    # Horarios disponibles
    HORARIOS_DISPONIBLES = [
        "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
        "18:00", "19:00", "20:00", "21:00", "22:00"
    ]
    
    # Canchas disponibles
    CANCHAS_DISPONIBLES = ["Cancha 1", "Cancha 2", "Cancha 3"]

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'

# Configuración por entorno
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Obtener configuración según el entorno"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default']) 