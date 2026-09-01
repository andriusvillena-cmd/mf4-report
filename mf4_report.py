"""mf4-report: automated report for an MDF4 vehicle measurement file."""

import base64
import io
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from asammdf import MDF

RANGES = {
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

TOLERANCE = 0.02
MIN_FROZEN_SAMPLES = 10


def check_range(signal, low, high):
    """Values outside the declared range, with a tolerance band for sensor noise."""
    margin = (high - low) * TOLERANCE
    outside = (signal.samples < low - margin) | (signal.samples > high + margin)

    if not outside.any():
        return None

    return {
        "type": "out of range",
        "signal": signal.name,
        "samples": int(outside.sum()),
        "time_s": float(signal.timestamps[outside][0]),
        "detail": f"value {signal.samples[outside][0]:.1f}, limits [{low}, {high}]",
    }


def check_frozen(signal):
    """A live analogue sensor always carries noise.

    An exactly repeated value means a dead signal, not a quiet one. Signals with
    ten or fewer distinct values are treated as digital flags and skipped.
    """
    if len(np.unique(signal.samples)) <= 10:
        return None

    identical = np.diff(signal.samples) == 0
    run = longest = start = 0

    for i, repeated in enumerate(identical):
        if repeated:
            run += 1
            if run > longest:
                longest, start = run, i - run + 1
        else:
            run = 0

    if longest + 1 < MIN_FROZEN_SAMPLES:
        return None

    return {
        "type": "frozen signal",
        "signal": signal.name,
        "samples": longest + 1,
        "time_s": float(signal.timestamps[start]),
        "detail": f"value {signal.samples[start]:.3f} repeated {longest + 1} times",
    }


def statistics(signal):
    return {
        "signal": signal.name,
        "unit": signal.unit or "-",
        "min": float(signal.samples.min()),
        "max": float(signal.samples.max()),
        "mean": float(signal.samples.mean()),
        "samples": len(signal.samples),
    }


def plot_as_base64(mdf, names):
    """Draw every signal and return the image as text, ready to embed."""
    rows = len(names)
    fig, axes = plt.subplots(rows, 1, figsize=(11, 1.6 * rows), sharex=True)

    for axis, name in zip(axes, names):
        signal = mdf.get(name)
        axis.plot(signal.timestamps, signal.samples, linewidth=0.8)
        axis.set_ylabel(f"{name}\n[{signal.unit or '-'}]", fontsize=7)
        axis.tick_params(labelsize=7)
        axis.grid(alpha=0.3)

    axes[-1].set_xlabel("Time [s]")
    fig.tight_layout()

    memory = io.BytesIO()
    fig.savefig(memory, format="png", dpi=100)
    plt.close(fig)
    return base64.b64encode(memory.getvalue()).decode("ascii")


def write_html(source, findings, stats, image, output):
    finding_rows = "".join(
        f"<tr><td>{f['type']}</td><td>{f['signal']}</td>"
        f"<td>{f['time_s']:.2f}</td><td>{f['samples']}</td><td>{f['detail']}</td></tr>"
        for f in findings
    ) or "<tr><td colspan='5'>No findings. Measurement is clean.</td></tr>"

    stat_rows = "".join(
        f"<tr><td>{s['signal']}</td><td>{s['unit']}</td><td>{s['min']:.2f}</td>"
        f"<td>{s['max']:.2f}</td><td>{s['mean']:.2f}</td><td>{s['samples']}</td></tr>"
        for s in stats
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Report {source}</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 40px auto; max-width: 1000px; color: #1a1a1a; }}
 h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
 .meta {{ color: #666; font-size: .9rem; margin-bottom: 32px; }}
 h2 {{ font-size: 1.1rem; margin-top: 36px; }}
 table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
 th, td {{ border-bottom: 1px solid #ddd; padding: 7px 10px; text-align: left; }}
 th {{ background: #f4f4f4; font-weight: 600; }}
 .warn {{ color: #b00; font-weight: 600; }}
 img {{ width: 100%; margin-top: 12px; }}
</style>
</head>
<body>
<h1>Measurement report &mdash; {source}</h1>
<p class="meta">Generated on {datetime.now():%Y-%m-%d %H:%M} by mf4-report</p>

<h2>Findings <span class="warn">({len(findings)})</span></h2>
<table>
<tr><th>Type</th><th>Signal</th><th>t [s]</th><th>Samples</th><th>Detail</th></tr>
{finding_rows}
</table>

<h2>Statistics</h2>
<table>
<tr><th>Signal</th><th>Unit</th><th>Min</th><th>Max</th><th>Mean</th><th>Samples</th></tr>
{stat_rows}
</table>

<h2>Signals</h2>
<img src="data:image/png;base64,{image}" alt="Plots of every signal">
</body>
</html>"""

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    if len(sys.argv) < 2:
        print("Usage: python mf4_report.py <measurement.mf4>")
        sys.exit(1)

    source = sys.argv[1]
    mdf = MDF(source)

    findings, stats = [], []

    for name, (low, high) in RANGES.items():
        signal = mdf.get(name)
        stats.append(statistics(signal))
        for finding in (check_range(signal, low, high), check_frozen(signal)):
            if finding:
                findings.append(finding)

    image = plot_as_base64(mdf, list(RANGES))
    output = source.replace(".mf4", "_report.html")
    write_html(source, findings, stats, image, output)

    print(f"{source}: {len(findings)} findings  ->  {output}")


if __name__ == "__main__":
    main()
