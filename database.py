"""
Módulo de base de datos para Tennis Miligan
Soporta SQLite y PostgreSQL
"""
import sqlite3
import logging
from contextlib import contextmanager
from config import get_config

config = get_config()
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor de base de datos unificado"""
    
    def __init__(self):
        self.database_url = config.DATABASE_URL
        self.use_postgres = config.USE_POSTGRES
    
    @contextmanager
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        conn = None
        try:
            if self.use_postgres:
                import psycopg2
                conn = psycopg2.connect(self.database_url)
            else:
                conn = sqlite3.connect('tennis.db')
            yield conn
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Inicializar la base de datos con todas las tablas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                self._create_postgres_tables(cursor)
            else:
                self._create_sqlite_tables(cursor)
            
            conn.commit()
            logger.info(f"Base de datos inicializada ({'PostgreSQL' if self.use_postgres else 'SQLite'})")
    
    def _create_postgres_tables(self, cursor):
        """Crear tablas para PostgreSQL"""
        # Tabla clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                telefono VARCHAR(50),
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                precio DECIMAL(10,2) NOT NULL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _create_sqlite_tables(self, cursor):
        """Crear tablas para SQLite"""
        # Tabla clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla reservas
        cursor.execute('''
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
        
        # Tabla productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla compras
        cursor.execute('''
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        ''')
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Ejecutar consulta SQL de forma segura"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount
                
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                logger.error(f"Error ejecutando query: {e}")
                raise

# Instancia global del gestor de base de datos
db = DatabaseManager() 