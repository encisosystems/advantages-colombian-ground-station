# Archived TLE Snapshots

## Source

The Two-Line Element (TLE) sets in this directory were retrieved from the
[CelesTrak](https://celestrak.org) public orbital catalog, which aggregates
General Perturbations (GP) tracking data produced by the United States Space
Force (USSF) 18th Space Defense Squadron.  Rather than pulling live entries at
run-time, these specific snapshots were frozen on **2026-07-08** and committed
permanently to the repository.  This guarantees that the SGP4 propagation
routine inside `simulation.py` always starts from identical initial states,
allowing independent researchers to reproduce the exact visibility timelines,
Doppler profiles, and link-latency results presented in the study.

---

## Files

| File | Satellite | NORAD ID | Orbit type | Inclination | Representative of |
|------|-----------|----------|------------|-------------|-------------------|
| `tle_leo.txt` | ISS (ZARYA) | 25544 | LEO (~400 km) | 51.63° | Mid-inclination low Earth orbit |
| `tle_meo.txt` | NAVSTAR 65 (USA 213) | 36585 | MEO (~20 200 km) | 54.27° | GPS Block IIF medium Earth orbit |
| `tle_geo.txt` | AMAZONAS 3 | 39078 | GEO (~35 786 km) | 0.06° | Geostationary orbit — 61°W arc, ~74° elevation from Paipa |
| `tle_sso.txt` | LANDSAT 8 | 39084 | SSO (~705 km) | 98.23° | Sun-synchronous polar orbit |

---

## TLE Epoch and Propagation Notes

All four TLEs carry epochs on or near **day 189 of 2026** (≈ 2026-07-08 UTC),
which is the date the snapshots were archived.  The 30-day simulation window
used in `simulation.py` spans **2026-05-01 to 2026-05-31**.  When SGP4
back-propagates an element set by roughly 60 days, position errors grow
(particularly for high-drag objects such as ISS); however, the orbital
geometry — inclination, ground-track repeat, and pass-elevation distribution —
remains representative.  For highest-fidelity reconstruction of the exact
May 2026 contact windows, substitute element sets whose epochs fall within the
[2026-05-01, 2026-05-31] interval from the CelesTrak archive.

---

## TLE Format Reference

Each `.txt` file follows the standard three-line element set (3LE) format:

```
Line 0   Satellite name         (24 characters, right-padded with spaces)
Line 1   1 NNNNNUCCCCCCCC ...   (69 characters + newline)
Line 2   2 NNNNN ...            (69 characters + newline)
```

These files are consumed directly by the
[Skyfield](https://rhodesmill.org/skyfield/) `EarthSatellite` constructor and
are compatible with any SGP4/SDP4 implementation that accepts the 3LE format.

---

## Orbit-Type Definitions

| Orbit | Altitude range | Typical inclination | Notes |
|-------|---------------|---------------------|-------|
| LEO | 200 – 2 000 km | 0° – 98° | Orbital period ~90 – 127 min |
| MEO | 2 000 – 35 786 km | 0° – 65° | GPS/GNSS constellations ~55° |
| GEO | ≈ 35 786 km | < 1° (operational) | Fixed sky position; orbital period ≈ 24 h |
| SSO | 500 – 900 km | 96° – 100° | Dawn-dusk sun-synchronous repeat ground track |

---

## Citation

If you use these element sets in derived work, please cite both CelesTrak and
the USSF 18th Space Defense Squadron as the primary tracking data sources:

> Kelso, T. S. (2026). *CelesTrak GP Element Sets*.  
> https://celestrak.org · Accessed 2026-07-08.
