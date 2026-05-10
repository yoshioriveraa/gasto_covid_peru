# 📊 Análisis del Gasto COVID-19 en Perú (2020–2026)
### ETL + Exploración de Datos con Python y SQL · Portfolio Project

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas)](https://pandas.pydata.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 ¿Qué es este proyecto?

Un pipeline ETL completo + análisis exploratorio (EDA) sobre el gasto público COVID-19 del gobierno peruano, construido con datos reales del **SIAF (MEF)**. El dataset cubre **456,000+ registros** de 7 años (2020–2026), con 63 columnas del sistema presupuestal peruano.

> **Propósito:** Demostrar capacidad de análisis de datos en el contexto del sector público peruano, desde la ingesta de datos hasta hallazgos de negocio accionables.

---

## 📁 Estructura del proyecto

```
gasto-covid-peru/
│
├── etl.py              # Pipeline ETL: carga, limpieza y carga a SQLite
├── analisis.py         # EDA completo con 9 visualizaciones
├── consultas.sql       # 10 consultas SQL analíticas documentadas
├── README.md           # Este archivo
│
├── data/               # CSVs originales del MEF (no incluidos por tamaño)
│   ├── 2020-Gasto-COVID-19.csv
│   ├── 2021-Gasto-COVID-19.csv
│   └── ... (2022–2026)
│
├── outputs/            # Visualizaciones generadas
│   ├── 00_dashboard_resumen.png
│   ├── 01_evolucion_anual_pim_devengado.png
│   ├── 02_nivel_gobierno.png
│   ├── 03_top10_sectores.png
│   ├── 04_gasto_departamento.png
│   ├── 05_eficiencia_sector_heatmap.png
│   ├── 06_mensual_2020.png
│   ├── 07_caida_sectores_clave.png
│   └── 08_composicion_generica.png
│
└── gasto_covid.db      # Base SQLite generada por el ETL
```

---

## 🔧 Instalación y uso

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/gasto-covid-peru
cd gasto-covid-peru

# 2. Instalar dependencias
pip install pandas numpy matplotlib seaborn sqlalchemy

# 3. Colocar los CSVs en la carpeta data/

# 4. Ejecutar el ETL (genera gasto_covid.db)
python etl.py

# 5. Ejecutar el análisis (genera las visualizaciones)
python analisis.py
```

---

## 📊 Hallazgos principales

### 1. Escala del gasto y eficiencia

El gasto COVID-19 del Estado peruano totalizó aproximadamente **S/. 471 millones devengados** entre 2020 y 2026, con una **eficiencia presupuestal global del 91.6%** (devengado / PIM). Esto supera el promedio histórico del sector público peruano (~85%), lo que refleja la urgencia y prioridad política dada al gasto pandémico.

| Año  | PIM (M soles) | Devengado (M soles) | Eficiencia |
|------|:-------------:|:-------------------:|:----------:|
| 2020 | 238.5         | 221.2               | 92.7%      |
| 2021 | 204.8         | 187.4               | 91.5%      |
| 2022 | 60.2          | 53.0                | 88.0%      |
| 2023 | 8.6           | 7.7                 | 89.8%      |
| 2024 | 0.76          | 0.69                | 91.3%      |
| 2025 | 0.60          | 0.59                | 98.8%      |
| 2026 | 0.22          | 0.07                | 32.3%*     |

*\* 2026 con ejecución en curso al momento del corte de datos.*

---

### 2. Concentración en el Gobierno Nacional

El **80.3% del gasto** fue ejecutado por el Gobierno Nacional, con solo 12.9% Regional y 6.8% Local. Este patrón refleja una decisión de diseño: los bonos COVID (Bono Familiar Universal, Bono 380, Bono Independiente, Reactiva Perú) se gestionaron centralizadamente desde el MEF y el MIDIS.

> **Implicancia:** La descentralización fiscal peruana no se activó durante la crisis. Ante shocks sistémicos, el modelo operacional retorna al centro.

---

### 3. Los tres sectores que absorbieron el gasto

- **Desarrollo e Inclusión Social (MIDIS): S/. 151.6M (32.2%)** → Bonos a hogares vulnerables
- **Salud: S/. 88.1M (18.7%)** → Equipamiento UCI, insumos, personal de respuesta
- **Trabajo y Promoción del Empleo: S/. 87.0M (18.5%)** → Subsidio a trabajadores en suspensión perfecta

Estos tres sectores explican el **69.4% del gasto total COVID** — la respuesta peruana priorizó transferencias directas sobre infraestructura.

---

### 4. Estacionalidad y respuesta en 2020

El mes de mayor gasto en 2020 fue **octubre (S/. 52.1M)**, seguido de diciembre (S/. 39.8M). El inicio fue lento: en marzo (primer mes de emergencia) solo se ejecutaron S/. 8.8M. La respuesta más fuerte llegó con 4–7 meses de rezago respecto a la declaración de emergencia (marzo 2020), patrón típico del ciclo presupuestal peruano.

---

### 5. Concentración geográfica

**Lima concentra el 81% del gasto total (S/. 383M)**, seguida de La Libertad (S/. 6.6M) y Piura (S/. 6.5M). Este dato requiere contexto: Lima tiene el mayor número de beneficiarios absolutos, pero en términos per cápita el patrón podría ser diferente.

---

## 🗄️ Notas técnicas del dataset SIAF

| Campo     | Descripción técnica |
|-----------|---------------------|
| `MES_EJE = 0` | Registro del PIM/PIA anual sin desglose mensual. Se usa para calcular el presupuesto asignado. |
| `MES_EJE 1–12` | Ejecución mensual real (devengado, comprometido, girado). |
| Montos    | En el CSV original están en **céntimos de sol**. El ETL divide entre 100. |
| `NIVEL_GOBIERNO` | E = Nacional, R = Regional, M = Municipal (Local) |
| `MONTO_DEVENGADO` | La fase más relevante: representa la obligación de pago reconocida por el Estado. |

---

## 📈 Visualizaciones incluidas

| # | Visualización | Insight clave |
|---|---------------|---------------|
| 00 | Dashboard ejecutivo | Vista rápida de KPIs principales |
| 01 | PIM vs. Devengado por año | Evolución y eficiencia 2020–2026 |
| 02 | Por nivel de gobierno | Alta centralización en Gobierno Nacional |
| 03 | Top 10 sectores | MIDIS, Salud y Trabajo dominan el gasto |
| 04 | Por departamento | Lima vs. resto del país |
| 05 | Heatmap eficiencia | Sectores con bajo rendimiento identificados |
| 06 | Mensual 2020 | Respuesta fiscal a la pandemia mes a mes |
| 07 | Caída por sectores | Retiro progresivo del gasto post-pandemia |
| 08 | Por genérica | Las transferencias dominaron el gasto COVID |

---

## 🛠️ Stack tecnológico

| Herramienta | Uso |
|-------------|-----|
| **Python 3.10+** | Lenguaje principal |
| **pandas** | Manipulación y análisis de datos |
| **NumPy** | Cálculos numéricos y vectorizados |
| **Matplotlib + Seaborn** | Visualizaciones estáticas |
| **SQLite + sqlite3** | Almacenamiento y consultas SQL |
| **SQLAlchemy** | ORM para interacción con la DB |

---

## 📂 Fuente de datos

- **Portal de Transparencia Económica – MEF Perú**
- **Consulta Amigable del SIAF** (Sistema Integrado de Administración Financiera)
- Acceso: [https://apps5.mineco.gob.pe/transparencia/mensual/](https://apps5.mineco.gob.pe/transparencia/mensual/)
- Los datos son de uso público, publicados por el Ministerio de Economía y Finanzas del Perú.

---

## 👤 Autor

**Yoss Rivera**
Analista de Datos 
[LinkedIn](https://linkedin.com/in/yoshioriveraa) · [GitHub](https://github.com/yoshioriveraa)

---

*Este proyecto forma parte de mi portfolio de análisis de datos. Si trabajas en el sector público peruano o en temas de transparencia fiscal y quieres conversar, escríbeme.*
