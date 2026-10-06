import numpy as np

from mocca.mount import CompositeMount, EquatorialMount


def validate_position_vector(transformation_matrix, expected_vector):
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


def validate_position_and_direction_for_constant_hour_angle(mount, expected_position):
    """
    Validate the mount's transformation matrices for constant hour angle, such
    that the pointing direction stays constant for changing mount geometry.
    """
    constant_ha = 0.0

    # Point the telescope parallel to the celestial equator
    dec_equator = 0.0
    transformation = mount.transformation(constant_ha, dec_equator)

    validate_position_vector(transformation, expected_position)

    expected_direction = [0.0, 1.0, 0.0]  # along dome y-axis
    validate_direction_vector(transformation, expected_direction)

    # Point the the telescope along the yz-axis in the dome frame
    dec = 45.0
    transformation = mount.transformation(constant_ha, dec)

    validate_position_vector(transformation, expected_position)

    expected_direction = [0.0, np.sqrt(2.0) / 2, np.sqrt(2.0) / 2]
    validate_direction_vector(transformation, expected_direction)

    # Point the the telescope to the north celestial pole
    dec_ncp = 90.0
    transformation = mount.transformation(constant_ha, dec_ncp)

    validate_position_vector(transformation, expected_position)

    expected_direction = [0.0, 0.0, 1.0]  # along dome z-axis
    validate_direction_vector(transformation, expected_direction)


def test_equatorial_mount():
    """
    Check whether the EquatorialMount creates correct transformation matrices
    by varying the declination. To simplify the calculations, we consider a
    constant (zero) HA and a telescope at the north pole.
    """
    height = 1.0
    ha_axis_offset = 1.0
    dec_axis_offset = 1.0
    latitude = 90  # north pole
    mount = EquatorialMount(height, ha_axis_offset, dec_axis_offset, latitude)

    # Consider a constant (zero) hour angle
    expected_position = [-dec_axis_offset, 0.0, height + ha_axis_offset]
    validate_position_and_direction_for_constant_hour_angle(mount, expected_position)


def test_composite_mount_without_angle():
    """
    Check whether the CompositeMont creates correct transformation matrices
    by varying the declination. To simplify the calculations, we consider a
    constant (zero) HA and a telescope at the north pole.
    """
    # Construct the equatorial mount base
    height = 1.0
    ha_axis_offset = 1.0
    dec_axis_offset = 1.0
    latitude = 90  # north pole
    base_mount = EquatorialMount(height, ha_axis_offset, dec_axis_offset, latitude)

    # Add an offset mount, without considering an angular offset
    offset = 1.0
    angle = 0.0
    mount = CompositeMount(base_mount, offset, angle)

    # Consider a constant (zero) hour angle
    expected_position = [-dec_axis_offset + offset, 0.0, height + ha_axis_offset]
    validate_position_and_direction_for_constant_hour_angle(mount, expected_position)


def test_composite_mount_with_angle():
    """
    Check whether the CompositeMont creates correct transformation matrices
    by varying the declination. To simplify the calculations, we consider a
    constant (zero) HA and a telescope at the north pole.
    """
    # Construct the equatorial mount base
    height = 1.0
    ha_axis_offset = 1.0
    dec_axis_offset = 1.0
    latitude = 90  # north pole
    base_mount = EquatorialMount(height, ha_axis_offset, dec_axis_offset, latitude)

    # Add an offset mount, without considering an angular offset
    offset = 1.0
    angle = 0.0
    mount = CompositeMount(base_mount, offset, angle)

    # Consider a constant (zero) hour angle
    expected_position = [-dec_axis_offset + offset, 0.0, height + ha_axis_offset]
    validate_position_and_direction_for_constant_hour_angle(mount, expected_position)
