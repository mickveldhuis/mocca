import numpy as np
from pytransform3d import transformations as pt

from mocca.aperture import Aperture
from mocca.metadata import DomeInfo
from mocca.raytracing import find_ray_dome_intersection
from mocca.transformations import rot_z

# TODO: Convert to NamedTuple
ObstructionResult = tuple[float, np.ndarray]


def aperture_obstruction_condition(
    x: float, y: float, dome_radius: float, dome_slit_width: float
) -> bool:
    """
    Return whether the ray is blocked by the dome's opening slit.

    :param x: x position of the ray intersection inside the dome frame
    :param y: y position of the ray intersection inside the dome frame
    :param dome_radius: radius of the dome in meters
    :param dome_slit_width: width of the dome's opening in meters
    :returns: whether the ray is blocked by the dome
    """
    half_width = dome_slit_width / 2
    x_condition = x < -half_width or x > half_width

    # The dome's slit extends past zenith, to correct for
    # this discrepancy, we add a fudge factor (15 degrees)
    # inferred by the dome of the Blaauw observatory.
    r = dome_radius * np.sin(
        np.radians(15)
    )  # TODO: move this fudge factor to DomeInfo.
    y_condition = y < -r or y > dome_radius

    return x_condition or y_condition


def correct_for_dome_rotation(position: np.ndarray, dome_az: float) -> np.ndarray:
    """
    Rotate the intersections points by the dome azimuth, such that we can
    validate the obstruction condition assuming that the slit is parallel
    to the x and y axes.

    :param position: intersection position (3-vector)
    :param dome_az: dome's azimuth angle in degrees
    :returns: intersection positions corrected for the dome's rotation
    """
    az_corrected = (
        dome_az - 180
    ) % 360  # Correction assuming the azimuth is zero at the South
    rot = rot_z(az_corrected)

    homogeneous_position_vector = np.append(position, 1.0)
    corrected_position = pt.transform(rot, homogeneous_position_vector)

    return corrected_position[:3]


@np.vectorize(signature="(p),(q),(),()->()")
def check_obstruction(
    point: np.ndarray, direction: np.ndarray, dome_az: float, info: DomeInfo
) -> np.ndarray:
    """
    Checks whether an individual ray is blocked.

    :param point: ray origin (3-vector)
    :param direction: ray direction (3-vector)
    :param dome_az: dome azimuth (clockwise convention)
    :param info: dome properties
    """
    is_blocked = True

    dome_radius = info.radius
    dome_extent = info.extent
    dome_slit_width = info.slit_width
    intersection = find_ray_dome_intersection(
        point, direction, dome_radius, dome_extent
    )

    if intersection is not None:
        x, y, _ = correct_for_dome_rotation(intersection, dome_az)
        is_blocked = aperture_obstruction_condition(x, y, dome_radius, dome_slit_width)

    return is_blocked


def validate_ray_origins(origins: np.ndarray, dome_radius) -> None:
    """
    Check whether the rays are originating from inside the dome.

    :param origins: vector of shape (N, 3) with sampled ray origin positions
    :param dome_radius: radius of the hemispherical dome in meters
    """
    if origins.shape[0] == 0:
        raise ValueError("zero ray origin positions")

    offset_from_centre = np.linalg.norm(origins[:, :2], axis=1)
    if np.any(offset_from_centre > dome_radius):
        raise ValueError(
            f"one or more of the rays are origination from outside the dome (with radius {dome_radius:.2f})"
        )


def validate_ray_direction(direction: np.ndarray) -> None:
    """Check whether the direction vector is of unit length."""
    length = np.linalg.norm(direction)
    if not np.isclose(length, 1.0):
        raise ValueError(
            f"the ray's directon vector has length {length:.5f} != 1.0, but expecting a unit vector"
        )


def calculate_obstruction(
    dome_az: float, ha: float, dec: float, aperture: Aperture, info: DomeInfo
) -> ObstructionResult:
    """
    Compute the % obstruction of the aperture by the dome.

    :param dome_az: dome azimuth (clockwise convention)
    :param ha: hour angle in degrees
    :param dec: declination in degrees
    :param aperture: telescope aperture
    :param info: dome properties
    """
    ray_origins = aperture.sample(ha, dec)
    validate_ray_origins(ray_origins, info.radius)

    pointing = aperture.direction(ha, dec)
    validate_ray_direction(pointing)

    blocked = check_obstruction(ray_origins, pointing, dome_az, info)

    ratio = blocked.mean()

    return ratio, blocked
