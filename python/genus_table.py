#!/usr/bin/env python3
"""
Funciones generales para trabajar con la tabla de generos.

Modulo compartido; importado por los scripts de composicion taxonomica
(heatmaps, barplots, seleccion de taxones). Depende de silva_tax para
interpretar los linajes.

Uso:
    from genus_table import genus_matrix, mean_by_group, top_genera ...

"""
import csv
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from silva_tax import extract_rank  # noqa: E402

# -------------------[ configuracion ]---------------------------------#

NORES = "No_resolution"

# -------------------[ funciones ]-------------------------------------#

def load_taxonomy(path):
    """Construye un diccionario de taxonomia a partir de un archivo TSV."""
    tax = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter="\t")
        next(r)
        for row in r:
            if row:
                tax[row[0].strip()] = row[1].strip() if len(row) > 1 else ""
    return tax


def load_table(path):
    """Lee el TSV de biom convert, saltando su linea de comentario."""
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        lines = [l.rstrip("\n") for l in f if l.strip()]
    start = 1 if lines[0].startswith("# Constructed") else 0
    samples = lines[start].split("\t")[1:]
    counts = {}
    for line in lines[start + 1:]:
        p = line.split("\t")
        counts[p[0]] = [float(x) for x in p[1:]]
    return samples, counts


def load_metadata_column(path, column, id_col="sample-id"):
    """Lee una columna de la tabla de metadatos, saltando la fila #q2:types."""
    out = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter="\t")
        hdr = next(r)
        i_id, i_col = hdr.index(id_col), hdr.index(column)
        for row in r:
            if not row or row[0].startswith("#q2:types"):
                continue
            out[row[i_id].strip()] = row[i_col].strip()
    return out


def genus_matrix(table_file, taxonomy_file, keep_samples=None, include_nores=True):
    """Devuelve (samples, {genero: array de abundancia relativa})."""
    tax = load_taxonomy(taxonomy_file)
    samples, counts = load_table(table_file)
    sin_tax = [a for a in counts if a not in tax]
   
    if sin_tax:
        print(f"AVISO: {len(sin_tax)} de {len(counts)} ASVs no aparecen en "
              f"{taxonomy_file}; se cuentan como {NORES}. "
              f"Ejemplos: {sin_tax[:3]}", file=sys.stderr)

    if keep_samples is not None:
        keep = [i for i, s in enumerate(samples) if s in keep_samples]
        samples = [samples[i] for i in keep]
        counts = {a: [v[i] for i in keep] for a, v in counts.items()}

    n = len(samples)
    totals = [sum(v[i] for v in counts.values()) for i in range(n)]
    vacias = [samples[i] for i, t in enumerate(totals) if t == 0]
    if vacias:
        raise ValueError(f"Muestras con 0 lecturas: {vacias}. "
                         "Eliminalas antes de continuar.")

    agg = {}
    for asv, vals in counts.items():
        g = extract_rank(tax.get(asv, ""), "g__")
        if g is None:
            if not include_nores:
                continue
            g = NORES
        row = agg.setdefault(g, [0.0] * n)
        for i, v in enumerate(vals):
            row[i] += v

    rel = {g: np.array([c / t for c, t in zip(v, totals)])
           for g, v in agg.items()}
    return samples, rel


def mean_by_group(rel, samples, group_map):
    """Media de las abundancias relativas dentro de cada grupo. """
    faltan = [s for s in samples if s not in group_map]
    if faltan:
        raise KeyError(f"{len(faltan)} muestras sin grupo asignado en los "
                       f"metadatos: {faltan[:5]}")

    groups = sorted({group_map[s] for s in samples})
    idx = {g: [i for i, s in enumerate(samples) if group_map[s] == g]
           for g in groups}
    out = {t: np.array([rel[t][idx[g]].mean() for g in groups]) for t in rel}
    return groups, out


def top_genera(rel, n=20, exclude=(NORES,)):
    """Devuelve los n generos de mayor abundancia relativa media."""
    cand = [g for g in rel if g not in exclude]
    return sorted(cand, key=lambda g: -rel[g].mean())[:n]


def abundant_genera(rel, pct=5.0, exclude=(NORES,)):
    """Devuelve los generos que alcanzan pct% en al menos una muestra."""
    return [g for g in rel if g not in exclude and rel[g].max() * 100 >= pct]