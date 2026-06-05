import os
import pyodbc

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


def obtener_envio(envio_nro):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            e.EnvNro,
            e.Zip,
            ea.AmbId,
            a.AmbDsc
        FROM Envios e
        LEFT JOIN EnvAplicado ea
            ON ea.EnvNro = e.EnvNro
        LEFT JOIN Ambientes a
            ON a.AmbId = ea.AmbId
        WHERE e.EnvNro = ?
    """,
        envio_nro,
    )

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return None

    ambientes = []

    for r in rows:

        if r.AmbDsc and r.AmbDsc not in ambientes:
            ambientes.append(r.AmbDsc)

    first = rows[0]

    return {
        "envio": first.EnvNro,
        "zip": first.Zip,
        "ambientes": ambientes,
    }
