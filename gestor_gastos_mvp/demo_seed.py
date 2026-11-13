"""Crear datos SINTÉTICOS para capturas, sin mezclar con la BD real del usuario."""
from datos.conexion import abrir_db
from datos.repositorio import Repositorio
from pathlib import Path
from datetime import date
import sys
ruta=Path(sys.argv[1] if len(sys.argv)>1 else 'demo_gastos.db')
if ruta.exists():
    raise SystemExit('La base ya existe. Use una ruta nueva para evitar sobrescribir datos.')
con=abrir_db(ruta)
db=Repositorio(con)
categorias={}
for nombre,tipo in [('Trabajo','ingreso'),('Mesada','ingreso'),('Alimentación','gasto'),('Transporte','gasto'),('Servicios','gasto'),('Ocio','gasto')]:
    categorias[nombre]=db.crear_categoria(nombre,tipo)
mes=date.today().strftime('%Y-%m')
for tipo,monto,dia,nombre,desc in [
    ('ingreso',170000,1,'Trabajo','Ingreso semanal'),('ingreso',100000,2,'Mesada','Aporte mensual'),
    ('ingreso',45000,5,'Trabajo','Trabajo adicional'),('gasto',26500,3,'Alimentación','Supermercado'),
    ('gasto',16000,4,'Transporte','Recarga bip'),('gasto',36000,6,'Servicios','Aporte al hogar'),
    ('gasto',12000,7,'Ocio','Salida de fin de semana'),('gasto',8500,8,'Alimentación','Colación')]:
    db.registrar(tipo,monto,f'{mes}-{dia:02d}',categorias[nombre],desc)
con.close()
print(ruta.resolve())
