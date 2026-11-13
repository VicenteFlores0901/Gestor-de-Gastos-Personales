"""Servicio de persistencia parametrizada y transaccional."""
import sqlite3
from typing import Any
from negocio.movimiento import (Movimiento, ValidacionError, validar_nombre_categoria,
                                validar_tipo, validar_categoria_id)


class Repositorio:
    """Interfaz CRUD sobre una conexión sqlite3 gestionada por el llamador."""

    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def crear_categoria(self, nombre: str, tipo: str) -> int:
        nombre = validar_nombre_categoria(nombre)
        tipo = validar_tipo(tipo)
        with self.con:
            cur = self.con.execute('INSERT INTO categoria(nombre,tipo) VALUES(?,?)', (nombre, tipo))
        return int(cur.lastrowid)

    def categorias(self, tipo: str | None = None) -> list[dict[str, Any]]:
        if tipo is None:
            cursor = self.con.execute('SELECT id,nombre,tipo FROM categoria ORDER BY tipo,nombre')
        else:
            cursor = self.con.execute('SELECT id,nombre,tipo FROM categoria WHERE tipo=? ORDER BY nombre',
                                      (validar_tipo(tipo),))
        return [dict(fila) for fila in cursor.fetchall()]

    def editar_categoria(self, categoria_id: object, nombre: str, tipo: str) -> None:
        ident = validar_categoria_id(categoria_id)
        nombre = validar_nombre_categoria(nombre)
        tipo = validar_tipo(tipo)
        with self.con:
            cur = self.con.execute('UPDATE categoria SET nombre=?,tipo=? WHERE id=?', (nombre,tipo,ident))
            if not cur.rowcount:
                raise ValidacionError('Categoría no encontrada.')

    def eliminar_categoria(self, categoria_id: object) -> None:
        ident = validar_categoria_id(categoria_id)
        with self.con:
            cur = self.con.execute('DELETE FROM categoria WHERE id=?', (ident,))
            if not cur.rowcount:
                raise ValidacionError('Categoría no encontrada.')

    def _verificar_categoria(self, mov: Movimiento) -> None:
        row = self.con.execute('SELECT tipo FROM categoria WHERE id=?', (mov.categoria_id,)).fetchone()
        if row is None or row['tipo'] != mov.tipo:
            raise ValidacionError('Categoría inexistente o incompatible con tipo.')

    def registrar(self, tipo: object, monto: object, fecha: object,
                  categoria_id: object, descripcion: object = '') -> int:
        mov = Movimiento.construir(tipo, monto, fecha, categoria_id, descripcion)
        with self.con:
            self._verificar_categoria(mov)
            cur = self.con.execute(
                'INSERT INTO movimiento(tipo,monto,fecha,categoria_id,descripcion) VALUES (?,?,?,?,?)',
                (mov.tipo,mov.monto,mov.fecha,mov.categoria_id,mov.descripcion))
        return int(cur.lastrowid)

    def editar_movimiento(self, ident: object, tipo: object, monto: object, fecha: object,
                         categoria_id: object, descripcion: object = '') -> None:
        ident = validar_categoria_id(ident)
        mov = Movimiento.construir(tipo,monto,fecha,categoria_id,descripcion)
        with self.con:
            self._verificar_categoria(mov)
            cur = self.con.execute(
                'UPDATE movimiento SET tipo=?,monto=?,fecha=?,categoria_id=?,descripcion=? WHERE id=?',
                (mov.tipo,mov.monto,mov.fecha,mov.categoria_id,mov.descripcion,ident))
            if not cur.rowcount:
                raise ValidacionError('Movimiento no encontrado.')

    def eliminar_movimiento(self, ident: object) -> None:
        ident = validar_categoria_id(ident)
        with self.con:
            cur = self.con.execute('DELETE FROM movimiento WHERE id=?',(ident,))
            if not cur.rowcount:
                raise ValidacionError('Movimiento no encontrado.')

    @staticmethod
    def _limitar_periodo(mes: str) -> tuple[str,str]:
        import re
        from datetime import date
        if not isinstance(mes,str) or not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',mes):
            raise ValidacionError('Mes debe ser AAAA-MM.')
        anio,numero = map(int,mes.split('-'))
        if not 1 <= anio <= 9999:
            raise ValidacionError('Año fuera de rango.')
        siguiente = f'{anio+1:04d}-01' if numero == 12 else f'{anio:04d}-{numero+1:02d}'
        if numero == 12 and anio == 9999:
            siguiente='9999-12-32'  # cota exclusiva sintética superior
        return mes+'-01',siguiente+'-01' if numero != 12 or anio != 9999 else siguiente

    def movimientos(self, mes: str | None = None, categoria_id: object | None = None) -> list[dict]:
        params = []
        sql = ('SELECT m.id,m.tipo,m.monto,m.fecha,m.descripcion,m.categoria_id,c.nombre AS categoria '
               'FROM movimiento m JOIN categoria c ON c.id=m.categoria_id WHERE 1=1')
        if mes:
            inicio,fin = self._limitar_periodo(mes)
            sql += ' AND m.fecha>=? AND m.fecha<?'
            params.extend([inicio,fin])
        if categoria_id not in (None,''):
            sql += ' AND m.categoria_id=?'
            params.append(validar_categoria_id(categoria_id))
        sql += ' ORDER BY m.fecha DESC, m.id DESC'
        return [dict(row) for row in self.con.execute(sql,params).fetchall()]

    def resumen_mensual(self, mes: str) -> dict:
        inicio,fin=self._limitar_periodo(mes)
        rows=self.con.execute('SELECT tipo,COALESCE(SUM(monto),0) AS total FROM movimiento '
                              'WHERE fecha>=? AND fecha<? GROUP BY tipo',(inicio,fin)).fetchall()
        totales={r['tipo']:r['total'] for r in rows}
        ingresos=totales.get('ingreso',0)
        gastos=totales.get('gasto',0)
        return {'mes':mes,'ingresos':ingresos,'gastos':gastos,'saldo':ingresos-gastos}

    def gastos_por_categoria(self, mes: str) -> list[dict]:
        inicio,fin=self._limitar_periodo(mes)
        filas=self.con.execute(
            'SELECT c.nombre AS categoria, SUM(m.monto) AS total FROM movimiento m '
            'JOIN categoria c ON c.id=m.categoria_id '
            "WHERE m.tipo='gasto' AND m.fecha>=? AND m.fecha<? "
            'GROUP BY c.id,c.nombre ORDER BY total DESC,c.nombre', (inicio,fin)).fetchall()
        return [dict(fila) for fila in filas]

    def prueba_integridad(self) -> str:
        return self.con.execute('PRAGMA integrity_check').fetchone()[0]
