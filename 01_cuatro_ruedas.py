import matplotlib.pyplot as plt
from asammdf import MDF

mdf = MDF("run01_frenada_musplit.mf4")

ruedas = ["Wheel_Speed_FL", "Wheel_Speed_FR", "Wheel_Speed_RL", "Wheel_Speed_RR"]

fig, ax = plt.subplots(figsize=(11, 6))

for nombre in ruedas:
    senal = mdf.get(nombre)
    ax.plot(senal.timestamps, senal.samples, linewidth=0.9, label=nombre)

referencia = mdf.get("Vehicle_Speed")
ax.plot(referencia.timestamps, referencia.samples, "k--", linewidth=1.5, label="Vehicle_Speed")

ax.set_xlabel("Tiempo [s]")
ax.set_ylabel("Velocidad [km/h]")
ax.set_title("Frenada mu-split: velocidades de rueda")
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()
plt.show()