import numpy as np
import matplotlib.pyplot as plt
from skyfield.api import Topos, load, EarthSatellite

# 2. Load timescale and ephemeris data
ts = load.timescale()
# Set up a 30-day simulation window (e.g., May 2026)
t0 = ts.utc(2026, 5, 1)
t1 = ts.utc(2026, 5, 31)
# Generate time array at 1-minute intervals
t = ts.linspace(t0, t1, 43200)

# 3. Define Ground Station: Paipa, Colombia (WGS84)
# Utilizing the high-altitude Andean node parameters
colombia_gs = Topos(latitude_degrees=5.783333,
                    longitude_degrees=-73.117778,
                    elevation_m=2600.0)

# 4. Define Satellite using TLE (Two-Line Element)
# Example TLE for a low-inclination LEO satellite (~28.5 deg)
line1 = '1 20580U 90037B   26121.12345678  .00000100  00000-0  12345-4 0  9991'
line2 = '2 20580  28.5000 123.4567 0001234  45.6789 234.5678 15.12345678123456'
satellite = EarthSatellite(line1, line2, 'Low-Inclination LEO Demo', ts)

# 5. Calculate Slant Range and Elevation Geometry
# Computes the exact vector difference between GS and Satellite
difference = satellite - colombia_gs
topocentric = difference.at(t)
alt, az, distance = topocentric.altaz()

# 6. Determine Visibility (Contact Time)
# Assuming a minimum elevation angle of 10 degrees to avoid terrain masking/noise
min_elevation = 10.0
visible = alt.degrees > min_elevation

# Calculate total contact minutes over 30 days
visible_minutes = np.sum(visible)
print(f"Total contact time (minutes) over 30 days: {visible_minutes}")

# 7. Plot Elevation Angle for the First Visible Pass
pass_indices = np.where(visible)[0]
if len(pass_indices) > 0:
    first_pass_start = pass_indices[0]
    first_pass_end = first_pass_start
    # Find the end index of this specific pass
    while first_pass_end + 1 < len(pass_indices) and pass_indices[first_pass_end + 1] == pass_indices[first_pass_end] + 1:
        first_pass_end += 1

    pass_t = t[first_pass_start:first_pass_end+1]
    pass_alt = alt.degrees[first_pass_start:first_pass_end+1]

    plt.figure(figsize=(8, 4))
    plt.plot(pass_t.utc_datetime(), pass_alt, color='#1f77b4', linewidth=2)
    plt.title('Tracking Geometry: Elevation Angle During First Pass', fontsize=12)
    plt.xlabel('Time (UTC)', fontsize=10)
    plt.ylabel('Elevation (Degrees)', fontsize=10)
    plt.axhline(y=10, color='r', linestyle='--', label='10° Mask Angle')
    plt.legend()
    plt.grid(True, alpha=0.5)
    plt.show()
