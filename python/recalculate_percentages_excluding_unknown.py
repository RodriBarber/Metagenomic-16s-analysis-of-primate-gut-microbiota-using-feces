#!/usr/bin/env python3
"""
Recalcular los porcentajes, la media y la desviación estándar por muestra de los géneros, 
excluyendo los datos desconocidos.

input:
    tsv/contaminacion/ncbi_species_environment_summary_5_groups.tsv
output:
    tsv/contaminacion/ncbi_species_environment_percentages_excluding_unknown.tsv
    tsv/contaminacion/ncbi_genus_species_percentages_mean_sd_excluding_unknown.tsv
"""
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

# -------------------[ configuracion ]---------------------------------------#

input:Path = Path("tsv/contaminacion/ncbi_species_environment_summary_5_groups.tsv")
output1:Path = Path("tsv/contaminacion/ncbi_species_environment_percentages_excluding_unknown.tsv")
output2:Path = Path("tsv/contaminacion/ncbi_genus_species_percentages_mean_sd_excluding_unknown.tsv")

CATEGORIES = ('fecal_gut_samples contaminant_samples animal_samples other_samples').split()

IDS = ['silva_genus', 'ncbi_genus_name', 'ncbi_genus_taxid',
       'ncbi_species_name', 'ncbi_species_taxid']


# -------------------[ configuracion ]---------------------------------------#

def number(value):
    "convierte un valor a cadena con formato de punto flotante, sin notación científica"
    return format(value, '.10g')


def write(path, fields, rows):
    """Guarda los datos en un archivo TSV."""
    part = path.with_name(path.name + '.part')
    with part.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    part.replace(path)


# -------------------[ main ]---------------------------------------#

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path.cwd(), help='Analysis directory (default: current directory)')
    args = parser.parse_args()
    base = args.base.resolve()
    source = base / input
    species_output = base / output1
    genus_output = base / output2
    for path in (species_output, genus_output):
        if path.exists():
            raise RuntimeError(f'Ya existe {path}. Conserva o renombra esa salida antes de repetir.')

    # Lee la tabla de entrada y valida los datos
    species_rows, seen, identities = [], set(), {}
    groups = defaultdict(list)
    required = IDS + ['total_samples'] + CATEGORIES + ['unknown_samples']
    with source.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        fields = reader.fieldnames or []
        if set(required) - set(fields) or len(fields) != len(set(fields)):
            raise RuntimeError(f'Cabecera incorrecta. Columnas requeridas: {required}')
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise RuntimeError(f'Fila incompleta o mal formada: {reader.line_num}')
            ids = {k: row[k].strip() for k in IDS}
            taxid, genus = ids['ncbi_species_taxid'], ids['silva_genus']
            if not all(ids.values()) or taxid in seen:
                raise RuntimeError(f'Identidad vacía o TaxID repetido: {taxid}')
            seen.add(taxid)
            identity = tuple(ids[k] for k in IDS[:3])
            if genus in identities and identities[genus] != identity:
                raise RuntimeError(f'Identidad de género contradictoria: {genus}')
            identities[genus] = identity
            total = int(row['total_samples'])
            counts = {c: int(row[c]) for c in CATEGORIES + ['unknown_samples']}
            if total <= 0 or any(v < 0 for v in counts.values()) or sum(counts.values()) != total:
                raise RuntimeError(f'Recuentos inválidos para TaxID {taxid}')
            known = total - counts['unknown_samples']
            pct = {c: 100.0 * counts[c] / known for c in CATEGORIES} if known else None
            if pct is not None and not math.isclose(sum(pct.values()), 100, abs_tol=1e-8):
                raise RuntimeError(f'Los porcentajes no suman 100 para TaxID {taxid}')
            out = dict(ids, total_samples=total, **counts)
            out.update(known_source_samples=known,
                       unknown_pct_of_total=number(100.0 * counts['unknown_samples'] / total),
                       percentage_status='included' if known else 'only_unknown')
            out.update({c + '_pct': number(pct[c]) if pct is not None else 'NA' for c in CATEGORIES})
            species_rows.append(out)
            groups[genus].append((total, known, counts['unknown_samples'], pct))
    if not seen:
        raise RuntimeError('La tabla de entrada está vacía')

    # Calcula los porcentajes medios y la desviación estándar por género, excluyendo los datos desconocidos
    genus_fields = IDS[:3] + ['n_species_with_biosamples', 'n_species_used',
        'n_species_only_unknown', 'total_biosamples', 'known_source_samples',
        'unknown_source_samples', 'unknown_pct_of_total_biosamples']
    genus_rows = []
    for genus in sorted(groups, key=str.casefold):
        entries = groups[genus]
        valid = [e[3] for e in entries if e[3] is not None]
        n = len(valid)
        total, known, unknown = (sum(e[i] for e in entries) for i in range(3))
        out = dict(zip(IDS[:3], identities[genus]))
        out.update(n_species_with_biosamples=len(entries), n_species_used=n,
            n_species_only_unknown=len(entries)-n, total_biosamples=total,
            known_source_samples=known, unknown_source_samples=unknown,
            unknown_pct_of_total_biosamples=number(100.0 * unknown / total))
        for c in CATEGORIES:
            values = [p[c] for p in valid]
            out[c + '_mean_pct'] = number(mean(values)) if n else 'NA'
            out[c + '_sd_pp'] = number(stdev(values)) if n > 1 else 'NA'
        genus_rows.append(out)
    species_fields = required + ['known_source_samples', 'unknown_pct_of_total',
        'percentage_status'] + [c + '_pct' for c in CATEGORIES]
    genus_fields += [field for c in CATEGORIES for field in (c + '_mean_pct', c + '_sd_pp')]

    # Guarda los resultados en archivos TSV
    write(species_output, species_fields, species_rows)
    write(genus_output, genus_fields, genus_rows)
    n_used = sum(r['n_species_used'] for r in genus_rows)
    
    print('TERMINADO')
    print(f'TaxID de especie con BioSamples: {len(seen):,}')
    print(f'Especies utilizadas: {n_used:,}')
    print('Validación: recuentos coherentes y porcentajes por especie válida suman 100.')
    print(f'Salida: {species_output}\nSalida: {genus_output}')


if __name__ == '__main__':
    main()