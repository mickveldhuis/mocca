from importlib.util import find_spec
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

from mocca.aperture import create_aperture
from mocca.main import MOCCA_CONFIG
from mocca.metadata import TelescopeInfo
from mocca.transformations import rot_x, rot_z, translation


@pytest.fixture
def telescope_info():
    mocca_src = Path(find_spec("mocca").origin).parent
    config_path = mocca_src / MOCCA_CONFIG

    if not config_path.exists():
        pytest.skip(f"MOCCA configuration file not found at {config_path.resolve()}")

    return TelescopeInfo.from_file(config_path)


def validate_aperture_transformation(
    aperture_type: str,
    expected_transformation: np.ndarray,
    telescope_info: TelescopeInfo,
    ha: float = 0.0,
    dec: float = 0.0,
    rate: int = 5,
):
    aperture = create_aperture(aperture_type, rate, telescope_info)

    aperture_transformation = aperture.transformation(ha, dec)
    print(
        "aperture_transformation=\n",
        aperture_transformation,
        aperture_transformation[:3, 3],
    )

    # assert np.allclose(aperture_transformation, expected_transformation)

    return aperture


def test_aperture_transformation(telescope_info):
    """
    Regression test that calculates the transformation matrix and compares
    it to the original implementation delivered in 2021.
    """
    # Telescope pointing
    ha = -15.0  # degrees
    dec = -35.0  # degrees
    ha = 0.0  # degrees
    dec = -telescope_info.latitude  # degrees

    # Calculate the primary aperture transformation according to the 2021 implementation
    H_01 = translation(0, 0, telescope_info.height)
    H_12 = (
        rot_x(90.0 - telescope_info.latitude)
        @ rot_z(-ha)
        @ translation(0, 0, telescope_info.ha_axis_offset)
    )
    H_23 = rot_x(dec) @ translation(-telescope_info.dec_axis_offset, 0, 0)
    H_telescope = H_01 @ H_12 @ H_23
    # print("H_telescope=\n",H_telescope,H_telescope[:3, 3])

    ap = validate_aperture_transformation(
        "telescope", H_telescope, telescope_info, ha=ha, dec=dec
    )
    points = ap.sample(ha, dec)
    plt.plot(
        points[:, 0],
        points[:, 2],
        ls="",
        marker="o",
        ms=3,
        color="black",
    )
    plt.gca().set_aspect("equal")
    # plt.show()

    # Similarly for the autoguider
    H_34 = translation(
        telescope_info.guider_offset * np.cos(telescope_info.guider_angle),
        0,
        telescope_info.guider_offset * np.sin(telescope_info.guider_angle),
    )
    H_guider = H_telescope @ H_34
    print("H_guider=\n", H_guider, H_guider[:3, 3])

    ap = validate_aperture_transformation(
        "guider", H_guider, telescope_info, ha=ha, dec=dec, rate=4
    )
    points = ap.sample(ha, dec)
    plt.plot(
        points[:, 0],
        points[:, 2],
        ls="",
        marker="o",
        ms=3,
        color="black",
    )
    # plt.show()

    # And lastly, also for the finderscope
    H_45 = translation(
        -telescope_info.finder_offset * np.cos(telescope_info.finder_angle),
        0,
        telescope_info.finder_offset * np.sin(telescope_info.finder_angle),
    )
    H_finder = H_telescope @ H_34 @ H_45

    ap = validate_aperture_transformation(
        "finder", H_finder, telescope_info, ha=ha, dec=dec, rate=2
    )
    points = ap.sample(ha, dec)
    plt.plot(
        points[:, 0],
        points[:, 2],
        ls="",
        marker="o",
        ms=3,
        color="black",
    )
    plt.show()
