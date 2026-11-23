"""Respaldo lógico de PostgreSQL usando la conexión ya configurada en Django.

Ejecutar desde la raíz del proyecto con:
    python manage.py shell -c 'exec(open("backup_quecomemos_railway.py").read())'
No modifica tablas ni aplica migraciones. No imprimir credenciales.
"""
from datetime import datetime
from pathlib import Path
import os
import subprocess

from django.db import connection

if connection.vendor != "postgresql":
    raise RuntimeError("La conexión Django no es PostgreSQL. Backup cancelado.")

db = connection.settings_dict
required = ("NAME", "HOST", "USER", "PASSWORD")
if any(not db.get(key) for key in required):
    raise RuntimeError("Faltan parámetros de conexión PostgreSQL. Backup cancelado.")

backup_dir = Path.home() / "quecomemos_db_backups"
backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
backup_dir.chmod(0o700)
backup_file = backup_dir / f"quecomemos_railway_{datetime.now():%Y%m%d_%H%M%S}.dump"
if backup_file.exists():
    raise RuntimeError("Ya existe un backup con este nombre; no se sobrescribirá.")

bin_dir = Path(subprocess.check_output(["brew", "--prefix", "libpq"], text=True).strip()) / "bin"
pg_dump = str(bin_dir / "pg_dump")
pg_restore = str(bin_dir / "pg_restore")

pg_env = os.environ.copy()
pg_env.update({
    "PGHOST": str(db["HOST"]),
    "PGPORT": str(db.get("PORT") or 5432),
    "PGDATABASE": str(db["NAME"]),
    "PGUSER": str(db["USER"]),
    "PGPASSWORD": str(db["PASSWORD"]),
})
sslmode = (db.get("OPTIONS") or {}).get("sslmode")
if sslmode:
    pg_env["PGSSLMODE"] = str(sslmode)

old_umask = os.umask(0o077)
try:
    print("Origen:", db["HOST"], "/", db["NAME"])
    print("Archivo:", backup_file)
    print("Realizando copia de solo lectura de PostgreSQL...")
    subprocess.run(
        [pg_dump, "--format=custom", "--no-owner", "--no-acl", "--no-password", "--file", str(backup_file)],
        env=pg_env,
        check=True,
    )
    if not backup_file.is_file() or backup_file.stat().st_size == 0:
        raise RuntimeError("El archivo de backup está vacío o no existe.")
    print("Verificando que pg_restore pueda leer el archivo completo...")
    subprocess.run(
        [pg_restore, "--file", os.devnull, str(backup_file)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    backup_file.chmod(0o600)
    print(f"BACKUP OK. Tamaño: {backup_file.stat().st_size / 1024 / 1024:.2f} MiB")
    print("Ubicación:", backup_file)
    print("Verificación: pg_restore leyó el archivo sin errores (no se restauraron datos).")
except Exception:
    print("ERROR: la copia o la verificación falló. No consideres válido el archivo parcial, si existe.")
    raise
finally:
    os.umask(old_umask)
