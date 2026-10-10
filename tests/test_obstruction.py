import numpy as np
import pytest

from mocca.aperture import create_aperture
from mocca.obstruction import aperture_obstruction_condition, calculate_obstruction

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


@pytest.mark.parametrize(
    "x,y,expected_output",
    [
        (-1.5, -0.5, True),
        (-1.001, 2.0, True),
        (0.0, 10.0, True),
        (0.0, 0.0, False),
        (1.0, 1.0, False),
    ],
)
def test_aperture_obstruction_condition(x, y, expected_output):
    """Check whether the obstruction condition behaves as expected."""
    radius = 4.0
    slit_width = 2.0

    if expected_output:
        # Checks whether a ray is correctly assessed as: BLOCKED
        assert aperture_obstruction_condition(x, y, radius, slit_width)
    else:
        # Checks whether a ray is correctly assessed as: NOT BLOCKED
        assert not aperture_obstruction_condition(x, y, radius, slit_width)
