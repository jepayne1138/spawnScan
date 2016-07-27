from __future__ import division
import math


EARTH_RADIUS = 6371  # In meters
M_IN_KM = 1000
DEGREES_OF_LAT = 180
ALTITUDE = 0

# A little redundant, but I believe it illustrates the values best
HEX_INSCRIBED_RADIUS = (3 ** (1 / 2)) / 2  # One inscribed radius
HEX_LNG_RATIO = HEX_INSCRIBED_RADIUS * 2
HEX_LAT_RATIO = (3 / 2)  # Multiple hex radius by (3/2)
HEX_OFFSET_RATIO = HEX_LNG_RATIO / 2

# The start can be half a radius above the minimum latitude
# (otherwise we miss coverage below where the hexagons meet)
LAT_START_RATIO = (1 / 2)


# Rough ASCII example of hex steps
#
#   |---|  By 30/60/90 triangle, we see inscribed radius is root(3)/2 * R
#          As we need to double that for step size, we get root(3) * R
#
#  / \ / \
# |   |   |    --
#  \ / \ /      | Radius of one hex * half of radius of next = (3/2)*R
#   |   |      --
#    \ /
#
#   |-|  Offset of the bottom row is one inscribed radius
#        which we have determined to be (root(3)/2) * R
#
#  Hopefully this makes clear the added ratios for calculating the step
#  distances for maximal coverage


def meridian_distance(lat1, lat2):
    """Calculate the meridian distance between two latitudes

    Meridian distance is the distance between two points with the same
    longitude, but different latitudes.

    Meridian distance 'm' is given in terms of the delta latitude D by:
      m(D) = earth_radius * (pi/180) * delta_degrees

    Returns:
      float: Meridian distance (in meters)
    """
    delta_lat = abs(lat1 - lat2)
    return EARTH_RADIUS * M_IN_KM * math.radians(delta_lat)


def longitude_distance(lng1, lng2, lat):
    """Calculate the longitude distance between to longitudes

    Longitude distance is based on latitude, so by using the average
    latitude, we get a sufficiently accurate longitude distance for close
    enough longitude arguments.

    TODO: Perform check to make sure the longitude arguments aren't too
      far apart for accuracy.

    Given by:
      cos(avg_latitude) * earth_radius * (pi/180) * delta_degrees

    Args:
      lng1 (float): Starting longitude.
      lng2 (float): Ending longitude.
      lat (float): Latitude at which to calculate the longitude distance.
    """
    delta_lng = abs(lng1 - lng2)
    return EARTH_RADIUS * M_IN_KM * math.radians(delta_lng) * math.cos(lat)


def ave_latitude(lat1, lat2):
    return (abs(lat1) + abs(lat2)) / 2


def approx_area(lat1, lng1, lat2, lng2):
    """Calculate the approximate area of the bounded rectangle

    Returns:
      float: Approximate area in m^2
    """
    lat_dist = meridian_distance(lat1, lat2)
    lng_dist = longitude_distance(lng1, lng2, ave_latitude(lat1, lat2))
    return lat_dist * lng_dist


def delta_latitude(distance):
    """Calculate the difference in latitude to move the desired distance

    Args:
      distance (float): Desired meridian distance (in meters)
    """
    return (DEGREES_OF_LAT * distance) / (EARTH_RADIUS * M_IN_KM * math.pi)


def delta_longitude(distance, latitude):
    """Calculate the difference in latitude to move the desired distance

    Args:
      distance (float): Desired meridian distance (in meters)
      latitude (float): Latitude at which to perform the calculation.
    """
    return (
        (DEGREES_OF_LAT * distance) /
        (EARTH_RADIUS * M_IN_KM * math.pi * math.cos(latitude))
    )


def hex_lat_step_size(radius=100):
    return delta_latitude(radius * HEX_LAT_RATIO)


def hex_lng_step_size(radius=100, latitude=0):
    return delta_longitude(radius * HEX_LNG_RATIO, latitude=latitude)


def hex_lat_offset_size(radius=100):
    return radius * HEX_OFFSET_RATIO


def hex_grid(lat1, lng1, lat2, lng2, radius=100, error=0.05):
    """Return a list of points to cover bounded rectangle in hexagons

    Error is a percent value that all values will be shrunk by to create
    overlap that will reduce error chance.

    TODO: Correct for instance where lat or lng cross over a meridian, hence
          we cannot just increment a counter and multiply by step size.
    """
    error_modifier = 1 - error

    ave_lat = ave_latitude(lat1, lat2)
    hex_lat_step = hex_lat_step_size(radius) * error_modifier
    hex_lng_step = hex_lng_step_size(radius, ave_lat) * error_modifier
    hex_lng_offset = hex_lng_step / 2

    # Get upper and lower latitudes and longitudes from the bounding points
    lower_lat, upper_lat = sorted([lat1, lat2])
    lower_lng, upper_lng = sorted([lng1, lng2])

    point_lat = lower_lat + delta_latitude(radius * LAT_START_RATIO * error_modifier)
    point_lng = lower_lng

    scan_points = []
    offset = 0  # Offset toggles between one and zero to indicate offset row
    # TODO:  Document this better
    while point_lat < upper_lat:
        while point_lng < (upper_lng + ((1 - offset) * hex_lng_step)):
            scan_points.append((point_lat, point_lng, ALTITUDE))
            point_lng += hex_lng_step

        # When a longitude row is done, reset increment latitude by a step
        offset = 1 if not offset else 0  # Toggle offset
        point_lng = lower_lng + (offset * hex_lng_offset)
        point_lat += hex_lat_step

    return scan_points
