import numpy as np
import pytest

from mocca.raytracing import (
    find_ray_cylinder_intersection,
    find_ray_dome_intersection,
    find_ray_hemisphere_intersection,
)


@pytest.mark.parametrize(
    "origin, direction, expected_t",
    [
        (
            np.zeros(3),
            np.array([0.0, 0.0, 1.0]),
            None,
        ),
        (
            np.array([0.0, 2.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            -1.0,
        ),
        (
            np.zeros(3),
            np.array([np.sqrt(2) / 2, np.sqrt(2) / 2, 0.0]),
            1.0,
        ),
    ],
)
def test_ray_cylinder_intersection(origin, direction, expected_t):
    """Validate find_ray_cylinder_intersection() for an infinite cylinder of unit radius."""
    radius = 1.0

    t = find_ray_cylinder_intersection(origin, direction, radius)
    if expected_t is None:
        assert t is None
    else:
        assert np.isclose(t, expected_t)


@pytest.mark.parametrize(
    "origin,direction,expected_t",
    [
        (
            np.zeros(3),
            np.array([0.0, 0.0, 1.0]),
            2.0,
        ),
        (
            np.array([0.0, 0.0, 1.5]),
            np.array([0.0, 0.0, 1.0]),
            0.5,
        ),
        (
            np.array([2.0, 2.0, 0.0]),
            np.array([1.0, 0.0, 0.0]),
            None,
        ),
    ],
)
def test_ray_hemisphere_intersection(origin, direction, expected_t):
    """Validate find_ray_hemisphere_intersection() for a dome of unit radius and extent."""
    radius = 1.0
    extent = 1.0

    t = find_ray_hemisphere_intersection(origin, direction, radius, extent)
    if expected_t is None:
        assert t is None
    else:
        assert np.isclose(t, expected_t)


def test_ray_dome_intersection():
    """Validate find_ray_dome_intersection() using a ray parallel to the z-axis."""
    origin = np.array([0.0, 0.0, 0.0])
    direction = np.array([0.0, 0.0, 1.0])

    radius = 1.0
    extent = 1.0

    intersection = find_ray_dome_intersection(origin, direction, radius, extent)

    expected_height = 2.0
    assert np.allclose(intersection[:2], [0.0, 0.0])
    assert np.isclose(np.linalg.norm(intersection), expected_height)
