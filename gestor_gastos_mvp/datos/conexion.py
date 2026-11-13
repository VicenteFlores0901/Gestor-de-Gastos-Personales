"""Inicialización SQLite sin servicios de red y con integridad referencial."""
from pathlib import Path
import sqlite3

ESQUEMA = Path(__file__).with_name('esquema.sql')


def abrir_db(ruta: str | Path = ':memory:') -> sqlite3.Connection:
    """Abre una base local, crea el esquema y habilita claves foráneas."""
    if str(ruta) != ':memory:':
        Path(ruta).expanduser().parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(ruta), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    con.execute('PRAGMA busy_timeout = 10000')
    con.executescript(ESQUEMA.read_text(encoding='utf-8'))
    return con


def ruta_default() -> Path:
    """Ruta dentro del perfil del usuario (el ACL real se valida en Windows)."""
    import os
    return Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'GestorGastosPersonales' / 'gastos.db'
