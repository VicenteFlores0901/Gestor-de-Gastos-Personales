"""Benchmark reproducible para 5000 movimientos y diez iteraciones."""
from time import perf_counter
import json
from statistics import mean
from datos.conexion import abrir_db
from datos.repositorio import Repositorio

con=abrir_db()
repo=Repositorio(con)
cat=repo.crear_categoria('Comida','gasto')
with con:
    con.executemany('INSERT INTO movimiento(tipo,monto,fecha,descripcion,categoria_id) VALUES(?,?,?,?,?)',
                    [('gasto',1000,'2025-10-15','prueba',cat)]*5000)
# calentamiento, no pertenece a las diez medidas
repo.resumen_mensual('2025-10')
tiempos=[]
for i in range(10):
    t0=perf_counter()
    resultado=repo.resumen_mensual('2025-10')
    tiempos.append(round((perf_counter()-t0)*1000,4))
plan=[r[3] for r in con.execute(
  'EXPLAIN QUERY PLAN SELECT tipo, COALESCE(SUM(monto),0) FROM movimiento WHERE fecha>=? AND fecha<? GROUP BY tipo',
  ('2025-10-01','2025-11-01'))]
reporte={'escenario':'5000 gastos de CLP 1000 en octubre 2025; 10 ejecuciones, SQLite en memoria',
        'esperado_gastos':5000000,'observado_gastos':resultado['gastos'],
        'n_ejecuciones':len(tiempos),'muestras_ms':tiempos,
        'promedio_ms':round(mean(tiempos),4),'max_ms':max(tiempos),
        'plan_consulta':plan,'resultado':'APROBADO' if max(tiempos)<2000 else 'RECHAZADO'}
print(json.dumps(reporte,ensure_ascii=False,indent=2))
con.close()
