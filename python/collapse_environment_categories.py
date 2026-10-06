#!/usr/bin/env python3
"""
Colapsa las 9 categorias de la tabla en 5 grupos.

  fecal_gut          <- fecal_gut_samples
  animal             <- other_animal_samples
  contaminant        <- soil, water, sediment, plant, food
  other              <- other_samples
  isolation_source_unknown <- unknown_samples

input:
    tsv/ncbi_species_environment_summary_9_categories.tsv
output:
    tsv/ncbi_species_environment_summary_5_groups.tsv
"""
import argparse
import csv
from collections import Counter
from pathlib import Path

# -------------------[ configuracion ]---------------------------------------#

input= Path('contaminacion/ncbi_species_environment_summary_9_categories.tsv')
output = Path('contaminacion/ncbi_species_environment_summary_5_groups.tsv')

CATEGORIES = (
    'fecal_gut_samples other_animal_samples soil_samples water_samples '
    'sediment_samples plant_samples food_samples other_samples '
    'isolation_source_unknown'
).split()
GROUPS = {
    'fecal_gut_samples': ['fecal_gut_samples',],
    'contaminant_samples': ['soil_samples', 'water_samples', 'sediment_samples','plant_samples', 'food_samples'],
    'animal_samples': ['other_animal_samples'],
    'other_samples': ['other_samples'],
    'unknown_samples': ['isolation_source_unknown']
}
IDENTITY = ['silva_genus', 'ncbi_genus_name', 'ncbi_genus_taxid',
            'ncbi_species_name', 'ncbi_species_taxid']

# -------------------[ funciones ]---------------------------------------#

def checked_reader(handle, required):
    """Lee un archivo TSV y valida que tenga las columnas requeridas y que no haya filas incompletas."""
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
    """Escribe un archivo TSV con los datos proporcionados."""
    temporary = path.with_name(path.name + '.part')
    with temporary.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)

# -------------------[ main ]---------------------------------------#

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path.cwd())
    args = parser.parse_args()
    base = args.base.resolve()
    input_path = base / input
    output2 = base / output
    if output2.exists():
        raise RuntimeError(f'La salida ya existe: {output2}. Consérvala o renómbrala antes de repetir.')

    # Asigna los grupos a las categorias y valida que no falte ninguna categoria
    assert Counter(c for group in GROUPS.values() for c in group) == Counter(CATEGORIES)

    # Lee la tabla de entrada y valida que los grupos sumen total_samples en cada fila
    rows3 = []
    total = 0
    with input_path.open(encoding='utf-8-sig', newline='') as handle:
        for row in checked_reader(handle, IDENTITY + ['total_samples'] + CATEGORIES):
            grouped = {group: sum(int(row[c]) for c in cats)
                       for group, cats in GROUPS.items()}
            declared = int(row['total_samples'])
            if sum(grouped.values()) != declared:
                raise RuntimeError(
                    f'Los grupos no suman total_samples en la línea {len(rows3) + 2}')
            common = {key: row[key].strip() for key in IDENTITY}
            rows3.append(dict(common, total_samples=declared, **grouped))
            total += declared

    if not rows3:
        raise RuntimeError('La tabla no contiene filas')

    # Escribe la tabla de salida
    write_table(output2, IDENTITY + ['total_samples'] + list(GROUPS), rows3)
    print(f'\nTERMINADO\nFilas: {len(rows3):,}\nBioSamples: {total:,}', flush=True)
    print('Validación: los grupos suman total_samples en cada fila.')
    print(f'Salida:\n{output2}')

if __name__ == '__main__':
    main()