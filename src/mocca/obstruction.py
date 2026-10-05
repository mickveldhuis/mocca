import numpy as np
from pytransform3d import transformations as pt

from mocca.aperture import Aperture
from mocca.metadata import DomeInfo
from mocca.raytracting import find_intersection, get_ray_intersection
from mocca.transformations import rot_z


@np.vectorize(signature="(p),(q),(),()->()")
def check_obstruction(
    point: np.ndarray, direction: np.ndarray, dome_az: float, dome_info: DomeInfo
) -> np.ndarray:
    """
    Checks whether an individual ray is blocked.

    :param point: ray origin
    :param ha: hour angle in degrees
    :param dec: declination in degrees
    :param dome_az: dome azimuth (clockwise convention)
    """
    is_blocked = True

    dome_radius = dome_info.dome_radius
    dome_extent = dome_info.dome_extent
    dome_slit_width = dome_info.dome_slit_width
    has_intersection, t = find_intersection(point, direction, dome_radius, dome_extent)

    if has_intersection:
        points = get_ray_intersection(point, direction, t)

        az_corrected = (
            dome_az - 180
        ) % 360  # Correction assuming the azimuth is zero at the South
        rot = rot_z(az_corrected)

        dummy = np.ones(points[0].size)
        pp = np.column_stack((points[0], points[1], points[2], dummy))

        product = pt.transform(rot, pp)

        r = dome_radius * np.sin(np.radians(15))  # TODO: document this magic angle!

        x_cond = -dome_slit_width / 2 < product[:, 0] < dome_slit_width / 2
        y_cond = -r < product[:, 1] < dome_radius

        is_ray_in_slit = points[2] > dome_extent and x_cond and y_cond

        is_blocked = not is_ray_in_slit

    return is_blocked


def calculate_obstruction(
    dome_az: float, ha: float, dec: float, aperture: Aperture, info: DomeInfo
) -> tuple[float, np.ndarray]:
    """
    Compute the % obstruction of the aperture by the dome.

    :param dome_az: dome azimuth (clockwise convention)
    :param ha: hour angle in degrees
    :param dec: declination in degrees
    :param aperture: telescope aperture
    """
    ray_origins = aperture.sample(ha, dec)
    pointing = aperture.direction(ha, dec)

    blocked = check_obstruction(ray_origins, pointing, dome_az, info)

    ratio = blocked[blocked].size / blocked.size

    return ratio, blocked
