import math


def gps_to_xy(lat, lon, origin_lat, origin_lon):
    """
    Convert GPS coordinates to local metres.

    X = east/west metres
    Y = north/south metres
    """

    lat_scale = 111320

    lon_scale = 111320 * math.cos(
        math.radians(origin_lat)
    )

    x = (lon - origin_lon) * lon_scale
    y = (lat - origin_lat) * lat_scale

    return x, y