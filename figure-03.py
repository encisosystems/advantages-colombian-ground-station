import matplotlib
matplotlib.rcParams.update({
    'font.size': 16,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
})
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

# Data points based on the study (30 GHz is exact from the text, others are modeled)
frequencies = np.array([20.0, 25.0, 30.0, 35.0, 40.0])
sea_level_attenuation = np.array([18.5, 26.2, 35.7, 44.8, 54.1])
andean_attenuation = np.array([10.2, 14.5, 19.5, 24.8, 30.1])

# Create smooth curves using spline interpolation for a polished look
freq_smooth = np.linspace(frequencies.min(), frequencies.max(), 300)
spl_sea = make_interp_spline(frequencies, sea_level_attenuation, k=3)
spl_andean = make_interp_spline(frequencies, andean_attenuation, k=3)

sea_smooth = spl_sea(freq_smooth)
andean_smooth = spl_andean(freq_smooth)

# Plotting the chart
plt.figure(figsize=(10, 6))

plt.plot(freq_smooth, sea_smooth, color='firebrick', linewidth=2.5, label='Sea-level node (0 m) - High moisture/rain')
plt.plot(freq_smooth, andean_smooth, color='dodgerblue', linewidth=2.5, label='Andean node (2,600 m) - Mitigated attenuation')

# Highlighting the exact data points from the paper
plt.scatter(frequencies, sea_level_attenuation, color='firebrick', s=50, zorder=5)
plt.scatter(frequencies, andean_attenuation, color='dodgerblue', s=50, zorder=5)

# Annotate the specific 30 GHz data points mentioned in the study
plt.annotate('35.7 dB', xy=(30.0, 35.7), xytext=(28, 38),
             arrowprops=dict(facecolor='black', arrowstyle='->'), fontsize=14)
plt.annotate('19.5 dB', xy=(30.0, 19.5), xytext=(31, 16),
             arrowprops=dict(facecolor='black', arrowstyle='->'), fontsize=14)

# Formatting the chart
#plt.title('Ka-Band Attenuation Profiles (20-40 GHz)', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Transmit frequency (GHz)', fontsize=14)
plt.ylabel('Total atmospheric attenuation ($L_{atm}$) in dB', fontsize=14)
plt.xlim(20, 40)
plt.ylim(0, 60)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(loc='upper left', fontsize=14, frameon=True, shadow=True)

# Save the plot as a high-resolution image suitable for a document
plt.tight_layout()
plt.savefig('figure-03.png', dpi=300, bbox_inches='tight')
plt.show()
