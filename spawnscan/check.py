from __future__ import division
import json
import spawnscan.stepcalculator as stepcalc


SCAN_TIME = 4.5  # Time for a single worker to scan a single point
M2_TO_KM2 = 1 / (stepcalc.M_IN_KM ** 2)

with open('config.json') as file:
    config = json.load(file)


def calcwork(radius=100, error=0.05):
    totalwork = 0
    area = 0
    for rect in config['work']:
        area += stepcalc.approx_area(*rect) * M2_TO_KM2
        totalwork += len(
            stepcalc.hex_grid(*rect, radius=radius, error=error)
        )
    print(
        (
            'Total of {} steps covering {} km^2, approx {} seconds for scan'
        ).format(
            totalwork, area, totalwork / (SCAN_TIME * len(config['users']))
        )
    )
