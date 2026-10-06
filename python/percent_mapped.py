#!/usr/bin/env python3
"""
Devuelve el porcentaje de reads asignadas a cada nivel taxonomico.
 
input: 
    tsv/feature-table-ms4.tsv
    tsv/taxonomy-ms4.tsv
output: 
    tsv/percent_mapped_by_sample.tsv
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from silva_tax import deepest_rank, RANK_NAMES  # noqa: E402

from genus_table import load_table, load_taxonomy  # noqa: E402

# -------------------[ configuracion ]---------------------------------------#

TABLE_FILE = Path("tsv/feature-table-ms4.tsv")
TAXONOMY_FILE = Path("tsv/taxonomy-ms4.tsv")
OUT_TSV = Path("tsv/percent_mapped_by_sample.tsv")

# -------------------[ main ]------------------------------------------------#
def main():
    for p in (TABLE_FILE, TAXONOMY_FILE):
        if not p.exists():
            sys.exit(f"ERROR: no existe {p}")

    tax = load_taxonomy(TAXONOMY_FILE)
    samples, rows = load_table(TABLE_FILE)
    n = len(samples)
    ranks = sorted(RANK_NAMES)

    # read counts por rango y por muestra, y numero de ASVs por rango
    by_rank = {r: [0.0] * n for r in list(ranks) + [-1]}
    asv_by_rank = {r: 0 for r in list(ranks) + [-1]}
    missing_ids, missing_reads = 0, 0.0

    for fid, counts in rows.items():
        if fid not in tax:
            missing_ids += 1
            missing_reads += sum(counts)
        r = deepest_rank(tax.get(fid, ""))
        asv_by_rank[r] += 1
        acc = by_rank[r]
        for i, v in enumerate(counts):
            acc[i] += v

    totals = [sum(by_rank[r][i] for r in by_rank) for i in range(n)]
    grand = sum(totals)

    if missing_ids:
        print(f"AVISO: {missing_ids} features de la tabla no estan en la "
              f"taxonomia ({100 * missing_reads / grand:.2f}% de reads).\n")

    # resumen por rango, acumulado desde el nivel mas profundo hacia arriba
    print(f"ASVs: {len(rows):,}   Muestras: {n}   Reads: {grand:,.0f}\n")
    print(f"{'Nivel':<12}{'Reads (>= nivel)':>20}{'% total':>10}{'ASVs':>8}")
    cum_r, cum_a = 0.0, 0
    cum_by_sample = {}
    for r in sorted(ranks, reverse=True):
        cum_r += sum(by_rank[r])
        cum_a += asv_by_rank[r]
        # acumulado por muestra, necesario para la tabla de abajo
        prev = cum_by_sample.get(r + 1, [0.0] * n)
        cum_by_sample[r] = [p + v for p, v in zip(prev, by_rank[r])]
        print(f"{RANK_NAMES[r]:<12}{cum_r:>20,.0f}"
              f"{100 * cum_r / grand:>9.2f}%{cum_a:>8,}")
    print(f"{'Sin asignar':<12}{sum(by_rank[-1]):>20,.0f}"
          f"{100 * sum(by_rank[-1]) / grand:>9.2f}%{asv_by_rank[-1]:>8,}")

    # tabla de porcentaje de reads asignadas a cada rango, por muestra
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    cols = [RANK_NAMES[r] for r in sorted(ranks, reverse=True)]
    with OUT_TSV.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["sample-id", "total_reads"] + [f"pct_{c}" for c in cols])
        for i, s in enumerate(samples):
            t = totals[i]
            pcts = [100 * cum_by_sample[r][i] / t if t else 0
                    for r in sorted(ranks, reverse=True)]
            w.writerow([s, f"{t:.0f}"] + [f"{p:.2f}" for p in pcts])

    # porcentaje de reads asignadas a genero, por muestra
    gi = 6  # LEVEL_RANK["g__"] en SILVA 144
    pg = [100 * cum_by_sample[gi][i] / totals[i] if totals[i] else 0
          for i in range(n)]
    order = sorted(range(n), key=lambda i: pg[i])
    print(f"\nGenero, por muestra: media {sum(pg)/n:.1f}%  "
          f"min {pg[order[0]]:.1f}% ({samples[order[0]]})  "
          f"max {pg[order[-1]]:.1f}% ({samples[order[-1]]})")

    print(f"\n{OUT_TSV}")


if __name__ == "__main__":
    main()