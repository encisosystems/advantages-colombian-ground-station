# Advantages of an Equatorial Ground Station in Colombia

**Abstract:** As multi-orbit satellite constellations and deep space exploration missions proliferate, terrestrial ground segments face significant coverage gaps due to a historical "polar-first" infrastructure bias. This legacy architecture results in critical blind spots for low-inclination orbits and substantial latency penalties during equatorial crossings. This paper evaluates the strategic advantages of establishing an equatorial ground station in Colombia, leveraging both its $0°$ latitude proximity and the high-altitude topography of the Andes. Using high-fidelity orbital simulations, we demonstrate that a Colombian node transforms network performance by increasing contact time for low-inclination missions from zero to an average of **97.5 minutes per day**.

Furthermore, the station provides a symmetric tracking geometry that yields a **27% smoother Doppler rate** ($\dot{f}_D$), significantly reducing the complexity of ground-based digital signal processing. Despite high tropical precipitation, we prove that the **2,600-meter altitude** successfully mitigates rain fade, maintaining a robust **16.9 dB link margin** in the Ka-band at 99.9% availability. These findings confirm that a Colombian node can slash system latency by **50%** for Sun-Synchronous Orbits (SSO), reducing wait times from 100 to 50 minutes. To support open science and ensure independent verification, the complete simulation framework and visualization suite used in this study are provided in a public, open-access repository. This study concludes that an integrated equatorial node is essential for closing the global coverage gap and providing a high-throughput egress point for next-generation deep space tracking and multi-orbit telemetry.

**Key Words:** Equatorial Ground Stations, Andean High-Altitude Topography, Ka-Band Rain Fade Mitigation, Doppler Shift Symmetry, Multi-Orbit (LEO/MEO/GEO) Tracking, Latency Reduction, Computational Reproducibility.

---

## Repository Structure

```
.
├── figure-01.py        # Global ground track map with LEO coverage footprint
├── figure-02.py        # Daily contact time vs. orbital inclination (baseline vs. augmented network)
├── figure-03.py        # Ka-band atmospheric attenuation profiles (20–40 GHz)
├── figure-04.py        # Doppler shift curves at 30 GHz (polar vs. equatorial geometry)
├── figure-05.py        # S4 scintillation index map — Colombian Andes (solar maximum)
├── figure-06.py        # Cross-platform validation: Python/Skyfield vs. NASA GMAT (Table 2)
├── simulation.py       # Core SGP4 satellite tracking and visibility simulation
├── run_all.py          # Runs all figures sequentially
├── Makefile            # Convenience targets (see below)
├── requirements.txt    # Python dependencies
├── data/
│   ├── tle_leo.txt     # ISS (ZARYA) — LEO ~422 km, 51.6°
│   ├── tle_meo.txt     # NAVSTAR 65 — MEO ~20 200 km, 54.3°
│   ├── tle_geo.txt     # AMAZONAS 3 — GEO ~35 786 km, 0.06°
│   └── tle_sso.txt     # Landsat 8 — SSO ~701 km, 98.2°
└── gmat/
    ├── gmat_leo.script     # NASA GMAT script for LEO (ISS) validation
    ├── gmat_sso.script     # NASA GMAT script for SSO (Landsat 8) validation
    ├── contacts_leo.txt    # GMAT-generated contact events — LEO
    ├── contacts_sso.txt    # GMAT-generated contact events — SSO
    ├── rangedata_leo.txt   # GMAT range/Doppler data — LEO
    └── rangedata_sso.txt   # GMAT range/Doppler data — SSO
```

All TLE snapshots were frozen on **2026-07-08** to guarantee reproducible SGP4 propagation results. See [data/README.md](data/README.md) for details.

---

## Installation

```bash
conda install -y -c conda-forge cartopy
pip install -r requirements.txt
```

Or use the Makefile shortcut:

```bash
make install
```

---

## Running the Figures

Generate all figures at once:

```bash
make                # default target (same as: make all)
make all            # build all figures
make figures        # run all figure scripts via run_all.py
```

Generate individual figures:

```bash
make figure-01      # Ground station visibility map
make figure-02      # Pass duration vs elevation mask
make figure-03      # Ka-band atmospheric attenuation
make figure-04      # Doppler shift profile
make figure-05      # Coverage map
make figure-06      # Cross-platform validation
make simulation     # First-pass tracking geometry
make help           # Show all targets and usage
```

Output format is controlled by `FMT` (`png` by default):

```bash
make figures FMT=svg
make figure-06 FMT=eps
```

Each script saves a 300 dpi file in the selected format (e.g. `figure-0N.png`, `figure-0N.svg`, or `figure-0N.eps`) in the repository root. Remove all generated figure files with `make clean`.

---

## Cross-Platform Validation (figure-06)

`figure-06.py` independently verifies the Python/Skyfield (SGP4) results against NASA GMAT for three metrics over a 7-day window (2026-Jul-08 → 2026-Jul-15):

| Metric | Description |
|--------|-------------|
| Mean single-pass duration | seconds per pass |
| Cumulative daily contact time | minutes per day |
| Peak Doppler shift | kHz, Ka-band 30 GHz |

**To run with full GMAT comparison:**

1. Open `gmat/gmat_leo.script` and `gmat/gmat_sso.script` in [NASA GMAT](https://gmat.gsfc.nasa.gov/).
2. Run each script — output files are written to the `gmat/` directory.
3. Re-run `python figure-06.py` — it auto-parses the GMAT files and renders the two-panel comparison figure.

The pre-computed GMAT output files (`contacts_*.txt`, `rangedata_*.txt`) are already committed, so the full validation figure can be reproduced without a GMAT installation.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
