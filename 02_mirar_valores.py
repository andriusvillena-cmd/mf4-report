from asammdf import MDF

mdf = MDF("run01_frenada_musplit.mf4")
rl = mdf.get("Wheel_Speed_RL")
vehiculo = mdf.get("Vehicle_Speed")

ventana = (rl.timestamps >= 4.96) & (rl.timestamps <= 5.05)

for t, r, v in zip(rl.timestamps[ventana], rl.samples[ventana], vehiculo.samples[ventana]):
    print(f"{t:6.2f} s   RL {r:7.2f} km/h   vehiculo {v:7.2f} km/h")