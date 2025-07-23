"""
Modelos de datos para Tennis Miligan
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from database import db
import logging

logger = logging.getLogger(__name__)

class BaseModel:
    """Modelo base con funcionalidades comunes"""
    
    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """Obtener todos los registros"""
        raise NotImplementedError
    
    @classmethod
    def get_by_id(cls, id: int) -> Optional[Dict[str, Any]]:
        """Obtener registro por ID"""
        raise NotImplementedError
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo registro"""
        raise NotImplementedError
    
    @classmethod
    def update(cls, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar registro"""
        raise NotImplementedError
    
    @classmethod
    def delete(cls, id: int) -> bool:
        """Eliminar registro"""
        raise NotImplementedError

class Cliente(BaseModel):
    """Modelo para clientes"""
    
    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        query = """
            SELECT id, nombre, apellido, telefono, email, created_at 
            FROM clientes ORDER BY nombre, apellido
        """
        try:
            result = db.execute_query(query, fetch_all=True)
            return [
                {
                    'id': row[0],
                    'nombre': row[1],
                    'apellido': row[2],
                    'telefono': row[3],
                    'email': row[4],
                    'created_at': row[5]
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error obteniendo clientes: {e}")
            return []
    
    @classmethod
    def get_by_id(cls, id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT id, nombre, apellido, telefono, email, created_at 
            FROM clientes WHERE id = %s
        """
        try:
            result = db.execute_query(query, (id,), fetch_one=True)
            if result:
                return {
                    'id': result[0],
                    'nombre': result[1],
                    'apellido': result[2],
                    'telefono': result[3],
                    'email': result[4],
                    'created_at': result[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error obteniendo cliente {id}: {e}")
            return None
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO clientes (nombre, apellido, telefono, email) 
            VALUES (%s, %s, %s, %s) RETURNING id
        """
        try:
            result = db.execute_query(
                query, 
                (data['nombre'], data.get('apellido'), 
                 data.get('telefono'), data.get('email')),
                fetch_one=True
            )
            if result:
                return {'id': result[0], 'mensaje': 'Cliente creado correctamente'}
            return {'mensaje': 'Error al crear cliente'}
        except Exception as e:
            logger.error(f"Error creando cliente: {e}")
            return {'mensaje': 'Error al crear cliente'}
    
    @classmethod
    def update(cls, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            UPDATE clientes 
            SET nombre = %s, apellido = %s, telefono = %s, email = %s 
            WHERE id = %s
        """
        try:
            result = db.execute_query(
                query,
                (data['nombre'], data.get('apellido'), 
                 data.get('telefono'), data.get('email'), id)
            )
            if result > 0:
                return {'mensaje': 'Cliente actualizado correctamente'}
            return {'mensaje': 'Cliente no encontrado'}
        except Exception as e:
            logger.error(f"Error actualizando cliente {id}: {e}")
            return {'mensaje': 'Error al actualizar cliente'}
    
    @classmethod
    def delete(cls, id: int) -> bool:
        query = "DELETE FROM clientes WHERE id = %s"
        try:
            result = db.execute_query(query, (id,))
            return result > 0
        except Exception as e:
            logger.error(f"Error eliminando cliente {id}: {e}")
            return False

class Reserva(BaseModel):
    """Modelo para reservas"""
    
    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        query = """
            SELECT r.id, r.cliente_id, r.nombre, r.cancha, r.horario, 
                   r.fecha, r.estado, r.created_at, c.nombre as cliente_nombre
            FROM reservas r
            LEFT JOIN clientes c ON r.cliente_id = c.id
            ORDER BY r.fecha DESC, r.horario
        """
        try:
            result = db.execute_query(query, fetch_all=True)
            return [
                {
                    'id': row[0],
                    'cliente_id': row[1],
                    'nombre': row[2],
                    'cancha': row[3],
                    'horario': row[4],
                    'fecha': row[5],
                    'estado': row[6],
                    'created_at': row[7],
                    'cliente_nombre': row[8]
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error obteniendo reservas: {e}")
            return []
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO reservas (cliente_id, nombre, cancha, horario, fecha) 
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        try:
            result = db.execute_query(
                query,
                (data['cliente_id'], data['nombre'], data['cancha'], 
                 data['horario'], data['fecha']),
                fetch_one=True
            )
            if result:
                return {'id': result[0], 'mensaje': 'Reserva creada correctamente'}
            return {'mensaje': 'Error al crear reserva'}
        except Exception as e:
            logger.error(f"Error creando reserva: {e}")
            return {'mensaje': 'Error al crear reserva'}
    
    @classmethod
    def update(cls, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            UPDATE reservas 
            SET nombre = %s, cancha = %s, horario = %s, fecha = %s, estado = %s
            WHERE id = %s
        """
        try:
            result = db.execute_query(
                query,
                (data['nombre'], data['cancha'], data['horario'], 
                 data['fecha'], data.get('estado', 'activa'), id)
            )
            if result > 0:
                return {'mensaje': 'Reserva actualizada correctamente'}
            return {'mensaje': 'Reserva no encontrada'}
        except Exception as e:
            logger.error(f"Error actualizando reserva {id}: {e}")
            return {'mensaje': 'Error al actualizar reserva'}
    
    @classmethod
    def delete(cls, id: int) -> bool:
        query = "DELETE FROM reservas WHERE id = %s"
        try:
            result = db.execute_query(query, (id,))
            return result > 0
        except Exception as e:
            logger.error(f"Error eliminando reserva {id}: {e}")
            return False

class Producto(BaseModel):
    """Modelo para productos"""
    
    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        query = "SELECT id, nombre, precio, stock, created_at FROM productos ORDER BY nombre"
        try:
            result = db.execute_query(query, fetch_all=True)
            return [
                {
                    'id': row[0],
                    'nombre': row[1],
                    'precio': float(row[2]),
                    'stock': row[3],
                    'created_at': row[4]
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error obteniendo productos: {e}")
            return []
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO productos (nombre, precio, stock) 
            VALUES (%s, %s, %s) RETURNING id
        """
        try:
            result = db.execute_query(
                query,
                (data['nombre'], data['precio'], data.get('stock', 0)),
                fetch_one=True
            )
            if result:
                return {'id': result[0], 'mensaje': 'Producto creado correctamente'}
            return {'mensaje': 'Error al crear producto'}
        except Exception as e:
            logger.error(f"Error creando producto: {e}")
            return {'mensaje': 'Error al crear producto'}

class Compra(BaseModel):
    """Modelo para compras"""
    
    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        query = """
            SELECT c.id, c.cliente_id, c.nombre_cliente, c.producto, 
                   c.cantidad, c.precio_unitario, c.total, c.pagado, 
                   c.fecha, c.created_at, cl.nombre as cliente_nombre
            FROM compras c
            LEFT JOIN clientes cl ON c.cliente_id = cl.id
            ORDER BY c.fecha DESC
        """
        try:
            result = db.execute_query(query, fetch_all=True)
            return [
                {
                    'id': row[0],
                    'cliente_id': row[1],
                    'nombre_cliente': row[2],
                    'producto': row[3],
                    'cantidad': row[4],
                    'precio_unitario': float(row[5]),
                    'total': float(row[6]),
                    'pagado': bool(row[7]),
                    'fecha': row[8],
                    'created_at': row[9],
                    'cliente_nombre': row[10]
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error obteniendo compras: {e}")
            return []
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO compras (cliente_id, nombre_cliente, producto, 
                                cantidad, precio_unitario, total, pagado, fecha) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        try:
            result = db.execute_query(
                query,
                (data['cliente_id'], data['nombre_cliente'], data['producto'],
                 data['cantidad'], data['precio_unitario'], data['total'],
                 data.get('pagado', 0), data['fecha']),
                fetch_one=True
            )
            if result:
                return {'id': result[0], 'mensaje': 'Compra registrada correctamente'}
            return {'mensaje': 'Error al registrar compra'}
        except Exception as e:
            logger.error(f"Error creando compra: {e}")
            return {'mensaje': 'Error al registrar compra'} 