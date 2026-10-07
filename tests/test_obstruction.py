import numpy as np
import pytest

from mocca.aperture import create_aperture
from mocca.obstruction import calculate_obstruction, find_ray_dome_intersection

TEST_RATE = 4


@pytest.mark.parametrize(
    "ha,dec,az,percentage",
    [
        (150.0, 90.0, 10.0, 3.42),
        # TODO: validate the % for the 2nd test
        # case (this **maybe** used to be 53%)
        (-7.5, -35, 180.0, 46.15),
    ],
)
def test_primary_aperture_obstruction(
    telescope_info, dome_info, ha, dec, az, percentage
):
    """Check the calculated primary aperture obstruction against known simulated values."""
    aperture_type = "telescope"  # primary aperture identifier
    aperture = create_aperture(aperture_type, TEST_RATE, telescope_info)

    blockage, _ = calculate_obstruction(az, ha, dec, aperture, dome_info)

    assert np.isclose(blockage, percentage / 1e2, rtol=1e-3)


def test_ray_dome_intersection():
    origin = np.array([0.0, 0.0, 0.0])
    direction = np.array([0.0, 0.0, 1.0])

    radius = 1.0
    extent = 1.0

    intersection = find_ray_dome_intersection(origin, direction, radius, extent)

    expected_height = 2.0
    assert np.allclose(intersection[:2], [0.0, 0.0])
    assert np.isclose(np.linalg.norm(intersection), expected_height)
