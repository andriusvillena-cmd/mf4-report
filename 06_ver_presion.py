import matplotlib.pyplot as plt
from asammdf import MDF

mdf = MDF("run01_frenada_musplit.mf4")
presion = mdf.get("Brake_Pressure")

fig, (completa, zoom) = plt.subplots(2, 1, figsize=(11, 7))

completa.plot(presion.timestamps, presion.samples, linewidth=0.8, color="tab:red")
completa.axhline(250, color="k", linestyle="--", linewidth=1)
completa.set_ylabel("Presion [bar]")
completa.set_title("Completa. Linea negra = limite superior declarado")
completa.grid(alpha=0.3)

zoom.plot(presion.timestamps, presion.samples, linewidth=0.8, color="tab:red")
zoom.axhline(0, color="k", linestyle="--", linewidth=1)
zoom.set_ylim(-1.5, 1.5)
zoom.set_ylabel("Presion [bar]")
zoom.set_xlabel("Tiempo [s]")
zoom.set_title("La misma, ampliada alrededor de cero. Linea negra = limite inferior")
zoom.grid(alpha=0.3)

plt.tight_layout()
plt.show()