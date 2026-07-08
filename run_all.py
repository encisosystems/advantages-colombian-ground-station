"""
Run all figures sequentially and save outputs as high-resolution PNGs.

Setup (run once):
    conda install -c conda-forge cartopy
    pip install skyfield scipy shapely matplotlib numpy
"""

import runpy
import sys
from pathlib import Path

figures = [
    'figure-01.py',
    'figure-02.py',
    'figure-03.py',
    'figure-04.py',
    'figure-05.py',
    'figure-06.py',
    'simulation.py',
]

root = Path(__file__).parent

for script in figures:
    path = root / script
    print(f'\n--- Running {script} ---')
    try:
        runpy.run_path(str(path), run_name='__main__')
        print(f'    Done.')
    except Exception as e:
        print(f'    ERROR: {e}', file=sys.stderr)

print('\nAll figures generated.')
