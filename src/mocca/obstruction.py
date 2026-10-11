import logging

import numpy as np
from pytransform3d import transformations as pt

from mocca.aperture import Aperture
from mocca.raytracing import find_ray_dome_intersection, find_ray_dome_intersections
from mocca.transformations import rot_z
from mocca.types import BatchObstructionResult, DomeInfo, ObstructionResult

logger = logging.getLogger("MOCCA")


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
            f"one or more of the rays are originating from outside the dome (with radius {dome_radius:.2f})"
        )


def validate_ray_direction(direction: np.ndarray) -> None:
    """Check whether the direction vector is of unit length."""
    length = np.linalg.norm(direction)
    if not np.isclose(length, 1.0):
        raise ValueError(
            f"the ray's direction vector has length {length:.5f} != 1.0, but expecting a unit vector"
        )


def aperture_obstruction_condition(
    x: np.ndarray, y: np.ndarray, dome_radius: float, dome_slit_width: float
) -> bool:
    """
    Return whether the ray is blocked by the dome's opening slit.

    :param x: x position of the ray intersection inside the dome frame
    :param y: y position of the ray intersection inside the dome frame
    :param dome_radius: radius of the dome in meters
    :param dome_slit_width: width of the dome's opening in meters
    :returns: whether the ray is blocked by the dome or not
    """
    half_width = dome_slit_width / 2
    x_condition = x < -half_width or x > half_width

    # The dome's slit extends past zenith, to correct for
    # this discrepancy, we add a fudge factor (15 degrees)
    # inferred by the dome of the Blaauw observatory.
    slit_overshoot = dome_radius * np.sin(
        np.radians(15)
    )  # TODO: move this fudge factor to DomeInfo.
    y_condition = y < -slit_overshoot or y > dome_radius

    return x_condition or y_condition


def batch_aperture_obstruction_condition(
    x: np.ndarray, y: np.ndarray, dome_radius: float, dome_slit_width: float
) -> bool:
    """
    Return whether the ray is blocked by the dome's opening slit.

    :param x: x positions of the ray intersections inside the dome frame (N,)
    :param y: y positions of the ray intersections inside the dome frame (N,)
    :param dome_radius: radius of the dome in meters
    :param dome_slit_width: width of the dome's opening in meters
    :returns: whether the rays are blocked by the dome or not
    """
    half_width = dome_slit_width / 2
    x_condition = (x < -half_width) | (x > half_width)

    # The dome's slit extends past zenith, to correct for
    # this discrepancy, we add a fudge factor (15 degrees)
    # inferred by the dome of the Blaauw observatory.
    slit_overshoot = dome_radius * np.sin(
        np.radians(15)
    )  # TODO: move this fudge factor to DomeInfo.
    y_condition = (y < -slit_overshoot) | (y > dome_radius)

    return x_condition | y_condition


def correct_for_dome_rotation(
    position: np.ndarray, dome_azimuth: np.ndarray
) -> np.ndarray:
    """
    Rotate the intersections points by the dome azimuth, such that we can
    validate the obstruction condition assuming that the slit is parallel
    to the x and y axes.

    We also assume that the azimuth is zero towards the South.

    :param position: intersection position (N, 3)
    :param dome_azimuth: dome's azimuth angles in degrees
    :returns: intersection positions corrected for the dome's rotation
    """
    corrected_azimuth = (
        dome_azimuth - 180
    ) % 360  # Correction assuming the azimuth is zero at the South

    rot = rot_z(corrected_azimuth)
    homogeneous_position_vector = np.append(position, 1.0)
    corrected_position = pt.transform(rot, homogeneous_position_vector)

    return corrected_position[:3]


def batch_correct_for_dome_rotation(
    position: np.ndarray, dome_azimuths: np.ndarray
) -> np.ndarray:
    """
    Rotate the intersections points by the dome azimuth, such that we can
    validate the obstruction condition assuming that the slit is parallel
    to the x and y axes.

    We also assume that the azimuth is zero towards the South.

    :param position: intersection position (N, 3)
    :param dome_azimuths: dome's azimuth angles in degrees
    :returns: intersection positions corrected for the dome's rotation
    """
    corrected_azimuths = (
        dome_azimuths - 180
    ) % 360  # Correction assuming the azimuth is zero at the South

    c_az = np.cos(corrected_azimuths)
    s_az = np.sin(corrected_azimuths)

    x, y, z = position.T

    corrected_x = x * c_az - y * s_az
    corrected_y = x * s_az + y * c_az

    corrected_position = np.column_stack([corrected_x, corrected_y, z])

    return corrected_position


def check_obstruction(
    origin: np.ndarray, direction: np.ndarray, azimuth: float, dome: DomeInfo
) -> bool:
    """
    Checks whether an individual ray is blocked.

    :param origin: ray origin (3,)
    :param direction: ray direction (3,)
    :param azimuth: dome azimuth (clockwise convention)
    :param dome: dome properties
    """
    intersection = find_ray_dome_intersection(
        origin, direction, dome.radius, dome.extent
    )
    if intersection is None:
        # If there's no intersection with the hemispherical
        # cap of the dome, the ray is definitely blocked.
        return True

    position = correct_for_dome_rotation(intersection, azimuth)
    print(position)
    x, y, _ = position.T

    return aperture_obstruction_condition(x, y, dome.radius, dome.slit_width)


def batch_check_obstruction(
    origins: np.ndarray, direction: np.ndarray, azimuth: float, dome: DomeInfo
) -> bool:
    """
    Checks whether an individual ray is blocked.

    :param origin: ray origin (3,)
    :param direction: ray direction (3,)
    :param azimuth: dome azimuth (clockwise convention)
    :param dome: dome properties
    """
    intersections = find_ray_dome_intersections(
        origins, direction, dome.radius, dome.extent
    )

    # TODO: for future update, where we compute the obstruction for multiple azimuth angles
    # at the same time, note that we only need to recalculate the dome azimuth correction,
    # while reusing the found dome intersections.
    positions = correct_for_dome_rotation(intersections, azimuth)
    x, y, _ = positions.T

    return batch_aperture_obstruction_condition(x, y, dome.radius, dome.slit_width)


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
    logger.info(
        "sampling the aperture for an hour angle of %.2f and declination of %.2f",
        ha,
        dec,
    )
    ray_origins = aperture.sample(ha, dec)
    validate_ray_origins(ray_origins, info.radius)

    pointing = aperture.direction(ha, dec)
    validate_ray_direction(pointing)

    n_rays = ray_origins.shape[0]
    logger.info(
        "checking the obstruction at an azimuth of %.2f degrees using %i rays",
        dome_az,
        n_rays,
    )

    blocked_rays_list = [
        check_obstruction(ray_origins[ray_index, :], pointing, dome_az, info)
        for ray_index in range(n_rays)
    ]
    blocked_rays_mask = np.array(blocked_rays_list)

    return ObstructionResult(ratio=blocked_rays_mask.mean(), mask=blocked_rays_mask)


def batch_calculate_obstruction(
    ha: float, dec: float, dome_azimuths: np.ndarray, aperture: Aperture, info: DomeInfo
) -> BatchObstructionResult:
    """
    Compute the % obstruction of the aperture by the dome.

    :param dome_azimuths: array of dome azimuth angles (clockwise convention)
    :param ha: hour angle in degrees
    :param dec: declination in degrees
    :param aperture: telescope aperture
    :param info: dome properties
    """
    logger.info(
        "sampling the aperture for an hour angle of %.2f and declination of %.2f",
        ha,
        dec,
    )
    ray_origins = aperture.sample(ha, dec)
    validate_ray_origins(ray_origins, info.radius)

    pointing = aperture.direction(ha, dec)
    validate_ray_direction(pointing)

    n_rays = ray_origins.shape[0]
    logger.info(
        "checking the obstruction at an azimuth angles between %.2f and %.2f degrees using %i rays",
        dome_azimuths.min(),
        dome_azimuths.max(),
        n_rays,
    )

    blocked_rays = batch_check_obstruction(ray_origins, pointing, dome_azimuths, info)
    print(blocked_rays)

    # return ObstructionResult(ratio=blocked_rays_mask.mean(), mask=blocked_rays_mask)
    return ObstructionResult(ratio=None, mask=None)
