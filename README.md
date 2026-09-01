# mf4-report

![tests](https://github.com/andriusvillena-cmd/mf4-report/actions/workflows/tests.yml/badge.svg)

Automated reporting tool for MDF4 vehicle measurement files. Detects signal
anomalies and produces a self-contained HTML report with plots and statistics.

## Usage

    python mf4_report.py <measurement.mf4>

Produces `<measurement>_report.html` next to the input file.
`example_report.html` in this repository is the output for
`run01_braking_splitmu.mf4`.

## Requirements

    pip install -r requirements.txt

---

# Safety analysis and traceability

The checks implemented here are derived from a safety goal, not chosen
arbitrarily. This section shows the chain from vehicle-level hazard down to the
individual test case, in the style of ISO 26262.

Note: this is a portfolio exercise. The HARA below is illustrative and was not
produced under a certified process.

## Safety goal

**SG-01** &mdash; The vehicle shall not suffer an unintended ESP intervention
that causes a loss of directional stability or an involuntary deviation from
the intended trajectory.

**ASIL D.** Rationale: severity can reach life-threatening injury at motorway
speed; exposure is maximal because ESP is active whenever the vehicle is
moving; controllability is poor because the driver does not anticipate the
vehicle deviating on its own.

## Fault tolerant time interval

**FTTI = 100 ms.**

An unintended single-wheel brake application builds a yaw moment. At 100 km/h
the resulting deviation becomes uncontrollable in roughly 300 ms, which is also
the order of human reaction time under full concentration. The FTTI is set below
that with margin, so the system reaches its safe state before the driver would
need to intervene.

At a 100 Hz sampling rate, 100 ms equals **10 samples**. This is the origin of
the `MIN_FROZEN_SAMPLES = 10` constant in `mf4_report.py`.

## Functional safety requirements

| ID | Requirement | Derived from |
|---|---|---|
| **FSR-01.1** | The system shall detect an implausible wheel speed by cross-checking it against the other wheels and the vehicle reference speed. | SG-01 |
| **FSR-01.2** | On detecting an implausible wheel speed, the system shall inhibit ESP intervention and signal the fault to the driver, within the FTTI. | SG-01 |
| **FSR-02** | The system shall detect a stuck analogue signal. A live analogue sensor always carries noise; an exactly repeated value indicates a dead signal, not a quiet one. | SG-01 |
| **FSR-03** | The system shall detect sensor values outside the declared measurement range, allowing a tolerance band for normal sensor noise around rest value. | SG-01 |

## Test cases

| Test case | Verifies | Acceptance criterion |
|---|---|---|
| `test_finds_the_three_seeded_faults` | FSR-01.1, FSR-02, FSR-03 | On a reference measurement with three known seeded faults, the detector reports exactly those three: no false negatives, no false positives. |
| `test_does_not_fire_on_clean_runs[run02]` | FSR-01.1, FSR-02, FSR-03 | On a fault-free measurement (dry asphalt), no finding is reported. |
| `test_does_not_fire_on_clean_runs[run03]` | FSR-01.1, FSR-02, FSR-03 | On a fault-free measurement (wet asphalt), no finding is reported. |
| `test_the_pressure_spike_is_at_the_right_instant` | FSR-03 | The out-of-range brake pressure event is reported at t = 7.42 s &plusmn; 0.01 s. |
| `test_the_wheel_dropout_lasts_35_samples` | FSR-01.1 | The wheel speed dropout is reported as 35 samples, i.e. 350 ms at 100 Hz. |

## Verification status

All test cases execute automatically on every push via GitHub Actions, in a
clean environment. Current status is shown by the badge at the top of this file.

## Detection criteria as implemented

| Family | Criterion | Constant |
|---|---|---|
| Plausibility | A wheel below 1 km/h while the vehicle reference exceeds 5 km/h is not physically possible. | &mdash; |
| Liveness | 10 or more consecutive identical samples on an analogue signal. Signals with 10 or fewer distinct values are treated as digital flags and skipped. | `MIN_FROZEN_SAMPLES = 10` |
| Range | Value outside the declared range plus a tolerance of 2 % of the range width, to avoid firing on sensor noise around rest value. | `TOLERANCE = 0.02` |

## Sample data

`run01_braking_splitmu.mf4`, `run02_braking_dry.mf4` and
`run03_braking_wet.mf4` are **synthetic**. They were generated for practice,
with three faults deliberately seeded in run01, and are not measurements from a
real vehicle.

They represent emergency braking from 100 to 0 km/h: split-mu (left wheels on
ice, right on dry asphalt), dry asphalt, and wet asphalt.

---

## Related

[can-physical-decoder](https://github.com/andriusvillena-cmd/can-physical-decoder)
and
[flexray-physical-decoder](https://github.com/andriusvillena-cmd/flexray-physical-decoder)
— decoding CAN and FlexRay frames straight from an oscilloscope trace, with the
CRCs verified.
