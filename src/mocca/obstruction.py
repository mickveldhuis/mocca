import numpy as np
from pytransform3d import transformations as pt

from mocca.aperture import Aperture
from mocca.metadata import Metadata
from mocca.raytracting import find_intersection, get_ray_intersection
from mocca.transformations import rot_z


@np.vectorize(signature="(p),(q),(),()->()")
def check_blockage(
    point: np.ndarray, direction: np.ndarray, dome_az: float, metadata: Metadata
):
    """
    Checks whether an individual ray is blocked.

    Parameters
    ----------

    point (3-vector): ray origin
    ha (float): hour angle in degrees
    dec (float): declination in degrees
    dome_az (float): dome azimuth (clockwise convention)
    """
    is_blocked = True

    dome_radius = metadata.dome_radius
    dome_extent = metadata.dome_extent
    dome_slit_width = metadata.dome_slit_width
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

        r = dome_radius * np.sin(np.radians(15))

        x_cond = -dome_slit_width / 2 < product[:, 0] < dome_slit_width / 2
        y_cond = -r < product[:, 1] < dome_radius

        is_ray_in_slit = points[2] > dome_extent and x_cond and y_cond

        is_blocked = not is_ray_in_slit

    return is_blocked


def calculate_obstruction(
    aperture: Aperture, ha: float, dec: float, dome_az: float, metadata: Metadata
):
    """
    Compute the % obstruction of the aperture by the dome.

    Parameters
    ----------

    ha (float): hour angle in degrees
    dec (float): declination in degrees
    dome_az (float): dome azimuth (clockwise convention)
    plot_result (bool): if True, a plot with the sampled aperture and obstructed points will be shown
    """
    ratio = None

    positions = aperture.sample(ha, dec)
    pointing = aperture.direction(ha, dec)

    # Compute the no. rays, emanating from those points, blocked by the dome
    blocked = check_blockage(positions, pointing, dome_az, metadata)

    ratio = blocked[blocked].size / blocked.size

    return ratio, blocked
