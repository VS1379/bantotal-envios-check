import base64
import os
import pyodbc

from zip_processor import procesar_zip

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.environ.get('DB_HOST')},{os.environ.get('DB_PORT', '1433')};"
        f"DATABASE={os.environ.get('DB_NAME')};"
        f"UID={os.environ.get('DB_USER')};"
        f"PWD={os.environ.get('DB_PASS')};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def obtener_envio(nro):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        EnvioId,
        ZipBase64
    FROM Envio
    WHERE EnvioId = ?
    """

    cursor.execute(query, nro)
    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {"envio": row[0], "zip": row[1]}


def analizar_envio_db(nro):
    base = {
        "envio": nro,
        "ticket": None,
        "progreso": 0,
        "skipped": False,
        "sqls": [],
        "hasDrop": False,
        "hasCreate": False,
    }

    data = obtener_envio(nro)

    if not data or not data["zip"]:
        return {**base, "error": "sin zip"}

    try:
        # FIX base64 padding
        def decode_base64(data):
            data = data.strip()
            missing = len(data) % 4
            if missing:
                data += "=" * (4 - missing)
            return base64.b64decode(data)

        zip_bytes = decode_base64(data["zip"])

        # 🔥 TODA la lógica pesada ahora vive acá
        res = procesar_zip(zip_bytes, nro)

        return {**base, "progreso": 100, **res}

    except Exception as e:
        return {**base, "error": f"ERROR: {str(e)}"}
