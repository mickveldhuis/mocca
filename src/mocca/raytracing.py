import numpy as np


def calculate_hit(origin: np.ndarray, direction: np.ndarray, t: float):
    """Return the position of a hit, i.e. an intersection."""
    return origin + t * direction


def find_ray_cylinder_intersection(
    origin: np.ndarray, direction: np.ndarray, dome_radius: float
) -> float | None:
    """
    Find a possible ray-wall intersection.

    :param origin: ray origin (3-vector)
    :param direction: ray unit direction vector
    :param dome_radius: radius of the dome in meters
    :returns: the distance from the origin to the intersection, if found, else None
    """
    x, y, _ = origin
    dx, dy, _ = direction

    a2 = dx**2 + dy**2
    a1 = x * dx + y * dy
    a0 = x**2 + y**2 - dome_radius**2

    delta = a1**2 - a0 * a2
    if delta < 0.0:
        return None

    t = (-a1 + np.sqrt(delta)) / a2

    return t


def find_ray_hemisphere_intersection(
    origin: np.ndarray, direction: np.ndarray, dome_radius: float, dome_extent: float
) -> float | None:
    """
    Find a possible ray-hemisphere intersection.

    :param origin: ray origin (3-vector)
    :param direction: ray unit direction vector
    :param dome_radius: radius of the dome in meters
    :param dome_extent: height of the walls in meters
    :returns: the distance from the origin to the intersection, if found, else None
    """
    x, y, z = origin
    dx, dy, dz = direction

    a0 = x**2 + y**2 + (z - dome_extent) ** 2 - dome_radius**2
    a1 = x * dx + y * dy + (z - dome_extent) * dz

    delta = a1**2 - a0
    if delta < 0.0:
        return None

    t = -a1 + np.sqrt(delta)

    return t


def find_ray_dome_intersection(
    origin: np.ndarray, direction: np.ndarray, dome_radius: float, dome_extent: float
) -> np.ndarray | None:
    """
    Find ray-dome intersection when the rays hit the hemispherical cap of the dome,
    which, inlcuding the walls, is modelled as a capsule.

    :param origin: ray origin (3-vector)
    :param direction: ray unit direction vector
    :param dome_radius: radius of the dome in meters
    :param dome_extent: height of the walls in meters
    :returns: the position of the intersection with the hemispherical cap, if found, else None
    """
    # Special case: the ray is parallel to the dome's z-axis
    _, _, dz = direction
    if np.isclose(dz, 1.0):
        x, y, z = origin

        z_hemisphere_squared = dome_radius**2 - x**2 - y**2
        if z_hemisphere_squared < 0.0:
            return None

        z_dome = dome_extent + np.sqrt(z_hemisphere_squared)
        t = z_dome - z

        return calculate_hit(origin, direction, t) if t > 0.0 else None

    # When the ray is **not** parallel to the dome's z-axis, we first
    # check for intersections with the cylindrical dome walls.
    t = find_ray_cylinder_intersection(origin, direction, dome_radius)
    if t is None or t < 0.0:
        return None

    _, _, z_hit = calculate_hit(origin, direction, t)

    # Only check the hemisphere when the hit is above the cylindrical wall
    if z_hit > dome_extent:
        t = find_ray_hemisphere_intersection(
            origin, direction, dome_radius, dome_extent
        )
        if t is not None and t > 0.0:
            return calculate_hit(origin, direction, t)

    return None
