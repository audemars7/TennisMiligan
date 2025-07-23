#!/usr/bin/env python3
"""
Script para agregar la columna apellido a la tabla clientes
"""

import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def add_apellido_column():
    """Agregar columna apellido a la tabla clientes"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url or database_url.startswith('sqlite'):
        print("❌ DATABASE_URL no configurado para PostgreSQL")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔄 Agregando columna apellido...")
        
        # Verificar si la columna ya existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='clientes' AND column_name='apellido'
        """)
        
        if cursor.fetchone():
            print("✅ La columna 'apellido' ya existe en la tabla clientes")
        else:
            # Agregar la columna apellido
            cursor.execute(
                "ALTER TABLE clientes ADD COLUMN apellido VARCHAR(255)"
            )
            conn.commit()
            print("✅ Columna 'apellido' agregada exitosamente")
        
        # Mostrar estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='clientes' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Estructura actual de la tabla clientes:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    add_apellido_column() 