import matplotlib.pyplot as plt


def plot_aperture_obstruction(ap_x, ap_z, is_blocked, aperture_r, dome_az):
    """Plot the aperture w/ obstructed sample points.

    Parameters
    ----------

    ap_x, ap_z: x, z coordinates of the sampled points
    is_blocked: boolean array of len(ap_x) signifying whether a point is obstructed
    aperture_r: radius of the aperture in meters
    dome_az: position of the dome (azimuth angle in deg)
    """
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
        label="{:.1%} Blocked".format(percentage),
    )
    frame.plot(
        ap_x[~is_blocked],
        ap_z[~is_blocked],
        ls="",
        marker="o",
        ms=3,
        color="black",
        label="{:.1%} Clear".format(1 - percentage),
    )

    frame.set_xlabel(r"$x$ (m)", fontsize=18)
    frame.set_ylabel(r"$z$ (m)", fontsize=18)
    frame.grid(ls="--", alpha=0.5)

    frame.set_ylim(-2 * aperture_r, 2 * aperture_r)
    frame.set_xlim(-2 * aperture_r, 2 * aperture_r)

    frame.set_title(
        "Dome azimuth = {:.1f} deg".format(float(dome_az) % 360), fontsize=18
    )

    frame.legend(fontsize=12, loc="lower right")
    fig.tight_layout()

    plt.show()
