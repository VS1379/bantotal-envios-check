import os
import zipfile
import tempfile
from sql_checker import analizar_sql

RAR_PASSWORD = os.getenv("RAR_PASSWORD")


def procesar_zip(zip_bytes, envio_nro):
    sqls = []
    hasDrop = False
    hasCreate = False

    tmp = os.path.join(tempfile.gettempdir(), f"{envio_nro}.zip")

    try:
        # escribir zip
        with open(tmp, "wb") as f:
            f.write(zip_bytes)

        # leer zip
        with zipfile.ZipFile(tmp) as z:
            for name in z.namelist():

                if not name.lower().endswith(".sql"):
                    continue

                try:
                    if RAR_PASSWORD:
                        raw = z.read(name, pwd=RAR_PASSWORD.encode())
                    else:
                        raw = z.read(name)

                    contenido = raw.decode("utf-8", errors="replace")

                    drop, create = analizar_sql(contenido)

                    sqls.append(os.path.basename(name))

                    if drop:
                        hasDrop = True
                    if create:
                        hasCreate = True

                except Exception as e:
                    # no cortar todo → seguir
                    print(f"[WARN] {envio_nro} -> error en {name}: {e}")
                    continue

        return {
            "sqls": sqls,
            "hasDrop": hasDrop,
            "hasCreate": hasCreate,
        }

    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
