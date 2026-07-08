import os
import matplotlib
matplotlib.rcParams.update({
    'font.size': 14,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
})
import numpy as np
import matplotlib.pyplot as plt
from skyfield.api import Topos, load, EarthSatellite

# 1. TLE files archived in data/
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

TLE_FILES = {
    'LEO — ISS (ZARYA)':       'tle_leo.txt',
    'MEO — NAVSTAR 65':        'tle_meo.txt',
    'GEO — AMAZONAS 3':        'tle_geo.txt',
    'SSO — LANDSAT 8':         'tle_sso.txt',
}

# 2. Load timescale
ts = load.timescale()

def load_tle(filepath):
    """Parse a 3-line element set file and return an EarthSatellite."""
    with open(filepath) as fh:
        lines = [ln.rstrip('\n') for ln in fh if ln.strip()]
    return EarthSatellite(lines[1], lines[2], lines[0].strip(), ts)

# 3. Set up a 30-day simulation window (May 2026) at 1-minute intervals
t0 = ts.utc(2026, 5, 1)
t1 = ts.utc(2026, 5, 31)
t = ts.linspace(t0, t1, 43200)

# 4. Define Ground Station: Paipa, Colombia (WGS84)
colombia_gs = Topos(latitude_degrees=5.783333,
                    longitude_degrees=-73.117778,
                    elevation_m=2600.0)

# 5. Minimum elevation mask angle
min_elevation = 10.0

# 6. Load all satellites and compute visibility
satellites = {
    label: load_tle(os.path.join(DATA_DIR, fname))
    for label, fname in TLE_FILES.items()
}

print(f"\n{'Satellite':<26}  {'Contact time (min / 30 days)':>28}")
print('-' * 57)

results = {}
for label, sat in satellites.items():
    alt, _az, _dist = (sat - colombia_gs).at(t).altaz()
    visible = alt.degrees > min_elevation
    contact_min = int(np.sum(visible))
    results[label] = {'alt': alt, 'visible': visible, 'contact_min': contact_min}
    print(f"  {label:<24}  {contact_min:>28}")

# 7. Plot first visible pass for each satellite (2×2 subplots)
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

fig, axes = plt.subplots(2, 2, figsize=(14, 8))
axes = axes.flatten()

for ax, (label, res), color in zip(axes, results.items(), COLORS):
    alt_deg = res['alt'].degrees
    visible = res['visible']
    pass_indices = np.where(visible)[0]

    if len(pass_indices) == 0:
        ax.text(0.5, 0.5, 'No passes above 10°\nduring simulation window',
                ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title(label, fontsize=12)
        continue

    # GEO satellites are continuously visible — show the first 24 h only
    continuously_visible = (pass_indices[0] == 0 and
                            np.sum(visible) > 0.9 * len(t))
    if continuously_visible:
        end_idx = min(1440, len(t))          # 1 440 min = 24 h
        pass_t = t[:end_idx]
        pass_alt = alt_deg[:end_idx]
        subtitle = '(first 24 h — continuously visible)'
    else:
        # Isolate the first discrete pass
        i_start = pass_indices[0]
        i_end = i_start
        while (i_end + 1 < len(pass_indices) and
               pass_indices[i_end + 1] == pass_indices[i_end] + 1):
            i_end += 1
        pass_t = t[i_start:i_end + 1]
        pass_alt = alt_deg[i_start:i_end + 1]
        subtitle = f'(first pass — {len(pass_t)} min)'

    ax.plot(pass_t.utc_datetime(), pass_alt, color=color, linewidth=2)
    ax.axhline(y=min_elevation, color='gray', linestyle='--',
               linewidth=1, label=f'{min_elevation:.0f}° mask')
    ax.set_title(f'{label}\n{subtitle}', fontsize=11)
    ax.set_xlabel('Time (UTC)', fontsize=11)
    ax.set_ylabel('Elevation (°)', fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.4)
    ax.tick_params(axis='x', rotation=25)

plt.suptitle(
    'Tracking Geometry: First Visible Pass — Paipa GS (5.78°N, 73.12°W, 2 600 m)',
    fontsize=13, y=1.01
)
plt.tight_layout()
plt.savefig('simulation.png', dpi=300, bbox_inches='tight')
plt.show()
