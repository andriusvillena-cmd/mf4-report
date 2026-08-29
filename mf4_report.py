"""mf4-report: informe automatico de un fichero de medida MDF4."""

import base64
import io
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from asammdf import MDF

RANGOS = {
    "Vehicle_Speed":  (0, 300),
    "Wheel_Speed_FL": (0, 300),
    "Wheel_Speed_FR": (0, 300),
    "Wheel_Speed_RL": (0, 300),
    "Wheel_Speed_RR": (0, 300),
    "Brake_Pressure": (0, 250),
    "Yaw_Rate":       (-180, 180),
    "Steering_Angle": (-780, 780),
    "Long_Accel":     (-2, 2),
    "Lat_Accel":      (-2, 2),
}

TOLERANCIA = 0.02
MINIMO_CONGELADAS = 10


def comprobar_rango(senal, minimo, maximo):
    margen = (maximo - minimo) * TOLERANCIA
    fuera = (senal.samples < minimo - margen) | (senal.samples > maximo + margen)
    if not fuera.any():
        return None
    return {
        "tipo": "fuera de rango",
        "senal": senal.name,
        "muestras": int(fuera.sum()),
        "instante": float(senal.timestamps[fuera][0]),
        "detalle": f"valor {senal.samples[fuera][0]:.1f}, limite [{minimo}, {maximo}]",
    }


def comprobar_congelada(senal):
    if len(np.unique(senal.samples)) <= 10:
        return None
    iguales = np.diff(senal.samples) == 0
    racha = mejor = inicio = 0
    for i, repetido in enumerate(iguales):
        if repetido:
            racha += 1
            if racha > mejor:
                mejor, inicio = racha, i - racha + 1
        else:
            racha = 0
    if mejor + 1 < MINIMO_CONGELADAS:
        return None
    return {
        "tipo": "senal congelada",
        "senal": senal.name,
        "muestras": mejor + 1,
        "instante": float(senal.timestamps[inicio]),
        "detalle": f"valor {senal.samples[inicio]:.3f} repetido {mejor + 1} veces",
    }


def estadisticos(senal):
    return {
        "senal": senal.name,
        "unidad": senal.unit or "-",
        "minimo": float(senal.samples.min()),
        "maximo": float(senal.samples.max()),
        "media": float(senal.samples.mean()),
        "muestras": len(senal.samples),
    }


def grafica_en_base64(mdf, nombres):
    """Dibuja todas las senales y devuelve la imagen como texto para incrustar."""
    filas = len(nombres)
    fig, ejes = plt.subplots(filas, 1, figsize=(11, 1.6 * filas), sharex=True)

    for eje, nombre in zip(ejes, nombres):
        senal = mdf.get(nombre)
        eje.plot(senal.timestamps, senal.samples, linewidth=0.8)
        eje.set_ylabel(f"{nombre}\n[{senal.unit or '-'}]", fontsize=7)
        eje.tick_params(labelsize=7)
        eje.grid(alpha=0.3)

    ejes[-1].set_xlabel("Tiempo [s]")
    fig.tight_layout()

    memoria = io.BytesIO()
    fig.savefig(memoria, format="png", dpi=100)
    plt.close(fig)
    return base64.b64encode(memoria.getvalue()).decode("ascii")


def escribir_html(archivo, hallazgos, stats, imagen, salida):
    filas_hallazgos = "".join(
        f"<tr><td>{h['tipo']}</td><td>{h['senal']}</td>"
        f"<td>{h['instante']:.2f}</td><td>{h['muestras']}</td><td>{h['detalle']}</td></tr>"
        for h in hallazgos
    ) or "<tr><td colspan='5'>Sin hallazgos. Medida correcta.</td></tr>"

    filas_stats = "".join(
        f"<tr><td>{s['senal']}</td><td>{s['unidad']}</td><td>{s['minimo']:.2f}</td>"
        f"<td>{s['maximo']:.2f}</td><td>{s['media']:.2f}</td><td>{s['muestras']}</td></tr>"
        for s in stats
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Informe {archivo}</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 40px auto; max-width: 1000px; color: #1a1a1a; }}
 h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
 .meta {{ color: #666; font-size: .9rem; margin-bottom: 32px; }}
 h2 {{ font-size: 1.1rem; margin-top: 36px; }}
 table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
 th, td {{ border-bottom: 1px solid #ddd; padding: 7px 10px; text-align: left; }}
 th {{ background: #f4f4f4; font-weight: 600; }}
 .aviso {{ color: #b00; font-weight: 600; }}
 img {{ width: 100%; margin-top: 12px; }}
</style>
</head>
<body>
<h1>Informe de medida &mdash; {archivo}</h1>
<p class="meta">Generado el {datetime.now():%d/%m/%Y %H:%M} por mf4-report</p>

<h2>Hallazgos <span class="aviso">({len(hallazgos)})</span></h2>
<table>
<tr><th>Tipo</th><th>Senal</th><th>t [s]</th><th>Muestras</th><th>Detalle</th></tr>
{filas_hallazgos}
</table>

<h2>Estadisticos</h2>
<table>
<tr><th>Senal</th><th>Unidad</th><th>Minimo</th><th>Maximo</th><th>Media</th><th>Muestras</th></tr>
{filas_stats}
</table>

<h2>Senales</h2>
<img src="data:image/png;base64,{imagen}" alt="Graficas de todas las senales">
</body>
</html>"""

    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    if len(sys.argv) < 2:
        print("Uso: python mf4_report.py <archivo.mf4>")
        sys.exit(1)

    archivo = sys.argv[1]
    mdf = MDF(archivo)

    hallazgos = []
    stats = []

    for nombre, (minimo, maximo) in RANGOS.items():
        senal = mdf.get(nombre)
        stats.append(estadisticos(senal))
        for hallazgo in (comprobar_rango(senal, minimo, maximo), comprobar_congelada(senal)):
            if hallazgo:
                hallazgos.append(hallazgo)

    imagen = grafica_en_base64(mdf, list(RANGOS))
    salida = archivo.replace(".mf4", "_informe.html")
    escribir_html(archivo, hallazgos, stats, imagen, salida)

    print(f"{archivo}: {len(hallazgos)} hallazgos  ->  {salida}")

if __name__ == "__main__":
    main()
