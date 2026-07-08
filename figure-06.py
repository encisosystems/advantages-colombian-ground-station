"""
figure-06.py — Cross-Platform Software Validation Figure
=========================================================
Computes three performance metrics over a 7-day window using
Python/Skyfield (SGP4) and optionally reads NASA GMAT output files
to produce a two-panel validation figure (Table 2 companion).

Metrics (per orbit):
  1. Mean single-pass duration        (seconds)
  2. Cumulative daily contact time    (minutes / day)
  3. Peak Doppler shift               (kHz, Ka-band 30 GHz)

Orbits:
  LEO — ISS (ZARYA),  ~422 km, 51.6°   [data/tle_leo.txt]
  SSO — LANDSAT 8,    ~701 km, 98.2°   [data/tle_sso.txt]

Ground station:
  Paipa, Colombia — 5.783333° N, 73.117778° W, 2600 m, 10° mask

Validation window:
  2026 Jul 08 00:00 UTC  →  2026 Jul 15 00:00 UTC  (7 days, 1-min cadence)

GMAT workflow:
  1. Open gmat/gmat_leo.script and gmat/gmat_sso.script in NASA GMAT.
  2. Run each script — outputs appear in the gmat/ directory:
       gmat/contacts_leo.txt   gmat/contacts_sso.txt
       gmat/rangedata_leo.txt  gmat/rangedata_sso.txt
  3. Re-run this script — it auto-parses the GMAT files, computes ε,
     and renders the full two-panel comparison figure.
"""

import os
import re
import numpy as np
import matplotlib
matplotlib.rcParams.update({
    'font.size': 14,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
})
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from skyfield.api import Topos, load, EarthSatellite

# ── Physical constants ─────────────────────────────────────────────────────────
F0_HZ   = 30.0e9        # Ka-band carrier frequency, Hz
C_KM_S  = 299_792.458   # speed of light, km/s

# ── Simulation parameters ──────────────────────────────────────────────────────
MIN_EL  = 10.0           # elevation mask, degrees
N_DAYS  = 7              # validation window length, days
N_STEPS = N_DAYS * 1440  # 1-minute cadence  (10 080 steps)
EPS_THRESHOLD = 0.11     # ε threshold from the paper, %

# ── File paths ─────────────────────────────────────────────────────────────────
_HERE    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_HERE, 'data')
GMAT_DIR = os.path.join(_HERE, 'gmat')

# ── GMAT reference values ──────────────────────────────────────────────────────
# Populated automatically if gmat/contacts_*.txt / gmat/rangedata_*.txt exist.
# You can also hard-code values here after a GMAT run, e.g.:
#   GMAT_REF['LEO']['mean_pass_s'] = 352.4
GMAT_REF = {
    'LEO': {'mean_pass_s': None, 'daily_min': None, 'peak_doppler_khz': None},
    'SSO': {'mean_pass_s': None, 'daily_min': None, 'peak_doppler_khz': None},
}

# ── Orbit display labels ───────────────────────────────────────────────────────
ORBIT_LABELS = {
    'LEO': 'LEO — ISS (~422 km, 51.6°)',
    'SSO': 'SSO — Landsat 8 (~701 km, 98.2°)',
}

# ── Skyfield setup ─────────────────────────────────────────────────────────────
ts = load.timescale()

def _load_tle(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path) as fh:
        lines = [ln.rstrip('\n') for ln in fh if ln.strip()]
    return EarthSatellite(lines[1], lines[2], lines[0].strip(), ts)

paipa = Topos(latitude_degrees=5.783333,
              longitude_degrees=-73.117778,
              elevation_m=2600.0)

# Validation window — 7 days from 2026 Jul 08 00:00 UTC
_T0 = ts.utc(2026, 7, 8)
_T1 = ts.utc(2026, 7, 15)
_t  = ts.linspace(_T0, _T1, N_STEPS)


# ── Python metric computation ──────────────────────────────────────────────────

def _detect_passes(visible):
    """Return list of (start_idx, end_idx) inclusive for each pass above mask."""
    passes, in_pass, start = [], False, 0
    for i, v in enumerate(visible):
        if v and not in_pass:
            in_pass, start = True, i
        elif not v and in_pass:
            in_pass = False
            passes.append((start, i - 1))
    if in_pass:
        passes.append((start, len(visible) - 1))
    return passes


def compute_python_metrics(sat):
    """
    Compute (mean_pass_s, daily_min, peak_doppler_khz) using Skyfield/SGP4.

    Pass duration and daily contact time use Skyfield's find_events() for
    sub-second accuracy at rise/set boundaries.  Doppler is derived via
    central-difference on the 1-minute geometric-range grid.
    """
    # ── Precise pass detection via event-finding ───────────────────────
    t_ev, ev_type = sat.find_events(paipa, _T0, _T1, altitude_degrees=MIN_EL)
    # ev_type: 0 = rise above mask, 1 = culmination, 2 = set below mask

    pass_durations = []
    rise_tt = None
    for ev_t, et in zip(t_ev, ev_type):
        if et == 0:
            rise_tt = ev_t.tt                            # Terrestrial Time, days
        elif et == 2 and rise_tt is not None:
            pass_durations.append((ev_t.tt - rise_tt) * 86400.0)  # → seconds
            rise_tt = None

    mean_pass_s = float(np.mean(pass_durations)) if pass_durations else 0.0
    daily_min   = float(np.sum(pass_durations)) / 60.0 / N_DAYS

    # ── Doppler via range central-difference on 1-minute grid ──────────
    topo           = (sat - paipa).at(_t)
    alt, _az, dist = topo.altaz()
    visible        = alt.degrees > MIN_EL
    r_km           = dist.km

    range_rate_km_s = np.gradient(r_km, 60.0)
    f_D_kHz         = -F0_HZ * range_rate_km_s / C_KM_S / 1e3

    # Extend pass mask by ±1 step to capture horizon Doppler peaks
    mask = visible.copy()
    mask[1:]  |= visible[:-1]
    mask[:-1] |= visible[1:]
    peak_doppler_khz = float(np.max(np.abs(f_D_kHz[mask]))) if mask.any() else 0.0

    return dict(mean_pass_s=mean_pass_s,
                daily_min=daily_min,
                peak_doppler_khz=peak_doppler_khz)


# ── GMAT output parsing ────────────────────────────────────────────────────────

def _paipa_ecef_km():
    """Return Paipa WGS-84 ECEF position vector [km]."""
    lat = np.radians(5.783333)
    lon = np.radians(-73.117778)
    h   = 2.6                           # km
    a   = 6378.137                      # km (WGS-84 semi-major axis)
    f   = 1.0 / 298.257223563
    e2  = 2.0 * f - f * f
    N   = a / np.sqrt(1.0 - e2 * np.sin(lat) ** 2)
    x   = (N + h) * np.cos(lat) * np.cos(lon)
    y   = (N + h) * np.cos(lat) * np.sin(lon)
    z   = (N * (1.0 - e2) + h) * np.sin(lat)
    return np.array([x, y, z])


def _parse_gmat_contacts(filepath):
    """
    Parse a GMAT ContactLocator report.
    Each data line ends with the pass duration in seconds (float).
    Returns (mean_pass_s, daily_min) or (None, None) on failure.
    """
    durations = []
    with open(filepath, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            # Skip header / label lines
            low = line.lower()
            if any(kw in low for kw in ('duration', 'start', 'stop', 'event', 'total', 'contact')):
                continue
            # Last token should be the duration in seconds
            m = re.search(r'(\d+\.\d+)\s*$', line)
            if m:
                try:
                    d = float(m.group(1))
                    if 0.0 < d < 86400.0:   # sanity: 0 to 24 h
                        durations.append(d)
                except ValueError:
                    pass

    if not durations:
        return None, None

    mean_pass_s = float(np.mean(durations))
    daily_min   = float(np.sum(durations)) / 60.0 / N_DAYS
    return mean_pass_s, daily_min


def _parse_gmat_rangedata(filepath):
    """
    Parse a GMAT ReportFile with columns:
      SC.UTCGregorian   SC.EarthFixed.X  Y  Z  VX  VY  VZ
    (GMAT UTCGregorian occupies 4 whitespace-delimited tokens:
       e.g. '08 Jul 2026 03:41:05.326')
    Returns peak_doppler_khz or None on failure.
    """
    gs_ecef = _paipa_ecef_km()
    rows = []
    with open(filepath, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            tokens = line.split()
            if len(tokens) < 10:   # 4 time + 6 state
                continue
            try:
                floats = [float(tok) for tok in tokens[-6:]]
                rows.append(floats)
            except ValueError:
                continue   # header or malformed line

    if len(rows) < 2:
        return None

    arr    = np.array(rows)              # (N, 6)
    r_sat  = arr[:, :3]                  # (N, 3) km  — ECEF position
    v_sat  = arr[:, 3:]                  # (N, 3) km/s — ECEF velocity

    dr  = r_sat - gs_ecef[np.newaxis, :]     # (N, 3) topocentric ECEF
    rng = np.linalg.norm(dr, axis=1)         # (N,)   range km

    # Range rate = radial component of satellite ECEF velocity
    range_rate = np.einsum('ij,ij->i', dr / rng[:, np.newaxis], v_sat)   # km/s
    f_D_kHz    = -F0_HZ * range_rate / C_KM_S / 1e3

    # Approximate elevation mask in ECEF: project LOS onto up-vector at Paipa
    lat = np.radians(5.783333)
    lon = np.radians(-73.117778)
    up  = np.array([np.cos(lat) * np.cos(lon),
                    np.cos(lat) * np.sin(lon),
                    np.sin(lat)])
    sin_el  = np.dot(dr / rng[:, np.newaxis], up)
    el_mask = np.degrees(np.arcsin(np.clip(sin_el, -1.0, 1.0))) > MIN_EL

    if not el_mask.any():
        return None

    # Extend mask by ±1 step to capture horizon peaks
    ext = el_mask.copy()
    ext[1:]  |= el_mask[:-1]
    ext[:-1] |= el_mask[1:]
    return float(np.max(np.abs(f_D_kHz[ext])))


def _try_load_gmat(orbit_key_lower):
    """
    Try to read GMAT output files for an orbit key ('leo' or 'sso').
    Returns a partial dict with found values; missing keys are omitted.
    """
    contacts_path  = os.path.join(GMAT_DIR, f'contacts_{orbit_key_lower}.txt')
    rangedata_path = os.path.join(GMAT_DIR, f'rangedata_{orbit_key_lower}.txt')
    result = {}

    if os.path.isfile(contacts_path):
        mean_s, daily_min = _parse_gmat_contacts(contacts_path)
        if mean_s is not None:
            result['mean_pass_s'] = mean_s
        if daily_min is not None:
            result['daily_min'] = daily_min

    if os.path.isfile(rangedata_path):
        peak = _parse_gmat_rangedata(rangedata_path)
        if peak is not None:
            result['peak_doppler_khz'] = peak

    return result


# ── Console table ──────────────────────────────────────────────────────────────

def _print_table(python_metrics):
    sep = '─' * 74
    print()
    print(sep)
    print('  Cross-Platform Validation — Python / Skyfield (SGP4) Computed Values')
    print(sep)
    print(f'  {"Orbit":<34}  {"Metric":<26}  {"Python Value":>12}')
    print(sep)
    for orb, label in ORBIT_LABELS.items():
        m = python_metrics[orb]
        gref = GMAT_REF[orb]

        def _eps_str(py_val, gmat_val):
            if gmat_val is None:
                return '(GMAT TBD)'
            return f'ε = {abs(py_val - gmat_val) / abs(gmat_val) * 100:.3f} %'

        print(f'  {label:<34}  {"Mean Pass Duration":<26}  '
              f'{m["mean_pass_s"]:>9.1f} s   {_eps_str(m["mean_pass_s"], gref["mean_pass_s"])}')
        print(f'  {"" :<34}  {"Daily Contact Time":<26}  '
              f'{m["daily_min"]:>8.2f} min   {_eps_str(m["daily_min"], gref["daily_min"])}')
        print(f'  {"" :<34}  {"Peak Doppler Shift":<26}  '
              f'±{m["peak_doppler_khz"]:>7.2f} kHz   {_eps_str(m["peak_doppler_khz"], gref["peak_doppler_khz"])}')
        print()
    print(sep)
    print('  ↑ Copy these values into the Python column of Table 2.')
    if any(GMAT_REF[o][k] is None for o in GMAT_REF for k in GMAT_REF[o]):
        print('  ↑ Run GMAT scripts in gmat/ to populate the GMAT reference column.')
    print(sep)
    print()


# ── Figure ─────────────────────────────────────────────────────────────────────

def _plot_figure(python_metrics, epsilon):
    """
    Two-panel figure:
      Left  — Normalized comparison bars (Python vs GMAT; Python = 1.0).
               Shown only when at least one GMAT value is available.
      Right — ε residuals bar chart with 0.11% threshold line.
    When no GMAT data exist, only the right panel is drawn (Python-only mode).
    """
    gmat_any = any(
        GMAT_REF[orb][mk] is not None
        for orb in ('LEO', 'SSO')
        for mk in ('mean_pass_s', 'daily_min', 'peak_doppler_khz')
    )

    metric_keys = [
        ('LEO', 'mean_pass_s'),
        ('LEO', 'daily_min'),
        ('LEO', 'peak_doppler_khz'),
        ('SSO', 'mean_pass_s'),
        ('SSO', 'daily_min'),
        ('SSO', 'peak_doppler_khz'),
    ]
    x_labels = [
        'Pass Dur.\n(LEO)', 'Daily Cont.\n(LEO)', 'Peak Dopp.\n(LEO)',
        'Pass Dur.\n(SSO)', 'Daily Cont.\n(SSO)', 'Peak Dopp.\n(SSO)',
    ]
    bar_colors = ['#1f77b4'] * 3 + ['#ff7f0e'] * 3

    # ── Layout ─────────────────────────────────────────────────────────
    if gmat_any:
        fig, (ax_cmp, ax_eps) = plt.subplots(1, 2, figsize=(14, 6))
    else:
        fig, ax_eps = plt.subplots(1, 1, figsize=(8, 6))
        ax_cmp = None

    x = np.arange(6)

    # ── Right panel: ε residuals ────────────────────────────────────────
    for i, (orb, mk) in enumerate(metric_keys):
        ep = epsilon[orb][mk]
        if ep is not None:
            ax_eps.bar(x[i], ep, color=bar_colors[i], alpha=0.85,
                       edgecolor='black', linewidth=0.5, zorder=3)
            ax_eps.text(x[i], ep + 0.004,
                        f'{ep:.3f}%', ha='center', va='bottom', fontsize=10)
        else:
            ax_eps.bar(x[i], EPS_THRESHOLD * 0.4,
                       color='lightgray', hatch='//', edgecolor='darkgray',
                       linewidth=0.5, zorder=3)
            ax_eps.text(x[i], EPS_THRESHOLD * 0.42,
                        'TBD', ha='center', va='bottom', fontsize=9, color='gray')

    ax_eps.axhline(EPS_THRESHOLD, color='red', linestyle='--', linewidth=1.5,
                   label=f'Threshold  ε = {EPS_THRESHOLD} %', zorder=4)
    ax_eps.set_xticks(x)
    ax_eps.set_xticklabels(x_labels, fontsize=11)
    ax_eps.set_ylabel('Absolute Platform Discrepancy  ε (%)', fontsize=13)
    ax_eps.set_ylim(0.0, EPS_THRESHOLD * 1.7)
    ax_eps.legend(fontsize=12)
    ax_eps.grid(True, axis='y', linestyle=':', alpha=0.6, zorder=0)
    ax_eps.set_title('Platform Residuals', fontsize=13)

    # Colour x-tick labels to match orbit groups
    for i, lbl in enumerate(ax_eps.get_xticklabels()):
        lbl.set_color('#1f77b4' if i < 3 else '#d62728')

    # ── Left panel: normalised comparison (Python = 1) ──────────────────
    if ax_cmp is not None:
        w = 0.35
        py_vals   = np.ones(6)
        gmat_vals = np.array([
            GMAT_REF[orb][mk] / python_metrics[orb][mk]
            if GMAT_REF[orb][mk] is not None else np.nan
            for (orb, mk) in metric_keys
        ], dtype=float)

        ax_cmp.bar(x - w / 2, py_vals, w,
                   label='Python / Skyfield', color='#2ca02c', alpha=0.85,
                   edgecolor='black', linewidth=0.5)

        # Draw GMAT bars; hatched where no value
        for i, gv in enumerate(gmat_vals):
            if not np.isnan(gv):
                ax_cmp.bar(x[i] + w / 2, gv, w,
                           color='#9467bd', alpha=0.85,
                           edgecolor='black', linewidth=0.5)
            else:
                ax_cmp.bar(x[i] + w / 2, 1.0, w,
                           color='lightgray', hatch='//',
                           edgecolor='darkgray', linewidth=0.5)
                ax_cmp.text(x[i] + w / 2, 1.001,
                            'TBD', ha='center', va='bottom', fontsize=9, color='gray')

        ax_cmp.axhline(1.0, color='black', linestyle=':', linewidth=0.8)
        ax_cmp.set_xticks(x)
        ax_cmp.set_xticklabels(x_labels, fontsize=11)
        ax_cmp.set_ylabel('Normalised Value  (Python = 1.0)', fontsize=13)
        ax_cmp.set_ylim(0.998, 1.002)
        ax_cmp.set_title('Python vs NASA GMAT', fontsize=13)
        ax_cmp.grid(True, axis='y', linestyle=':', alpha=0.6)

        leo_patch  = mpatches.Patch(color='#1f77b4', label='LEO group')
        sso_patch  = mpatches.Patch(color='#d62728',  label='SSO group')
        py_patch   = mpatches.Patch(color='#2ca02c', label='Python / Skyfield')
        gmat_patch = mpatches.Patch(color='#9467bd', label='NASA GMAT')
        ax_cmp.legend(handles=[py_patch, gmat_patch, leo_patch, sso_patch],
                      fontsize=11, ncol=2)

        for i, lbl in enumerate(ax_cmp.get_xticklabels()):
            lbl.set_color('#1f77b4' if i < 3 else '#d62728')

    plt.tight_layout()
    outpath = os.path.join(_HERE, 'figure-06.png')
    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    print(f'  Figure saved → figure-06.png')
    plt.show()


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    # Load satellites
    sats = {
        'LEO': _load_tle('tle_leo.txt'),
        'SSO': _load_tle('tle_sso.txt'),
    }

    # Compute Python metrics
    print('\n  Computing Python/Skyfield metrics …')
    python_metrics = {k: compute_python_metrics(v) for k, v in sats.items()}

    # Auto-populate GMAT_REF from output files if present
    for orb in ('LEO', 'SSO'):
        updates = _try_load_gmat(orb.lower())
        for key, val in updates.items():
            if GMAT_REF[orb][key] is None:   # don't overwrite hard-coded values
                GMAT_REF[orb][key] = val

    # Print console table
    _print_table(python_metrics)

    # Compute ε
    epsilon = {}
    for orb in ('LEO', 'SSO'):
        epsilon[orb] = {}
        for mk in ('mean_pass_s', 'daily_min', 'peak_doppler_khz'):
            py_val  = python_metrics[orb][mk]
            gm_val  = GMAT_REF[orb][mk]
            if gm_val is not None and gm_val != 0.0:
                epsilon[orb][mk] = abs(py_val - gm_val) / abs(gm_val) * 100.0
            else:
                epsilon[orb][mk] = None

    # Generate figure
    _plot_figure(python_metrics, epsilon)


if __name__ == '__main__':
    main()
