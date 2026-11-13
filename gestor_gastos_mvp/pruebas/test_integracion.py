import sqlite3
import pytest
from negocio.movimiento import ValidacionError
from datos.conexion import abrir_db
from datos.repositorio import Repositorio


def test_crud_movimientos_y_resumen(repo):
    db,gasto,ingreso=repo
    id1=db.registrar('ingreso','100000','2025-06-07',ingreso,'Sueldo')
    id2=db.registrar('gasto','35000','2025-06-08',gasto,'Compras')
    assert db.resumen_mensual('2025-06')=={'mes':'2025-06','ingresos':100000,'gastos':35000,'saldo':65000}
    assert len(db.movimientos('2025-06'))==2
    db.editar_movimiento(id2,'gasto','15000','2025-06-08',gasto,'Ajuste')
    assert db.resumen_mensual('2025-06')['saldo']==85000
    db.eliminar_movimiento(id1)
    assert db.resumen_mensual('2025-06')['ingresos']==0


def test_categorias_edicion_y_restrict(repo):
    db,gasto,ingreso=repo
    db.editar_categoria(gasto,'Comida','gasto')
    assert db.categorias('gasto')[0]['nombre']=='Comida'
    db.registrar('gasto',9000,'2025-05-01',gasto,'Prueba')
    with pytest.raises(sqlite3.IntegrityError):db.eliminar_categoria(gasto)
    assert db.movimientos('2025-05')[0]['categoria']=='Comida'
    db.eliminar_categoria(ingreso)
    assert len(db.categorias())==1


def test_categoria_incompatible_rechazada(repo):
    db,gasto,ingreso=repo
    with pytest.raises(ValidacionError):db.registrar('gasto',100,'2025-01-01',ingreso)
    with pytest.raises(ValidacionError):db.registrar('gasto',100,'2025-01-01',999)
    assert db.movimientos()==[]


def test_restriccion_trigger_en_sql(repo):
    db,gasto,ingreso=repo
    with pytest.raises(sqlite3.IntegrityError):
        with db.con:
            db.con.execute("INSERT INTO movimiento(tipo,monto,fecha,descripcion,categoria_id) VALUES(?,?,?,?,?)",
                           ('gasto',100,'2025-01-01','prueba',ingreso))
    assert db.prueba_integridad()=='ok'


def test_inyeccion_sql_literal(repo):
    db,gasto,ingreso=repo
    payload="x'); DROP TABLE movimiento; --"
    db.registrar('gasto','200','2025-01-01',gasto,payload)
    rows=db.movimientos('2025-01')
    assert rows[0]['descripcion']==payload
    assert db.con.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='movimiento'").fetchone()[0]==1


def test_filtro_categoria_y_mes(repo):
    db,gasto,ingreso=repo
    otro=db.crear_categoria('Transporte','gasto')
    db.registrar('gasto',100,'2025-03-01',gasto,'A')
    db.registrar('gasto',200,'2025-03-02',otro,'B')
    db.registrar('gasto',300,'2025-04-02',gasto,'C')
    assert len(db.movimientos('2025-03'))==2
    assert len(db.movimientos('2025-03',gasto))==1
    assert len(db.movimientos('2025-04',gasto))==1
    assert len(db.movimientos('2025-05'))==0
    graf=db.gastos_por_categoria('2025-03')
    assert [x['total'] for x in graf]==[200,100]


def test_suma_negativa_y_diciembre(repo):
    db,gasto,ingreso=repo
    db.registrar('gasto',1000,'2024-12-31',gasto)
    db.registrar('ingreso',500,'2025-01-01',ingreso)
    assert db.resumen_mensual('2024-12')['saldo']==-1000
    assert db.resumen_mensual('2025-01')['saldo']==500


def test_casos_error(repo):
    db,gasto,ingreso=repo
    with pytest.raises(ValidacionError):db.editar_movimiento(999,'gasto',50,'2025-01-01',gasto)
    with pytest.raises(ValidacionError):db.eliminar_movimiento(999)
    with pytest.raises(ValidacionError):db.editar_categoria(999,'No existe','gasto')
    with pytest.raises(ValidacionError):db.eliminar_categoria(999)
    with pytest.raises(sqlite3.IntegrityError):db.crear_categoria('Alimentación','gasto')
    with pytest.raises(ValidacionError):db.movimientos('2025-00')


def test_actualizacion_categoria_tipo_con_movimiento(repo):
    db,gasto,ingreso=repo
    db.registrar('gasto',100,'2025-01-01',gasto)
    with pytest.raises(sqlite3.IntegrityError):db.editar_categoria(gasto,'Alimentación','ingreso')
    assert db.categorias('gasto')[0]['id']==gasto


def test_archivo_persistente_y_fk(tmp_path):
    ruta=tmp_path/'test'/'gastos.db'
    con=abrir_db(ruta)
    db=Repositorio(con)
    ident=db.crear_categoria('Prueba','gasto')
    db.registrar('gasto',1500,'2025-01-01',ident)
    con.close()
    con=abrir_db(ruta)
    assert Repositorio(con).resumen_mensual('2025-01')['gastos']==1500
    assert con.execute('PRAGMA foreign_keys').fetchone()[0]==1
    con.close()
