"""Tests de regresion del detector de anomalias.

run01 lleva tres fallos sembrados y conocidos; run02 y run03 estan limpios.
Estos tests comprueban que el detector encuentra exactamente eso: ni menos
(falsos negativos) ni mas (falsos positivos).

Se ejecutan con: pytest
"""

from pathlib import Path

import pytest
from asammdf import MDF

from mf4_report import RANGOS, comprobar_congelada, comprobar_rango

AQUI = Path(__file__).parent

CON_FALLOS = "run01_frenada_musplit.mf4"
LIMPIOS = ["run02_frenada_asfalto.mf4", "run03_frenada_mojado.mf4"]

FALLOS_CONOCIDOS = {
    ("fuera de rango", "Brake_Pressure"),
    ("senal congelada", "Wheel_Speed_RL"),
    ("senal congelada", "Yaw_Rate"),
}


def analizar(archivo):
    """Pasa las dos comprobaciones a todas las senales y devuelve los hallazgos."""
    mdf = MDF(AQUI / archivo)
    hallazgos = []

    for nombre, (minimo, maximo) in RANGOS.items():
        senal = mdf.get(nombre)
        for hallazgo in (comprobar_rango(senal, minimo, maximo), comprobar_congelada(senal)):
            if hallazgo:
                hallazgos.append(hallazgo)

    return hallazgos


def test_detecta_los_tres_fallos_sembrados():
    """Sobre el ensayo con fallos conocidos debe encontrar esos tres, ni uno mas."""
    encontrados = {(h["tipo"], h["senal"]) for h in analizar(CON_FALLOS)}
    assert encontrados == FALLOS_CONOCIDOS


@pytest.mark.parametrize("archivo", LIMPIOS, ids=lambda n: n[:5])
def test_no_dispara_en_ensayos_limpios(archivo):
    """Un ensayo sin defectos no debe generar ningun hallazgo."""
    hallazgos = analizar(archivo)
    assert hallazgos == [], f"Falsos positivos: {[h['senal'] for h in hallazgos]}"


def test_el_pico_de_presion_esta_en_el_instante_correcto():
    """El pico de 411 bar ocurre en t = 7.42 s."""
    presion = [h for h in analizar(CON_FALLOS) if h["senal"] == "Brake_Pressure"][0]
    assert presion["instante"] == pytest.approx(7.42, abs=0.01)


def test_la_caida_de_rueda_dura_35_muestras():
    """La caida de Wheel_Speed_RL son 35 muestras a 100 Hz, o sea 350 ms."""
    rueda = [h for h in analizar(CON_FALLOS) if h["senal"] == "Wheel_Speed_RL"][0]
    assert rueda["muestras"] == 35
