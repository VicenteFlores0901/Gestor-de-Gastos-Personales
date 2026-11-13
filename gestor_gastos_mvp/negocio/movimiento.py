"""Modelo y validaciones de ingresos y gastos (CLP, sin decimales)."""
from dataclasses import dataclass
from datetime import date, datetime
import re

MAX_MONTO = 999_999_999
MAX_DESCRIPCION = 120
TIPOS = ('ingreso', 'gasto')


class ValidacionError(ValueError):
    """Señala una entrada que viola una regla del negocio."""


def validar_tipo(tipo: str) -> str:
    if not isinstance(tipo, str) or tipo.strip().lower() not in TIPOS:
        raise ValidacionError('Tipo debe ser ingreso o gasto.')
    return tipo.strip().lower()


def validar_monto(monto: object) -> int:
    """No acepta decimales, booleanos ni sintaxis de conversión permisiva."""
    if isinstance(monto, bool) or not re.fullmatch(r'[0-9]+', str(monto).strip()):
        raise ValidacionError('Monto debe ser entero positivo en CLP.')
    valor = int(str(monto).strip())
    if not 0 < valor <= MAX_MONTO:
        raise ValidacionError('Monto fuera del rango permitido.')
    return valor


def validar_fecha(valor: object) -> str:
    if valor is None or valor == '':
        return date.today().isoformat()
    if isinstance(valor, datetime):
        valor = valor.date()
    if isinstance(valor, date):
        fecha = valor
    else:
        texto = str(valor)
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', texto):
            raise ValidacionError('Fecha debe ser AAAA-MM-DD.')
        try:
            fecha = date.fromisoformat(texto)
        except ValueError as error:
            raise ValidacionError('Fecha inexistente.') from error
    if fecha > date.today():
        raise ValidacionError('Fecha futura no permitida.')
    return fecha.isoformat()


def validar_descripcion(descripcion: object) -> str:
    if descripcion is None:
        return ''
    if not isinstance(descripcion, str):
        raise ValidacionError('Descripción debe ser texto.')
    texto = descripcion.strip()
    if len(texto) > MAX_DESCRIPCION or '\x00' in texto:
        raise ValidacionError('Descripción inválida o demasiado larga.')
    return texto


def validar_categoria_id(categoria_id: object) -> int:
    if isinstance(categoria_id, bool) or not re.fullmatch(r'[0-9]+', str(categoria_id).strip()):
        raise ValidacionError('Seleccione categoría válida.')
    valor = int(str(categoria_id).strip())
    if valor <= 0:
        raise ValidacionError('Seleccione categoría válida.')
    return valor


def validar_nombre_categoria(nombre: object) -> str:
    if not isinstance(nombre, str) or not 1 <= len(nombre.strip()) <= 60:
        raise ValidacionError('Nombre de categoría debe tener entre 1 y 60 caracteres.')
    if '\x00' in nombre:
        raise ValidacionError('Nombre de categoría inválido.')
    return nombre.strip()


@dataclass(frozen=True)
class Movimiento:
    """Objeto de transferencia validado para la capa de persistencia."""
    tipo: str
    monto: int
    fecha: str
    categoria_id: int
    descripcion: str = ''

    @classmethod
    def construir(cls, tipo: object, monto: object, fecha: object,
                  categoria_id: object, descripcion: object = '') -> 'Movimiento':
        return cls(validar_tipo(tipo), validar_monto(monto), validar_fecha(fecha),
                   validar_categoria_id(categoria_id), validar_descripcion(descripcion))
