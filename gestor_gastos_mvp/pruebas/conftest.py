import pytest
from datos.conexion import abrir_db
from datos.repositorio import Repositorio


@pytest.fixture()
def repo():
    con = abrir_db()
    db = Repositorio(con)
    gasto = db.crear_categoria('Alimentación','gasto')
    ingreso = db.crear_categoria('Trabajo','ingreso')
    yield db, gasto, ingreso
    con.close()
