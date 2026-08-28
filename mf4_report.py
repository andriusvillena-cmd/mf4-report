"""mf4-report: informe automatico de un fichero de medida MDF4."""

import sys
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
    """Devuelve un hallazgo si la senal sale del rango declarado, o None."""
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
    """Devuelve un hallazgo si la senal repite el mismo valor, o None."""
    if len(np.unique(senal.samples)) <= 10:
        return None

    iguales = np.diff(senal.samples) == 0

    racha = 0
    mejor = 0
    inicio = 0
    for i, repetido in enumerate(iguales):
        if repetido:
            racha += 1
            if racha > mejor:
                mejor = racha
                inicio = i - racha + 1
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


# --- prueba ---

if len(sys.argv) < 2:
    print("Uso: python mf4_report.py <archivo.mf4>")
    sys.exit(1)

mdf = MDF(sys.argv[1])
hallazgos = []

for nombre, (minimo, maximo) in RANGOS.items():
    senal = mdf.get(nombre)

    for hallazgo in (comprobar_rango(senal, minimo, maximo), comprobar_congelada(senal)):
        if hallazgo:
            hallazgos.append(hallazgo)

for h in hallazgos:
    print(f"{h['tipo']:18} {h['senal']:16} t = {h['instante']:5.2f} s   {h['detalle']}")