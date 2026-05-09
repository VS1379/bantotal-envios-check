import os
import base64
import pyodbc
import sys
import json
from zip_processor import procesar_zip

# =========================
# DB CONFIG
# =========================
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.environ.get('DB_HOST')},{os.environ.get('DB_PORT', '1433')};"
    f"DATABASE={os.environ.get('DB_NAME')};"
    f"UID={os.environ.get('DB_USER')};"
    f"PWD={os.environ.get('DB_PASS')};"
    "TrustServerCertificate=yes;"
)


def get_connection():
    return pyodbc.connect(conn_str)


# =========================
# ANALIZAR 1 ENVIO
# =========================
def analizar_envio(envio_nro):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT EnvNro, Zip
        FROM Land.dbo.Envios
        WHERE EnvNro = ?
        """,
        envio_nro,
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"envio": envio_nro, "error": "No encontrado"}

    zip_base64 = row.Zip

    base = {
        "envio": envio_nro,
        "ticket": None,
        "progreso": 0,
        "skipped": False,
        "sqls": [],
        "hasDrop": False,
        "hasCreate": False,
    }

    if not zip_base64:
        return {**base, "skipped": True}

    try:
        # FIX base64 padding
        def decode_base64(data):
            data = data.strip()
            missing = len(data) % 4
            if missing:
                data += "=" * (4 - missing)
            return base64.b64decode(data)

        zip_bytes = decode_base64(zip_base64)

        # 🔥 TODA la lógica va acá
        res = procesar_zip(zip_bytes, envio_nro)

        return {**base, "progreso": 100, **res}

    except Exception as e:
        return {**base, "error": f"ZIP error: {repr(e)}"}


# =========================
# MULTIPLE
# =========================
def analizar_envios(lista):
    return [analizar_envio(n) for n in lista]


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    import json
    import sys

    payload = json.loads(sys.argv[1])
    envios = payload.get("envios", [])

    result = analizar_envios(envios)

sys.stdout.reconfigure(encoding="utf-8")

print("RESULT:" + json.dumps(result, ensure_ascii=False))
