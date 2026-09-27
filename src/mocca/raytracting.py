import numpy as np


def find_intersection(
    point: np.ndarray, direction: np.ndarray, dome_radius: float, dome_extent: float
):
    """Find ray-capsule (i.e. ray-dome) intersection.

    Parameters
    -----------
    point: ray origin (3-vector)
    direction: ray unit direction vector

    Returns
    -------
    has_intersection: boolean signifying whether there is an intersection
    t               : distance between the ray origin and intersection
    """
    has_intersection = False
    t = None

    # In case the ray is ~parallel to the dome z-axis
    if np.isclose(direction[0], 0) and np.isclose(direction[1], 0):
        z = dome_extent + np.sqrt(dome_radius**2 - point[0] ** 2 - point[1] ** 2)
        t = z - point[2]

        has_intersection = True
        return has_intersection, t

    # If the direction vector is not (nearly) parallel to the dome z-axis
    a2 = direction[0] ** 2 + direction[1] ** 2
    a1 = point[0] * direction[0] + point[1] * direction[1]
    a0 = point[0] ** 2 + point[1] ** 2 - dome_radius**2

    delta = a1**2 - a0 * a2
    t = (-a1 + np.sqrt(delta)) / a2

    if point[2] + t * direction[2] >= dome_extent:
        a0 = (
            point[0] ** 2
            + point[1] ** 2
            + (point[2] - dome_extent) ** 2
            - dome_radius**2
        )
        a1 = (
            point[0] * direction[0]
            + point[1] * direction[1]
            + (point[2] - dome_extent) * direction[2]
        )

        t = -a1 + np.sqrt(a1**2 - a0)

    if t:
        has_intersection = True

    return has_intersection, t


def get_ray_intersection(point: np.ndarray, direction: np.ndarray, t: float):
    """
    Return the ray intersection, based on the origin
    (point) and direction vectors.
    """
    return point + t * direction
