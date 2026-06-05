import os
import sys
import json
import base64
import traceback

from repository import obtener_envio
from zip_processor import procesar_zip

sys.stdout.reconfigure(encoding="utf-8")

print("MAIN.PY INICIADO", flush=True)


def decode_base64(data):
    data = data.strip()

    missing = len(data) % 4

    if missing:
        data += "=" * (4 - missing)

    return base64.b64decode(data)


def analizar_envio(envio_nro):
    print(f"ANALIZANDO ENVIO {envio_nro}", flush=True)
    base = {
        "envio": envio_nro,
        "ticket": None,
        "progreso": 0,
        "skipped": False,
        "sqls": [],
        "hasDrop": False,
        "hasCreate": False,
        "drops": [],
        "creates": [],
    }

    data = obtener_envio(envio_nro)

    if not data:
        return {**base, "error": "No encontrado"}

    if not data["zip"]:
        return {**base, "skipped": True}

    try:

        zip_bytes = decode_base64(data["zip"])

        print(f"[DEBUG] Analizando envío {envio_nro}", flush=True)
        print("LLAMANDO A PROCESAR ZIP", flush=True)
        res = procesar_zip(zip_bytes, envio_nro)

        return {
            **base,
            **res,
            "progreso": 100,
            "ambientes": data["ambientes"],
        }
    except Exception:
        return {**base, "error": traceback.format_exc()}


def analizar_envios(lista):
    return [analizar_envio(n) for n in lista]


if __name__ == "__main__":

    payload = json.loads(sys.argv[1])

    envios = payload.get("envios", [])

    result = analizar_envios(envios)

    print("RESULT:" + json.dumps(result, ensure_ascii=False))
