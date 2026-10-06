#!/usr/bin/env python3

"""
Funciones generales para trabajar con etiquetas taxonomicas de SILVA 144.

Modulo compartido: necesario importarlo desde los demas scripts.

Uso:
    import sys; sys.path.insert(0, "python")
    from silva_tax import is_real, deepest_rank, extract_rank, LEVEL_RANK
"""

# ------------[ configuracion ]---------------------------------------#

# 6 prefijos de SILVA 144, con su rango numerico correspondiente.
LEVEL_RANK = {"d__": 0, "k__": 1, "p__": 2, "c__": 3, "o__": 4,
              "f__": 5, "g__": 6, "s__": 7}

RANK_NAMES = {0: "Dominio", 1: "Reino", 2: "Filo", 3: "Clase", 4: "Orden",
              5: "Familia", 6: "Genero", 7: "Especie"}

# Posibles valores de SILVA que no aportan informacion taxonomica
PLACEHOLDERS = ("uncultured", "metagenome", "unidentified", "unknown",
                "unclassified", "unassigned")

EXACT_PLACEHOLDERS = ("incertae_sedis", "incertae sedis")

# ------------[ funciones ]---------------------------------------#

def is_real(value):
    """True si la etiqueta aporta informacion taxonomica."""
    v = value.strip().lower()
    if not v or len(v) < 2 or v.isdigit():
        return False
    if v in EXACT_PLACEHOLDERS:
        return False
    return not any(p in v for p in PLACEHOLDERS)


def parse_taxon(taxon_str):
    """Devuelve {prefijo: valor} solo con los rangos informativos."""
    out = {}
    for part in taxon_str.split(";"):
        part = part.strip()
        idx = part.find("__")
        if idx == -1:
            continue
        prefix, value = part[:idx + 2], part[idx + 2:]
        if prefix in LEVEL_RANK and is_real(value):
            out[prefix] = value.strip()
    return out


def extract_rank(taxon_str, prefix="g__"):
    """Valor de un rango concreto, o None si no existe o no es informativo.

    Busca por prefijo en lugar de tomar el ultimo campo de la cadena: si la
    ASV se queda en familia, el ultimo campo es una familia, no un genero.
    """
    return parse_taxon(taxon_str).get(prefix)


def deepest_rank(taxon_str):
    """Rango numerico mas profundo con contenido informativo; -1 si ninguno."""
    ranks = [LEVEL_RANK[p] for p in parse_taxon(taxon_str)]
    return max(ranks) if ranks else -1
