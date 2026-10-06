#!/usr/bin/env python3

"""
Cuenta las BioSamples descargadas por TaxID de especie, y las clasifica en 20 y 9 categorías.

Solo se incluyen las especies representadas en los metadatos, las especies ausentes
no se consideran ceros medidos.

"""
import argparse
import csv
import gzip
from collections import Counter
from pathlib import Path

# -------------------[ configuracion ]---------------------------------#

CATEGORIES = (
    'fecal_samples gut_samples urine_samples blood_samples respiratory_samples '
    'oral_samples skin_samples wound_samples urogenital_samples other_animal_samples '
    'soil_samples freshwater_samples marine_samples water_samples wastewater_samples '
    'sediment_samples plant_samples food_samples other_samples isolation_source_unknown'
).split()
GROUPS = {
    'fecal_gut_samples': ['fecal_samples', 'gut_samples'],
    'other_animal_samples': ['urine_samples', 'blood_samples', 'respiratory_samples',
        'oral_samples', 'skin_samples', 'wound_samples', 'urogenital_samples',
        'other_animal_samples'],
    'soil_samples': ['soil_samples'],
    'water_samples': ['wastewater_samples', 'water_samples', 'freshwater_samples', 'marine_samples'],
    'sediment_samples': ['sediment_samples'],
    'plant_samples': ['plant_samples'],
    'food_samples': ['food_samples'],
    'other_samples': ['other_samples'],
    'isolation_source_unknown': ['isolation_source_unknown'],
}
IDENTITY = ['silva_genus', 'ncbi_genus_name', 'ncbi_genus_taxid',
            'ncbi_species_name', 'ncbi_species_taxid']
UNKNOWN = {'', 'na', 'n/a', 'nan', 'none'}


INPUT= Path("ncbi_biosample_metadata_all_species.tsv.gz")
DICTIONARY= Path("isolation_source_classification.tsv")
OUTPUT20= Path("ncbi_species_environment_summary_20_categories.tsv")
OUTPUT9= Path("ncbi_species_environment_summary_9_categories.tsv")
PENDING= Path("unmapped_isolation_sources_species.tsv")

# -------------------[ funciones ]-------------------------------------#

def norm(value):
    """Normaliza un valor de isolation_source para compararlo con la tabla de mapeo."""
    return value.strip().casefold()


def checked_reader(handle, required):
    """Lee un TSV y comprueba que la cabecera contiene los campos requeridos."""
    reader = csv.DictReader(handle, delimiter='\t')
    fields = reader.fieldnames or []
    missing = set(required) - set(fields)
    if missing or len(fields) != len(set(fields)):
        raise RuntimeError(f'Cabecera incorrecta; faltan: {sorted(missing)}')
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise RuntimeError(f'Fila incompleta o mal formada: {reader.line_num}')
        yield row


def write_table(path, fields, rows):
    """Escribe un TSV con los campos y filas indicados"""
    temporary = path.with_name(path.name + '.part')
    with temporary.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)

# -------------------[ main ]-------------------------------------#

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path.cwd())
    args = parser.parse_args()
    base = args.base.resolve()
    input_path = base / INPUT
    dictionary = base / DICTIONARY
    output20 = base / OUTPUT20
    output9 = base / OUTPUT9
    pending = base / PENDING
    for path in (output20, output9):
        if path.exists():
            raise RuntimeError(f'La salida ya existe: {path}. Consérvala o renómbrala antes de repetir.')

    # Lee la tabla de mapeo de isolation_source a categoría, y valida que no haya contradicciones
    mapping = {}
    with dictionary.open(encoding='utf-8-sig', newline='') as handle:
        for row in checked_reader(handle, ['isolation_source', 'category']):
            key = norm(row['isolation_source'])
            category = row['category'].strip()
            if key in UNKNOWN:
                continue
            if category not in CATEGORIES:
                raise RuntimeError(f'Categoría no válida: {category!r}')
            if key in mapping and mapping[key] != category:
                raise RuntimeError(f'Categorías contradictorias para: {key!r}')
            mapping[key] = category

    assert Counter(c for group in GROUPS.values() for c in group) == Counter(CATEGORIES)
    summary, seen, unmapped = {}, set(), Counter()
    total = 0
    with gzip.open(input_path, 'rt', encoding='utf-8-sig', newline='') as handle:
        for row in checked_reader(handle, IDENTITY + ['biosample_accession', 'isolation_source']):
            accession = row['biosample_accession'].strip()
            taxid = row['ncbi_species_taxid'].strip()
            if not accession or not taxid or not row['silva_genus'].strip():
                raise RuntimeError('Falta accession, TaxID de especie o género SILVA')
            if accession in seen:
                raise RuntimeError(f'BioSample duplicado: {accession}')
            seen.add(accession)
            identity = {key: row[key].strip() for key in IDENTITY}
            if taxid not in summary:
                summary[taxid] = {'identity': identity, 'total': 0, 'counts': Counter()}
            data = summary[taxid]
            if data['identity'] != identity:
                raise RuntimeError(f'Identidad taxonómica inconsistente para TaxID {taxid}')
            source = row['isolation_source']
            key = norm(source)
            category = 'isolation_source_unknown' if key in UNKNOWN else mapping.get(key)
            if category is None:
                unmapped[source] += 1
            else:
                data['counts'][category] += 1
            data['total'] += 1
            total += 1
            if total % 100000 == 0:
                print(f'Procesados {total:,} BioSamples', flush=True)

    # Escribe la tabla de términos sin clasificar
    write_table(pending, ['isolation_source', 'count'],
        ({'isolation_source': s, 'count': n} for s, n in unmapped.most_common()))
    if unmapped:
        raise SystemExit(f'Hay {len(unmapped):,} términos sin clasificar. Revisar {pending}. No se han generado resúmenes.')
    if not total:
        raise RuntimeError('La tabla no contiene BioSamples')

    # Genera las tablas de resumen de 20 y 9 categorías
    rows20, rows9 = [], []
    for data in sorted(summary.values(), key=lambda d: (
            d['identity']['silva_genus'].casefold(),
            d['identity']['ncbi_species_name'].casefold(),
            d['identity']['ncbi_species_taxid'])):
        counts = {cat: data['counts'][cat] for cat in CATEGORIES}
        grouped = {group: sum(counts[c] for c in cats) for group, cats in GROUPS.items()}
        if sum(counts.values()) != data['total'] or sum(grouped.values()) != data['total']:
            raise RuntimeError('Las categorías no suman total_samples')
        common = dict(data['identity'], total_samples=data['total'])
        rows20.append(dict(common, **counts))
        rows9.append(dict(common, **grouped))
    write_table(output20, IDENTITY + ['total_samples'] + CATEGORIES, rows20)
    write_table(output9, IDENTITY + ['total_samples'] + list(GROUPS), rows9)


    print(f'\nTERMINADO\nBioSamples: {total:,}\nTaxID de especie: {len(summary):,}', flush=True)
    print('Solo se incluyen taxones con BioSamples descargados; también nombres provisionales sp./uncultured.')
    print('Validación: ambas tablas suman total_samples en cada fila.')
    print(f'Salidas:\n{output20}\n{output9}')


if __name__ == '__main__':
    main()
