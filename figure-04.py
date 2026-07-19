import os
import matplotlib
matplotlib.rcParams.update({
    'font.size': 16,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
})
import numpy as np
import matplotlib.pyplot as plt

# Time vector for a 10-minute pass (-300 to 300 seconds)
t = np.linspace(-300, 300, 500)

# Simplistic Doppler S-Curve generation using arctan for visual shape
# Scaled to match the document's maximum Doppler Shifts (kHz)
# Equatorial: smoother rate, max ~650 kHz
# Polar: steeper rate, max ~720 kHz
equatorial_shift = -650 * (2 / np.pi) * np.arctan(0.015 * t)
polar_shift = -720 * (2 / np.pi) * np.arctan(0.025 * t)

plt.figure(figsize=(10, 6))

# Plotting the curves
plt.plot(t, polar_shift, label='Polar node (78° N)',
         color='red', linestyle='--')
plt.plot(t, equatorial_shift, label='Equatorial node (0°)',
         color='blue', linewidth=2)

# Formatting the plot
#plt.title('Doppler Shift Complexity (30 GHz Ka-Band Downlink)', fontsize=14)
plt.xlabel('Time relative to maximum elevation (seconds)', fontsize=14)
plt.ylabel('Doppler frequency shift (kHz)', fontsize=14)
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=14)

# Annotating maximums
plt.annotate('Max 720 kHz', xy=(-250, 660), color='red')
plt.annotate('Max 650 kHz', xy=(-250, 400), color='blue')

plt.tight_layout()
_fmt = os.environ.get('FIGURE_FORMAT', 'png')
plt.savefig(f'figure-04.{_fmt}', dpi=300, bbox_inches='tight')
plt.show()
