# Análisis metagenómico 16S de microbiota intestinal de primates

Reanálisis de los datos de amplicón 16S rRNA (región V4, single-end) de
[Amato et al. 2019, *ISME J*](https://doi.org/10.1038/s41396-018-0175-0),
con dos objetivos: caracterizar la composición taxonómica de la microbiota
fecal de 15 especies de primates y evaluar la presencia de contaminación
ambiental.

## Datos

154 muestras del proyecto ENA [ERP104379](https://www.ebi.ac.uk/ena/browser/view/ERP104379).
No se incluyen en el repositorio: descárgalas con `python/download_16S_data.sh`.
El análisis usa las 134 muestras con datos de dieta disponibles (15 especies).

## Requisitos

- QIIME 2 (entorno `rachis-qiime2-2026.7`)
- Python 3 con pandas, matplotlib, seaborn, scipy, biopython

## Uso

El pipeline completo está documentado en `metag_16s_v2.qmd`, que debe
ejecutarse por orden.

## Estructura

| Carpeta | Contenido |
|---|---|
| `python/` | Scripts de análisis y figuras |
| `metadata/` | Tabla de muestras, especies e índices de dieta |
| `tsv/` | Tablas intermedias y de resultados |
| `plots/` | Figuras |
| `contaminacion/` | Clasificación de origen de los géneros vía NCBI BioSample |

## Decisiones metodológicas

- Filtrado por prevalencia: ≥2 muestras (los grupos más pequeños tienen 5
  individuos; un umbral porcentual excluiría la señal específica de
  hospedador).
- Filtrado por abundancia: 0.01% del total de lecturas.
- Clasificador: SILVA 144 V4-515f-806r. Incluye el rango reino, por lo que
  en `qiime taxa collapse` el nivel 6 es FAMILIA y el 7 GÉNERO.
- Las etiquetas no informativas de SILVA (`uncultured`, `Incertae_Sedis`)
  no cuentan como asignación.
