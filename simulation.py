import argparse
import os

import matplotlib
if os.environ.get('MPLBACKEND') is None and os.environ.get('DISPLAY') is None:
    matplotlib.use('Agg')

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


def parse_args():
    parser = argparse.ArgumentParser(description='Orbital visibility simulation with optional Monte Carlo analysis.')
    parser.add_argument('--mc-trials', type=int, default=0,
                        help='Number of Monte Carlo trials to run. 0 disables Monte Carlo.')
    parser.add_argument('--mc-seed', type=int, default=42,
                        help='Random seed for reproducible Monte Carlo sampling.')
    parser.add_argument('--phase-range-hours', type=float, default=24.0,
                        help='Range of random orbital phase offsets to sample, in hours.')
    return parser.parse_args()


# 2. Load timescale
ts = load.timescale()


def load_tle(filepath):
    """Parse a 3-line element set file and return an EarthSatellite."""
    with open(filepath) as fh:
        lines = [ln.rstrip('\n') for ln in fh if ln.strip()]
    return EarthSatellite(lines[1], lines[2], lines[0].strip(), ts)


def compute_contact_metrics(sat, ground_station, t, min_elevation):
    """Compute elevation, visibility mask, and contact minutes for one deterministic realization."""
    alt, _az, _dist = (sat - ground_station).at(t).altaz()
    visible = alt.degrees > min_elevation
    contact_min = int(np.sum(visible))
    return alt, visible, contact_min


def run_deterministic_simulation(satellites, ground_station, t, min_elevation):
    """Run the baseline single deterministic pass for each satellite."""
    results = {}
    for label, sat in satellites.items():
        alt, visible, contact_min = compute_contact_metrics(sat, ground_station, t, min_elevation)
        results[label] = {'alt': alt, 'visible': visible, 'contact_min': contact_min}
    return results


def compute_latency_proxy(contact_minutes, baseline_latency_minutes=100.0, target_latency_minutes=54.2, contact_scale_minutes=600.0):
    """Return a simple latency proxy from contact minutes using a linear reduction model."""
    contact_ratio = np.clip(contact_minutes / float(contact_scale_minutes), 0.0, 1.0)
    reduction_fraction = (baseline_latency_minutes - target_latency_minutes) / baseline_latency_minutes
    latency_minutes = baseline_latency_minutes * (1.0 - reduction_fraction * contact_ratio)
    return float(np.clip(latency_minutes, target_latency_minutes, baseline_latency_minutes))


def run_monte_carlo_simulation(satellites, ground_station, t, min_elevation, trials, seed, phase_range_hours):
    """Run a Monte Carlo sweep over random orbital phase offsets and summarize contact times."""
    rng = np.random.default_rng(seed)
    phase_range_seconds = float(phase_range_hours) * 3600.0
    contact_histories = {label: [] for label in satellites}

    for _ in range(int(trials)):
        phase_offset_seconds = rng.uniform(0.0, phase_range_seconds)
        trial_t = t + phase_offset_seconds
        for label, sat in satellites.items():
            _alt, _visible, contact_min = compute_contact_metrics(sat, ground_station, trial_t, min_elevation)
            contact_histories[label].append(contact_min)

    summary = {}
    for label, values in contact_histories.items():
        values_array = np.asarray(values, dtype=float)
        latency_values = np.array([
            compute_latency_proxy(contact_minutes=contact_min)
            for contact_min in values_array
        ])
        summary[label] = {
            'values': values_array,
            'mean': float(values_array.mean()),
            'std': float(values_array.std(ddof=0)),
            'ci_low': float(np.percentile(values_array, 2.5)),
            'ci_high': float(np.percentile(values_array, 97.5)),
            'latency_mean': float(latency_values.mean()),
            'latency_p95': float(np.percentile(latency_values, 95.0)),
            'latency_reduction_pct': float((100.0 - latency_values.mean()) / 100.0 * 100.0),
        }

    return summary


def plot_baseline_visibility(results, t, min_elevation):
    """Plot the first visible pass for each satellite in a 2x2 panel."""
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

        continuously_visible = (pass_indices[0] == 0 and np.sum(visible) > 0.9 * len(t))
        if continuously_visible:
            end_idx = min(1440, len(t))
            pass_t = t[:end_idx]
            pass_alt = alt_deg[:end_idx]
            subtitle = '(first 24 h — continuously visible)'
        else:
            i_start = pass_indices[0]
            i_end = i_start
            while (i_end + 1 < len(pass_indices) and pass_indices[i_end + 1] == pass_indices[i_end] + 1):
                i_end += 1
            pass_t = t[i_start:i_end + 1]
            pass_alt = alt_deg[i_start:i_end + 1]
            subtitle = f'(first pass — {len(pass_t)} min)'

        ax.plot(pass_t.utc_datetime(), pass_alt, color=color, linewidth=2)
        ax.axhline(y=min_elevation, color='gray', linestyle='--', linewidth=1, label=f'{min_elevation:.0f}° mask')
        ax.set_title(f'{label}\n{subtitle}', fontsize=11)
        ax.set_xlabel('Time (UTC)', fontsize=11)
        ax.set_ylabel('Elevation (°)', fontsize=11)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.4)
        ax.tick_params(axis='x', rotation=25)

    plt.suptitle('Tracking Geometry: First Visible Pass — Paipa GS (5.78°N, 73.12°W, 2 600 m)', fontsize=13, y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    _fmt = os.environ.get('FIGURE_FORMAT', 'png')
    plt.savefig(f'simulation.{_fmt}', dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_monte_carlo_summary(summary):
    """Plot the Monte Carlo distributions of contact time for each satellite."""
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = list(summary.keys())
    values = [summary[label]['values'] for label in labels]
    positions = np.arange(len(labels))

    bp = ax.boxplot(values, patch_artist=True, vert=True)
    for box in bp['boxes']:
        box.set(facecolor='#4c78a8', alpha=0.7)
    for whisker in bp['whiskers']:
        whisker.set(color='#4c78a8')
    for cap in bp['caps']:
        cap.set(color='#4c78a8')
    for median in bp['medians']:
        median.set(color='#f58518', linewidth=2)

    ax.set_title('Monte Carlo contact-time distribution (contact minutes / 30 days)')
    ax.set_ylabel('Contact time (min / 30 days)')
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=15, ha='right')
    ax.grid(axis='y', alpha=0.3)

    _fmt = os.environ.get('FIGURE_FORMAT', 'png')
    plt.tight_layout()
    plt.savefig(f'simulation_mc_summary.{_fmt}', dpi=300, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    args = parse_args()

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

    results = run_deterministic_simulation(satellites, colombia_gs, t, min_elevation)
    for label, res in results.items():
        print(f"  {label:<24}  {res['contact_min']:>28}")

    plot_baseline_visibility(results, t, min_elevation)

    if args.mc_trials > 1:
        print(f"\nMonte Carlo summary ({args.mc_trials} trials, seed={args.mc_seed})")
        print('-' * 74)
        mc_summary = run_monte_carlo_simulation(
            satellites,
            colombia_gs,
            t,
            min_elevation,
            args.mc_trials,
            args.mc_seed,
            args.phase_range_hours,
        )
        for label, summary in mc_summary.items():
            print(
                f"  {label:<24}  mean={summary['mean']:>8.1f}  std={summary['std']:>7.1f}  "
                f"95% CI [{summary['ci_low']:>6.1f}, {summary['ci_high']:>6.1f}]  "
                f"latency≈{summary['latency_mean']:>5.1f} min (p95 {summary['latency_p95']:>5.1f}, "
                f"reduction {summary['latency_reduction_pct']:>4.1f}%)"
            )
        plot_monte_carlo_summary(mc_summary)
