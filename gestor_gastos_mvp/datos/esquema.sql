PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS categoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK(length(trim(nombre)) BETWEEN 1 AND 60),
    tipo TEXT NOT NULL CHECK(tipo IN ('ingreso','gasto')),
    UNIQUE(nombre, tipo)
);
CREATE TABLE IF NOT EXISTS movimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('ingreso','gasto')),
    monto INTEGER NOT NULL CHECK(monto > 0 AND monto <= 999999999),
    fecha TEXT NOT NULL CHECK(length(fecha) = 10),
    descripcion TEXT NOT NULL DEFAULT '' CHECK(length(descripcion) <= 120),
    categoria_id INTEGER NOT NULL REFERENCES categoria(id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_movimiento_fecha_tipo_monto ON movimiento(fecha,tipo,monto);
CREATE INDEX IF NOT EXISTS idx_movimiento_categoria_fecha ON movimiento(categoria_id,fecha);
CREATE TRIGGER IF NOT EXISTS trg_mov_tipo_insert
BEFORE INSERT ON movimiento
WHEN (SELECT tipo FROM categoria WHERE id = NEW.categoria_id) IS NOT NEW.tipo
    BEGIN SELECT RAISE(ABORT, 'Categoría incompatible con el tipo'); END;
CREATE TRIGGER IF NOT EXISTS trg_mov_tipo_update
BEFORE UPDATE OF tipo, categoria_id ON movimiento
WHEN (SELECT tipo FROM categoria WHERE id = NEW.categoria_id) IS NOT NEW.tipo
    BEGIN SELECT RAISE(ABORT, 'Categoría incompatible con el tipo'); END;
CREATE TRIGGER IF NOT EXISTS trg_categoria_tipo_update
BEFORE UPDATE OF tipo ON categoria
WHEN EXISTS(SELECT 1 FROM movimiento WHERE categoria_id = OLD.id AND tipo != NEW.tipo)
    BEGIN 
        SELECT RAISE(ABORT, 'Categoría con movimientos incompatibles'); END;
