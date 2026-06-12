import os
import sys
import json
import base64
import traceback

from repository import obtener_envio, obtener_total_ambientes
from zip_processor import procesar_zip

sys.stdout.reconfigure(encoding="utf-8")

print("MAIN.PY INICIADO", flush=True)


def decode_base64(data):
    data = data.strip()

    missing = len(data) % 4

    if missing:
        data += "=" * (4 - missing)

    return base64.b64decode(data)


total_ambientes = obtener_total_ambientes()


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

    # 🔥 calcular progreso acá
    ambientes_instalados = len(data["ambientes"])

    progreso = (
        round((ambientes_instalados / total_ambientes) * 100) if total_ambientes else 0
    )

    try:

        zip_bytes = decode_base64(data["zip"])

        print(f"[DEBUG] Analizando envio {envio_nro}", flush=True)

        res = procesar_zip(zip_bytes, envio_nro)

        return {
            **base,
            **res,
            "envio": data["envio"],
            "envioAlternativo": data["envioAlternativo"],
            "progreso": progreso,
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
