from dataclasses import dataclass

import numpy as np
import pytest

from mocca.mount import CompositeMount, EquatorialMount, Transformable

EQUATOR_DEC = 0.0
EQUATOR_DIRECTION = [0.0, 1.0, 0.0]

NCP_DEC = 90.0
NCP_DIRECTION = [0.0, 0.0, 1.0]


@dataclass
class MockEquatorialMount:
    """
    Mock equatorial mount parameters; assume
    a mount at the north pole by default.
    """

    height: float = 1.0
    ha_axis_offset: float = 1.0
    dec_axis_offset: float = 1.0
    latitude: float = 90.0  # north pole


@pytest.fixture
def north_pole_mount():
    """
    Return an EquatorialMount instance
    for a mount at the north pole.
    """
    mount = MockEquatorialMount()

    return EquatorialMount(
        mount.height, mount.ha_axis_offset, mount.dec_axis_offset, mount.latitude
    )


def validate_position_vector(
    transformation_matrix: np.ndarray, expected_vector: np.ndarray
):
    """
    The third column of the transformation matrix gives
    the position of the origin inside of the dome frame.
    """
    assert len(expected_vector) == 3

    position_vector = transformation_matrix[:3, 3]
    assert np.allclose(position_vector, expected_vector)


def validate_direction_vector(transformation_matrix, expected_vector):
    """
    Assuming the optical axis is the direction direction,
    the second column is the y-axis, i.e. the direction vector.
    """
    assert len(expected_vector) == 3

    direction_vector = transformation_matrix[:3, 1]
    assert np.allclose(direction_vector, expected_vector)


def validate_position_and_direction_vectors(
    mount: Transformable,
    expected_position: np.ndarray,
    expected_direction: np.ndarray,
    ha: float = 0.0,
    dec: float = 0.0,
):
    """
    Validate the mount's transformation matrices by comparing the origin
    position of the frame and the pointing direction vectors.
    """
    transformation = mount.transformation(ha, dec)

    validate_position_vector(transformation, expected_position)

    validate_direction_vector(transformation, expected_direction)


@pytest.mark.parametrize(
    "dec,direction",
    [
        (EQUATOR_DEC, EQUATOR_DIRECTION),
        (
            45.0,
            [0.0, np.sqrt(2.0) / 2, np.sqrt(2.0) / 2],
        ),  # point along the yz-axis in the dome frame
        (NCP_DEC, NCP_DIRECTION),
    ],
)
def test_equatorial_mount(north_pole_mount, dec, direction):
    """
    Check whether the EquatorialMount creates correct transformation
    matrices by varying the declination.

    To simplify the calculations, we consider a constant
    (zero) HA and a telescope at the north pole.
    """
    expected_position = [
        -north_pole_mount.dec_axis_offset,
        0.0,
        north_pole_mount.height + north_pole_mount.ha_axis_offset,
    ]

    validate_position_and_direction_vectors(
        north_pole_mount, expected_position, direction, dec=dec
    )


@pytest.mark.parametrize(
    "dec,direction,position",
    [
        (EQUATOR_DEC, EQUATOR_DIRECTION, [-1.0, 0.0, 3.0]),
        (NCP_DEC, NCP_DIRECTION, [-1.0, -1.0, 2.0]),
    ],
)
def test_composite_mount_without_angle(north_pole_mount, dec, direction, position):
    """
    Check whether the CompositeMount creates correct transformation
    matrices by varying the declination.

    To simplify the calculations, we consider a constant
    (zero) HA and a telescope at the north pole.
    """
    offset = 1.0
    angle = 0.0
    mount = CompositeMount(north_pole_mount, offset, angle)

    validate_position_and_direction_vectors(mount, position, direction, dec=dec)


@pytest.mark.parametrize(
    "dec,direction,position",
    [
        (EQUATOR_DEC, EQUATOR_DIRECTION, [-1.0, 0.0, 1.0]),
        (NCP_DEC, NCP_DIRECTION, [-1.0, 1.0, 2.0]),
    ],
)
def test_composite_mount_with_angle(north_pole_mount, dec, direction, position):
    """
    Check whether the CompositeMount creates correct transformation
    matrices by varying the declination.

    To simplify the calculations, we consider a constant
    (zero) HA and a telescope at the north pole.
    """
    offset = 1.0
    angle = 180
    mount = CompositeMount(north_pole_mount, offset, angle)

    validate_position_and_direction_vectors(mount, position, direction, dec=dec)
