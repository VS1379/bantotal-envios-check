from dotenv import load_dotenv
from pathlib import Path
import os
import pyodbc
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

env_file = BASE_DIR / "config.env"

load_dotenv(env_file)

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


def obtener_total_ambientes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM Ambientes
        WHERE AmbBaja = 'N'
        AND TipEnvId = 1
    """)
    total = {"Bantotal": cursor.fetchone()[0]}
    cursor.execute("""
        SELECT COUNT(*)
        FROM Ambientes
        WHERE AmbBaja = 'N'
        AND TipEnvId = 3
    """)
    total["BSM"] = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*)
        FROM Ambientes
        WHERE AmbBaja = 'N'
        AND TipEnvId = 4
    """)
    total["Canales/Bpeople"] = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*)
        FROM Ambientes
        WHERE AmbBaja = 'N'
        AND TipEnvId = 5
    """)
    total["IBNode"] = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*)
        FROM Ambientes
        WHERE AmbBaja = 'N'
        AND TipEnvId = 7
    """)
    total["IBNodeAdmin"] = cursor.fetchone()[0]
    conn.close()
    return total


def obtener_envio(numero):
    conn = get_connection()
    cursor = conn.cursor()

    numero = str(numero)

    if (
        numero.startswith("413")
        or numero.startswith("533")
        or numero.startswith("534")
        or numero.startswith("535")
        or numero.startswith("536")
    ):

        cursor.execute(
            """
            SELECT
                E.EnvNro,
                E.EnvIdAlternativo,
                E.Zip
            FROM Envios E
            WHERE E.EnvIdAlternativo = ?
            """,
            int(numero),
        )

    else:

        cursor.execute(
            """
            SELECT
                E.EnvNro,
                E.EnvIdAlternativo,
                E.Zip
            FROM Envios E
            WHERE E.EnvNro = ?
            """,
            int(numero),
        )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    env_nro = row.EnvNro

    cursor.execute(
        """
        SELECT A.AmbDsc
        FROM EnvAplicado EA
        INNER JOIN Ambientes A
            ON A.AmbId = EA.AmbId
        WHERE EA.EnvNro = ?
        ORDER BY A.AmbSeq
        """,
        env_nro,
    )

    ambientes = [r.AmbDsc for r in cursor.fetchall()]

    conn.close()

    return {
        "envio": env_nro,  # número real
        "envioAlternativo": row.EnvIdAlternativo,
        "zip": row.Zip,
        "ambientes": ambientes,
    }
