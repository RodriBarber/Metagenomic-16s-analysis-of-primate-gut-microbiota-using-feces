#!/usr/bin/env python3
"""
Calcula el porcentaje de especies de cada género en cinco categorías de muestras biológicas
y genera estadísticas de recuento (media y desviación estándar) por género.

El TaxID de cada especie tiene el mismo peso. Denominador del porcentaje: todas las muestras biológicas,
incluidas las de origen desconocido. Desviación estándar (SD) de la muestra (n-1); no aplicable (NA) para 
una sola especie. Solo se incluyen las especies presentes en los datos de entrada. Sin dependencias externas.

input:
    tsv/ncbi_species_environment_summary_5_groups.tsv
output:
    tsv/ncbi_species_environment_percentages_5_groups.tsv
    tsv/ncbi_genus_species_counts_mean_sd_5_groups.tsv
    tsv/ncbi_genus_species_percentages_mean_sd_5_groups.tsv
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

# -------------------[ configuracion ]---------------------------------------#

input=Path('contaminacion/ncbi_species_environment_summary_5_groups.tsv')
output1 = Path('contaminacion/ncbi_species_environment_percentages_5_groups.tsv')
output2 = Path('contaminacion/ncbi_genus_species_counts_mean_sd_5_groups.tsv')
output3 = Path('contaminacion/ncbi_genus_species_percentages_mean_sd_5_groups.tsv')

CATEGORIES = ('fecal_gut_samples contaminant_samples animal_samples other_samples unknown_samples').split()

IDS = ['silva_genus', 'ncbi_genus_name', 'ncbi_genus_taxid',
       'ncbi_species_name', 'ncbi_species_taxid']

# -------------------[ funciones ]---------------------------------------#

def write(path, fields, rows):
    """Escribe un archivo TSV con los datos proporcionados."""
    part = path.with_name(path.name + '.part')
    with part.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    part.replace(path)

# -------------------[ main ]---------------------------------------#

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path.cwd())
    args = parser.parse_args()
    base = args.base.resolve()
    source = base / input
    pct_path = base / output1
    count_path = base / output2
    mean_pct_path = base / output3
    for path in [pct_path, count_path, mean_pct_path]:
        if path.exists():
            raise RuntimeError(f'La salida ya existe: {path}. Renómbrala antes de repetir.')

    # Lee el archivo de entrada y agrupa los datos por género, calculando porcentajes
    groups = defaultdict(list)
    seen = set()
    genera = {}
    pct_rows = []
    with source.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        fields = reader.fieldnames or []
        missing = set(IDS + ['total_samples'] + CATEGORIES) - set(fields)
        if missing or len(fields) != len(set(fields)):
            raise RuntimeError(f'Cabecera inválida. Faltan: {sorted(missing)}')
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise RuntimeError(f'Fila mal formada: {reader.line_num}')
            taxid = row['ncbi_species_taxid'].strip()
            genus = row['silva_genus'].strip()
            if not taxid or not genus or taxid in seen:
                raise RuntimeError(f'TaxID repetido/vacío o género vacío: {taxid}')
            seen.add(taxid)
            genus_identity = tuple(row[k].strip() for k in IDS[:3])
            if genus in genera and genera[genus] != genus_identity:
                raise RuntimeError(f'Identidad de género contradictoria: {genus}')
            genera[genus] = genus_identity
            counts = {c: int(row[c]) for c in CATEGORIES}
            total = int(row['total_samples'])
            if total <= 0 or any(v < 0 for v in counts.values()) or sum(counts.values()) != total:
                raise RuntimeError(f'Recuentos inválidos para TaxID {taxid}')
            pct = {c: 100.0 * counts[c] / total for c in CATEGORIES}
            groups[genus].append((total, counts, pct))
            out = {k: row[k] for k in IDS}
            out['total_samples'] = total
            out.update({c + '_pct': format(pct[c], '.10g') for c in CATEGORIES})
            pct_rows.append(out)
    if not seen:
        raise RuntimeError('Tabla vacía')

    # Calcula estadísticas de recuento, media y desviación estándar por género
    common = IDS[:3] + ['n_species_with_biosamples', 'total_biosamples']
    count_fields = common + [suffix for c in CATEGORIES for suffix in (c + '_mean', c + '_sd')]
    pct_fields = common + [suffix for c in CATEGORIES for suffix in (c + '_mean_pct', c + '_sd_pp')]
    count_rows, mean_pct_rows = [], []
    for genus in sorted(groups, key=str.casefold):
        values = groups[genus]
        metadata = dict(zip(IDS[:3], genera[genus]))
        metadata.update(n_species_with_biosamples=len(values), total_biosamples=sum(v[0] for v in values))
        out_count, out_pct = dict(metadata), dict(metadata)
        for c in CATEGORIES:
            for index, out, mean_suffix, sd_suffix in (
                    (1, out_count, '_mean', '_sd'),
                    (2, out_pct, '_mean_pct', '_sd_pp')):
                nums = [v[index][c] for v in values]
                out[c + mean_suffix] = format(mean(nums), '.10g')
                out[c + sd_suffix] = format(stdev(nums), '.10g') if len(nums) > 1 else 'NA'
        count_rows.append(out_count)
        mean_pct_rows.append(out_pct)

    # Escribe los archivos de salida
    write(pct_path, IDS + ['total_samples'] + [c + '_pct' for c in CATEGORIES], pct_rows)
    write(count_path, count_fields, count_rows)
    write(mean_pct_path, pct_fields, mean_pct_rows)
    print(f'TERMINADO\nTaxID de especie: {len(seen):,}\nGéneros: {len(groups):,}')
    print('Taxones sin BioSamples no incluidos; se conservan nombres provisionales del inventario.')
    for path in [pct_path, count_path, mean_pct_path]:
        print(f'Salida: {path}')


if __name__ == '__main__':
    main()
