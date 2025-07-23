#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a PostgreSQL
Uso: python migrate_to_postgres.py
"""

import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_sqlite_data():
    """Obtener todos los datos de SQLite"""
    conn = sqlite3.connect('tennis.db')
    cursor = conn.cursor()
    
    # Obtener datos de clientes
    cursor.execute("SELECT id, nombre, telefono, email FROM clientes")
    clientes = cursor.fetchall()
    
    # Obtener datos de reservas
    cursor.execute("SELECT id, cliente_id, nombre, cancha, horario, fecha, estado, created_at FROM reservas")
    reservas = cursor.fetchall()
    
    # Obtener datos de productos
    try:
        cursor.execute("SELECT id, nombre, precio, stock FROM productos")
        productos = cursor.fetchall()
    except sqlite3.OperationalError:
        # Si no existe la columna stock, usar solo nombre y precio
        cursor.execute("SELECT id, nombre, precio FROM productos")
        productos = [(id, nombre, precio, 0) 
                     for id, nombre, precio in cursor.fetchall()]
    
    # Obtener datos de compras
    cursor.execute("SELECT id, cliente_id, nombre_cliente, producto, cantidad, precio_unitario, total, pagado, fecha FROM compras")
    compras = cursor.fetchall()
    
    conn.close()
    
    return {
        'clientes': clientes,
        'reservas': reservas,
        'productos': productos,
        'compras': compras
    }

def create_tables(cursor):
    """Crear tablas en PostgreSQL si no existen"""
    print("📋 Creando tablas...")
    
    # Tabla clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            apellido VARCHAR(255),
            telefono VARCHAR(50),
            email VARCHAR(255)
        )
    """)
    
    # Agregar columna apellido si no existe
    try:
        cursor.execute("ALTER TABLE clientes ADD COLUMN apellido VARCHAR(255)")
    except Exception:
        pass  # La columna ya existe
    
    # Tabla reservas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER,
            nombre VARCHAR(255) NOT NULL,
            cancha VARCHAR(100) NOT NULL,
            horario VARCHAR(50) NOT NULL,
            fecha DATE NOT NULL,
            estado VARCHAR(50) DEFAULT 'activa',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla productos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            precio DECIMAL(10,2) NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)
    
    # Tabla compras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER,
            nombre_cliente VARCHAR(255),
            producto VARCHAR(255),
            cantidad INTEGER,
            precio_unitario DECIMAL(10,2),
            total DECIMAL(10,2),
            pagado BOOLEAN DEFAULT FALSE,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def migrate_to_postgres(data):
    """Migrar datos a PostgreSQL"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url or database_url.startswith('sqlite'):
        print("❌ DATABASE_URL no configurado para PostgreSQL")
        print("Configura la variable DATABASE_URL en tu archivo .env")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Crear tablas primero
        create_tables(cursor)
        
        print("🔄 Migrando datos a PostgreSQL...")
        
        # Migrar clientes
        print("📋 Migrando clientes...")
        for cliente in data['clientes']:
            cursor.execute("""
                INSERT INTO clientes (id, nombre, telefono, email) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, cliente)
        
        # Migrar productos
        print("📦 Migrando productos...")
        for producto in data['productos']:
            cursor.execute("""
                INSERT INTO productos (id, nombre, precio, stock) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, producto)
        
        # Migrar reservas
        print("🎾 Migrando reservas...")
        for reserva in data['reservas']:
            cursor.execute("""
                INSERT INTO reservas (id, cliente_id, nombre, cancha, horario, fecha, estado, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, reserva)
        
        # Migrar compras
        print("💰 Migrando compras...")
        for compra in data['compras']:
            cursor.execute("""
                INSERT INTO compras (id, cliente_id, nombre_cliente, producto, cantidad, precio_unitario, total, pagado, fecha) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, compra)
        
        conn.commit()
        conn.close()
        
        print("✅ Migración completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

def main():
    print("🚀 Iniciando migración de SQLite a PostgreSQL...")
    
    # Verificar que existe el archivo SQLite
    if not os.path.exists('tennis.db'):
        print("❌ No se encontró el archivo tennis.db")
        return
    
    # Obtener datos de SQLite
    print("📥 Extrayendo datos de SQLite...")
    data = get_sqlite_data()
    
    print(f"📊 Datos encontrados:")
    print(f"   - Clientes: {len(data['clientes'])}")
    print(f"   - Reservas: {len(data['reservas'])}")
    print(f"   - Productos: {len(data['productos'])}")
    print(f"   - Compras: {len(data['compras'])}")
    
    # Migrar a PostgreSQL
    if migrate_to_postgres(data):
        print("\n🎉 ¡Migración completada!")
        print("💡 Recuerda actualizar tu DATABASE_URL en producción")
    else:
        print("\n❌ La migración falló")

if __name__ == "__main__":
    main() 