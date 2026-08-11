import os
import tempfile
import zipfile

from sql_checker import analizar_sql

RAR_PASSWORD = os.getenv("RAR_PASSWORD")
RAR_PASSWORD_BPEOPLE = os.getenv("RAR_PASSWORD_BPEOPLE")


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

            for name in archivos:

                if not name.lower().endswith(".sql"):
                    continue
                ...
                try:

                    # -------------------------
                    # Intento SIN password
                    # -------------------------

                    try:
                        raw = z.read(name)

                    except RuntimeError:

                        passwords = []

                        if RAR_PASSWORD:
                            passwords.append(RAR_PASSWORD)

                        if RAR_PASSWORD_BPEOPLE:
                            passwords.append(RAR_PASSWORD_BPEOPLE)

                        if not passwords:
                            raise Exception(
                                f"No hay contraseña configurada para {name}"
                            )

                        raw = None

                        for pwd in passwords:
                            try:
                                raw = z.read(name, pwd=pwd.encode("utf-8"))
                                break
                            except RuntimeError:
                                pass

                        if raw is None:
                            raise Exception(f"Ninguna contraseña funcionó para {name}")

                    contenido = raw.decode("utf-8", errors="replace")

                    resultado = analizar_sql(contenido)

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
