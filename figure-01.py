import matplotlib
matplotlib.rcParams.update({
    'font.size': 16,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
})
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from matplotlib.offsetbox import AnchoredText
import matplotlib.ticker as mticker # Import mticker

# Function to generate a typical satellite ground track
def generate_ground_track(inclination, nodes_per_orbit=200):
    # A simplified sinusoidal-like path for illustration
    time = np.linspace(0, 1, nodes_per_orbit)
    lons = np.linspace(-180, 180, nodes_per_orbit)
    # Sinusoid with inclination amplitude, shifted
    lats = inclination * np.sin(time * 2 * np.pi)
    return lons, lats

# Define station locations and characteristics
station_data = {
    'Svalbard': {'lat': 78.0, 'lon': 15.0, 'no_signal': True, 'text_offset': (2, 2)},
    'Troll': {'lat': -72.0, 'lon': 2.5, 'no_signal': True, 'text_offset': (2, 2)}
}

# Define Colombia Paipa Node (based on visual center)
node_loc = {'lat': 5.78, 'lon': -73.11}

# Create figure and axes with PlateCarree projection (like the original)
fig = plt.figure(figsize=(20, 12), dpi=100)
ax = plt.axes(projection=ccrs.PlateCarree())

# Add map features
ax.add_feature(cfeature.LAND, facecolor='#E0E0E0') # Light gray land
ax.add_feature(cfeature.OCEAN, facecolor='white')
ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linestyle='-', edgecolor='black', linewidth=0.2)

# Set map limits
ax.set_extent([-180, 180, -90, 90], crs=ccrs.PlateCarree())

# --- Add Shaded Coverage and Blind Spot Regions ---

# LEO Coverage Band (+28°)
ax.fill_between([-180, 180], [-28, -28], [28, 28],
                color='#B2E0F7', alpha=0.5,
                edgecolor='none', label='LEO Coverage Band')

# Polar Station Blind Spots (Outside coverage band)
ax.fill_between([-180, 180], [-90, -90], [-28, -28],
                color='#C0C0C0', alpha=0.3,
                edgecolor='none', label='Polar Blind Spot')
ax.fill_between([-180, 180], [28, 28], [90, 90],
                color='#C0C0C0', alpha=0.3,
                edgecolor='none', label='Polar Blind Spot')


# --- Add Node Coverage Footprint ---

# Geodetically accurate visibility footprint projected onto the equirectangular map.
# Derived from line-of-sight geometry: h = 1,000 km altitude, epsilon = 10 deg elevation mask.
# rho (nadir angle): sin(rho) = R_E * cos(eps) / (R_E + h)
# eta (geocentric angular radius): eta = 90 deg - eps - rho
R_E = 6371.0       # km, mean Earth radius
h_sat = 1000.0     # km, satellite altitude
elev_min = np.radians(10.0)  # minimum elevation angle
rho = np.arcsin(R_E * np.cos(elev_min) / (R_E + h_sat))  # nadir angle
eta = np.pi / 2.0 - elev_min - rho  # geocentric angular radius of coverage footprint

lat0 = np.radians(node_loc['lat'])
lon0 = np.radians(node_loc['lon'])
azimuths = np.linspace(0, 2 * np.pi, 361)
fp_lats_rad = np.arcsin(
    np.sin(lat0) * np.cos(eta) + np.cos(lat0) * np.sin(eta) * np.cos(azimuths)
)
fp_lons_rad = lon0 + np.arctan2(
    np.sin(azimuths) * np.sin(eta) * np.cos(lat0),
    np.cos(eta) - np.sin(lat0) * np.sin(fp_lats_rad)
)
fp_lats = np.degrees(fp_lats_rad)
fp_lons = np.degrees(fp_lons_rad)

ax.fill(fp_lons, fp_lats,
        facecolor='#9E9E9E', edgecolor='black', alpha=0.5,
        transform=ccrs.PlateCarree())
# Label for the node
ax.text(node_loc['lon'] + 27, 23,
        'COLOMBIAN NODE\nCOVERAGE FOOTPRINT\n(h=1,000 km, \u03b5=10\u00b0)',
        fontsize=14, fontweight='bold', va='bottom', ha='left')


# --- Add Ground Tracks ---
track_lons, track_lats = generate_ground_track(28)
ax.plot(track_lons, track_lats, 'k--', linewidth=1, label='Typical Ground Track')

# Mark a node on the ground track (e.g., node near 0 lon)
# Find the index closest to 0 longitude
node_idx = np.abs(track_lons - (-20)).argmin() # Arbitrary node point near original
# The original has it near Venezuela.
# Let's find one near Colombia on the sinusoidal track
node_idx = np.abs(track_lats - node_loc['lat']).argmin()
# Shift it slightly to not be exactly at the same point
ax.scatter(track_lons[node_idx], track_lats[node_idx], s=10, color='black')


# --- Add Polar Ground Stations with Red Crosses Below ---

# Simplified station icon
station_icon = dict(marker='s', s=100, color='#3182CE', edgecolor='black', zorder=10) # Square station

# Create station markers
for name, data in station_data.items():
    ax.scatter(data['lon'], data['lat'], **station_icon, label='Polar Ground Station')

    # Place Red Cross BELOW the antenna
    # Offset by a constant number of degrees latitude
    cross_lat = data['lat'] - 4.0 # Adjust dy to place it clearly below

    # Plot large, bold red cross
    #ax.scatter(data['lon'], cross_lat, marker='x', s=250, color='red', linewidth=3, zorder=11, label='No Signal')

    # Add text label (e.g., station name) with offset
    # Text is anchored to the station icon, not the cross
    text_x, text_y = data['text_offset']
    ax.text(data['lon'] + text_x, data['lat'] + text_y, f"{name.upper()} ({int(abs(data['lat']))}°{ 'N)' if data['lat'] >= 0 else 'S)'}",
            fontsize=14, color='black', ha='left', va='bottom' if text_y > 0 else 'top', zorder=12)

# Add a specific Colombian Node mark
# The original node footprint center has a red X which is inside.
# Let's make it more generic. The node is at node_loc.
ax.scatter(node_loc['lon'], node_loc['lat'], marker='x', s=150, color='red', linewidth=2, zorder=10)


# --- Add All Text Boxes and Labels ---

# Title text boxes
# Text boxes on PlateCarree are easier to place by coordinates
ax.text(180, 35, 'POLAR GROUND STATION "BLIND SPOTS"\n(NO VISIBILITY FOR 28° INCLINATION LEO)',
        fontsize=14, fontweight='bold', ha='right', va='top', bbox=dict(boxstyle="square", fc="white", ec="black", lw=0.5))
ax.text(50, -37, 'POLAR GROUND STATION "BLIND SPOTS"\n(NO VISIBILITY FOR 28° INCLINATION LEO)',
        fontsize=14, fontweight='bold', ha='center', va='top', bbox=dict(boxstyle="square", fc="white", ec="black", lw=0.5))

ax.text(-155, 22, 'LEO CONSTELLATION\nCOVERAGE BAND\n(+28° INCLINATION)',
        fontsize=14, fontweight='bold', ha='center', va='bottom')

ax.text(-60, -22, 'TYPICAL SATELLITE\nGROUND TRACK\n(28° INCLINATION)',
        fontsize=14, color='black', ha='center', va='bottom')
ax.text(110, -3, 'TYPICAL SATELLITE\nGROUND TRACK\n(28° INCLINATION)',
        fontsize=14, color='black', ha='center', va='top')

ax.text(0, -85, 'POLAR NETWORKS:\nCONTINUOUS VISIBILITY FOR POLAR ORBITS,\nZERO VISIBILITY FOR LOW INCLINATION LEO',
        fontsize=14, fontweight='bold', ha='center', va='center', bbox=dict(boxstyle="square", fc="white", ec="black", lw=0.5))

# Lon/Lat labels
gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False,
                  linestyle=':', color='black', linewidth=0.2)
gl.top_labels = True
gl.right_labels = False
gl.bottom_labels = False
gl.ylabels_left = True
gl.xlocator = mticker.FixedLocator([-180, -120, -60, -40, -30, 0, 30, 60, 90, 120, 150])
gl.ylocator = mticker.FixedLocator([-90, -28, -10, 0, 10, 28, 30, 40, 90])
# Set explicit labels for consistency with image
gl.xformatter = mticker.FuncFormatter(lambda x, p: f"{int(abs(x))}°{ 'W' if x < 0 else 'E'}" if x !=0 else "0°")
gl.yformatter = mticker.FuncFormatter(lambda y, p: f"{int(abs(y))}°{ 'N' if y >= 0 else 'S'}")
gl.xlabel_style = {'size': 14, 'color': 'black'}
gl.ylabel_style = {'size': 14, 'color': 'black'}


# --- Add Inset Map for 3D Orbital Plane ---

inset_ax = fig.add_axes([0.05, 0.05, 0.2, 0.2], projection=ccrs.Orthographic(-60, 0))
inset_ax.add_feature(cfeature.LAND, facecolor='#E0E0E0')
inset_ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.3)
inset_ax.set_global()
# Draw coverage band as a filled region around the globe
inset_ax.fill_between(np.linspace(-180, 180, 100), -28, 28,
             color='#B2E0F7', alpha=0.7, transform=ccrs.PlateCarree())
inset_ax.gridlines(linestyle=':', linewidth=0.2) # Corrected line
# Text for inset
inset_ax.text(0.5, -0.1, '3D ORBITAL PLANE\n(SIDE VIEW)', transform=inset_ax.transAxes,
              fontsize=14, fontweight='bold', ha='center', va='top')


# --- Add Legend ---

# Create custom legend entries for simplicity
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# Legend items based on visual similarity and text
legend_elements = [
    mpatches.Patch(facecolor='#B2E0F7', edgecolor='none', alpha=0.5, label='Coverage band (+28°)'),
    mpatches.Patch(facecolor='#C0C0C0', edgecolor='none', alpha=0.3, label='Polar station "blind spots"\n(No visibility)'),
    mpatches.Patch(facecolor='#9E9E9E', edgecolor='black', alpha=0.5, label='Colombian node coverage'),
    Line2D([0], [0], color='black', linestyle='--', linewidth=1, label='LEO orbital ground track'),
    Line2D([0], [0], marker='s', color='#3182CE', markerfacecolor='#3182CE', markeredgecolor='black', markersize=8, linestyle='none', label='Polar ground station'),
    Line2D([0], [0], marker='x', color='red', markerfacecolor='red', markeredgecolor='red', markersize=10, markeredgewidth=2, linestyle='none', label='Colombian node')
]

ax.legend(handles=legend_elements, loc='lower right', frameon=True, fontsize=14,
          framealpha=1.0, facecolor='white', edgecolor='black', title_fontsize='small')

# Set final title
#fig.suptitle('Ground Station Line-of-Sight Visibility\nLow Inclination LEO Constellation', fontsize=16, fontweight='bold')

plt.savefig('figure-01.png', dpi=300, bbox_inches='tight')
plt.show()
