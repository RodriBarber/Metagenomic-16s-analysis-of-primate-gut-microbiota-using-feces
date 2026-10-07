<<<<<<< HEAD
# Análisis Metagenómico de la microbiota intestinal de primates utilizando
heces V2
=======
# Análisis Metagenómico de la microbiota intestinal en primates

>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
Rodrigo Barber
2026-01-09

# Obtención y preparado de los datos

Se procede al análisis metagenomico por amplicon de 16s rRNAa de la
región V4 y en formato single-end. Los datos han sido obtenidos del
estudio de [Amato et al,
2018](https://pubmed.ncbi.nlm.nih.gov/29995839/). Concretamente, se han
descargado los archivos FASTQ correspondientes a las muestras de heces
de primates del ENA (European Nucleotide Archive).
Link:“https://www.ebi.ac.uk/ena/browser/view/ERP104379”

## Obtención de las lecturas

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4

# Creamos el directorio de trabajo para almacenar los archivos FASTQ
mkdir -p /data/DATA10TB/Rodri/16s_v2

# Cambiamnos el directorio de trabajo y creamos un directorio para almacenar los archivos FASTQ
cd /data/DATA10TB/Rodri/16s_v2
mkdir -p reads
```

Ejecutamos el script “download_16S_data.sh” para descargar los archivos
FASTQ de las muestras de heces de primates. Archivo que esta en el disco
data/DATA10TB/Rodri/16s_v2/reads.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Ejecutamos el script para descargar los FASTQ
chmod +x ./reads/download_16S_data.sh
./reads/download_16S_data.sh

# Comprobamos que los archivos se han descargado correctamente

ls -l ./reads/*.fastq.gz | wc -l
```

Observamos que hay 154 archivos FASTQ descargados, que corresponden a
las 154 muestras de heces de primates del estudio de Amato et al, 2018.

Comprobamos que los archivos son correctos mediante la verificación de
los valores MD5.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Creamos un directorio para almacenar los archivos .tsv en general y descargamos el archivo de verificación de MD5 desde el ENA
mkdir -p tsv
curl -s "https://www.ebi.ac.uk/ena/portal/api/filereport?accession=ERP104379&result=read_run&fields=run_accession,fastq_md5,fastq_bytes&format=tsv&limit=0" > tsv/ena_md5.tsv

cd reads
bad=0
while IFS=$'\t' read -r run md5 bytes; do
    f="${run}.fastq.gz"
    [[ -f "$f" ]] || { echo "FALTA: $f"; continue; }
    got=$(md5sum "$f" | cut -d' ' -f1)
    if [[ "$got" != "$md5" ]]; then
        echo "MD5 NO COINCIDE: $f (esperado $md5, obtenido $got)"
        bad=$((bad+1))
    fi
done < <(tail -n +2 ../tsv/ena_md5.tsv)
echo "Ficheros con MD5 incorrecto: $bad"
```

No hay ningun fichero incorrecto, por lo que podemos continuar con el
análisis.

## Tabla de metadatos

Descargamos en formato .tsv la tabla de metadatos del estudio de Amato
et al, 2018. Esta tabla contiene información sobre las muestras, como el
ID de la muestra, el tipo de primate del que proviene, el origen del
tejido y otros datos relevantes. Se obtiene desde la web del ENA.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Creamos un directorio para almacenar los metadatos
mkdir metadata

# Una vez descargado el archivo, lo movemos al directorio de metadatos y le cambiamos el nombre a "metadata.tsv"
mv ./metadata/filereport_read_run_ERP104379.tsv ./metadata/metadata.tsv
```

## Tabla de fenotipos-metadatos

Creamos una tabla combinando el ID de las muestras con el nombre de la
especie y su fenotipo alimenticio. Para ello combinamos las tablas de
maría con la tabla de metadatos.

<<<<<<< HEAD
- sample-id
- Especie
- TrophicGuild
- Carn
- frug_idx
- fol_idx
- ins_idx
- Ethanol
=======
-   sample-id
-   Especie
-   TrophicGuild
-   Carn
-   frug_idx
-   fol_idx
-   ins_idx
-   Ethanol
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4

Se eliminan muestras que corresponden a especies que de las que no
disponemos de informacion sobre su fenotipo alimenticio.

Lagothrix lagotricha Alouatta pigra Ateles hybridus Alouatta palliata

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
cd /data/DATA10TB/Rodri/16s_v2/reads

ids=(ERR2124868 ERR2124869 ERR2124870 ERR2124871 ERR2124872 ERR2124873
     ERR2124874 ERR2124875 ERR2124876 ERR2124877 ERR2124878 ERR2124879
     ERR2124880 ERR2124881 ERR2124882 ERR2124883 ERR2124959 ERR2124960
     ERR2124961 ERR2124962)

# Lista para comprobar antes de borrar los archivos FASTQ
for id in "${ids[@]}"; do
    [[ -f "$id.fastq.gz" ]] && echo "existe: $id.fastq.gz" || echo "NO esta: $id.fastq.gz"
done

# Borramos los archivos FASTQ correspondientes 
for id in "${ids[@]}"; do rm -f "$id.fastq.gz"; done

# Verificamos que los archivos se han eliminado correctamente
ls -l *.fastq.gz | wc -l
```

Tras eliminar estas muestras, nos quedamos con 134 muestras totales (se
eliminan 20).

## Archivo manifiesto

Ahora hacemos el archivo manifiesto, que es un archivo .tsv que contiene
la información de las muestras y sus correspondientes archivos FASTQ.
Este archivo es necesario para poder procesar los datos con QIIME2.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
cd ./metadata

# Creamos el archivo manifiesto

{
    printf "sample-id\tabsolute-filepath\n"
    for file in /data/DATA10TB/Rodri/16s_v2/reads/*.fastq.gz; do
        sample_id=$(basename "$file" .fastq.gz)
        printf "%s\t%s\n" "$sample_id" "$file"
    done
} > manifest.tsv

# Verificamos que el archivo manifiesto se ha creado correctamente
ls -l manifest.tsv
```

A continuación visualizamos la tabla de metadatos en QIIME2 para
comprobar que se ha creado correctamente.

Para la tabla de metadatos, se ha creado un archivo .tsv con la
información de las muestras y sus correspondientes archivos FASTQ. Este
archivo es necesario para poder procesar los datos con QIIME2.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Importamos la tabla de metadatos en QIIME2
qiime metadata tabulate --m-input-file ./metadata/sample-metadata.tsv --o-visualization sample-metadata.qzv

# Guardamos los archivos de visualizacion
mkdir -p plots
mv sample-metadata.qzv ./plots/

# visualizamos la tabla de metadatos en QIIME2
qiime tools view plots/sample-metadata.qzv
```

# Pre-procesamiento de las lecturas

## Presencia de primers

Se procede a dectectar la presencia del primer 515F en las lecturas.
Solo se busca el primer fw porque el rv no esta presente en las
lecturas. Es un estudio single-end.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7


# Creamos un directorio para almacenar los resultados de los análisis 
mkdir -p analysis/primer_check

# Comprobamos % de lecturas que contienen el primer 515F anclado a 5' y no anclado
reads_dir="/data/DATA10TB/Rodri/16s_v2/reads"
{
printf "sample\tpct_515F_anclado\tpct_515F_libre\n"
for f in "$reads_dir"/*.fastq.gz; do
    s=$(basename "$f" .fastq.gz)
    a=$(cutadapt -g "^GTGYCAGCMGCCGCGGTAA" -e 0.1 -j 4 -o /dev/null "$f" 2>&1 \
        | grep -oP 'Reads with adapters:.*\(\K[0-9.]+(?=%\))')
    l=$(cutadapt -g "GTGYCAGCMGCCGCGGTAA" -e 0.1 -j 4 -o /dev/null "$f" 2>&1 \
        | grep -oP 'Reads with adapters:.*\(\K[0-9.]+(?=%\))')
    printf "%s\t%s\t%s\n" "$s" "${a:-NA}" "${l:-NA}"
done
} | tee analysis/primer_check/primer_check_515F.tsv
```

La presencia de primers se evaluó con cutadapt buscando 515F
(GTGYCAGCMGCCGCGGTAA) anclado al extremo 5’ de las lecturas, con una
tasa de error del 10%. En las 134 muestras la fracción de lecturas con
primer anclado fue del 0.0%. La búsqueda sin anclar dio valores
residuales (media 0.125%, máximo 0.5%), atribuibles a coincidencias
internas de la sonda degenerada. Se concluye que las lecturas
depositadas en el ENA ya no contienen los primers de amplificación.

## Resumen de la calidad de las secuencias

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Importamos los datos de secuenciación en QIIME2
qiime tools import --type 'SampleData[SequencesWithQuality]' --input-path metadata/manifest.tsv --output-path analysis/demux.qza --input-format SingleEndFastqManifestPhred33V2

# Visualizamos el resumen de las secuencias
qiime demux summarize --i-data analysis/demux.qza --o-visualization plots/demux.qzv
qiime tools view plots/demux.qzv
```

Los datos muestra un total de 4.326.533 lecturas en las 134 muestras
biológicas, con una mediana de de 28.830 lecturas por muestra. El máximo
es de 76.792 y el mínimo de 16.966 lecturas por muestra. Todo esto nos
indica que la profundidad de secuenciación es suficiente para el
análisis de la diversidad microbiana.

Por otro lado, la longitud de las lecturas es de 151 pb. La calidad a su
vez es buena, con las lecturas manteniendo en general un score de
calidad superior a Q30.

## Denoising y trimming de las lecturas

En base a los resultados obtenidos se elimina exclusivamente la última
base de las lecturas, que es la única quyo score disminuye de Q15.
Además se procede al filtrado de calidad, denoising y eliminacón de las
quimeras de PCR por dada2.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Trimming de las lecturas y denoising con DADA2 
qiime dada2 denoise-single --i-demultiplexed-seqs analysis/demux.qza --p-trim-left 0 --p-trunc-len 150 --o-representative-sequences analysis/asv-seqs.qza --o-table analysis/asv-table.qza --o-denoising-stats analysis/denoising-stats.qza --o-base-transition-stats analysis/base-transition-stats.qza

# Visualizamos los resultados del denoising
qiime metadata tabulate --m-input-file analysis/denoising-stats.qza --o-visualization plots/denoising-stats.qzv

qiime tools view plots/denoising-stats.qzv
```

Al comprobar el porcentaje de lecturas que pasan todos los filtros de
calidad, denoising y eliminación de quimeras, se observa que entre el
64% - 96% de las reads sobrevivien al filtrado global. No obstante, en
la mayoría de las muestrtas este porcentaje no disminuye del 85%, lo que
indica que mantenemos una cantidad adecuada de lecturas (entre 15k y
68k) para el análisis.

## Tabla de ASVs y resumen de los datos

A continuación, creamos una tabla con la distribución de las secuencias
y de las ASVs asociadas a cada muestra.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Creamos la tabla de características y el resumen de los datos
qiime feature-table summarize --i-table analysis/asv-table.qza --m-metadata-file metadata/sample-metadata.tsv --o-summary plots/asv-table.qzv --o-sample-frequencies analysis/sample-frequencies.qza --o-feature-frequencies analysis/asv-frequencies.qza

# Visualizamos el resumen de los datos
qiime tools view plots/asv-table.qzv
```

Al visualizar los datos, observamos como el min y max de reads se
mantienen similares (16k y 68k respectivamente) que antes del filtrado y
denoising. Sin embargo la bajado a subido a 26.658 reads por muestra, lo
que indica que la mayoría de las muestras tienen una buena profundidad
de secuenciación. Viendo la distribución de las reads, cabe destacar que
algunas muestras presentan una profundidad de secuenciaciópn más elevada
(50k-70k).

En cuanto a las ASVs, la frecuencia mínima total es de 2 y la máxima de
28k. Mientras que la mediana se encuentra en 18. Esto indica que la
mayoría de las muestras tienen una diversidad microbiana moderada, con
algunas muestras que presentan una diversidad más elevada.

## Mapa de los ids de las ASVs y sus secuencias

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# ASV-table
qiime feature-table tabulate-seqs --i-data analysis/asv-seqs.qza --m-metadata-file analysis/asv-frequencies.qza --o-visualization plots/asv-seqs.qzv

# Visualizamos los resultados 
qiime tools view plots/asv-seqs.qzv
```

Se encuentra 14.811 ASVs diferentes.

## Filtrado de las ASVs por prevalencia

El filtrado por prevalencia se fijó en un mínimo de 2 muestras (que cada
ASV aparezca en al menos 2 muestras). Dado que el diseño compara 15
especies de primates con tamaños muestrales desiguales (5–12
individuos), se consideran adecuadas las condiciones de filtrado, ya que
un úmero superior podría eliminar ASVs reales. El criterio adoptado
descarta las ASVs presentes en un único individuo y delega la
eliminación del ruido de baja frecuencia al posterior filtrado por
abundancia.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Filtramos las ASVs por prevalencia (eliminamos aquellas que aparecen en menos de 2 muestras)
qiime feature-table filter-features --i-table analysis/asv-table.qza --p-min-samples 2 --o-filtered-table analysis/asv-table-ms2.qza

# Sincronizamos secuencias con la tabla filtrada
qiime feature-table filter-seqs --i-data analysis/asv-seqs.qza --i-table analysis/asv-table-ms2.qza --o-filtered-data analysis/asv-seqs-ms2.qza

# Resumen de los datos filtrados
qiime feature-table summarize --i-table analysis/asv-table-ms2.qza --m-metadata-file metadata/sample-metadata.tsv --o-summary plots/asv-table-ms2.qzv --o-sample-frequencies analysis/sample-frequencies-ms2.qza --o-feature-frequencies analysis/asv-frequencies-ms2.qza

# Visualizamos el resumen de los datos filtrados
qiime tools view plots/asv-table-ms2.qzv
```

## Filtrado de las ASVs por abundancia

A continuación visualizamos las frecuencias de las ASVs en función de su
abundancia y prevalenica con el scriprt “Plot_hist_freq_vs_prev.py” y el
script “plot_thresholds_comparison.py” para determinar el umbral de
abundancia a usar en el filtrado.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Creamos el directorio para almacenar los archivos TSV
mkdir -p tsv

# Transformamos la tabla de ASVs a formato TSV para poder analizarla con Python
qiime tools export --input-path ./analysis/asv-table-ms2.qza --output-path ./tsv
biom convert -i ./tsv/feature-table.biom -o ./tsv/feature-table-ms2.tsv --to-tsv

# Cambiamos de directorio y ejecutamos el script de Python para generar el histograma de frecuencias vs prevalencia
 
python3 python/Plot_hist_freq_vs_prev.py
python3 python/plot_thresholds_comparison.py
```

En base a los gráficos y la literatura filtramos por abundancia con un
umbral del 0.01%, que corresponde con un umbral de 374 reads. Por lo que
de 6.197 ASVs totales, se eliminan 4197 y sobreviven 2000 (se mantienen
un 32% de las ASVs totales).

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Filtramos las ASVs por abundancia 
# Usamos umbral del 0.01%
qiime feature-table filter-features --i-table analysis/asv-table-ms2.qza --p-min-frequency 374 --o-filtered-table analysis/asv-table-ms3.qza

# Sincronizamos secuencias con la tabla filtrada
qiime feature-table filter-seqs --i-data analysis/asv-seqs.qza --i-table analysis/asv-table-ms3.qza --o-filtered-data analysis/asv-seqs-ms3.qza

# Resumen de los datos filtrados
qiime feature-table summarize --i-table analysis/asv-table-ms3.qza --m-metadata-file metadata/sample-metadata.tsv --o-summary plots/asv-table-ms3.qzv --o-sample-frequencies analysis/sample-frequencies-ms3.qza --o-feature-frequencies analysis/asv-frequencies-ms3.qza

# Visualizamos el resumen de los datos filtrados
qiime tools view plots/asv-table-ms3.qzv
```

Efectivamente, tras el filtrado por abundancia mantenemos 2000 ASvs
diferentes.

# Anotación taxonómica

Para la anotación taxonómica se usa un clasificador pre-entrenado de
“SILVA_144_SSURef_NR99_uniform_classifier_V4-515f-806r”. Este
clasificador ha sido entrenado con secuencias de referencia de SILVA y
permite asignar taxonomía a las ASVs obtenidas en el análisis.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Descargamos el clasificador pre-entrenado de SILVA 144 para la región V4 del gen 16S rRNA
mkdir -p classifiers
cd classifiers
wget https://www.arb-silva.de/fileadmin/silva_databases/current/QIIME2/2026.7/SSU/V4-515f-806r/uniform/SILVA_144_SSURef_NR99_uniform_classifier_V4-515f-806r.qza
cd ..

# Anotación taxonómica de las ASVs con un classificador pre-entrenado de SILVA 144 para la región V4 del gen 16S rRNA
qiime feature-classifier classify-sklearn --i-classifier classifiers/SILVA_144_SSURef_NR99_uniform_classifier_V4-515f-806r.qza --i-reads analysis/asv-seqs-ms3.qza --o-classification analysis/taxonomy-ms3.qza

# Visualizamos los resultados de la anotación taxonómica
qiime metadata tabulate --m-input-file analysis/taxonomy-ms3.qza --o-visualization plots/taxonomy-ms3.qzv
qiime tools view plots/taxonomy-ms3.qzv

# Sincronizamos secuencias con la tabla filtrada
qiime feature-table tabulate-seqs --i-data analysis/asv-seqs-ms3.qza --i-taxonomy analysis/taxonomy-ms3.qza --m-metadata-file analysis/asv-frequencies-ms3.qza --o-visualization plots/asv-seqs-ms3.qzv

# y lo visualizamos
qiime tools view plots/asv-seqs-ms3.qzv
```

Tras revisar el archivo el número de secuencias anotadas es de 2000. Es
decir, todas las secuencias han sido anotadas taxonómicamente, aunque a
veces la clasificación solo llega a niveles taxonomicos muy bajos. El
problema es que el clasificador SILVA solo esta curado a nivel de
genero, por lo que no se puede llegar a nivel de especie. Por lo tanto,
para el análisis de la composición taxonómica se usará el nivel de
género.

## Filtrado de las ASVs por mitocondria y cloroplastos

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Filtramos las ASVs por mitocondria y cloroplastos
qiime taxa filter-table --i-table analysis/asv-table-ms3.qza --i-taxonomy analysis/taxonomy-ms3.qza --p-exclude mitochondria,chloroplast --o-filtered-table analysis/asv-table-ms4.qza

# Sincronizamos secuencias con la tabla filtrada
qiime feature-table filter-seqs --i-data analysis/asv-seqs-ms3.qza --i-table analysis/asv-table-ms4.qza --o-filtered-data analysis/asv-seqs-ms4.qza

# Hacemos un resumen de los datos filtrados y lo visualizamos
qiime feature-table summarize --i-table analysis/asv-table-ms4.qza --m-metadata-file metadata/sample-metadata.tsv --o-summary plots/asv-table-ms4.qzv --o-sample-frequencies analysis/sample-frequencies-ms4.qza --o-feature-frequencies analysis/asv-frequencies-ms4.qza

qiime tools view plots/asv-table-ms4.qzv
```

Al filtrar por mitocondria y cloroplastos, se eliminan 6 ASVs, por lo
que nos quedamos con 1994 ASVs diferentes. Esto indica que la mayoría de
las secuencias corresponden a bacterias y no a contaminantes eucariotas.
Aedmás, la mediana de lecturas por muestra disminuye tras todos los
procesos de filtrado a 20k. Con un max en 63k y un min en 12k.

## Actualización de la taxonomía tras el filtrado por mitocondria y cloroplastos

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Actualizamos la taxonomía tras el filtrado por mitocondria y cloroplastos
qiime rescript filter-taxa --i-taxonomy analysis/taxonomy-ms3.qza --m-ids-to-keep-file analysis/asv-seqs-ms4.qza --o-filtered-taxonomy analysis/taxonomy-ms4.qza
```

## Porcentaje de reads mapeadas

Identificamos el % reads mapeadas a cada nivel taxonomico. Para ello
exportamos la tabla de frecuencias de las ASVs filtradas por mitocondria
y cloroplastos y ejecutamos el script de Python “percent_mapped.py”.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Exportamos la tabla de frecuencias de las ASVs filtradas por mitocondria y cloroplastos
qiime tools export --input-path analysis/taxonomy-ms4.qza --output-path tsv            # crea taxonomy.tsv
cd tsv 
mv taxonomy.tsv taxonomy-ms4.tsv
cd ..

qiime tools export --input-path analysis/asv-table-ms4.qza --output-path tsv           # crea feature-table.biom
biom convert -i tsv/feature-table.biom -o tsv/feature-table-ms4.tsv --to-tsv 

# Ejecutamos el script de Python para calcular el porcentaje de reads mapeadas
python3 python/percent_mapped.py

# visualizamos el resultado
python3 python/plot_percent_mapped.py
```

Tras el filtrado, la anotación con SILVA 144 asignó el 100% de las 1.994
ASVs al menos a nivel de dominio. La resolución alcanzó género en el
63.2% de las lecturas (57.4% de las ASVs) y familia en el 90.2% (87.9%
de las ASVs). Estos datos son suficientes para el análisis de la
composición taxonómica de la microbiota intestinal de los primates.

# Construcción del árbol filogenético

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
conda activate rachis-qiime2-2026.7

# Descargamos la base de datos de referencia para la inserción filogenética 
mkdir reference_DB
cd reference_DB
# wget https://data.qiime2.org/classifiers/sepp-ref-dbs/sepp-refs-silva-128.qza #SILVA 128
wget https://data.qiime2.org/classifiers/sepp-ref-dbs/sepp-refs-gg-13-8.qza 
cd ..

# Construcción del árbol filogenético mediante inserción filogenética 
qiime fragment-insertion sepp --i-representative-sequences analysis/asv-seqs-ms4.qza --i-reference-database reference_DB/sepp-refs-gg-13-8.qza  --o-tree analysis/insertion-tree.qza --o-placements analysis/insertion-placements.qza

# Visualizamos el árbol filogenético
qiime tools export --input-path analysis/insertion-tree.qza --output-path exported-tree
```

Una vez generado el archivo .nwk con el árbol, se visualiza en iTol. Se
identifican dos problemas: 1. El nombre de las ASVs no corresponde al
género 2. Existen identificadores repetidos.

## Comprobación del número de ASVs insertadas en el árbol filogenético

En primer lugar se comprueba que todas las ASVs han sido insertadas
correctamente en el árbol filogenético. Para ello, se exporta el archivo
“placements.json” y se cuenta el número de ASVs insertadas.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
conda activate rachis-qiime2-2026.7

# Exportamos el archivo placements.json para comprobar el número de ASVs insertadas en el árbol filogenético
qiime tools export --input-path analysis/insertion-placements.qza --output-path tsv

python -c "
import json

with open('tsv/placements.json') as f:
    data = json.load(f)

names = set()

for placement in data['placements']:
    for name in placement.get('nm', []):
        names.add(name[0])

print('ASVs insertados:', len(names))
"
```

Obtenemos 1994 ASVs insertadas en el árbol filogenético, que es el mismo
número de ASVs que teníamos tras el filtrado por mitocondria y
cloroplastos. Por lo tanto, la base de datos de greengenes es adecuada
para la inserción filogenética de nuestras ASVs (solo para la
construcción del árbol, no para la anotación taxonómica).

## Eliminación de ASVs duplicadas por género

En primer lugar, filtramos la taxonomia para obtener solo las ASVs que
legan a nivel de género. Si hay generos duplicados, se procede a
eliminar las ASVs duplicadas por género, manteniendo solo una ASV por
género. Para ello, usamos un script de Python “fix_asvs_dups.py”.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Ejecutamos el script de Python para eliminar las ASVs duplicadas por género
python3 ./python/fix_asvs_dups.py
```

## Construcción de un árbol filogenético sin duplicados por género

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
conda activate rachis-qiime2-2026.7

# Filtramos las secuencias para quedarnos solo con una ASV por género
qiime feature-table filter-seqs --i-data analysis/asv-seqs-ms4.qza --m-metadata-file tsv/taxonomy_unique.tsv --o-filtered-data analysis/asv-seqs-ms4-one-per-genus.qza

qiime fragment-insertion sepp --i-representative-sequences analysis/asv-seqs-ms4-one-per-genus.qza --i-reference-database reference_DB/sepp-refs-gg-13-8.qza --o-tree analysis/insertion-tree-one-per-genus.qza --o-placements analysis/insertion-placements-one-per-genus.qza

# Visualizamos el árbol filogenético
qiime tools export --input-path analysis/insertion-tree-one-per-genus.qza --output-path exported-tree/tree_v2
```

## Poda y corrección de los nombres de las secuencias para visualizarlas en iTOL

Para visualizar solo las ASVs insertadas y no la estructura
pre-establecida por Greengenes, se poda el árbol filogenético para
mantener solo las ASVs de interes. Además, se genera un archivo de
etiquetas para iTOL con los nombres de las secuencias correspondientes
al género.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
conda activate rachis-qiime2-2026.7

# Exportamos los archivos necesarios para la poda del árbol y la generación de etiquetas para iTOL
qiime tools export --input-path analysis/asv-seqs-ms4-one-per-genus.qza --output-path exported-tree/tree_v2
grep ">" exported-tree/tree_v2/dna-sequences.fasta | sed 's/>//' > exported-tree/tree_v2/mis_asv_ids.txt

wc -l exported-tree/tree_v2/mis_asv_ids.txt

# Activamos el entorno de python
conda activate python

# Ejecutamos el script de python para mantener solo las ASVs insertadas en el árbol 
python3 ./python/prune_tree_v2.py

# Transformamos los ids en nombres de las secuencias para poder visualizarlos en iTOL
python3 ./python/make_itol_labels_v2.py
```

## Modificación del árbol para representar presencia/ausencia o abundancia de ASVs por género

Para identificar patrones visuales que indicquen anomalias en la
composición de la microbiota, se genera un archivo de presencia/ausencia
o de abundancia relativa de ASVs por especie. Para ello, se usa un
script de Python que genera un archivo compatible con iTOL.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Abundancia de ASVs por género
python3 ./python/plot_tree_abundaces.py

# Presencia/ausencia de ASVs por género
python3 ./python/plot_tree_presence.py
```

# Análisis de diversidad

Para evaluar la diversidad de las muestras y la profundidad del
muestreo, se generan curvas de rarefacción. Estas curvas muestran la
relación entre el número de secuencias muestreadas y el número de ASVs
observadas. Como valor de profundidad máxima se utiliza el valor de la
mediana de secuencias por muestra, que es de 20k.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4

# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Ejecutamos el análisis de rarefacción para evaluar la diversidad de las muestras
qiime diversity alpha-rarefaction --i-table analysis/asv-table-ms4.qza --p-max-depth 20000 --m-metadata-file metadata/sample-metadata.tsv --o-visualization analysis/alpha-rarefaction.qzv

# Visualizamos los resultados del análisis de rarefacción
qiime tools view analysis/alpha-rarefaction.qzv
```

Como podemos ver en ambas figuras, todas las muestras se aplanan muy
rápido entorno a las 2k-3k lecturas, lo que indica que la profundidad de
secuenciación es suficiente para capturar la diversidad microbiana de
las muestras. Sin embargo, a partir de las 9k algunas curvas empiezan a
caer y llegan a 0 en 13k lecturas (no tienen suficiente profundidad de
secuenciación para un submuestreo tan elevado). Por eso se ha decidido
usar un tamaño de muestra de 9k secuencias para el remuestreo
(bootstrapping) en el análisis de diversidad alfa y beta.

## Alpha y beta diversidad

A continuación se hace un análisis de diversidad alfa y beta para
evaluar la biodiversidad de las muestras y la similitud entre ellas.
Para ello se utiliza el método de remuestreo (bootstrapping) con 10
iteraciones y un tamaño de muestra de 9k secuencias por muestra.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4

# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Ejecutamos el análisis de diversidad alfa y beta mediante remuestreo (bootstrapping) con 10 iteraciones y un tamaño de muestra de 9.000 secuencias por muestra
qiime boots kmer-diversity --i-table analysis/asv-table-ms4.qza --i-sequences analysis/asv-seqs-ms4.qza --m-metadata-file metadata/sample-metadata.tsv --p-sampling-depth 9000 --p-n 10 --p-replacement --p-alpha-average-method median --p-beta-average-method medoid --output-dir analysis/boots-kmer-diversity

# Visualizamos los resultados del análisis de diversidad alfa y beta
qiime tools view analysis/boots-kmer-diversity/scatter_plot.qzv
```

Como se pude observar el la figura (beta_diversity.png), las replicas
biológicas de cada especie se agrupan juntas, lo que indica que la
diversidad de las muestras es consistente dentro de cada especie. Lo que
es más importante, es que los indiciduos relacionados filogeneticamente
tienden a agruparse juntoos. Patrón que también se obvserba levemente en
función de la dieta. Aunque en este caso existe más dispersión en la
distribución de las muestras. No obstante, el porcentaje de variabilidad
explicada es solo del 25%, por lo que hay hay bastante estructura no
capturada.

Además también se presentan valores de shanon muy elevados
(alpha_diversity.png), lo que indica que la diversidad de las muestras
es alta. En general, se observa una buena diversidad de las muestras y
una buena consistencia entre las réplicas biológicas.

# Análisis de la composición taxonómica

## Barplot completo

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
eval "$(conda shell.bash hook)"
conda activate rachis-qiime2-2026.7

# Generamos un gráfico de barras de la composición taxonómica global
qiime taxa barplot --i-table analysis/asv-table-ms4.qza --i-taxonomy analysis/taxonomy-ms4.qza --m-metadata-file metadata/sample-metadata.tsv --o-visualization plots/taxa-bar-plots-ms4.qzv

# Visualizamos
qiime tools view plots/taxa-bar-plots-ms4.qzv
```

Como el número de muestras es muy elevado y la abundacia relativa muy
repartida, el gráfico de barras completo no es muy informativo. Por lo
que se decide hacer un gráfico de barras a nivel de género,
rerpresentando los 20 géneros mas abundantes. Para eso se usa el script
“plot_genus_barplot”

## Barplot a nivel de género

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de QIIME2
python3 python/plot_genus_barplot.py
```

## Heat Map

A continuación realizamos un heat map de la composición taxonómica a
nivel de genero. Para ello se clusterizan tanto las sp de primates como
los géneros bacterianos. Representandose los 20 géneros más abundantes.
Para ello se usa el script “heatmap_clustered.py”.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4

# Activamos el entorno de conda
conda activate python

# Activamos el entorno de QIIME2
python3 python/heatmap_clustered.py
```

# Análisis de bacterias contaminantes

Una vez tenemos la composición taxonómica de las muestras, se procede a
identificar los géneros bacterianos que pueden ser contaminantes
ambientales. En primer lugar se identifican los géneros bacterianos
únicos presentes en las muestras.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Ejecutamos el script de Python para identificar los géneros bacterianos únicos presentes en las muestras
python3 python/unique_genera.py

# Contamos el número de géneros únicos encontrados
cat ./tsv/genera_unique.txt | wc -l
```

Como podemos observar encotramos 198 géneros diferentes. Como dentro de
un género puede existir mucha variabilidad, tenemos que identificar el
número de especies por genero y luego caracerizar las especies dentro de
cada genero para identificar el origen general de las muestras
(biosamples) dónde se han detectado esas especies. De esta forma luego
se puede identificar si un genero entero suele tener o no un origen
ambiental similar, lo que sera imprescindible para caracterizar la
contamianción ambiental.

## Búsqueda de especies por género en NCBI

En primer lugar ejecutamos el script de Python
“count_ncbi_species_per_silva_genus.py” que consulta la base de datos de
NCBI para obtener el número de especies que corresponden a cada género y
reporta si ha sido posible encontrar el género en NCBI (el clasificador
es de SILVA y pueden existir discrepancias con la taxonomia de NCBI)

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Creamos un directorio para almacenar los resultados del análisis de contaminación
mkdir -p contaminacion

# Ejecutamos el script de Python para contar el número de especies por género en NCBI
python3 ./python/count_ncbi_species_per_silva_genus.py

# Chequeamos el número de géneros únicos encontrados en NCBI
python - <<'PY'
import csv
from collections import Counter

with open(
    "contaminacion/ncbi_species_per_silva_genus.tsv",
    encoding="utf-8-sig",
    newline=""
) as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))

print("RESUMEN:")
for status, count in sorted(Counter(r["status"] for r in rows).items()):
    print(f"{status}: {count}")

print("\nCASOS PENDIENTES:")
for row in rows:
    if row["status"] != "complete":
        print(
            row["silva_genus"],
            row["status"],
            row["message"],
            sep="\t",
        )
PY
```

Del total de los 198 géneros únicos, solo se han encontrado en el NCBI
150 con éxito, 46 no han sido encontrados y 2 son ambiguos (tienen
varios TaxIDs). Estos dos géneros son “Morganella” y “Schwartzia”.
Chequeamos en el NCBI estos géneros para ver si existe alguna
discrepancia y seleccionar el TaxId adecuado.

<<<<<<< HEAD
- Morganella: 108061,90690,581
- Schwartzia: 164984,55506

``` {bash}
=======
-   Morganella: 108061,90690,581
-   Schwartzia: 164984,55506

``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Chequeamos en el NCBI los géneros "Morganella" y "Schwartzia"
python - <<'PY'
from Bio import Entrez

Entrez.email = "rodrigo.barber@cnb.csic.es"

with Entrez.efetch(
    db="taxonomy",
    id="108061,90690,581,164984,55506",
    retmode="xml",
) as handle:
    records = Entrez.read(handle)

for record in records:
    print("Nombre:", record["ScientificName"])
    print("TaxID:", record["TaxId"])
    print("Rango:", record["Rank"])
    print("Linaje:", record.get("Lineage", ""))
    print()
PY
```

En el caso de Morganella, nos quedamos con el TaxID 581 y en el de
Schwartzia, con el TaxID 55506. Esto se debe a que en ambos casos, el
TaxID seleccionado es el único que corresponde al dominio de bacterias.
Para arreglar la tabla, a continuación se ejecuta el siguiente codigo.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Corrección de la tabla cbi_species_per_silva_genus.tsv
python3 python/fix_ncbi_species_per_silva_genus.py    # crea ncbi_species_per_silva_genus_resolved.tsv

# Chequeamos que la tabla se ha corregido correctamente
awk -F'\t' 'NR > 1 && $5 != "" {count++} END {print count}' ./contaminacion/ncbi_species_per_silva_genus_resolved.tsv
```

Tras correguir el error, ahora tenemos 151 géneros únicos encontrados en
NCBI con éxito, 46 no han sido encontrados y 1 resulta ser eucariota (el
género “Trichomitus”). La presencia de un eucariota es algo anómalo que
quiza se deba a la homonimia entre reinos de diferentes bases de datos.

A continuación para cada género creamos una tabla con el número de
especies y su TaxID en NCBI.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Creamos tablas por género con la inforamción de las especies
python3 python/download_ncbi_species_by_genus.py
```

Finalmente combinamos todas esas tablas en una sola tabla con toda la
información de las especies por género.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Hacemos el merge de todas las tablas por género en una sola tabla
python - <<'PY'
import csv
from pathlib import Path

folder = Path("contaminacion/ncbi_species_by_genus")
output = Path("contaminacion/ncbi_species_inventory_all_genera.tsv")
temporary = output.with_suffix(".tsv.part")

files = sorted(folder.glob("genus_*.tsv"))
if not files:
    raise SystemExit("ERROR: no se encontraron tablas")

fields = None
seen = set()
species_ids = set()
genera = set()
total = 0

with temporary.open("w", encoding="utf-8", newline="") as out:
    for file in files:
        with file.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")

            if fields is None:
                fields = reader.fieldnames
                writer = csv.DictWriter(
                    out, fieldnames=fields,
                    delimiter="\t", lineterminator="\n"
                )
                writer.writeheader()
            elif reader.fieldnames != fields:
                raise RuntimeError(f"Cabecera diferente: {file}")

            for row in reader:
                key = (
                    row["ncbi_genus_taxid"],
                    row["ncbi_species_taxid"],
                )

                if key in seen:
                    raise RuntimeError(f"Registro duplicado: {key}")

                seen.add(key)
                species_ids.add(row["ncbi_species_taxid"])
                genera.add(row["ncbi_genus_taxid"])
                writer.writerow(row)
                total += 1

temporary.replace(output)

print("Archivos procesados:", len(files))
print("Géneros con especies:", len(genera))
print("Filas de especies:", total)
print("TaxID de especie únicos:", len(species_ids))
print("Tabla creada:", output)
PY
```

## Recopilacion de biosamples por genero

Para cada género se cuenta el número de Biosamples que estan disponibles
en NCBI.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Contamos el número de Biosamples por género
python3 python/count_biosamples_per_species.py # crea ncbi_biosample_counts_per_species.tsv
```

A continuación, para todos esos generos con información de biosamples,
se ejecuta el script “download_ncbi_species_by_genus.py”, que recopila
los metadatos de cada biosamples de cada especie.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Contamos el número de Biosamples por género
python3 python/download_ncbi_species_by_genus.py # crea la carpeta "contaminacion/biosample_metadata_by_species" 
```

Finalmente, se combinan todos los metadatos de los biosamples en una
sola tabla.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Contamos el número de Biosamples por género
python3 python/built_biosample_metadata_table.py # crea "ncbi_biosample_metadata_all_species.tsv.gz" 
```

## Clasificación del origen de los géneros bacterianos

Una vez obtenido el número de biosamples y su origen, se colapsan los
más de 32000 origenes distintos del NCBI en 20 y 9 categorias
principales. Para ello se utiliza el archivo
“isolation_source_classification.tsv” que contiene todas las categorias
del NCBI y su clasificación.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Contamos el número de Biosamples por género
python3 python/build_species_environment_tables.py # crea "ncbi_species_environment_summary_20_categories.tsv" 
                                                   # crea "ncbi_species_environment_summary_9_categories.tsv"
```

Finalmente, para que sea lo más informativo posible, se agrupan todas
las categorias en 4 grandes grupos:

<<<<<<< HEAD
- Gut –\> gut/heces
- Contaminante –\> suelo/agua/sedimento/planta/alimento
- Animal –\> other_animal
- other –\> otras categorias
- unknown –\> origen desconocido

``` {bash}
=======
-   Gut –\> gut/heces
-   Contaminante –\> suelo/agua/sedimento/planta/alimento
-   Animal –\> other_animal
-   other –\> otras categorias
-   unknown –\> origen desconocido

``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Contamos el número de Biosamples por género
python3 python/collapse_environment_categories.py   # crea "ncbi_species_environment_summary_4_groups.tsv"
```

## Cálculo de estadisiticas

A continuación, se calcula el procentaje de biosamples que tienen un
origen concreto para cada género bacteriano y se calcula la media y la
desviación estandar. De esta forma se podrá identificar los géneros
bacterianos que tienen un origen ambiental predominante y que por lo
tanto pueden ser considerados como contaminantes ambientales.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Contamos el número de Biosamples por género
python3 python/summarize_genus_species_statistics.py 
# crea "ncbi_species_environment_percentages_3_groups.tsv" 
# crea "ncbi_genus_species_counts_mean_sd_3_groups.tsv"
# crea "ncbi_genus_species_percentages_mean_sd_3_groups.tsv"
```

Como se ha observado que existen muchos biosamples con origen
desconocido, se decide recalcular las estadísticas excluyendo los
biosamples con origen desconocido.

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Contamos el número de Biosamples por género
python3 python/recalculate_percentages_excluding_unknown.py
# crea "ncbi_species_environment_percentages_excluding_unknown.tsv" 
# crea "ncbi_genus_species_percentages_mean_sd_excluding_unknown.tsv"
```

## Visualización de los resultados

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Creamos la carpeta plots
mkdir -p plots

# Ejecutamos el script de Python para generar los gráficos de los resultados del análisis de contaminación
python3 python/plot_mean_sd_distributions.py
```

## Identificacion de géneros bacterianos contaminantes

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# Ejecutamos el script de Python para generar clasificar los géneros bacterianos en contaminantes y no contaminantes
python3 python/classify_genera.py
```

Solo se ha identificado un género bacteriano como contaminante
ambiental, que es el género “Macellibacteroides”. Además, este génmero
no se encuentra entre el top 50 más abundantes, por lo que no se
considera un problema para el análisis de la composición taxonómica de
la microbiota intestinal de los primates. Por otro lado, se han
identificado otros 84 generos bacterianos que tienen origen intestinal,
que esl lo que cabría encontrar en un estudio de microbiota intestinal.
Por lo tanto, se puede concluir que la mayoría de los géneros
bacterianos presentes en las muestras son de origen intestinal y no
contaminantes ambientales.

# HeatMap completo con la información de los géneros bacterianos contaminantes y no contaminantes

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# heat map con todas y con colores por especie
python3 python/heatmap_clustered_all_samples.py
```

# Abundancia relativa de los géneros bacterianos contaminantes a lo latgo de las muestars

<<<<<<< HEAD
``` {bash}
=======
``` bash
>>>>>>> cc340b6b9c1be919f536bc017d9d8f4dbbaa14d4
# Activamos el entorno de conda
conda activate python

# heat map con todas y con colores por especie
python3 python/plot_cont_dis.py
```

Como podemos osbervar, este género no se encuentra encasi ninguna mustra
y su abundancia relativa en aquellas en las que esta presente es muy
baja. Por lo tanto, se puede concluir que las muestras utilizadas
realmente eran frescas y no presentan una contaminación ambiental
significativa.
