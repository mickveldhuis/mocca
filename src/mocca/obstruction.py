import numpy as np
from pytransform3d import transformations as pt

from mocca.aperture import Aperture
from mocca.metadata import DomeInfo
from mocca.transformations import rot_z


def find_ray_dome_intersection(
    origin: np.ndarray, direction: np.ndarray, dome_radius: float, dome_extent: float
) -> np.ndarray | None:
    """
    Find ray-dome intersection when the rays hit the hemispherical cap of the dome,
    which, inlcuding the walls, is modelled as a capsule.

    :param origin: ray origin (3-vector)
    :param direction: ray unit direction vector
    :returns: the intersection with the hemispherical cap, if found, else None
    """

    def calculate_hit(origin: np.ndarray, direction: np.ndarray, t: float):
        return origin + t * direction

    assert np.isclose(np.linalg.norm(direction), 1.0), "direction is not a unit vector"
    assert np.linalg.norm(origin[:2]) < dome_radius, (
        "origin vector is not inside of the dome"
    )

    # Unpack the origin and direction for clarity
    x, y, z = origin
    dx, dy, dz = direction

    t = None
    intersection = None

    #  Case 1: the ray is parallel to the dome's z-axis
    if np.isclose(dz, 1.0):
        z_hemisphere_squared = dome_radius**2 - x**2 - y**2
        if z_hemisphere_squared < 0.0:
            return None

        z_dome = dome_extent + np.sqrt(z_hemisphere_squared)
        t = z_dome - z
        intersection = calculate_hit(origin, direction, t)

        return intersection

    # Case 2: the ray is **not** parallel to the dome's z-axis, for which
    # we first check
    a2 = dx**2 + dy**2
    a1 = x * dx + y * dy
    a0 = x**2 + y**2 - dome_radius**2

    delta = a1**2 - a0 * a2
    if delta < 0.0:
        return None

    t = (-a1 + np.sqrt(delta)) / a2
    _, _, z_hit = calculate_hit(origin, direction, t)

    # Checking for intersections with the hemispherical cap of the dome
    if z_hit > dome_extent:
        a0 = x**2 + y**2 + (z - dome_extent) ** 2 - dome_radius**2
        a1 = x * dx + y * dy + (z - dome_extent) * dz

        delta = a1**2 - a0
        if delta < 0.0:
            return None

        t = -a1 + np.sqrt(delta)
        intersection = calculate_hit(origin, direction, t)

    return intersection


def aperture_obstruction_condition(
    x: float, y: float, z: float, dome_radius: float, dome_slit_width: float
) -> bool:
    half_width = dome_slit_width / 2
    x_condition = x < -half_width or x > half_width

    r = dome_radius * np.sin(np.radians(15))  # TODO: document this magic angle!
    y_condition = y < -r or y > dome_radius

    return x_condition or y_condition


@np.vectorize(signature="(p),(q),(),()->()")
def check_obstruction(
    point: np.ndarray, direction: np.ndarray, dome_az: float, info: DomeInfo
) -> np.ndarray:
    """
    Checks whether an individual ray is blocked.

    :param point: ray origin
    :param ha: hour angle in degrees
    :param dec: declination in degrees
    :param dome_az: dome azimuth (clockwise convention)
    :param info: dome properties
    """
    is_blocked = True

    dome_radius = info.dome_radius
    dome_extent = info.dome_extent
    dome_slit_width = info.dome_slit_width
    intersection = find_ray_dome_intersection(
        point, direction, dome_radius, dome_extent
    )

    if intersection is not None:
        az_corrected = (
            dome_az - 180
        ) % 360  # Correction assuming the azimuth is zero at the South
        rot = rot_z(az_corrected)

        dummy = np.ones(intersection[0].size)
        pp = np.column_stack((intersection[0], intersection[1], intersection[2], dummy))

        product = pt.transform(rot, pp)

        r = dome_radius * np.sin(np.radians(15))  # TODO: document this magic angle!

        x_cond = -dome_slit_width / 2 < product[:, 0] < dome_slit_width / 2
        y_cond = -r < product[:, 1] < dome_radius

        is_ray_in_slit = intersection[2] > dome_extent and x_cond and y_cond

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
    :param info: dome properties
    """
    ray_origins = aperture.sample(ha, dec)
    pointing = aperture.direction(ha, dec)

    blocked = check_obstruction(ray_origins, pointing, dome_az, info)

    ratio = blocked[blocked].size / blocked.size

    return ratio, blocked
