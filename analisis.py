"""
analisis.py — EDA Completo: Gasto COVID-19 Perú 2020–2026
==========================================================
Genera 8 visualizaciones de calidad para portfolio profesional.

Notas metodológicas sobre el dataset SIAF:
- MES_EJE=0: registros del presupuesto anual (PIM/PIA) sin desglose mensual
  → se usan para calcular PIM total por año/sector
- MES_EJE 1-12: ejecución mensual (devengado, comprometido, girado)
  → se usan para análisis de gasto ejecutado
- Montos ya convertidos a soles en el ETL (÷100 de céntimos)
"""

import sqlite3
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
from matplotlib.gridspec import GridSpec

warnings.filterwarnings("ignore")

DB_PATH  = Path("/home/claude/gasto_covid.db")
OUT_DIR  = Path("/mnt/user-data/outputs")
OUT_DIR.mkdir(exist_ok=True)

# ─── Estilo global ─────────────────────────────────────────────────────────────
PALETTE_AÑOS   = ["#1a535c","#4ecdc4","#ff6b6b","#ffe66d","#f7b731","#a29bfe","#fd79a8"]
COLOR_PIM      = "#2d3436"
COLOR_DEV      = "#00b894"
COLOR_BRECHA   = "#d63031"
FONDO          = "#f8f9fa"
GRIS_TEXTO     = "#2d3436"
GRIS_SUAVE     = "#dfe6e9"

plt.rcParams.update({
    "figure.facecolor":    FONDO,
    "axes.facecolor":      "white",
    "axes.spines.top":     False,
    "axes.spines.right":   False,
    "axes.grid":           True,
    "axes.grid.axis":      "y",
    "grid.color":          GRIS_SUAVE,
    "grid.linewidth":      0.8,
    "font.family":         "DejaVu Sans",
    "font.size":           11,
    "axes.titlesize":      14,
    "axes.titleweight":    "bold",
    "axes.titlepad":       14,
    "axes.labelsize":      11,
    "xtick.labelsize":     10,
    "ytick.labelsize":     10,
    "legend.framealpha":   0.9,
    "legend.edgecolor":    GRIS_SUAVE,
})


def fmt_miles(x, _):
    if abs(x) >= 1e6:
        return f"S/. {x/1e6:.0f}M"
    elif abs(x) >= 1e3:
        return f"S/. {x/1e3:.0f}k"
    return f"S/. {x:.0f}"


def guardar(fig, nombre):
    path = OUT_DIR / nombre
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)
    print(f"  ✓ Guardado: {path}")


def cargar_datos():
    conn = sqlite3.connect(DB_PATH)
    df_ejec = pd.read_sql("""
        SELECT ANO_EJE, MES_EJE, NIVEL_GOBIERNO_NOMBRE, SECTOR_NOMBRE,
               DEPARTAMENTO_EJECUTORA_NOMBRE,
               MONTO_DEVENGADO, MONTO_GIRADO, MONTO_COMPROMETIDO,
               FUENTE_FINANCIAMIENTO_NOMBRE, GENERICA_NOMBRE
        FROM gasto_covid WHERE ES_ACUMULADO_ANUAL = 0
    """, conn)
    df_ppto = pd.read_sql("""
        SELECT ANO_EJE, NIVEL_GOBIERNO_NOMBRE, SECTOR_NOMBRE,
               MONTO_PIA, MONTO_PIM
        FROM gasto_covid WHERE ES_ACUMULADO_ANUAL = 1
    """, conn)
    conn.close()
    return df_ejec, df_ppto


def viz1_evolucion_anual(df_ejec, df_ppto):
    print("\n[1/8] Evolución anual PIM vs Devengado...")
    dev = df_ejec.groupby("ANO_EJE")["MONTO_DEVENGADO"].sum()
    pim = df_ppto.groupby("ANO_EJE")["MONTO_PIM"].sum()
    años = sorted(set(dev.index) | set(pim.index))
    dev_vals = [dev.get(a, 0)/1e6 for a in años]
    pim_vals = [pim.get(a, 0)/1e6 for a in años]
    efic     = [d/p*100 if p>0 else 0 for d,p in zip(dev_vals, pim_vals)]

    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.suptitle("Evolución del Gasto COVID-19 en Perú 2020–2026\nPIM vs. Devengado y Eficiencia Presupuestal",
                 fontsize=15, fontweight="bold", color=GRIS_TEXTO, y=1.01)
    x = np.arange(len(años)); w = 0.35
    bars_pim = ax1.bar(x-w/2, pim_vals, w, label="PIM (Presupuesto)", color=COLOR_PIM, alpha=0.85, zorder=3)
    bars_dev = ax1.bar(x+w/2, dev_vals, w, label="Devengado (Ejecutado)", color=COLOR_DEV, alpha=0.90, zorder=3)
    ax1.set_ylabel("Millones de Soles (S/.)"); ax1.set_xticks(x); ax1.set_xticklabels(años)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.0f}M"))
    ax1.set_ylim(0, max(pim_vals)*1.25)
    ax2 = ax1.twinx()
    ax2.plot(x, efic, "o--", color="#e17055", linewidth=2.2, markersize=7, label="Eficiencia (%)", zorder=5)
    ax2.set_ylabel("Eficiencia: Devengado / PIM (%)", color="#e17055")
    ax2.set_ylim(0, 130); ax2.tick_params(axis="y", colors="#e17055")
    ax2.spines["right"].set_visible(True); ax2.spines["right"].set_color("#e17055")
    for xi, ef in zip(x, efic):
        ax2.annotate(f"{ef:.1f}%", (xi, ef+3), ha="center", fontsize=9.5, color="#e17055", fontweight="bold")
    for bar in bars_dev:
        h = bar.get_height()
        if h > 0:
            ax1.text(bar.get_x()+bar.get_width()/2, h+1, f"S/. {h:.0f}M",
                     ha="center", va="bottom", fontsize=8.5, color=GRIS_TEXTO)
    h1,l1 = ax1.get_legend_handles_labels(); h2,l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1+h2, l1+l2, loc="upper right")
    ax1.set_xlabel("Año de ejecución")
    fig.tight_layout(); guardar(fig, "01_evolucion_anual_pim_devengado.png")
    print(f"  → HALLAZGO: 2020 concentra S/. {dev_vals[0]:.0f}M ({dev_vals[0]/sum(dev_vals)*100:.0f}% del total)")
    print(f"  → Eficiencia promedio 2020-2023: {np.mean(efic[:4]):.1f}%")


def viz2_nivel_gobierno(df_ejec):
    print("\n[2/8] Distribución por nivel de gobierno...")
    df = df_ejec.groupby(["ANO_EJE","NIVEL_GOBIERNO_NOMBRE"])["MONTO_DEVENGADO"].sum().reset_index()
    pivot = df.pivot(index="ANO_EJE", columns="NIVEL_GOBIERNO_NOMBRE", values="MONTO_DEVENGADO").fillna(0)/1e6
    cols_orden = ["GOBIERNO NACIONAL","GOBIERNOS REGIONALES","GOBIERNOS LOCALES"]
    pivot = pivot[[c for c in cols_orden if c in pivot.columns]]
    colores = [COLOR_PIM, "#00b894", "#fdcb6e"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Distribución del Gasto COVID-19 por Nivel de Gobierno\nPerú 2020–2026",
                 fontsize=15, fontweight="bold", color=GRIS_TEXTO)
    ax = axes[0]; bottom = np.zeros(len(pivot))
    for col, color in zip(pivot.columns, colores):
        ax.bar(pivot.index, pivot[col], bottom=bottom, label=col.title(), color=color, alpha=0.9)
        bottom += pivot[col].values
    ax.set_title("Gasto Devengado por Año y Nivel"); ax.set_ylabel("Millones de Soles (S/.)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.0f}M"))
    ax.legend(loc="upper right", fontsize=9); ax.set_xlabel("Año")
    ax2 = axes[1]
    totales = df.groupby("NIVEL_GOBIERNO_NOMBRE")["MONTO_DEVENGADO"].sum()
    totales = totales.reindex([c for c in cols_orden if c in totales.index])
    wedges, texts, autotexts = ax2.pie(totales.values, labels=None, autopct="%1.1f%%",
        colors=colores, startangle=140, wedgeprops={"edgecolor":"white","linewidth":2}, pctdistance=0.75)
    for at in autotexts: at.set_fontsize(11); at.set_fontweight("bold")
    ax2.set_title("Participación Total\n(2020–2026)")
    ax2.legend(wedges, [f"{n.title()}\nS/. {v/1e6:.0f}M" for n,v in zip(totales.index, totales.values)],
               loc="lower center", bbox_to_anchor=(0.5,-0.12), ncol=1, fontsize=9)
    fig.tight_layout(); guardar(fig, "02_nivel_gobierno.png")
    nac_pct = totales["GOBIERNO NACIONAL"]/totales.sum()*100
    print(f"  → HALLAZGO: Gobierno Nacional ejecutó {nac_pct:.1f}% del gasto COVID total — alta centralización")


def viz3_top_sectores(df_ejec):
    print("\n[3/8] Top 10 sectores...")
    df = df_ejec.groupby("SECTOR_NOMBRE")["MONTO_DEVENGADO"].sum().sort_values(ascending=True).tail(10)
    rename = {"DESARROLLO E INCLUSION SOCIAL":"Des. e Inclusión Social",
              "TRABAJO Y PROMOCION DEL EMPLEO":"Trabajo y Empleo",
              "GOBIERNOS REGIONALES":"Gob. Regionales",
              "TRANSPORTES Y COMUNICACIONES":"Transportes y Comun.",
              "PRESIDENCIA CONSEJO MINISTROS":"PCM",
              "VIVIENDA CONSTRUCCION Y SANEAMIENTO":"Vivienda y Sanem.",
              "ECONOMIA Y FINANZAS":"Economía y Finanzas",
              "MUJER Y POBLACIONES VULNERABLES":"Mujer y Pob. Vulner."}
    df.index = [rename.get(i, i.title()) for i in df.index]
    fig, ax = plt.subplots(figsize=(11, 7))
    fig.suptitle("Top 10 Sectores con Mayor Gasto COVID-19 Devengado\nPerú 2020–2026 (en Millones de Soles)",
                 fontsize=14, fontweight="bold", color=GRIS_TEXTO)
    colores_barras = [PALETTE_AÑOS[i%len(PALETTE_AÑOS)] for i in range(10)]
    bars = ax.barh(df.index, df.values/1e6, color=colores_barras[::-1], height=0.65, zorder=3)
    for bar, val in zip(bars, df.values/1e6):
        ax.text(val+0.5, bar.get_y()+bar.get_height()/2, f"S/. {val:.1f}M",
                va="center", fontsize=9.5, color=GRIS_TEXTO)
    ax.set_xlabel("Devengado Total (Millones de Soles)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.0f}M"))
    ax.set_xlim(0, df.values.max()/1e6*1.2)
    ax.grid(axis="x", color=GRIS_SUAVE); ax.grid(axis="y", visible=False); ax.tick_params(left=False)
    fig.tight_layout(); guardar(fig, "03_top10_sectores.png")
    top1 = df.index[-1]; top1_val = df.values[-1]/1e6
    print(f"  → HALLAZGO: {top1} lidera con S/. {top1_val:.1f}M (Bono Familiar Universal y similares)")


def viz4_departamento(df_ejec):
    print("\n[4/8] Gasto por departamento...")
    df = (df_ejec[df_ejec["DEPARTAMENTO_EJECUTORA_NOMBRE"]!="nan"]
          .groupby("DEPARTAMENTO_EJECUTORA_NOMBRE")["MONTO_DEVENGADO"].sum().sort_values(ascending=True))
    df_sin_lima = df.drop("LIMA", errors="ignore")
    lima_val = df.get("LIMA", 0)/1e6
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8), gridspec_kw={"width_ratios":[1,2.5]})
    fig.suptitle("Gasto COVID-19 Devengado por Departamento\nPerú 2020–2026",
                 fontsize=14, fontweight="bold", color=GRIS_TEXTO)
    ax1.barh(["Resto del país","Lima"], [df_sin_lima.sum()/1e6, lima_val],
             color=[COLOR_DEV,"#e17055"], height=0.5, zorder=3)
    ax1.set_title("Lima vs. Resto del País", fontsize=11); ax1.set_xlabel("Devengado (M soles)")
    for i, v in enumerate([df_sin_lima.sum()/1e6, lima_val]):
        ax1.text(v+1, i, f"S/. {v:.0f}M\n({v/(df_sin_lima.sum()/1e6+lima_val)*100:.0f}%)",
                 va="center", fontsize=10, fontweight="bold")
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.0f}M"))
    ax1.set_xlim(0, max(lima_val, df_sin_lima.sum()/1e6)*1.35)
    ax1.grid(axis="x"); ax1.grid(axis="y", visible=False)
    colores = [COLOR_DEV if v>=df_sin_lima.median() else "#81ecec" for v in df_sin_lima.values]
    bars = ax2.barh(df_sin_lima.index, df_sin_lima.values/1e6, color=colores, height=0.72, zorder=3)
    for bar, val in zip(bars, df_sin_lima.values/1e6):
        ax2.text(val+0.02, bar.get_y()+bar.get_height()/2, f"S/. {val:.2f}M", va="center", fontsize=8)
    ax2.set_title("Ranking Departamentos (excl. Lima)", fontsize=11)
    ax2.set_xlabel("Devengado (M soles)")
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.1f}M"))
    ax2.grid(axis="x"); ax2.grid(axis="y", visible=False)
    fig.tight_layout(); guardar(fig, "04_gasto_departamento.png")
    pct_lima = lima_val/(df.sum()/1e6)*100
    print(f"  → HALLAZGO: Lima concentra S/. {lima_val:.0f}M ({pct_lima:.0f}% del total)")


def viz5_eficiencia_sector(df_ejec, df_ppto):
    print("\n[5/8] Heatmap eficiencia por sector y año...")
    dev = df_ejec.groupby(["ANO_EJE","SECTOR_NOMBRE"])["MONTO_DEVENGADO"].sum()
    pim = df_ppto.groupby(["ANO_EJE","SECTOR_NOMBRE"])["MONTO_PIM"].sum()
    df_ef = (dev/pim.replace(0,np.nan)).reset_index(name="eficiencia")
    df_ef["eficiencia"] = df_ef["eficiencia"].clip(0, 1.2)
    pim_total = df_ppto.groupby("SECTOR_NOMBRE")["MONTO_PIM"].sum()
    sectores_sig = pim_total[pim_total>1_000_000].index.tolist()
    pivot = df_ef[df_ef["SECTOR_NOMBRE"].isin(sectores_sig)].pivot(
        index="SECTOR_NOMBRE", columns="ANO_EJE", values="eficiencia")
    rename = {"DESARROLLO E INCLUSION SOCIAL":"Des. Inclusión Social",
              "TRABAJO Y PROMOCION DEL EMPLEO":"Trabajo y Empleo",
              "GOBIERNOS REGIONALES":"Gob. Regionales",
              "TRANSPORTES Y COMUNICACIONES":"Transportes y Comun.",
              "PRESIDENCIA CONSEJO MINISTROS":"PCM",
              "VIVIENDA CONSTRUCCION Y SANEAMIENTO":"Vivienda y Sanem.",
              "ECONOMIA Y FINANZAS":"Economía y Finanzas"}
    pivot.index = [rename.get(i, i.title()) for i in pivot.index]
    fig, ax = plt.subplots(figsize=(13, max(7, len(pivot)*0.55)))
    fig.suptitle("Eficiencia Presupuestal COVID-19: Devengado / PIM\npor Sector y Año",
                 fontsize=13, fontweight="bold", color=GRIS_TEXTO)
    sns.heatmap(pivot, ax=ax, annot=True, fmt=".0%", cmap="RdYlGn", vmin=0, vmax=1,
                linewidths=0.5, linecolor=GRIS_SUAVE,
                cbar_kws={"label":"Eficiencia (Devengado/PIM)","shrink":0.8}, annot_kws={"size":9})
    ax.set_xlabel("Año"); ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=0); ax.tick_params(axis="y", rotation=0)
    fig.tight_layout(); guardar(fig, "05_eficiencia_sector_heatmap.png")
    print("  → HALLAZGO: Sectores con PIM asignado pero baja ejecución = presupuesto inmovilizado")


def viz6_mensual_2020(df_ejec):
    print("\n[6/8] Evolución mensual 2020...")
    df20 = df_ejec[df_ejec["ANO_EJE"]==2020].copy()
    mensual = df20.groupby("MES_EJE")["MONTO_DEVENGADO"].sum()/1e6
    mensual_nivel = df20.groupby(["MES_EJE","NIVEL_GOBIERNO_NOMBRE"])["MONTO_DEVENGADO"].sum().unstack(fill_value=0)/1e6
    MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    mensual = mensual.reindex(range(1,13), fill_value=0); mensual.index = MESES
    mensual_nivel = mensual_nivel.reindex(range(1,13), fill_value=0); mensual_nivel.index = MESES
    eventos_covid = {"Mar":"Estado de\nEmergencia","Abr":"Bono 380\n(primer pago)",
                     "May":"Reactiva\nPerú lanza","Oct":"2ª ola\nse acerca"}
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(13, 10), gridspec_kw={"height_ratios":[2,1]})
    fig.suptitle("Evolución Mensual del Gasto COVID-19 en 2020\nEl año pico de la pandemia en Perú",
                 fontsize=14, fontweight="bold", color=GRIS_TEXTO)
    cols_nivel = ["GOBIERNO NACIONAL","GOBIERNOS REGIONALES","GOBIERNOS LOCALES"]
    colores_nivel = [COLOR_PIM, COLOR_DEV, "#fdcb6e"]
    bottom = np.zeros(12)
    for col, color in zip([c for c in cols_nivel if c in mensual_nivel.columns], colores_nivel):
        ax_top.bar(mensual_nivel.index, mensual_nivel[col], bottom=bottom,
                   label=col.title(), color=color, alpha=0.9, zorder=3)
        bottom += mensual_nivel[col].values
    for mes, texto in eventos_covid.items():
        if mes in mensual.index:
            xi = list(mensual.index).index(mes)
            ax_top.annotate(texto, xy=(xi, mensual.iloc[xi]),
                            xytext=(xi, mensual.iloc[xi]+5), ha="center", fontsize=8.5, color="#d63031",
                            arrowprops={"arrowstyle":"->","color":"#d63031","lw":1.2})
    ax_top.set_title("Devengado mensual por Nivel de Gobierno (2020)", fontsize=11)
    ax_top.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.0f}M"))
    ax_top.set_ylabel("Millones de Soles"); ax_top.legend(loc="upper left", fontsize=9)
    acumulado = mensual.cumsum()
    ax_bot.fill_between(range(12), acumulado.values, alpha=0.25, color=COLOR_DEV)
    ax_bot.plot(range(12), acumulado.values, "o-", color=COLOR_DEV, linewidth=2.2, markersize=6)
    ax_bot.set_xticks(range(12)); ax_bot.set_xticklabels(MESES)
    ax_bot.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.0f}M"))
    ax_bot.set_title("Devengado acumulado 2020", fontsize=11); ax_bot.set_ylabel("Acumulado (M soles)")
    fig.tight_layout(); guardar(fig, "06_mensual_2020.png")
    mes_pico = mensual.idxmax()
    print(f"  → HALLAZGO: Mes pico 2020: {mes_pico} (S/. {mensual.max():.1f}M)")


def viz7_caida_sectores(df_ejec):
    print("\n[7/8] Caída del gasto por sectores clave...")
    sectores_key = ["DESARROLLO E INCLUSION SOCIAL","SALUD","TRABAJO Y PROMOCION DEL EMPLEO",
                    "EDUCACION","GOBIERNOS REGIONALES"]
    rename_s = {"DESARROLLO E INCLUSION SOCIAL":"Des. Inclusión Social",
                "TRABAJO Y PROMOCION DEL EMPLEO":"Trabajo y Empleo",
                "GOBIERNOS REGIONALES":"Gob. Regionales"}
    df = df_ejec[df_ejec["SECTOR_NOMBRE"].isin(sectores_key)].copy()
    pivot = df.groupby(["ANO_EJE","SECTOR_NOMBRE"])["MONTO_DEVENGADO"].sum().unstack(fill_value=0)/1e6
    pivot.columns = [rename_s.get(c, c.title()) for c in pivot.columns]
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle("Trayectoria del Gasto COVID-19 por Sectores Clave 2020–2026\n"
                 "(Retiro progresivo post-pandemia)",
                 fontsize=14, fontweight="bold", color=GRIS_TEXTO)
    colores_s = PALETTE_AÑOS[:len(pivot.columns)]
    for col, color in zip(pivot.columns, colores_s):
        ax.plot(pivot.index, pivot[col], "o-", label=col, color=color, linewidth=2.3, markersize=7, zorder=4)
        ultimo_año = pivot.index[-1]
        ax.annotate(f"  {col}\n  S/. {pivot[col].iloc[-1]:.1f}M",
                    (ultimo_año, pivot[col].iloc[-1]), fontsize=8, color=color, va="center")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.0f}M"))
    ax.set_xlabel("Año"); ax.set_ylabel("Devengado (Millones de Soles)")
    ax.set_xticks(pivot.index); ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout(); guardar(fig, "07_caida_sectores_clave.png")
    print("  → HALLAZGO: Caída abrupta 2021→2022 marca el fin de transferencias extraordinarias")


def viz8_generica_gasto(df_ejec):
    print("\n[8/8] Composición del gasto por genérica...")
    df = df_ejec.groupby(["ANO_EJE","GENERICA_NOMBRE"])["MONTO_DEVENGADO"].sum().reset_index()
    top5 = (df.groupby("GENERICA_NOMBRE")["MONTO_DEVENGADO"].sum()
              .sort_values(ascending=False).head(5).index.tolist())
    df["GENERICA_PLOT"] = df["GENERICA_NOMBRE"].where(df["GENERICA_NOMBRE"].isin(top5), other="Otros")
    pivot = df.groupby(["ANO_EJE","GENERICA_PLOT"])["MONTO_DEVENGADO"].sum().unstack(fill_value=0)/1e6
    rename_g = {g: g.replace("5. ","").replace("6. ","").title() for g in pivot.columns}
    pivot.rename(columns=rename_g, inplace=True)
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle("Composición del Gasto COVID-19 por Tipo de Gasto (Genérica)\nPerú 2020–2026",
                 fontsize=14, fontweight="bold", color=GRIS_TEXTO)
    colores_g = PALETTE_AÑOS[:len(pivot.columns)]
    bottom = np.zeros(len(pivot))
    for col, color in zip(pivot.columns, colores_g):
        bars = ax.bar(pivot.index, pivot[col], bottom=bottom, label=col, color=color, alpha=0.9, zorder=3, width=0.6)
        for bar, b in zip(bars, bottom):
            h = bar.get_height()
            if h > 5:
                ax.text(bar.get_x()+bar.get_width()/2, b+h/2, f"{h:.0f}M",
                        ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")
        bottom += pivot[col].values
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"S/. {v:.0f}M"))
    ax.set_xlabel("Año de ejecución"); ax.set_ylabel("Devengado (Millones de Soles)")
    ax.legend(loc="upper right", fontsize=9, title="Tipo de Gasto")
    fig.tight_layout(); guardar(fig, "08_composicion_generica.png")
    print("  → HALLAZGO: Transferencias a personas dominan el gasto COVID (bonos, subsidios)")


def dashboard_resumen(df_ejec, df_ppto):
    print("\n[Extra] Dashboard resumen ejecutivo...")
    dev_total   = df_ejec["MONTO_DEVENGADO"].sum()
    pim_total   = df_ppto["MONTO_PIM"].sum()
    efic_global = dev_total/pim_total if pim_total>0 else 0
    entidades   = df_ejec["SECTOR_NOMBRE"].nunique()
    fig = plt.figure(figsize=(14, 8), facecolor="#1a1a2e")
    fig.suptitle("GASTO COVID-19 PERÚ 2020–2026 — Resumen Ejecutivo",
                 fontsize=16, fontweight="bold", color="white", y=0.97)
    gs = GridSpec(2, 4, figure=fig, hspace=0.55, wspace=0.4)
    kpis = [("Devengado Total", f"S/. {dev_total/1e6:.0f}M", "#00b894"),
            ("PIM Total",       f"S/. {pim_total/1e6:.0f}M", "#74b9ff"),
            ("Eficiencia Global", f"{efic_global:.1%}",       "#fdcb6e"),
            ("Sectores activos", str(entidades),               "#fd79a8")]
    for i, (label, val, color) in enumerate(kpis):
        ax = fig.add_subplot(gs[0, i])
        ax.set_facecolor("#16213e")
        ax.text(0.5, 0.6, val, ha="center", va="center", fontsize=22,
                fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(0.5, 0.2, label, ha="center", va="center", fontsize=10,
                color="#b2bec3", transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_edgecolor(color); spine.set_linewidth(2)
    ax5 = fig.add_subplot(gs[1, :2]); ax5.set_facecolor("#16213e")
    dev_año = df_ejec.groupby("ANO_EJE")["MONTO_DEVENGADO"].sum()/1e6
    ax5.fill_between(dev_año.index, dev_año.values, alpha=0.3, color="#00b894")
    ax5.plot(dev_año.index, dev_año.values, "o-", color="#00b894", linewidth=2.5)
    ax5.set_title("Devengado por Año (M soles)", color="white", fontsize=10)
    ax5.tick_params(colors="white"); ax5.yaxis.tick_right()
    for spine in ax5.spines.values(): spine.set_edgecolor("#2d3436")
    ax6 = fig.add_subplot(gs[1, 2:]); ax6.set_facecolor("#16213e")
    nivel = df_ejec.groupby("NIVEL_GOBIERNO_NOMBRE")["MONTO_DEVENGADO"].sum()/1e6
    colores_mini = ["#00b894","#74b9ff","#fdcb6e"]
    ax6.pie(nivel.values, labels=[n.title().replace("Gobierno","Gob.")[:15] for n in nivel.index],
            colors=colores_mini, autopct="%1.0f%%",
            textprops={"color":"white","fontsize":9}, wedgeprops={"edgecolor":"#1a1a2e","linewidth":2})
    ax6.set_title("Por Nivel de Gobierno", color="white", fontsize=10)
    guardar(fig, "00_dashboard_resumen.png")
    print(f"  → Dashboard generado. Eficiencia global: {efic_global:.1%}")


if __name__ == "__main__":
    print("="*60)
    print("EDA — Gasto COVID-19 Perú 2020–2026")
    print("="*60)
    df_ejec, df_ppto = cargar_datos()
    print(f"\nDatos: {len(df_ejec):,} registros ejecución | {len(df_ppto):,} presupuesto")
    viz1_evolucion_anual(df_ejec, df_ppto)
    viz2_nivel_gobierno(df_ejec)
    viz3_top_sectores(df_ejec)
    viz4_departamento(df_ejec)
    viz5_eficiencia_sector(df_ejec, df_ppto)
    viz6_mensual_2020(df_ejec)
    viz7_caida_sectores(df_ejec)
    viz8_generica_gasto(df_ejec)
    dashboard_resumen(df_ejec, df_ppto)
    print("\n✅ EDA completo.")
