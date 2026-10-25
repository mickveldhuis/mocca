import numpy as np
import numpy.typing as npt


def trans(t: float, axis: int = 0) -> npt.NDArray[np.double]:
    """
    Translate a vector along the x, y, or z axis.

    :param t: distance along the specified axis
    :param axis: axis (0, 1, or 2) along which to apply the translation
    :returns: a (4, 4) translation matrix
    """
    if axis >= 3:
        raise IndexError(
            f"axes {axis} out of range; either select axis 0, 1, or 2, corresponding to the x, y, or z axes"
        )

    mat = np.eye(4, dtype=np.double)
    mat[axis, 3] = t

    return mat


def trans_nd(
    distances: npt.NDArray[np.double], axis: int = 0
) -> npt.NDArray[np.double]:
    """
    Translate a vector by a set of distances along the x, y, or z axis.

    :param distances: distances along the specified axis
    :param axis: axis (0, 1, or 2) along which to apply the translation
    :returns: (..., 4, 4) translation matrices
    """
    if axis >= 3:
        raise IndexError(
            f"axes {axis} out of range; either select axis 0, 1, or 2, corresponding to the x, y, or z axes"
        )

    t = np.atleast_1d(distances)

    mat = np.zeros((*t.shape, 4, 4))
    mat[..., axis, 3] = t

    # Set all diagonal elements to one
    diag_idx = np.arange(4)
    mat[..., diag_idx, diag_idx] = 1.0

    return mat


def rot_x(angle: float) -> npt.NDArray[np.double]:
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


def rot_x_nd(angles: npt.NDArray[np.double]) -> npt.NDArray[np.double]:
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


def rot_y(angle: float) -> npt.NDArray[np.double]:
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


def rot_y_nd(angles: npt.NDArray[np.double]) -> npt.NDArray[np.double]:
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


def rot_z(angle: float) -> npt.NDArray[np.double]:
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


def rot_z_nd(angles: npt.NDArray[np.double]) -> npt.NDArray[np.double]:
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
