from asammdf import MDF

rangos = {
    
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

mdf = MDF("run01_frenada_musplit.mf4")

for nombre, (minimo, maximo) in rangos.items():
    senal = mdf.get(nombre)
    margen = (maximo - minimo) * TOLERANCIA

    fuera = (senal.samples < minimo - margen) | (senal.samples > maximo + margen)

    if fuera.any():
        t = senal.timestamps[fuera][0]
        v = senal.samples[fuera][0]
        print(f"{nombre:18} {fuera.sum():4d} muestras fuera de [{minimo}, {maximo}] +-{margen:.1f}   primera en t = {t:.2f} s con {v:.1f}")
    else:
        print(f"{nombre:18}    ok")