from __future__ import division
import json
import spawnscan.stepcalculator as stepcalc
from spawnscan.multiscan import THROTTLE


# TODO:  Estimating the time would be much better done by actually
# performing, say, 100 requests, timing it, and extrapolating results.
# This could also get thrown off though by log in times and possible
# login failures. Actual times ought to be faster.
# Also doesn't really properly take into account server throttling,
# basically just assumes that THROTTLE is properly set to align with
# server throttling in general.

SCAN_TIME = 0.22  # Time for a single worker to scan a single point ??
M2_TO_KM2 = 1 / (stepcalc.M_IN_KM ** 2)

with open('config.json') as file:
    config = json.load(file)


def calcwork(radius=100, error=0.05):
    totalwork = 0
    for rect in config['work']:
        totalwork += len(
            stepcalc.hex_grid(*rect, radius=radius, error=error)
        )
    return totalwork


def approx_total_area():
    return sum(
        [stepcalc.approx_area(*rect) for rect in config['work']]
    ) * M2_TO_KM2


def estimate_string(radius=100, error=0.05):
    totalwork = calcwork(radius, error)
    area = approx_total_area()
    return (
        (
            'Total of {} steps covering {} km^2, approx {} seconds for scan'
        ).format(
            totalwork, area, (totalwork * (SCAN_TIME + THROTTLE)) / len(config['users'])
        )
    )
