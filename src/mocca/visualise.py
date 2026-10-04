import matplotlib.pyplot as plt
import numpy as np


def plot_aperture_obstruction(
    ap_x: np.ndarray,
    ap_z: np.ndarray,
    is_blocked: np.ndarray,
    aperture_r: float,
    dome_az: float,
):
    """Plot the aperture w/ obstructed sample points."""
    percentage = is_blocked[is_blocked].size / is_blocked.size

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

    frame.set_ylim(-2 * aperture_r, 2 * aperture_r)
    frame.set_xlim(-2 * aperture_r, 2 * aperture_r)

    frame.set_title(f"Dome azimuth = {float(dome_az) % 360:.1f} deg", fontsize=18)

    frame.legend(fontsize=12, loc="lower right")
    fig.tight_layout()

    plt.show()
