import analysis_logic as logic

SECTION_WIDTH = 70

#Imprimir el título de una sección enmarcado por líneas separadoras.
def print_section(title):
    print("\n" + "=" * SECTION_WIDTH)
    print(title)
    print("=" * SECTION_WIDTH)

#Indica el tamaño y las columnas del conjunto de datos recién cargado.
def report_structure(raw_dataset):
    print_section("1. STRUCTURE AND VERIFICATION")
    row_count, column_count = raw_dataset.shape
    print(f"Records loaded : {row_count}")
    print(f"Columns loaded : {column_count}")
    print("Columns:", ", ".join(raw_dataset.columns))

#Indique los valores que faltan y la variedad de los campos categóricos
def report_exploration(raw_dataset):
    print_section("2. INITIAL EXPLORATION")
    missing = raw_dataset.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("No missing values detected.")
    else:
        print("Missing values per column:")
        for column, count in missing.items():
            print(f"  {column}: {count}")
    print(f"Distinct measured variables: {raw_dataset['variable'].nunique()}")
    print("Distinct written forms of department: "
        f"{raw_dataset['department'].nunique()}")

#Reporta qué ha cambiado en el paso de limpieza
def report_cleaning(raw_dataset, clean_dataset):
    
    print_section("3. CLEANING")
    removed = raw_dataset.shape[0] - clean_dataset.shape[0]
    print(f"Records before : {raw_dataset.shape[0]}")
    print(f"Records after  : {clean_dataset.shape[0]}")
    print(f"Records removed: {removed}")
    print(
        "Departments after normalization: "
        f"{clean_dataset['department'].nunique()}"
    )
    representativeness = clean_dataset["temporal_representativeness"]
    print(
        "Representativeness range: "
        f"{representativeness.min():.1f} to {representativeness.max():.1f}"
    )

#Reporta una vista previa de las tres columnas derivadas.
def report_enrichment(enriched_dataset):
    print_section("4. ENRICHMENT")
    preview_columns = [
        "variable", "average_value", "is_pollutant",
        "reliability_level", "who_exceedance_ratio",
    ]
    print("Preview of the derived columns:")
    print(enriched_dataset[preview_columns].head(8).to_string(index=False))

#Calcula, imprime y entrega los tres resúmenes analíticos.
def report_analysis(reliable_pollutants):
    print_section("5. ANALYSIS")

    by_pollutant = logic.summarize_average_by_pollutant(reliable_pollutants)
    print("Mean yearly average by pollutant:")
    print(by_pollutant.round(2).to_string())

    by_department = logic.summarize_pm25_by_department(reliable_pollutants)
    print("\nPM2.5 WHO exceedance ratio by department (top 10):")
    print(by_department.head(10).round(2).to_string())

    by_year = logic.summarize_pm25_trend_by_year(reliable_pollutants)
    print("\nNational mean PM2.5 by year:")
    print(by_year.round(2).to_string())

    return by_pollutant, by_department, by_year

#Genera los tres gráficos e indica dónde se han guardado.
def report_visualizations(by_pollutant, by_department, by_year):
    print_section("6. VISUALIZATIONS")
    pollutant_figure = logic.plot_average_by_pollutant(
        by_pollutant, logic.POLLUTANT_FIGURE_PATH
    )
    department_figure = logic.plot_pm25_by_department(
        by_department, logic.DEPARTMENT_FIGURE_PATH
    )
    trend_figure = logic.plot_pm25_trend_by_year(
        by_year, logic.TREND_FIGURE_PATH
    )
    print("Charts saved to:")
    for figure_path in (pollutant_figure, department_figure, trend_figure):
        print(f"  {figure_path}")

#funcion de orden y carga de graficas
def run_pipeline():
    try:
        raw_dataset = logic.load_raw_dataset(logic.RAW_DATASET_PATH)
    except (FileNotFoundError, ValueError) as loading_error:
        print(f"The analysis could not start: {loading_error}")
        return

    report_structure(raw_dataset)
    report_exploration(raw_dataset)

    clean_dataset = logic.clean_dataset(raw_dataset)
    logic.save_dataset(clean_dataset, logic.CLEAN_DATASET_PATH)
    report_cleaning(raw_dataset, clean_dataset)

    enriched_dataset = logic.enrich_dataset(clean_dataset)
    logic.save_dataset(enriched_dataset, logic.ENRICHED_DATASET_PATH)
    report_enrichment(enriched_dataset)

    reliable_pollutants = logic.select_reliable_pollutant_records(
        enriched_dataset
    )
    by_pollutant, by_department, by_year = report_analysis(reliable_pollutants)
    report_visualizations(by_pollutant, by_department, by_year)

    print_section("DONE")
    print("Generated files are in the outputs folder.")
    print("The original dataset was not modified.")


if __name__ == "__main__":
    run_pipeline()