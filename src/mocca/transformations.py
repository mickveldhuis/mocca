import numpy as np
import numpy.typing as npt


def translation(x: float, y: float, z: float) -> np.ndarray:
    """
    Translate a vector (x', y', z', 1) by x,
    y, and z along their respective axes.
    """
    return np.array(
        [
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1],
        ]
    )


def rot_x(angle: float) -> np.ndarray:
    """
    Rotate a vector (x, y, z, 1) about the x-axis
    in a right-handed coordinate system.
    """
    angle = np.radians(angle)

    return np.array(
        [
            [1, 0, 0, 0],
            [0, np.cos(angle), -np.sin(angle), 0],
            [0, np.sin(angle), np.cos(angle), 0],
            [0, 0, 0, 1],
        ]
    )


def rot_x_nd(angles: npt.NDArray[np.double]):
    """
    Rotate a vector (x, y, z, 1) about the x-axis
    in a right-handed coordinate system.

    :param angles: N-dim array of angles in degrees
    :returns: (..., 4, 4) array of 4x4 transformation matrices
    """
    a = np.atleast_1d(np.radians(angles))
    c, s = np.cos(a), np.sin(a)

    mat = np.zeros((*a.shape, 4, 4))
    mat[..., 1, 1], mat[..., 1, 2] = c, -s
    mat[..., 2, 1], mat[..., 2, 2] = s, c
    mat[..., 0, 0] = mat[..., 3, 3] = 1.0

    return mat


def rot_y(angle: float) -> np.ndarray:
    """
    Rotate a vector (x, y, z, 1) about the y-axis
    in a right-handed coordinate system.
    """
    angle = np.radians(angle)

    return np.array(
        [
            [np.cos(angle), 0, np.sin(angle), 0],
            [0, 1, 0, 0],
            [-np.sin(angle), 0, np.cos(angle), 0],
            [0, 0, 0, 1],
        ]
    )


def rot_y_nd(angles: npt.NDArray[np.double]):
    """
    Rotate a vector (x, y, z, 1) about the y-axis
    in a right-handed coordinate system.

    :param angles: N-dim array of angles in degrees
    :returns: (..., 4, 4) array of 4x4 transformation matrices
    """
    a = np.atleast_1d(np.radians(angles))
    c, s = np.cos(a), np.sin(a)

    mat = np.zeros((*a.shape, 4, 4))
    mat[..., 0, 0], mat[..., 0, 2] = c, s
    mat[..., 2, 0], mat[..., 2, 2] = -s, c
    mat[..., 1, 1] = mat[..., 3, 3] = 1.0

    return mat


def rot_z(angle: float) -> np.ndarray:
    """
    Rotate a vector (x, y, z, 1) about the z-axis
    in a right-handed coordinate system.
    """
    angle = np.radians(angle)

    return np.array(
        [
            [np.cos(angle), -np.sin(angle), 0, 0],
            [np.sin(angle), np.cos(angle), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )


def rot_z_nd(angles: npt.NDArray[np.double]):
    """
    Rotate a vector (x, y, z, 1) about the z-axis
    in a right-handed coordinate system.

    :param angles: N-dim array of angles in degrees
    :returns: (..., 4, 4) array of 4x4 transformation matrices
    """
    a = np.atleast_1d(np.radians(angles))
    c, s = np.cos(a), np.sin(a)

    mat = np.zeros((a.size, 4, 4))
    mat[..., 0, 0], mat[..., 0, 1] = c, -s
    mat[..., 1, 0], mat[..., 1, 1] = s, c
    mat[..., 2, 2] = mat[..., 3, 3] = 1.0

    return mat
