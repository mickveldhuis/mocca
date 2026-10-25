import numpy as np
import numpy.typing as npt


def calculate_hit(
    origin: npt.NDArray[np.double], direction: npt.NDArray[np.double], t: float
) -> np.ndarray:
    """Return the position of a hit, i.e. an intersection."""
    return origin + t * direction


def find_ray_cylinder_intersection(
    origin: npt.NDArray[np.double],
    direction: npt.NDArray[np.double],
    dome_radius: float,
) -> float | None:
    """
    Find a possible ray-wall intersection.

    :param origin: ray origin (3,)
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
    if delta < 0.0 or np.isclose(a2, 0.0):
        return None

    t = (-a1 + np.sqrt(delta)) / a2

    return t


def find_ray_cylinder_intersections(
    origins: npt.NDArray[np.double],
    directions: npt.NDArray[np.double],
    dome_radius: float,
) -> float:
    """
    Find a possible ray-wall intersection for multiple origins.

    :param origins: ray origin (N, 3)
    :param directions: ray unit direction vector (N, 3)
    :param dome_radius: radius of the dome in meters
    :returns: the distances from the origin to the intersection
    """
    x, y, _ = origins.T
    dx, dy, _ = directions.T

    a2 = dx**2 + dy**2
    a1 = x * dx + y * dy
    a0 = x**2 + y**2 - dome_radius**2

    delta = a1**2 - a0 * a2
    safe_delta = np.where(delta < 0.0, np.nan, delta)

    numerator = -a1 + np.sqrt(safe_delta)
    t = np.divide(
        numerator, a2, out=np.full_like(numerator, np.nan), where=~np.isclose(a2, 0.0)
    )

    return t


def find_ray_hemisphere_intersection(
    origin: npt.NDArray[np.double],
    direction: npt.NDArray[np.double],
    dome_radius: float,
    dome_extent: float,
) -> float | None:
    """
    Find a possible ray-hemisphere intersection.

    :param origin: ray origin (3,)
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


def find_ray_hemisphere_intersections(
    origins: npt.NDArray[np.double],
    directions: npt.NDArray[np.double],
    dome_radius: float,
    dome_extent: float,
) -> float:
    """
    Find a possible ray-hemisphere intersection.

    :param origins: ray origin (N, 3)
    :param directions: ray unit direction vector (N, 3)
    :param dome_radius: radius of the dome in meters
    :param dome_extent: height of the walls in meters
    :returns: the distances from the origin to the intersection
    """
    x, y, z = origins.T
    dx, dy, dz = directions.T

    a0 = x**2 + y**2 + (z - dome_extent) ** 2 - dome_radius**2
    a1 = x * dx + y * dy + (z - dome_extent) * dz

    delta = a1**2 - a0
    safe_delta = np.where(delta < 0.0, np.nan, delta)

    t = -a1 + np.sqrt(safe_delta)

    return t


def find_ray_dome_intersection(
    origin: npt.NDArray[np.double],
    direction: npt.NDArray[np.double],
    dome_radius: float,
    dome_extent: float,
) -> np.ndarray | None:
    """
    Find ray-dome intersection when the rays hit the hemispherical cap of the dome,
    which, inlcuding the walls, is modelled as a capsule.

    :param origin: ray origin (3,)
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


def find_ray_dome_intersections(
    origins: npt.NDArray[np.double],
    direction: npt.NDArray[np.double],
    dome_radius: float,
    dome_extent: float,
) -> np.ndarray:
    """
    Find ray-dome intersection when the rays hit the hemispherical cap of the dome,
    which, inlcuding the walls, is modelled as a capsule.

    :param origins: ray origin (N, 3)
    :param directions: ray unit direction vector (3,)
    :param dome_radius: radius of the dome in meters
    :param dome_extent: height of the walls in meters
    :returns: the positions of the intersections with the hemispherical cap
    """
    # Special case: the ray is parallel to the dome's z-axis
    _, _, dz = direction
    if np.isclose(dz, 1.0):
        x = origins[:, 0]
        y = origins[:, 1]
        z = origins[:, 2]

        z_hemisphere_squared = dome_radius**2 - x**2 - y**2
        safe_z_hemisphere_squared = np.where(
            z_hemisphere_squared < 0.0, np.nan, z_hemisphere_squared
        )

        z_dome = dome_extent + np.sqrt(safe_z_hemisphere_squared)
        t = z_dome - z
    else:
        # When the ray is **not** parallel to the dome's z-axis, we also check
        # whether the rays hit the walls of the dome.
        t_wall = find_ray_cylinder_intersections(
            origins, np.broadcast_to(direction, origins.shape), dome_radius
        )
        t_dome = find_ray_hemisphere_intersections(
            origins, direction, dome_radius, dome_extent
        )

        # Filter out rays that did not hit the hemispherical cap
        z_hits = origins[:, 2] + t_wall * dz
        has_hit_dome = z_hits > dome_extent

        t = np.where(has_hit_dome, t_dome, np.nan)

    # Disregard rays going against the pointing direction
    t = np.where(t < 0.0, np.nan, t)

    return origins + t[:, np.newaxis] * direction
