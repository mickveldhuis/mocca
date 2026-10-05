import numpy as np


def sample_unit_disk(sample_rate, r_min: float = 0):
    """
    Equidistant disk sampling based on:
    http://www.holoborodko.com/pavel/2015/07/23/generating-equidistant-points-on-unit-disk/

    :param r_min: inner radius of the unit circle that's left unsampled
    :returns: an array of xy coordinate samples with shape (N, 2)
    """
    if not 0 <= r_min < 1:
        raise ValueError("r_min should be between 0 and 1...")

    radial_delta = 1 / sample_rate

    x = np.empty(0)
    y = np.empty(0)

    radii = np.linspace(r_min, 1, sample_rate)
    k = np.ceil(r_min * (sample_rate + 1))

    if not r_min:
        x = np.concatenate([x, [0]])
        y = np.concatenate([y, [0]])

        radii = np.linspace(radial_delta, 1, sample_rate)
        k = 1

    for r in radii:
        n = int(np.round(np.pi / np.arcsin(1 / (2 * k))))

        theta = np.linspace(0, 2 * np.pi, n + 1)

        x_r = r * np.cos(theta)
        y_r = r * np.sin(theta)

        x = np.concatenate([x, x_r])
        y = np.concatenate([y, y_r])

        k += 1

    return np.column_stack([x, y])
