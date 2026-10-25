import numpy as np
import pytest

import mocca.transformations as mt


@pytest.fixture
def angles():
    n = 17
    angles = np.linspace(0, 360, n)

    return angles


def test_rot_x_nd(angles):
    """Regression test for calculating multi-angle rotation matrix interface."""
    matrices = mt.rot_x_nd(angles)
    assert matrices.shape == (angles.size, 4, 4)

    for i, a in enumerate(angles):
        print(matrices[i])

        assert np.allclose(matrices[i], mt.rot_x(a))


def test_rot_y_nd(angles):
    """Regression test for calculating multi-angle rotation matrix interface."""
    matrices = mt.rot_y_nd(angles)
    assert matrices.shape == (angles.size, 4, 4)

    for i, a in enumerate(angles):
        print(matrices[i])

        assert np.allclose(matrices[i], mt.rot_y(a))


def test_rot_z_nd(angles):
    """Regression test for calculating multi-angle rotation matrix interface."""
    matrices = mt.rot_z_nd(angles)
    assert matrices.shape == (angles.size, 4, 4)

    for i, a in enumerate(angles):
        print(matrices[i])

        assert np.allclose(matrices[i], mt.rot_z(a))


def test_trans_nd():
    """Regression test for the n-dim translation matrix interface."""
    distances = np.arange(10, 100, 10)

    for axis in (0, 1, 2):
        matrices = mt.trans_nd(distances, axis=axis)
        assert matrices.shape == (distances.size, 4, 4)

        for i, d in enumerate(distances):
            print(matrices[i])

            assert np.allclose(matrices[i], mt.trans(d, axis=axis))
