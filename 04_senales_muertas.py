import numpy as np
from asammdf import MDF

mdf = MDF("run01_frenada_musplit.mf4")

for nombre in mdf.channels_db:
    if nombre in ("time", "t"):
        continue

    senal = mdf.get(nombre)

    if len(np.unique(senal.samples)) <= 10:
        continue

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

    if mejor >= 10:
        print(f"{nombre:18} {mejor + 1:4d} muestras iguales desde t = {senal.timestamps[inicio]:5.2f} s")