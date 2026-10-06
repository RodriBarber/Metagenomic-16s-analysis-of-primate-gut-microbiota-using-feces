#!/usr/bin/env python3
"""
Crea dos tablas TSV:
    1. Abundancia relativa por ASV
    2. Abundancia relativa por género 

Outputs:
    tsv/rel_abundance_asv.tsv
    tsv/rel_abundance_genus.tsv
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from silva_tax import extract_rank   # noqa: E402
from genus_table import load_taxonomy, load_table # noqa: E402

# -------------------[ configuracion ]---------------------------------#

TABLE_FILE = Path("tsv/feature-table-ms4.tsv")
TAXONOMY_FILE = Path("tsv/taxonomy-ms4.tsv")
OUT_ASV = Path("tsv/rel_abundance_asv.tsv")
OUT_GENUS = Path("tsv/rel_abundance_genus.tsv")

# -------------------[ main ]----------------------------------------#    

def main():
    for p in (TABLE_FILE, TAXONOMY_FILE):
        if not p.exists():
            sys.exit(f"ERROR: no existe {p}")

    tax = load_taxonomy(TAXONOMY_FILE)
    samples, counts = load_table(TABLE_FILE)
    n = len(samples)
    totals = [sum(v[i] for v in counts.values()) for i in range(n)]

    missing = [a for a in counts if a not in tax]
    if missing:
        print(f"AVISO: {len(missing)} ASVs de la tabla no estan en la taxonomia")

    # Por ASV
    OUT_ASV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_ASV.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["asv_id", "taxon"] + samples)
        # ordenadas por abundancia media descendente
        order = sorted(counts, key=lambda a: -sum(counts[a]))
        for asv in order:
            rel = [c / t if t else 0.0 for c, t in zip(counts[asv], totals)]
            w.writerow([asv, tax.get(asv, "")] + [f"{v:.8g}" for v in rel])

    # Por genero
    agg = {}
    for asv, vals in counts.items():
        g = extract_rank(tax.get(asv, ""), "g__")
        if g is None:          # sin genero, Incertae_Sedis, uncultured...
            continue
        row = agg.setdefault(g, [0.0] * n)
        for i, v in enumerate(vals):
            row[i] += v

    with OUT_GENUS.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["genus"] + samples)
        for g in sorted(agg, key=lambda k: -sum(agg[k])):
            rel = [c / t if t else 0.0 for c, t in zip(agg[g], totals)]
            w.writerow([g] + [f"{v:.8g}" for v in rel])

    cubierto = [sum(agg[g][i] for g in agg) / totals[i] if totals[i] else 0
                for i in range(n)]
    
    print(f"ASVs: {len(counts):,}   muestras: {n}   "
          f"lecturas: {sum(totals):,.0f}")
    print(f"Fraccion de lecturas con genero: media "
          f"{100*sum(cubierto)/n:.1f}%  (min {100*min(cubierto):.1f}%, "
          f"max {100*max(cubierto):.1f}%)")
    print(f"\n{OUT_ASV}\n{OUT_GENUS}")


if __name__ == "__main__":
    main()
