import numpy as np
import pytest

from mocca.aperture import create_aperture
from mocca.obstruction import (
    aperture_obstruction_condition,
    batch_aperture_obstruction_condition,
    batch_calculate_obstruction,
    batch_correct_for_dome_rotation,
    calculate_obstruction,
    correct_for_dome_rotation,
)

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

    blockage, _ = calculate_obstruction(ha, dec, az, aperture, dome_info)

    assert np.isclose(blockage, percentage / 1e2, rtol=1e-3)


def test_batch_obstruction_calculation(telescope_info, dome_info):
    """Compare the batch calculation with the default the default implementation."""
    aperture_type = "telescope"  # primary aperture identifier
    aperture = create_aperture(aperture_type, TEST_RATE, telescope_info)

    ha = -7.5
    dec = -35

    azimuths = np.array([0.0, 180.0])

    batch_result = batch_calculate_obstruction(ha, dec, azimuths, aperture, dome_info)

    assert len(batch_result.ratios) == 2

    for index, az in enumerate(azimuths):
        # The default (non-batch) implementation is used as reference
        expected_blockage, _ = calculate_obstruction(ha, dec, az, aperture, dome_info)

        blockage = batch_result.ratios[index]

        assert np.isclose(blockage, expected_blockage, rtol=1e-3)


def test_batch_rotation():
    """Validate the output shape of the batch rotation operation."""
    n_angles = 5
    n_rays = 4

    mock_positions = np.random.rand(n_rays, 3)
    mock_azimuths = np.linspace(0.0, 180.0, n_angles)

    mock_output = batch_correct_for_dome_rotation(mock_positions, mock_azimuths)

    assert mock_output.shape[0] == n_angles
    assert mock_output.shape[1] == n_rays
    assert mock_output.shape[2] == 3

    for i, az in enumerate(mock_azimuths):
        for j, pos in enumerate(mock_positions):
            expected_position = correct_for_dome_rotation(mock_positions[j, :], az)
            batch_position = mock_output[i, j, :]

            assert np.allclose(batch_position, expected_position)


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


def test_batch_aperture_obstruction_condition():
    """
    Check whether the batch obstruction condition behaves
    as expected by comparing the output to the reference.
    """
    n_angles = 5
    n_rays = 25
    shape = (n_angles, n_rays)

    x = 10 * np.random.random_sample(shape) - 5
    y = 10 * np.random.random_sample(shape) - 5
    radius = 4.0
    slit_width = 2.0

    masks = batch_aperture_obstruction_condition(x, y, radius, slit_width)

    assert masks.shape[0] == n_angles
    assert masks.shape[1] == n_rays

    for i in range(n_angles):
        for j in range(n_rays):
            expected_value = aperture_obstruction_condition(
                x[i, j], y[i, j], radius, slit_width
            )
            assert masks[i, j] == expected_value
