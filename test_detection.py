"""Regression tests for the anomaly detector.

run01 carries three known seeded faults; run02 and run03 are clean. These tests
check that the detector finds exactly that: no fewer (false negatives) and no
more (false positives).

    pytest -v
"""

from pathlib import Path

import pytest
from asammdf import MDF

from mf4_report import RANGES, check_frozen, check_range

HERE = Path(__file__).parent

WITH_FAULTS = "run01_braking_splitmu.mf4"
CLEAN = ["run02_braking_dry.mf4", "run03_braking_wet.mf4"]

KNOWN_FAULTS = {
    ("out of range", "Brake_Pressure"),
    ("frozen signal", "Wheel_Speed_RL"),
    ("frozen signal", "Yaw_Rate"),
}


def analyse(filename):
    """Run both checks over every signal and return the findings."""
    mdf = MDF(HERE / filename)
    findings = []

    for name, (low, high) in RANGES.items():
        signal = mdf.get(name)
        for finding in (check_range(signal, low, high), check_frozen(signal)):
            if finding:
                findings.append(finding)

    return findings


def test_finds_the_three_seeded_faults():
    """On the reference run with known faults it must find those three, no more."""
    found = {(f["type"], f["signal"]) for f in analyse(WITH_FAULTS)}
    assert found == KNOWN_FAULTS


@pytest.mark.parametrize("filename", CLEAN, ids=lambda n: n[:5])
def test_does_not_fire_on_clean_runs(filename):
    """A run with no defects must produce no findings at all."""
    findings = analyse(filename)
    assert findings == [], f"False positives: {[f['signal'] for f in findings]}"


def test_the_pressure_spike_is_at_the_right_instant():
    """The 411 bar spike happens at t = 7.42 s."""
    pressure = [f for f in analyse(WITH_FAULTS) if f["signal"] == "Brake_Pressure"][0]
    assert pressure["time_s"] == pytest.approx(7.42, abs=0.01)


def test_the_wheel_dropout_lasts_35_samples():
    """The Wheel_Speed_RL dropout is 35 samples at 100 Hz, that is 350 ms."""
    wheel = [f for f in analyse(WITH_FAULTS) if f["signal"] == "Wheel_Speed_RL"][0]
    assert wheel["samples"] == 35
