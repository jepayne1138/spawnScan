from __future__ import division
import math


EARTH_RADIUS = 6371  # In meters
M_IN_KM = 1000
DEGREES_OF_LAT = 180


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


def delta_longitude(distance, lat):
    """Calculate the difference in latitude to move the desired distance

    Args:
      distance (float): Desired meridian distance (in meters)
      lat (float): Latitude at which to perform the calculation.
    """
    return (
        (DEGREES_OF_LAT * distance) /
        (EARTH_RADIUS * M_IN_KM * math.pi * math.cos(lat))
    )
