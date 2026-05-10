-- ============================================================
-- consultas.sql — Análisis Gasto COVID-19 Perú 2020–2026
-- Base de datos: gasto_covid.db (SQLite)
-- Tabla principal: gasto_covid
-- ============================================================
-- NOTA METODOLÓGICA:
--   ES_ACUMULADO_ANUAL = 1 → registros con MES_EJE=0 (PIM anual sin ejecución mensual)
--   ES_ACUMULADO_ANUAL = 0 → ejecución mensual (devengado, girado, comprometido)
-- ============================================================


-- ─── 1. RESUMEN EJECUTIVO POR AÑO ─────────────────────────────────────────
-- Cuánto se asignó, cuánto se ejecutó y qué tan eficiente fue cada año
SELECT
    ANO_EJE                                               AS año,
    ROUND(SUM(CASE WHEN ES_ACUMULADO_ANUAL=1 THEN MONTO_PIM   ELSE 0 END)/1e6, 2) AS pim_millones,
    ROUND(SUM(CASE WHEN ES_ACUMULADO_ANUAL=0 THEN MONTO_DEVENGADO ELSE 0 END)/1e6, 2) AS devengado_millones,
    ROUND(SUM(CASE WHEN ES_ACUMULADO_ANUAL=0 THEN MONTO_GIRADO    ELSE 0 END)/1e6, 2) AS girado_millones,
    ROUND(
        SUM(CASE WHEN ES_ACUMULADO_ANUAL=0 THEN MONTO_DEVENGADO ELSE 0 END) /
        NULLIF(SUM(CASE WHEN ES_ACUMULADO_ANUAL=1 THEN MONTO_PIM ELSE 0 END), 0) * 100
    , 1) AS eficiencia_pct,
    COUNT(DISTINCT CASE WHEN ES_ACUMULADO_ANUAL=0 THEN SECTOR_NOMBRE END) AS sectores_activos
FROM gasto_covid
GROUP BY ANO_EJE
ORDER BY ANO_EJE;


-- ─── 2. TOP 10 SECTORES CON MAYOR GASTO TOTAL (2020–2026) ──────────────────
-- Revela quiénes lideraron el gasto COVID en todo el período
SELECT
    SECTOR_NOMBRE                                       AS sector,
    ROUND(SUM(MONTO_DEVENGADO)/1e6, 2)                  AS devengado_millones,
    ROUND(SUM(MONTO_DEVENGADO) * 100.0 /
          (SELECT SUM(MONTO_DEVENGADO) FROM gasto_covid WHERE ES_ACUMULADO_ANUAL=0), 1) AS pct_total
FROM gasto_covid
WHERE ES_ACUMULADO_ANUAL = 0
GROUP BY SECTOR_NOMBRE
ORDER BY devengado_millones DESC
LIMIT 10;


-- ─── 3. EFICIENCIA PRESUPUESTAL POR SECTOR Y AÑO ──────────────────────────
-- Detecta sectores con presupuesto asignado pero ejecución baja (ineficiencia)
SELECT
    p.ANO_EJE                                           AS año,
    p.SECTOR_NOMBRE                                     AS sector,
    ROUND(p.pim / 1e6, 2)                               AS pim_millones,
    ROUND(e.devengado / 1e6, 2)                         AS devengado_millones,
    ROUND(e.devengado * 100.0 / NULLIF(p.pim, 0), 1)   AS eficiencia_pct,
    ROUND((p.pim - e.devengado) / 1e6, 2)               AS brecha_millones
FROM (
    SELECT ANO_EJE, SECTOR_NOMBRE, SUM(MONTO_PIM) AS pim
    FROM gasto_covid WHERE ES_ACUMULADO_ANUAL = 1
    GROUP BY ANO_EJE, SECTOR_NOMBRE
) p
LEFT JOIN (
    SELECT ANO_EJE, SECTOR_NOMBRE, SUM(MONTO_DEVENGADO) AS devengado
    FROM gasto_covid WHERE ES_ACUMULADO_ANUAL = 0
    GROUP BY ANO_EJE, SECTOR_NOMBRE
) e USING (ANO_EJE, SECTOR_NOMBRE)
WHERE p.pim > 1000000
ORDER BY año, eficiencia_pct ASC;


-- ─── 4. DISTRIBUCIÓN POR NIVEL DE GOBIERNO Y AÑO ──────────────────────────
-- Evalúa la centralización del gasto COVID
SELECT
    ANO_EJE                                             AS año,
    NIVEL_GOBIERNO_NOMBRE                               AS nivel_gobierno,
    ROUND(SUM(MONTO_DEVENGADO)/1e6, 2)                  AS devengado_millones,
    ROUND(SUM(MONTO_DEVENGADO) * 100.0 /
        SUM(SUM(MONTO_DEVENGADO)) OVER (PARTITION BY ANO_EJE), 1) AS pct_año
FROM gasto_covid
WHERE ES_ACUMULADO_ANUAL = 0
GROUP BY ANO_EJE, NIVEL_GOBIERNO_NOMBRE
ORDER BY ANO_EJE, devengado_millones DESC;


-- ─── 5. EVOLUCIÓN MENSUAL 2020 (AÑO PICO COVID) ───────────────────────────
-- Muestra cómo el gasto reaccionó mes a mes ante la pandemia
SELECT
    MES_EJE                                             AS mes,
    CASE MES_EJE
        WHEN 1 THEN 'Enero'   WHEN 2  THEN 'Febrero' WHEN 3  THEN 'Marzo'
        WHEN 4 THEN 'Abril'   WHEN 5  THEN 'Mayo'    WHEN 6  THEN 'Junio'
        WHEN 7 THEN 'Julio'   WHEN 8  THEN 'Agosto'  WHEN 9  THEN 'Setiembre'
        WHEN 10 THEN 'Octubre' WHEN 11 THEN 'Noviembre' WHEN 12 THEN 'Diciembre'
    END                                                 AS mes_nombre,
    ROUND(SUM(MONTO_DEVENGADO)/1e6, 2)                  AS devengado_millones,
    ROUND(SUM(SUM(MONTO_DEVENGADO)) OVER (ORDER BY MES_EJE)/1e6, 2) AS acumulado_millones
FROM gasto_covid
WHERE ANO_EJE = 2020 AND ES_ACUMULADO_ANUAL = 0
GROUP BY MES_EJE
ORDER BY MES_EJE;


-- ─── 6. RANKING DE DEPARTAMENTOS POR GASTO TOTAL ──────────────────────────
-- Muestra la concentración geográfica del gasto COVID
SELECT
    DEPARTAMENTO_EJECUTORA_NOMBRE                       AS departamento,
    ROUND(SUM(MONTO_DEVENGADO)/1e6, 3)                  AS devengado_millones,
    ROUND(SUM(MONTO_DEVENGADO) * 100.0 /
          (SELECT SUM(MONTO_DEVENGADO) FROM gasto_covid WHERE ES_ACUMULADO_ANUAL=0), 2) AS pct_total,
    COUNT(DISTINCT SECTOR_NOMBRE)                       AS sectores_ejecutores
FROM gasto_covid
WHERE ES_ACUMULADO_ANUAL = 0
  AND DEPARTAMENTO_EJECUTORA_NOMBRE NOT IN ('nan','EXTRANJERO','')
GROUP BY DEPARTAMENTO_EJECUTORA_NOMBRE
ORDER BY devengado_millones DESC;


-- ─── 7. ANÁLISIS POR FUENTE DE FINANCIAMIENTO ─────────────────────────────
-- Clave para entender si el gasto fue con recursos ordinarios o deuda pública
SELECT
    ANO_EJE                                             AS año,
    FUENTE_FINANCIAMIENTO_NOMBRE                        AS fuente,
    ROUND(SUM(MONTO_DEVENGADO)/1e6, 2)                  AS devengado_millones,
    ROUND(SUM(MONTO_DEVENGADO) * 100.0 /
          SUM(SUM(MONTO_DEVENGADO)) OVER (PARTITION BY ANO_EJE), 1) AS pct_año
FROM gasto_covid
WHERE ES_ACUMULADO_ANUAL = 0
GROUP BY ANO_EJE, FUENTE_FINANCIAMIENTO_NOMBRE
ORDER BY año, devengado_millones DESC;


-- ─── 8. COMPOSICIÓN DEL GASTO POR GENÉRICA ────────────────────────────────
-- Revela SI el gasto fue en transferencias, personal, bienes o inversión
SELECT
    ANO_EJE                                             AS año,
    GENERICA_NOMBRE                                     AS tipo_gasto,
    ROUND(SUM(MONTO_DEVENGADO)/1e6, 2)                  AS devengado_millones,
    ROUND(SUM(MONTO_DEVENGADO) * 100.0 /
          SUM(SUM(MONTO_DEVENGADO)) OVER (PARTITION BY ANO_EJE), 1) AS pct_año
FROM gasto_covid
WHERE ES_ACUMULADO_ANUAL = 0
GROUP BY ANO_EJE, GENERICA_NOMBRE
ORDER BY año, devengado_millones DESC;


-- ─── 9. SECTORES CON MAYOR BRECHA (PIM NO EJECUTADO) ──────────────────────
-- Presupuesto inmovilizado: recursos asignados que no llegaron a la población
SELECT
    SECTOR_NOMBRE                                       AS sector,
    ROUND(SUM(CASE WHEN ES_ACUMULADO_ANUAL=1 THEN MONTO_PIM ELSE 0 END)/1e6, 2) AS pim_total_millones,
    ROUND(SUM(CASE WHEN ES_ACUMULADO_ANUAL=0 THEN MONTO_DEVENGADO ELSE 0 END)/1e6, 2) AS devengado_millones,
    ROUND(
        (SUM(CASE WHEN ES_ACUMULADO_ANUAL=1 THEN MONTO_PIM ELSE 0 END) -
         SUM(CASE WHEN ES_ACUMULADO_ANUAL=0 THEN MONTO_DEVENGADO ELSE 0 END)) / 1e6
    , 2) AS brecha_millones
FROM gasto_covid
GROUP BY SECTOR_NOMBRE
HAVING pim_total_millones > 1
ORDER BY brecha_millones DESC
LIMIT 15;


-- ─── 10. PROGRAMAS PRESUPUESTALES COVID MÁS RELEVANTES ───────────────────
-- Los programas que canalizaron más recursos (nivel operativo del gasto)
SELECT
    PROGRAMA_PPTO_NOMBRE                                AS programa,
    COUNT(DISTINCT ANO_EJE)                             AS años_activo,
    ROUND(SUM(MONTO_DEVENGADO)/1e6, 2)                  AS devengado_millones
FROM gasto_covid
WHERE ES_ACUMULADO_ANUAL = 0
  AND PROGRAMA_PPTO_NOMBRE NOT IN ('nan','0')
GROUP BY PROGRAMA_PPTO_NOMBRE
ORDER BY devengado_millones DESC
LIMIT 15;
