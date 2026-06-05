import re

DROP_TABLE_RE = re.compile(
    r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([\[\]\w\.]+)",
    re.IGNORECASE,
)

CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+([\[\]\w\.]+)",
    re.IGNORECASE,
)


def analizar_sql(contenido):

    drops = DROP_TABLE_RE.findall(contenido)
    creates = CREATE_TABLE_RE.findall(contenido)

    return {
        "hasDrop": bool(drops),
        "hasCreate": bool(creates),
        "drops": sorted(set(drops)),
        "creates": sorted(set(creates)),
    }
