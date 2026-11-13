from datetime import date,timedelta
import pytest
from negocio.movimiento import (Movimiento, ValidacionError, validar_tipo,validar_monto,
 validar_fecha, validar_descripcion, validar_categoria_id, validar_nombre_categoria)


def test_tipo_normalizado():
    assert validar_tipo(' GASTO ')=='gasto'
    assert validar_tipo('Ingreso')=='ingreso'

@pytest.mark.parametrize('tipo',[None,'abono','',8])
def test_tipo_invalido(tipo):
    with pytest.raises(ValidacionError):validar_tipo(tipo)

@pytest.mark.parametrize('monto,resultado',[('12000',12000),(50,50),('00042',42),(999999999,999999999)])
def test_monto_valido(monto,resultado):
    assert validar_monto(monto)==resultado

@pytest.mark.parametrize('monto',[True,0,-10,'2.5','1e3','abc',1000000000])
def test_monto_invalido(monto):
    with pytest.raises(ValidacionError):validar_monto(monto)


def test_fecha_default_y_fecha_valida():
    assert validar_fecha('')==date.today().isoformat()
    assert validar_fecha(date(2025,10,12))=='2025-10-12'
    assert validar_fecha('2025-01-10')=='2025-01-10'

@pytest.mark.parametrize('fecha',['2026-02-30','12/11/2025','2025-1-01'])
def test_fecha_formato_invalido(fecha):
    with pytest.raises(ValidacionError):validar_fecha(fecha)


def test_fecha_futura():
    with pytest.raises(ValidacionError):validar_fecha(date.today()+timedelta(days=1))


def test_descripcion_maximo_y_invalida():
    assert validar_descripcion('  abono  ')=='abono'
    assert validar_descripcion(None)==''
    assert len(validar_descripcion('a'*120))==120
    for value in ('a'*121,123,'x\x00y'):
        with pytest.raises(ValidacionError):validar_descripcion(value)


def test_categoria_id_y_nombre():
    assert validar_categoria_id('25')==25
    assert validar_nombre_categoria('  Transporte  ')=='Transporte'
    for bad in (0,True,'a',-1):
        with pytest.raises(ValidacionError):validar_categoria_id(bad)
    for bad in ('','a'*61,'a\x00b',7):
        with pytest.raises(ValidacionError):validar_nombre_categoria(bad)


def test_creacion_movimiento():
    m=Movimiento.construir('GASTO','15000','2025-03-01',3,'Supermercado')
    assert m.monto==15000 and m.tipo=='gasto' and m.categoria_id==3
