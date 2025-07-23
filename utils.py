"""
Utilidades comunes para Tennis Miligan
"""
import re
from datetime import datetime
from typing import Optional, Dict, Any
from config import get_config

config = get_config()

def validar_fecha(fecha: str) -> bool:
    """Validar formato de fecha (YYYY-MM-DD)"""
    try:
        datetime.strptime(fecha, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validar_horario(horario: str) -> bool:
    """Validar formato de horario (HH:MM)"""
    if horario not in config.HORARIOS_DISPONIBLES:
        return False
    return True

def validar_nombre(nombre: str) -> bool:
    """Validar nombre (no vacío y longitud máxima)"""
    if not nombre or not nombre.strip():
        return False
    if len(nombre.strip()) > config.MAX_NOMBRE_LENGTH:
        return False
    return True

def validar_telefono(telefono: str) -> bool:
    """Validar formato de teléfono"""
    if not telefono:
        return True  # Opcional
    # Patrón básico para teléfonos peruanos
    pattern = r'^(\+51\s?)?[9]\d{8}$'
    return bool(re.match(pattern, telefono.strip()))

def validar_email(email: str) -> bool:
    """Validar formato de email"""
    if not email:
        return True  # Opcional
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def sanitizar_input(texto: str) -> str:
    """Sanitizar entrada de texto"""
    if not texto:
        return ""
    # Remover caracteres peligrosos
    texto = re.sub(r'[<>"\']', '', texto)
    return texto.strip()

def extraer_numero_cancha(cancha: str) -> Optional[int]:
    """Extraer número de cancha del texto"""
    if not cancha:
        return None
    match = re.search(r'(\d+)', cancha)
    return int(match.group(1)) if match else None

def validar_cancha(cancha: str) -> bool:
    """Validar que la cancha esté disponible"""
    return cancha in config.CANCHAS_DISPONIBLES

def validar_precio(precio: float) -> bool:
    """Validar precio (positivo y máximo razonable)"""
    return 0 < precio <= 10000

def validar_cantidad(cantidad: int) -> bool:
    """Validar cantidad (positiva y máxima razonable)"""
    return 0 < cantidad <= 1000

def formatear_fecha(fecha: str) -> str:
    """Formatear fecha para mostrar"""
    try:
        dt = datetime.strptime(fecha, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except ValueError:
        return fecha

def formatear_precio(precio: float) -> str:
    """Formatear precio para mostrar"""
    return f"S/. {precio:.2f}"

def validar_cliente_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar datos de cliente"""
    errores = []
    
    if not validar_nombre(data.get('nombre', '')):
        errores.append("Nombre inválido o muy largo")
    
    if data.get('telefono') and not validar_telefono(data['telefono']):
        errores.append("Formato de teléfono inválido")
    
    if data.get('email') and not validar_email(data['email']):
        errores.append("Formato de email inválido")
    
    return {
        'valido': len(errores) == 0,
        'errores': errores
    }

def validar_reserva_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar datos de reserva"""
    errores = []
    
    if not validar_nombre(data.get('nombre', '')):
        errores.append("Nombre inválido")
    
    if not validar_cancha(data.get('cancha', '')):
        errores.append("Cancha inválida")
    
    if not validar_horario(data.get('horario', '')):
        errores.append("Horario inválido")
    
    if not validar_fecha(data.get('fecha', '')):
        errores.append("Fecha inválida")
    
    return {
        'valido': len(errores) == 0,
        'errores': errores
    }

def validar_producto_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar datos de producto"""
    errores = []
    
    if not validar_nombre(data.get('nombre', '')):
        errores.append("Nombre inválido")
    
    if not validar_precio(data.get('precio', 0)):
        errores.append("Precio inválido")
    
    if not validar_cantidad(data.get('stock', 0)):
        errores.append("Stock inválido")
    
    return {
        'valido': len(errores) == 0,
        'errores': errores
    }

def validar_compra_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar datos de compra"""
    errores = []
    
    if not validar_nombre(data.get('producto', '')):
        errores.append("Producto inválido")
    
    if not validar_cantidad(data.get('cantidad', 0)):
        errores.append("Cantidad inválida")
    
    if not validar_precio(data.get('precio_unitario', 0)):
        errores.append("Precio unitario inválido")
    
    if not validar_precio(data.get('total', 0)):
        errores.append("Total inválido")
    
    return {
        'valido': len(errores) == 0,
        'errores': errores
    }

def calcular_total(cantidad: int, precio_unitario: float) -> float:
    """Calcular total de compra"""
    return round(cantidad * precio_unitario, 2)

def obtener_horarios_disponibles() -> list:
    """Obtener lista de horarios disponibles"""
    return config.HORARIOS_DISPONIBLES

def obtener_canchas_disponibles() -> list:
    """Obtener lista de canchas disponibles"""
    return config.CANCHAS_DISPONIBLES 