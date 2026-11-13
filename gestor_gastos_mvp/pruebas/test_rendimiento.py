from time import perf_counter
from datetime import date


def test_5000_registros_rendimiento(repo):
    db,gasto,ingreso=repo
    filas=[('gasto',1000,'2025-10-15','carga',gasto) for _ in range(5000)]
    with db.con:
        db.con.executemany('INSERT INTO movimiento(tipo,monto,fecha,descripcion,categoria_id) VALUES(?,?,?,?,?)',filas)
    tiempos=[]
    for _ in range(10):
        inicio=perf_counter();res=db.resumen_mensual('2025-10');tiempos.append(perf_counter()-inicio)
    assert res['gastos']==5_000_000
    assert max(tiempos)<2.0
