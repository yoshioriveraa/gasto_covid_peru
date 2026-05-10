"""
etl.py — Pipeline ETL para Gasto COVID-19 Perú 2020–2026
=========================================================
Carga los 7 CSVs anuales del MEF, aplica limpieza y normalización,
y consolida todo en una base de datos SQLite lista para análisis.

Autor: Portfolio Project — Análisis Gasto COVID-19
Fuente de datos: Consulta Amigable SIAF / Portal de Transparencia MEF
"""

import os
import logging
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ─── Configuración ────────────────────────────────────────────────────────────
DATA_DIR   = Path("/mnt/user-data/uploads")
OUTPUT_DIR = Path("/home/claude")
DB_PATH    = OUTPUT_DIR / "gasto_covid.db"
LOG_PATH   = OUTPUT_DIR / "etl_log.txt"

ARCHIVOS_ANUALES = {
    año: DATA_DIR / f"{año}-Gasto-COVID-19.csv"
    for año in range(2020, 2027)
}

# Columnas monetarias que deben dividirse entre 100 (céntimos → soles)
COLS_MONETARIAS = [
    "MONTO_PIA", "MONTO_PIM", "MONTO_CERTIFICADO",
    "MONTO_COMPROMETIDO_ANUAL", "MONTO_COMPROMETIDO",
    "MONTO_DEVENGADO", "MONTO_GIRADO"
]

# Columnas clave para validaciones
COLS_REQUERIDAS = ["ANO_EJE", "MES_EJE", "NIVEL_GOBIERNO", "SECTOR_NOMBRE",
                   "MONTO_DEVENGADO", "MONTO_PIM"]

# ─── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ─── Funciones de limpieza ────────────────────────────────────────────────────

def cargar_csv(año: int, path: Path) -> pd.DataFrame:
    """Lee el CSV con encoding latin1 (estándar SIAF) y agrega columna de año."""
    log.info(f"Cargando {path.name} ...")
    try:
        df = pd.read_csv(path, encoding="latin1", low_memory=False)
        log.info(f"  → {len(df):,} filas, {df.shape[1]} columnas")
        return df
    except Exception as e:
        log.error(f"  ✗ Error leyendo {path.name}: {e}")
        raise


def validar_columnas(df: pd.DataFrame, año: int) -> None:
    """Verifica que existan las columnas críticas."""
    faltantes = [c for c in COLS_REQUERIDAS if c not in df.columns]
    if faltantes:
        log.warning(f"  ⚠ Año {año}: columnas faltantes → {faltantes}")
    else:
        log.info(f"  ✓ Año {año}: todas las columnas requeridas presentes")


def limpiar_tipos(df: pd.DataFrame, año: int) -> pd.DataFrame:
    """
    Normaliza tipos de datos:
    - Columnas monetarias: int → float, dividir entre 100
    - Columnas texto: strip de espacios
    - MES_EJE y ANO_EJE: int
    """
    errores = []

    # Columnas monetarias
    for col in COLS_MONETARIAS:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce") / 100.0
                nulos = df[col].isna().sum()
                if nulos > 0:
                    errores.append(f"{col}: {nulos} valores no numéricos convertidos a NaN")
                    df[col] = df[col].fillna(0.0)
            except Exception as e:
                errores.append(f"Error en {col}: {e}")

    # Tipos enteros clave
    for col in ["ANO_EJE", "MES_EJE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Limpiar strings: strip y title-case para columnas de nombre
    cols_texto = [c for c in df.columns if c.endswith("_NOMBRE")]
    for col in cols_texto:
        df[col] = df[col].astype(str).str.strip()

    if errores:
        for e in errores:
            log.warning(f"  ⚠ Año {año} — {e}")
    else:
        log.info(f"  ✓ Año {año}: tipos OK, montos convertidos a soles")

    return df


def validar_integridad(df: pd.DataFrame, año: int) -> pd.DataFrame:
    """
    Validaciones de negocio:
    - DEVENGADO no puede superar PIM (alerta, no elimina)
    - MES_EJE debe estar entre 1 y 12
    - NIVEL_GOBIERNO debe ser E, R o M
    Retorna el df limpio con filas inválidas eliminadas donde corresponde.
    """
    n_orig = len(df)

    # Meses inválidos
    mask_mes = df["MES_EJE"].between(1, 12) | df["MES_EJE"].isna()
    n_mes_invalid = (~mask_mes).sum()
    if n_mes_invalid > 0:
        log.warning(f"  ⚠ Año {año}: {n_mes_invalid} filas con MES_EJE fuera de rango [1-12] — eliminadas")
        df = df[mask_mes]

    # Nivel de gobierno
    niveles_validos = {"E", "R", "M"}
    mask_nivel = df["NIVEL_GOBIERNO"].isin(niveles_validos)
    n_nivel_invalid = (~mask_nivel).sum()
    if n_nivel_invalid > 0:
        log.warning(f"  ⚠ Año {año}: {n_nivel_invalid} filas con NIVEL_GOBIERNO inválido — eliminadas")
        df = df[mask_nivel]

    # Alerta: devengado > PIM (anomalía presupuestal, no eliminar)
    if "MONTO_DEVENGADO" in df.columns and "MONTO_PIM" in df.columns:
        mask_anomalia = (df["MONTO_DEVENGADO"] > df["MONTO_PIM"]) & (df["MONTO_PIM"] > 0)
        n_anomalia = mask_anomalia.sum()
        if n_anomalia > 0:
            log.warning(
                f"  ⚠ Año {año}: {n_anomalia} filas con DEVENGADO > PIM "
                f"(S/. {df.loc[mask_anomalia,'MONTO_DEVENGADO'].sum():,.0f} en cuestión) — conservadas con flag"
            )
            df["FLAG_DEVENGADO_EXCEDE_PIM"] = mask_anomalia.astype(int)
        else:
            df["FLAG_DEVENGADO_EXCEDE_PIM"] = 0

    n_final = len(df)
    log.info(f"  ✓ Año {año}: {n_orig - n_final} filas eliminadas en validación ({n_final:,} filas finales)")
    return df


def agregar_campos_calculados(df: pd.DataFrame) -> pd.DataFrame:
    """Añade columnas de utilidad analítica."""
    # Ratio de eficiencia presupuestal
    df["RATIO_EFICIENCIA"] = np.where(
        df["MONTO_PIM"] > 0,
        (df["MONTO_DEVENGADO"] / df["MONTO_PIM"]).round(4),
        np.nan
    )

    # Fecha de referencia (primer día del mes de ejecución)
    df["FECHA_EJE"] = pd.to_datetime(
        df["ANO_EJE"].astype(str) + "-" + df["MES_EJE"].astype(str).str.zfill(2) + "-01",
        errors="coerce"
    )

    # Brecha presupuestal: PIM - DEVENGADO (cuánto quedó sin ejecutar)
    df["MONTO_BRECHA"] = (df["MONTO_PIM"] - df["MONTO_DEVENGADO"]).round(2)

    return df


# ─── Pipeline principal ───────────────────────────────────────────────────────

def ejecutar_etl() -> pd.DataFrame:
    log.info("=" * 60)
    log.info("INICIO ETL — Gasto COVID-19 Perú 2020–2026")
    log.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    frames = []
    resumen = []

    for año, path in ARCHIVOS_ANUALES.items():
        if not path.exists():
            log.warning(f"Archivo no encontrado: {path} — skipping")
            continue

        log.info(f"\n── Procesando año {año} ──")

        df = cargar_csv(año, path)
        validar_columnas(df, año)
        df = limpiar_tipos(df, año)
        df = validar_integridad(df, año)
        df = agregar_campos_calculados(df)

        resumen.append({
            "año": año,
            "filas": len(df),
            "devengado_total_soles": df["MONTO_DEVENGADO"].sum(),
            "pim_total_soles": df["MONTO_PIM"].sum(),
        })
        frames.append(df)

    log.info("\n" + "=" * 60)
    df_total = pd.concat(frames, ignore_index=True)
    log.info(f"CONSOLIDADO: {len(df_total):,} filas totales")

    # Resumen ejecutivo
    log.info("\n── Resumen por año ──")
    for r in resumen:
        ef = r['devengado_total_soles'] / r['pim_total_soles'] if r['pim_total_soles'] > 0 else 0
        log.info(
            f"  {r['año']}: {r['filas']:>7,} filas | "
            f"PIM S/. {r['pim_total_soles']/1e9:.2f}B | "
            f"Devengado S/. {r['devengado_total_soles']/1e9:.2f}B | "
            f"Eficiencia {ef:.1%}"
        )

    return df_total


def guardar_sqlite(df: pd.DataFrame) -> None:
    """Persiste el DataFrame consolidado en SQLite con índices optimizados."""
    log.info(f"\nGuardando en SQLite: {DB_PATH}")

    # Convertir FECHA_EJE a string (SQLite no tiene tipo datetime nativo)
    df_save = df.copy()
    if "FECHA_EJE" in df_save.columns:
        df_save["FECHA_EJE"] = df_save["FECHA_EJE"].astype(str)

    conn = sqlite3.connect(DB_PATH)
    df_save.to_sql("gasto_covid", conn, if_exists="replace", index=False, chunksize=10_000)

    # Índices para acelerar consultas frecuentes
    indices = [
        ("idx_año",       "CREATE INDEX IF NOT EXISTS idx_año ON gasto_covid(ANO_EJE)"),
        ("idx_nivel",     "CREATE INDEX IF NOT EXISTS idx_nivel ON gasto_covid(NIVEL_GOBIERNO)"),
        ("idx_sector",    "CREATE INDEX IF NOT EXISTS idx_sector ON gasto_covid(SECTOR_NOMBRE)"),
        ("idx_depto",     "CREATE INDEX IF NOT EXISTS idx_depto ON gasto_covid(DEPARTAMENTO_EJECUTORA_NOMBRE)"),
        ("idx_año_mes",   "CREATE INDEX IF NOT EXISTS idx_año_mes ON gasto_covid(ANO_EJE, MES_EJE)"),
    ]
    for nombre, sql in indices:
        conn.execute(sql)
        log.info(f"  ✓ Índice creado: {nombre}")

    conn.commit()

    # Verificación final
    n = conn.execute("SELECT COUNT(*) FROM gasto_covid").fetchone()[0]
    log.info(f"  ✓ Filas en DB: {n:,}")

    conn.close()
    log.info(f"  ✓ Base de datos guardada en: {DB_PATH}")


# ─── Ejecución ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df_consolidado = ejecutar_etl()
    guardar_sqlite(df_consolidado)
    log.info("\n✅ ETL completado exitosamente.")
    print(f"\nBase de datos disponible en: {DB_PATH}")
    print(f"Log disponible en: {LOG_PATH}")
