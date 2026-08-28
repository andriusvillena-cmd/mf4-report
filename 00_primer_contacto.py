"""
Primer contacto. Abre un MF4, dibuja dos senales y guarda la grafica en un PNG.

    py -3.13 -m pip install asammdf matplotlib
    cd C:\\Claude\\datos
    py -3.13 00_primer_contacto.py

Guarda siempre 'primer_contacto.png' en esta misma carpeta, y ademas intenta
abrir una ventana. Si tu Python no tiene tkinter, la ventana no aparecera pero
el PNG estara igual.
"""
import matplotlib
import matplotlib.pyplot as plt
from asammdf import MDF

mdf = MDF("run01_frenada_musplit.mf4")

velocidad = mdf.get("Vehicle_Speed")
presion = mdf.get("Brake_Pressure")

fig, (arriba, abajo) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))

arriba.plot(velocidad.timestamps, velocidad.samples)
arriba.set_ylabel(f"Velocidad [{velocidad.unit}]")
arriba.grid(alpha=0.3)

abajo.plot(presion.timestamps, presion.samples, color="tab:red")
abajo.set_ylabel(f"Presion [{presion.unit}]")
abajo.set_xlabel("Tiempo [s]")
abajo.grid(alpha=0.3)

fig.suptitle("Frenada de emergencia 100-0 km/h en mu-split")
plt.tight_layout()

# 1) Guardar siempre. Esto funciona con cualquier instalacion de Python.
fig.savefig("primer_contacto.png", dpi=110)
print("Grafica guardada en: primer_contacto.png")

# 2) Intentar abrir una ventana. Necesita un backend grafico (tkinter, Qt...).
backend = matplotlib.get_backend()
print("Backend de matplotlib:", backend)
if backend.lower() == "agg":
    print("  -> Sin backend grafico: no habra ventana. Abre el PNG a mano.")
    print("     Para tener ventanas: py -3.13 -m pip install PyQt5")
else:
    print("  -> Abriendo ventana. Cierrala para continuar.")
    plt.show()

# Y ahora, para ver que mas hay dentro del fichero:
print("\nCanales disponibles:")
for nombre in mdf.channels_db:
    if nombre not in ("time", "t"):
        canal = mdf.get(nombre)
        print(f" - {nombre:<20} [{canal.unit or '-'}]")
