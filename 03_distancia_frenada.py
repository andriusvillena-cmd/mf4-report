import numpy as np
from asammdf import MDF

archivos = ["run01_frenada_musplit.mf4", "run02_frenada_asfalto.mf4", "run03_frenada_mojado.mf4"]

for archivo in archivos:
    mdf = MDF(archivo)
    velocidad = mdf.get("Vehicle_Speed")
    presion = mdf.get("Brake_Pressure")

    t = velocidad.timestamps
    v_ms = velocidad.samples / 3.6

    inicio = np.argmax(presion.samples > 5)
    final = np.argmax(velocidad.samples < 0.5)

    distancia = np.trapezoid(v_ms[inicio:final], t[inicio:final])
    duracion = t[final] - t[inicio]

    print(f"{archivo:32} {distancia:6.1f} m   {duracion:5.2f} s")