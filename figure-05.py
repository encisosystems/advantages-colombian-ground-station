import matplotlib
matplotlib.rcParams.update({
    'font.size': 16,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
})
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# 1. Setup geographic bounds for the Colombian Andes
lat_min, lat_max = -4, 13
lon_min, lon_max = -82, -66

# 2. Generate synthetic S4 Index data for Solar Max
# Higher values (0.6 - 1.0) represent strong scintillation
lons = np.linspace(lon_min, lon_max, 100)
lats = np.linspace(lat_min, lat_max, 100)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Simulate an intensification zone (EIA) near the magnetic equator
# S4 is often higher in the evening/night during Solar Max
s4_data = 0.2 + 0.6 * np.exp(-((lat_grid - 5)**2 / 20 + (lon_grid + 74)**2 / 100))
s4_data += np.random.normal(0, 0.05, s4_data.shape) # Add some noise
s4_data = np.clip(s4_data, 0, 1) # Keep index between 0 and 1

# 3. Create the plot
fig = plt.figure(figsize=(10, 8))
ax = plt.axes(projection=ccrs.PlateCarree())

# Add geographic features
ax.set_extent([lon_min, lon_max, lat_min, lat_max])
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)

# Plot S4 Index distribution
mesh = ax.pcolormesh(lon_grid, lat_grid, s4_data,
                     shading='gouraud', cmap='plasma',
                     transform=ccrs.PlateCarree())

# 4. Formatting and Labels
cbar = plt.colorbar(mesh, orientation='vertical', pad=0.05, shrink=0.7)
cbar.set_label('S4 Index (Amplitude Scintillation)')

#plt.title('S4 Index Distribution Map: Colombian Andes\nSimulated Solar Maximum Conditions',
#          fontsize=14, pad=20)
# Show labels on left and bottom only — right side is reserved for the colorbar
gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
gl.top_labels = False
gl.right_labels = False

plt.savefig('figure-05.png', dpi=300, bbox_inches='tight')
plt.show()
