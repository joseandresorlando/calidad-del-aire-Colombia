#Note: En Vista que se esscribe todo en ingles todos los comentarios estaran en dicho idioma
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")  # save figures to files without needing a display
import matplotlib.pyplot as plt

# Configuracion de constantes
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATASET_PATH = PROJECT_ROOT / "data" / "air_quality_colombia.csv"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CLEAN_DATASET_PATH = OUTPUTS_DIR / "air_quality_clean.csv"
ENRICHED_DATASET_PATH = OUTPUTS_DIR / "air_quality_enriched.csv"
POLLUTANT_FIGURE_PATH = OUTPUTS_DIR / "average_by_pollutant.png"
DEPARTMENT_FIGURE_PATH = OUTPUTS_DIR / "pm25_by_department.png"
TREND_FIGURE_PATH = OUTPUTS_DIR / "pm25_trend_by_year.png"

#Cambia los nombres de los encabezados en español (sin acentos)
COLUMN_RENAME = {
    "ID Estacion": "station_id",
    "Autoridad Ambiental": "environmental_authority",
    "Estacion": "station_name",
    "Latitud": "latitude",
    "Longitud": "longitude",
    "Variable": "variable",
    "Unidades": "units",
    "Tiempo de exposicion (horas)": "exposure_hours",
    "Ano": "year",
    "Promedio": "average_value",
    "Suma": "sum_value",
    "No. de datos": "data_count",
    "Representatividad Temporal": "temporal_representativeness",
    "Excedencias limite actual": "exceedances_count",
    "Porcentaje excedencias limite actual": "exceedances_percentage",
    "Mediana": "median_value",
    "Percentil 98": "percentile_98",
    "Maximo": "maximum_value",
    "Fechas/horas del maximo": "maximum_datetime_text",
    "Minimo": "minimum_value",
    "Fechas/horas del minimo": "minimum_datetime_text",
    "Dias de excedencias": "exceedance_days",
    "Codigo del Departamento": "department_code",
    "Nombre del Departamento": "department",
    "Codigo del Municipio": "municipality_code",
    "Nombre del Municipio": "municipality",
    "Tipo de Estacion": "station_type",
    "Ubicacion": "location_wkt",
}

#Columnas que se reciben en formato de texto con una coma como separador de miles.
NUMERIC_COLUMNS = [
    "latitude", "longitude", "exposure_hours", "year", "average_value",
    "sum_value", "data_count", "temporal_representativeness",
    "exceedances_count", "exceedances_percentage", "median_value",
    "percentile_98", "maximum_value", "minimum_value", "exceedance_days",
]

#Columnas de estandarizacion texto.
CATEGORICAL_COLUMNS = [
    "environmental_authority", "variable", "units",
    "department", "municipality", "station_type",
]

#Campos obligatorios para análisis
REQUIRED_FIELDS = ["average_value", "year", "variable", "department"]

# Contaminantes atmosféricos, a diferencia de las variables meteorológicas
POLLUTANT_VARIABLES = ["PM2.5", "PM10", "PST", "SO2", "NO2", "NO", "O3", "CO"]

#Valores de la guía anual de la OMS 2021 (µg/m^3).
WHO_ANNUAL_GUIDELINE = {"PM2.5": 5.0, "PM10": 15.0}

MINIMUM_REPRESENTATIVENESS = 75.0
MAXIMUM_REPRESENTATIVENESS = 100.0
TOP_DEPARTMENTS_TO_PLOT = 12

#Cargar el archivo original (sin modificarlos)
def load_raw_dataset(dataset_path):
    try:
        raw_dataset = pd.read_csv(dataset_path, dtype=str, encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"The dataset was not found at '{dataset_path}'. "
            f"Place the original CSV in the data folder."
        )
    except UnicodeDecodeError:
        raise ValueError(
            f"The dataset at '{dataset_path}' is not valid UTF-8 text."
        )
    
    accent_free_headers = {
        header: strip_accents(header) for header in raw_dataset.columns
    }
    raw_dataset = raw_dataset.rename(columns=accent_free_headers)
    raw_dataset = raw_dataset.rename(columns=COLUMN_RENAME)
    return raw_dataset

#Quitar las tildes y ñ
def strip_accents(text):
    replacements = str.maketrans("óíáéúñÓÍÁÉÚÑ", "oiaeunOIAEUN")
    return text.translate(replacements)

#Limpiar los datos (sobre una copia) 
def clean_dataset(raw_dataset):
    '''Toma la tabla original y le aplica los cuatro arreglos de limpieza,
uno tras otro, sobre una copia.'''
    clean = raw_dataset.copy()
    clean = convert_numeric_columns(clean)
    clean = standardize_categorical_columns(clean)
    clean = remove_impossible_representativeness(clean)
    clean = drop_records_missing_key_fields(clean)
    return clean

#funcion para  organizar numeros
def convert_numeric_columns(dataset):
    """Convierte en números de verdad las columnas que venían escritas como texto con coma de miles."""
    for column in NUMERIC_COLUMNS:
        without_separator = dataset[column].str.replace(",", "", regex=False)
        dataset[column] = pd.to_numeric(without_separator, errors="coerce")
    return dataset

#funcion para  organizar el texto 
def standardize_categorical_columns(dataset):
    for column in CATEGORICAL_COLUMNS:
        standardized = dataset[column].str.strip().str.upper()
        standardized = standardized.str.translate(
            str.maketrans("ÓÍÁÉÚÑ", "OIAEUN")
        )
        dataset[column] = standardized
    return dataset
#Borra los valores que son físicamente imposibles en la columna de representatividad.
def remove_impossible_representativeness(dataset):
    is_impossible = (
        dataset["temporal_representativeness"] > MAXIMUM_REPRESENTATIVENESS
    )
    dataset.loc[is_impossible, "temporal_representativeness"] = pd.NA
    return dataset

#quitar filas inservibles
def drop_records_missing_key_fields(dataset):
    """Elimina las filas que no sirven porque les falta un dato básico (promedio, año, variable o departamento)."""
    dataset = dataset.dropna(subset=REQUIRED_FIELDS)
    return dataset.reset_index(drop=True)

'''-------------------------------------------------------'''
# Enriquecer: agregar tres columnas nuevas

def enrich_dataset(clean_dataset):
    """añade a la tabla tres columnas calculadas que no venían en el archivo original."""
    enriched = clean_dataset.copy()
    enriched = add_pollutant_flag(enriched)
    enriched = add_reliability_level(enriched)
    enriched = add_who_exceedance_ratio(enriched)
    return enriched

#-------------------------------------------------------
#Confiabilidad
def add_pollutant_flag(dataset):
    """Crea una columna que marca con sí/no si cada fila corresponde a un contaminante del aire."""
    dataset["is_pollutant"] = dataset["variable"].isin(POLLUTANT_VARIABLES)
    return dataset

#nivel de confianza
def add_reliability_level(dataset):
    '''Crea una columna que etiqueta cada medición como confiable, de baja calidad o desconocida.'''
    representativeness = dataset["temporal_representativeness"]
    is_reliable = representativeness >= MINIMUM_REPRESENTATIVENESS
    is_known = representativeness.notna()

    dataset["reliability_level"] = "Low representativeness"
    dataset.loc[~is_known, "reliability_level"] = "Unknown"
    dataset.loc[is_known & is_reliable, "reliability_level"] = "Reliable"
    return dataset

#cuanto se pasa del limite 
def add_who_exceedance_ratio(dataset):
    """Crea una columna que dice cuántas veces el promedio de PM2.5 o PM10 
    supera el límite recomendado por la OMS."""
    guideline_per_row = dataset["variable"].map(WHO_ANNUAL_GUIDELINE)
    dataset["who_exceedance_ratio"] = (
        dataset["average_value"] / guideline_per_row
    )
    return dataset

# ---------------------------------------------------------------------------
# guardar (solo en la carpeta outputs) 
# ---------------------------------------------------------------------------
def save_dataset(dataset, output_path):
    """Guarda una tabla en un archivo nuevo, siempre dentro de la carpeta de resultados."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False, encoding="utf-8")
    return dataset

# preguntas del análisis
def select_reliable_pollutant_records(enriched_dataset):
    """Separa el grupo de datos que de verdad sirve para responder las preguntas: 
    solo contaminantes y solo confiables. """
    is_pollutant = enriched_dataset["is_pollutant"]
    is_reliable = enriched_dataset["reliability_level"] == "Reliable"
    reliable_pollutants = enriched_dataset[is_pollutant & is_reliable]
    return reliable_pollutants.reset_index(drop=True)

#----->
def summarize_average_by_pollutant(reliable_pollutants):
    """Mostrar estadísticas resumidas del promedio anual de cada contaminante."""
    summary = (
        reliable_pollutants
        .groupby("variable")["average_value"]
        .agg(["count", "mean", "median", "max"])
        .sort_values("mean", ascending=False)
    )
    return summary


def summarize_pm25_by_department(reliable_pollutants):
    """muestra cuántas veces en promedio el PM2.5 supera el límite de la OMS 
    y los ordena de peor a mejor.."""
    pm25_records = reliable_pollutants[
        reliable_pollutants["variable"] == "PM2.5"
    ]
    summary = (
        pm25_records
        .groupby("department")["who_exceedance_ratio"]
        .agg(["count", "mean"])
        .sort_values("mean", ascending=False)
    )
    return summary


def summarize_pm25_trend_by_year(reliable_pollutants):
    """la media nacional anual de PM2,5 para cada año."""
    pm25_records = reliable_pollutants[
        reliable_pollutants["variable"] == "PM2.5"]
    summary = (pm25_records
        .groupby("year")["average_value"]
        .agg(["count", "mean"])
        .sort_index()
    )
    return summary


# Graficos
# ---------------------------------------------------------------------------

def plot_average_by_pollutant(pollutant_summary, output_path):
    """gráfico de barras horizontales con el valor medio de cada contaminante."""
    ordered = pollutant_summary.sort_values("mean")

    figure, axes = plt.subplots(figsize=(9, 5))
    axes.barh(ordered.index, ordered["mean"], color="#0672e6")
    axes.set_xlabel("Mean yearly average value")
    axes.set_ylabel("Pollutant")
    axes.set_title("Mean yearly average by pollutant (reliable records)")
    save_figure(figure, output_path)
    return output_path


def plot_pm25_by_department(department_summary, output_path):
    """gráfico de barras con el índice de PM2,5 de la OMS
    correspondiente a los departamentos con peores resultados."""
    top = department_summary.head(TOP_DEPARTMENTS_TO_PLOT)

    figure, axes = plt.subplots(figsize=(10, 5))
    axes.bar(top.index, top["mean"], color="#a5453b")
    axes.axhline(1.0, color="black", linestyle="--", linewidth=1)
    axes.set_xlabel("Department")
    axes.set_ylabel("Mean PM2.5 average / WHO guideline")
    axes.set_title("Times the PM2.5 average exceeds the WHO guideline")
    axes.tick_params(axis="x", rotation=45)
    save_figure(figure, output_path)
    return output_path


def plot_pm25_trend_by_year(year_summary, output_path):
    """gráfico de líneas que muestre la media nacional de PM2,5 a lo largo de los años."""
    figure, axes = plt.subplots(figsize=(9, 5))
    axes.plot(year_summary.index, year_summary["mean"],
              marker="o", color="#3b8a5a")
    axes.set_xlabel("Year")
    axes.set_ylabel("Mean PM2.5 yearly average")
    axes.set_title("National mean PM2.5 average over time")
    save_figure(figure, output_path)
    return output_path


def save_figure(figure, output_path):
    """Ordena el diseño, comprueba que la carpeta existe y guarda la figura."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=120)
    plt.close(figure)