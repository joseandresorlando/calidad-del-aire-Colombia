# Análisis de la Calidad del Aire en Colombia

Trabajo final de **Programación para Ciencia de Datos** — Universidad del Magdalena.
Análisis exploratorio del dataset **Calidad del Aire en Colombia** (datos.gov.co).

> El dataset original nunca se modifica: el programa solo lo lee. Todo lo
> generado se guarda en la carpeta `outputs/`.

## Estructura (dos archivos)

```
.
├── analysis_logic.py   # Lógica: configuración, carga, limpieza, enriquecimiento, análisis y gráficas
├── user_interface.py   # Interfaz: orquesta el flujo e imprime los reportes (punto de entrada)
├── data/
│   └── air_quality_colombia.csv   # ORIGINAL — solo lectura
└── outputs/                       # Se crea al ejecutar
    ├── air_quality_clean.csv
    ├── air_quality_enriched.csv
    ├── average_by_pollutant.png
    ├── pm25_by_department.png
    └── pm25_trend_by_year.png
```

La separación entre lógica e interfaz sigue la metodología del curso
(`business_logic.py` / `user_interface.py`).

## Cómo ejecutar

```bash
pip install pandas numpy matplotlib
python user_interface.py
```

## Flujo

1. Carga del original (solo lectura), con manejo de excepciones.
2. Exploración: ausencias y variedad de las categóricas.
3. Limpieza (sobre una copia) de cuatro problemas: separador de miles,
   categóricas inconsistentes, valores imposibles y filas sin campos clave.
4. Enriquecimiento con `is_pollutant`, `reliability_level`, `who_exceedance_ratio`.
5. Análisis por contaminante, por departamento y por año.
6. Tres gráficas guardadas en `outputs/`.
