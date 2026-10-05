import numpy as np


def sample_unit_disk(sample_rate, r_min: float = 0.0):
    """
    Equidistant disk sampling based on:
    http://www.holoborodko.com/pavel/2015/07/23/generating-equidistant-points-on-unit-disk/

    :param r_min: inner radius of the unit circle that's left unsampled
    :returns: an array of xy coordinate samples with shape (2, N)
    """
    if not 0 <= r_min < 1:
        raise ValueError("r_min should be between 0 and 1")

    radial_delta = 1 / sample_rate

    x = []
    y = []

    radii = np.linspace(r_min, 1, sample_rate)
    k = np.ceil(r_min * (sample_rate + 1))  # angular sampling density

    if np.isclose(r_min, 0.0):
        x.append(0)
        y.append(0)

        radii = np.linspace(radial_delta, 1, sample_rate)
        k = 1

    for r in radii:
        n_angular_samples = int(np.round(np.pi / np.arcsin(1 / (2 * k))))
        print(f"n = {n_angular_samples}")

        theta = np.linspace(0, 2 * np.pi, n_angular_samples + 1)
        x_r = r * np.cos(theta)
        y_r = r * np.sin(theta)

        x.extend(x_r)
        y.extend(y_r)

        k += 1

    return np.stack([np.array(x), np.array(y)])
