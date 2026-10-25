import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib.ticker import PercentFormatter

from mocca.aperture import Aperture
from mocca.utils import sample_unit_disk


def plot_aperture_obstruction(
    aperture: Aperture,
    is_blocked: npt.NDArray[np.double],
    dome_az: float,
) -> None:
    """Plot the aperture w/ obstructed sample points."""
    percentage = is_blocked[is_blocked].size / is_blocked.size

    # Resample the disk representing the aperture
    inner_blocked_radius = aperture.sec_radius / aperture.radius
    unit_disk = sample_unit_disk(aperture.sample_rate, r_min=inner_blocked_radius)
    disk = aperture.radius * unit_disk
    ap_x = disk[0]
    ap_z = disk[1]

    fig = plt.figure(figsize=(4.5, 4.5), num="MOCCA - Visualisation")
    frame = fig.add_subplot(1, 1, 1)

    frame.plot(
        ap_x[is_blocked],
        ap_z[is_blocked],
        ls="",
        marker="^",
        ms=3,
        color="green",
        label=f"{percentage:.1%} Blocked",
    )
    frame.plot(
        ap_x[~is_blocked],
        ap_z[~is_blocked],
        ls="",
        marker="o",
        ms=3,
        color="black",
        label=f"{1 - percentage:.1%} Clear",
    )

    frame.set_xlabel(r"$x$ (m)", fontsize=18)
    frame.set_ylabel(r"$z$ (m)", fontsize=18)
    frame.grid(ls="--", alpha=0.5)

    frame.set_ylim(-2 * aperture.radius, 2 * aperture.radius)
    frame.set_xlim(-2 * aperture.radius, 2 * aperture.radius)

    frame.set_title(f"Dome azimuth = {float(dome_az) % 360:.1f} deg", fontsize=18)

    frame.legend(fontsize=12, loc="lower right")

    frame.set_aspect("equal")

    fig.tight_layout()

    plt.show()


def plot_batch_obstruction(
    ratios: npt.NDArray[np.double], azimuths: npt.NDArray[np.double]
):
    """Display the aperture obstruction for the sampled azimuth angles on a polar graph."""
    fig = plt.figure(figsize=(5, 5), num="MOCCA - Batch Visualisation")
    frame = fig.add_subplot(1, 1, 1, polar=True)

    az = np.radians(azimuths)
    frame.plot(az, ratios, ls="", marker="*", ms=6, color="black")

    az_closed = np.concatenate([az, [az[-1], az[0]]])
    r_closed = np.concatenate([ratios, [0, 0]])
    frame.fill(
        az_closed,
        r_closed,
        alpha=0.2,
        color="red",
    )

    r_min = 0.0
    r_max = 1.2
    frame.set_rlim(r_min, r_max)
    frame.set_rlabel_position(90)

    frame.set_rticks(np.arange(r_min, r_max, 0.2))
    frame.yaxis.set_major_formatter(PercentFormatter(1))  # Note: y axis == r axis

    frame.grid(True)
    frame.set_aspect("equal")
    fig.tight_layout()

    plt.show()
