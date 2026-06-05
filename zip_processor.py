import os
import tempfile
import zipfile

from sql_checker import analizar_sql

RAR_PASSWORD = os.getenv("RAR_PASSWORD")


def procesar_zip(zip_bytes, envio_nro):
    print(f"[ZIP] Analizando envio {envio_nro}", flush=True)
    tmp_zip = os.path.join(tempfile.gettempdir(), f"{envio_nro}.zip")

    sqls = []
    has_drop = False
    has_create = False

    drops_encontrados = set()
    creates_encontrados = set()

    try:
        # =========================
        # GUARDAR ZIP TEMPORAL
        # =========================
        with open(tmp_zip, "wb") as f:
            f.write(zip_bytes)
        # =========================
        # ABRIR ZIP
        # =========================
        with zipfile.ZipFile(tmp_zip) as z:

            archivos = z.namelist()

            print(f"[ZIP] {envio_nro} contiene {len(archivos)} archivos", flush=True)

            for name in archivos:

                print(f"[ZIP] Analizando {name}", flush=True)

                if not name.lower().endswith(".sql"):
                    continue

                ...

                print(f"[INFO] Analizando SQL: {name}", flush=True)

                try:

                    # -------------------------
                    # Intento SIN password
                    # -------------------------

                    try:
                        raw = z.read(name)

                    except RuntimeError:

                        # -------------------------
                        # Intento CON password
                        # -------------------------

                        if not RAR_PASSWORD:
                            raise Exception(
                                f"ZIP protegido y no existe RAR_PASSWORD para {name}"
                            )

                        raw = z.read(name, pwd=RAR_PASSWORD.encode("utf-8"))

                    contenido = raw.decode("utf-8", errors="replace")

                    print(f"[INFO] Primeros 300 chars de {name}:", flush=True)
                    print(contenido[:300], flush=True)

                    resultado = analizar_sql(contenido)
                    print(
                        f"[SQL] drops={resultado['drops']} creates={resultado['creates']}",
                        flush=True,
                    )

                    print(f"[INFO] Resultado SQL: {resultado}", flush=True)

                    sqls.append(os.path.basename(name))

                    drops_encontrados.update(resultado.get("drops", []))

                    creates_encontrados.update(resultado.get("creates", []))

                    if resultado.get("hasDrop"):
                        has_drop = True

                    if resultado.get("hasCreate"):
                        has_create = True

                except Exception as e:

                    print(f"[WARN] {envio_nro} -> error en {name}: {e}", flush=True)

                    continue

        return {
            "sqls": sqls,
            "hasDrop": has_drop,
            "hasCreate": has_create,
            "drops": sorted(list(drops_encontrados)),
            "creates": sorted(list(creates_encontrados)),
        }

    finally:

        if os.path.exists(tmp_zip):
            try:
                os.remove(tmp_zip)
            except Exception:
                pass
