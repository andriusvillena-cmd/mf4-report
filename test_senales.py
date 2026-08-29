"""Comprobaciones automaticas sobre los ficheros de medida de la carpeta.

Un test por criterio de validacion, ejecutado sobre cada ensayo.
Se ejecutan con: pytest
"""

from pathlib import Path

import pytest
from asammdf import MDF

from mf4_report import RANGOS, comprobar_congelada, comprobar_rango

RUEDAS = ["Wheel_Speed_FL", "Wheel_Speed_FR", "Wheel_Speed_RL", "Wheel_Speed_RR"]

ENSAYOS = sorted(Path(__file__).parent.glob("run*.mf4"))


@pytest.mark.parametrize("archivo", ENSAYOS, ids=lambda p: p.stem)
def test_senales_dentro_del_rango_declarado(archivo):
    """Criterio de rango: ningun valor fuera de los limites del sensor, con margen."""
    mdf = MDF(archivo)
    hallazgos = [comprobar_rango(mdf.get(n), lo, hi) for n, (lo, hi) in RANGOS.items()]
    hallazgos = [h for h in hallazgos if h]

    assert hallazgos == [], f"Fuera de rango: {[h['senal'] for h in hallazgos]}"


@pytest.mark.parametrize("archivo", ENSAYOS, ids=lambda p: p.stem)
def test_senales_analogicas_vivas(archivo):
    """Criterio de vivacidad: una senal analogica viva siempre tiene ruido."""
    mdf = MDF(archivo)
    hallazgos = [comprobar_congelada(mdf.get(n)) for n in RANGOS]
    hallazgos = [h for h in hallazgos if h]

    assert hallazgos == [], f"Congeladas: {[h['senal'] for h in hallazgos]}"


@pytest.mark.parametrize("archivo", ENSAYOS, ids=lambda p: p.stem)
def test_velocidades_de_rueda_plausibles(archivo):
    """Criterio de plausibilidad: ninguna rueda parada con el vehiculo en marcha."""
    mdf = MDF(archivo)
    referencia = mdf.get("Vehicle_Speed").samples

    for nombre in RUEDAS:
        rueda = mdf.get(nombre).samples
        implausible = (rueda < 1.0) & (referencia > 5.0)

        assert not implausible.any(), (
            f"{nombre} a 0 km/h en {implausible.sum()} muestras con el vehiculo en marcha")