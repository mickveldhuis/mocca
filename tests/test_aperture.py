from importlib.util import find_spec
from pathlib import Path

import numpy as np
import pytest

from mocca.aperture import create_aperture
from mocca.main import MOCCA_CONFIG
from mocca.metadata import TelescopeInfo
from mocca.transformations import rot_x, rot_y, rot_z, translation

# Store all supported aperture types to parametrize tests
SUPPORTED_APERTURES = ["telescope", "guider", "finder"]

# Use a constant HA and declination for this test-suite
HA = -15.0  # degrees
DEC = -35.0  # degrees


@pytest.fixture
def telescope_info():
    mocca_src = Path(find_spec("mocca").origin).parent
    config_path = mocca_src / MOCCA_CONFIG

    if not config_path.exists():
        pytest.skip(f"MOCCA configuration file not found at {config_path.resolve()}")

    return TelescopeInfo.from_file(config_path)


@pytest.fixture
def reference_telescope_transformation(telescope_info):
    """
    Calculate the primary aperture transformation according my 2021
    undergraduate thesis.

    Refer to Chapter 3 (Equation 13) of:
    https://fse.studenttheses.ub.rug.nl/id/eprint/25172
    """
    H_01 = translation(0.0, 0.0, telescope_info.height)
    H_12 = (
        rot_x(90.0 - telescope_info.latitude)
        @ rot_z(-HA)
        @ translation(0.0, 0.0, telescope_info.ha_axis_offset)
    )
    H_23 = rot_x(DEC) @ translation(-telescope_info.dec_axis_offset, 0.0, 0.0)

    return H_01 @ H_12 @ H_23


@pytest.fixture
def reference_guider_transformation(telescope_info, reference_telescope_transformation):
    """
    Calculate the autoguider aperture transformation according my
    2021 undergraduate thesis.

    Refer to Chapter 3 (Equation 14) of:
    https://fse.studenttheses.ub.rug.nl/id/eprint/25172
    """
    # Note: this is the initial 2021 implementation, which differs from my
    # thesis AND is likely wrong; leaving it here for reference.
    # H_34 = translation(
    #     telescope_info.guider_offset * np.cos(telescope_info.guider_angle),
    #     0,
    #     telescope_info.guider_offset * np.sin(telescope_info.guider_angle),
    # )
    H_34 = rot_y(telescope_info.guider_angle) @ translation(
        0.0, 0.0, telescope_info.guider_offset
    )

    return reference_telescope_transformation @ H_34


@pytest.fixture
def reference_finder_transformation(telescope_info, reference_guider_transformation):
    """
    Calculate the autoguider aperture transformation according my
    2021 undergraduate thesis.

    Refer to Chapter 3 (Equation 15) of:
    https://fse.studenttheses.ub.rug.nl/id/eprint/25172
    """
    # Note: this is the initial 2021 implementation, which differs from my
    # thesis AND is likely wrong; leaving it here for reference.
    # H_45 = translation(
    #     -telescope_info.finder_offset * np.cos(telescope_info.finder_angle),
    #     0,
    #     telescope_info.finder_offset * np.sin(telescope_info.finder_angle),
    # )
    H_45 = translation(-telescope_info.finder_offset, 0.0, 0.0)

    return reference_guider_transformation @ H_45


def validate_aperture_origin_and_direction(
    aperture_type: str,
    reference_transformation: np.ndarray,
    telescope_info: TelescopeInfo,
    ha: float = 0.0,
    dec: float = 0.0,
):
    """
    Check whether the current implementation agrees with the reference from 2021.

    To do this, we check whether the position and direction vectors are still the same,
    since these influence the obstruction calculation. The rotation of the samples
    in the xz-plane is irrevant and may differ.

    :param aperture_type: string indicating the telescope, autoguider, or finderscope
    :param reference_transformation: the reference transformation according to the 2021 calculations
    :param telescope_info: telescope metadata
    :param ha: telescope hour angle
    :param dec: telescope declination
    """
    dummy_rate = 1  # not used in this test
    aperture = create_aperture(aperture_type, dummy_rate, telescope_info)
    transformation = aperture.transformation(ha, dec)

    aperture_origin = transformation[:3, 3]
    expected_origin = reference_transformation[:3, 3]
    assert np.allclose(aperture_origin, expected_origin)

    direction = aperture.direction(ha, dec)
    expected_direction = reference_transformation[:3, 1]
    assert np.allclose(direction, expected_direction)


@pytest.mark.parametrize("aperture_type", SUPPORTED_APERTURES)
def test_compare_aperture_origin_and_direction_to_reference(
    aperture_type,
    telescope_info,
    reference_telescope_transformation,
    reference_guider_transformation,
    reference_finder_transformation,
):
    """
    Regression test that calculates the transformation matrix and compares the origin
    and direction vectors to the original implementation delivered in 2021.
    """
    match aperture_type:
        case "telescope":
            validate_aperture_origin_and_direction(
                aperture_type,
                reference_telescope_transformation,
                telescope_info,
                ha=HA,
                dec=DEC,
            )
        case "guider":
            validate_aperture_origin_and_direction(
                aperture_type,
                reference_guider_transformation,
                telescope_info,
                ha=HA,
                dec=DEC,
            )
        case "finder":
            validate_aperture_origin_and_direction(
                aperture_type,
                reference_finder_transformation,
                telescope_info,
                ha=HA,
                dec=DEC,
            )
        case _:
            pytest.xfail(f"{aperture_type} not supported")
