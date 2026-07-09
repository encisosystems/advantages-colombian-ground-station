import matplotlib
matplotlib.rcParams.update({
    'font.size': 14,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
})
import matplotlib.pyplot as plt
import numpy as np


# Ten discrete inclination cases evaluated at 10° steps over a 30-day propagation cycle.
# No interpolation is applied; data paths are mapped directly to preserve physical fidelity.
x = np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90])

# Baseline (Polar-Only) network: Svalbard (78° N) and Troll (72° S).
# Total visibility gap (0 min/day) for low-inclination orbits (0° ≤ i ≤ 30°).
y_base = np.array([0, 0, 0, 0, 18, 55, 80, 100, 110, 120])

# Augmented (Polar + Colombia) network.
# Provides ~97.5 min/day across ~10 passes for equatorial missions (0° ≤ i ≤ 30°).
y_aug = np.array([97.5, 97.5, 97.5, 97.5, 82, 70, 78, 100, 112, 125])

# Initialize the plot
plt.figure(figsize=(8, 5))

# Plot direct line segments with markers — no interpolation
plt.plot(x, y_base, label='Baseline (Polar-Only)', color='blue', linestyle='--',
         linewidth=2, marker='o', markersize=6, zorder=5)
plt.plot(x, y_aug, label='Augmented (Polar + Colombia)', color='green',
         linewidth=2, marker='o', markersize=6, zorder=5)

# Format the chart (Axes, limits, legend, and grid)
plt.xlabel('Orbital Inclination (°)')
plt.ylabel('Daily Contact Time (Minutes)')
plt.xlim(0, 90)
plt.ylim(0, 140)
plt.xticks(x)
plt.legend()
plt.grid(True, linestyle=':', alpha=0.7)

# Adjust layout and display the plot
plt.tight_layout()
plt.savefig('figure-02.png', dpi=300, bbox_inches='tight')
plt.show()

