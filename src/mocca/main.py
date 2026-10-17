import argparse
import logging
from pathlib import Path

import numpy as np

from mocca.aperture import Aperture, create_aperture
from mocca.obstruction import batch_calculate_obstruction, calculate_obstruction
from mocca.types import DomeInfo, TelescopeInfo
from mocca.visualise import plot_aperture_obstruction

logger = logging.getLogger("MOCCA")


MOCCA_CONFIG = "mocca.toml"


def load_or_create_config(config_filename: str | None) -> Path:
    if config_filename:
        user_config = Path(config_filename).resolve()

        if not user_config.exists():
            raise FileNotFoundError(
                f"the provided MOCCA configuration file {user_config} does not exist"
            )

        return user_config

    # If the user didn't specify a configuration file, look in the current
    # working directory, and create one if it doesn't exist.
    user_config = Path.cwd() / MOCCA_CONFIG

    if not user_config.exists():
        logger.warning(
            "%s not found in the current working directory; creating one at: %s",
            MOCCA_CONFIG,
            user_config,
        )

        default_config = Path(__file__).parent / MOCCA_CONFIG
        default_config.copy(user_config)

        # Check again whether the copying is succesful
        if not user_config.exists():
            raise OSError(f"could not copy {default_config} to {user_config}")

    return user_config


def parse_cli_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Compute the fractional obstruction of a telescope by a hemispherical dome. The telescope should be affixed to an equatorial mount.",
    )

    def azimuth(value):
        az = float(value)
        if az < 0.0 or az > 360.0:
            raise argparse.ArgumentTypeError(
                "invalid azimuth: expecting a value on the following interval [0, 360) deg"
            )

        return az

    def hour_angle(value):
        ha = float(value)
        if ha < 0.0 or ha >= 24.0:
            raise argparse.ArgumentTypeError(
                "invalid hour angle: expecting a value on the following interval [0, 24) h"
            )

        # Convert to degrees for further processing
        return 15.0 * ha

    def declination(value):
        dec = float(value)
        if dec < -90.0 or dec > 90.0:
            raise argparse.ArgumentTypeError(
                "invalid declination: expecting a value on the following interval [-90, 90] deg"
            )

        return dec

    def positive_integer(value):
        val = int(value)
        if val < 0:
            raise argparse.ArgumentTypeError(
                "invalid value: expecting a positive integer"
            )

        return val

    parser.add_argument(
        "--az", type=azimuth, default=0.0, help="dome azimuth: 0 to 360 deg"
    )
    parser.add_argument(
        "--az-range", type=azimuth, nargs=3, help="dome azimuth: 0 to 360 deg"
    )
    parser.add_argument(
        "--ha", type=hour_angle, default=0.0, help="telescope hour angle: 0 to 24 h"
    )
    parser.add_argument(
        "--dec",
        type=declination,
        default=0.0,
        help="telescope declination -90 to 90 deg",
    )
    parser.add_argument(
        "-a",
        "--aperture",
        type=str,
        choices=["telescope", "guider", "finder"],
        default="telescope",
        help="telescope aperture for which to calculate the obstruction",
    )
    parser.add_argument(
        "-r",
        "--rate",
        type=positive_integer,
        default=4,
        help="number of radial circles of rays",
    )
    parser.add_argument(
        "-v",
        "--visualise",
        action="store_true",
        help="visualise the blocked rays inside of the circular aperture",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="configuration file with the telescope and dome configuration",
    )

    return parser.parse_args()


def process_single_azimuth(
    ha: float,
    dec: float,
    az: float,
    aperture: Aperture,
    dome: DomeInfo,
    aperture_name: str,
    visualise: bool = False,
):
    """
    Calculate the obstruction for a single dome orientation and telescope pointing, and optionally plot the results.

    :param ha: telescope hour angle (deg)
    :param dec: telescope declination (deg)
    :param az: dome orientation angle (deg)
    :param aperture: aperture configuration
    :param dome: dome properties
    :param visualise: enable plotting the aperture obstruction
    """
    blockage, blocked_rays = calculate_obstruction(ha, dec, az, aperture, dome)

    if blockage is not None:
        logger.info("%s aperture obstruction = %.3f", aperture_name, blockage)
    else:
        raise RuntimeError("The fractional obstruction could not be computed")

    if visualise:
        plot_aperture_obstruction(aperture, blocked_rays, az)


def process_batch(
    ha: float,
    dec: float,
    az_values: np.ndarray,
    aperture: Aperture,
    dome: DomeInfo,
    aperture_name: str,
    visualise: bool = False,
):
    """
    Calculate the obstruction for a multiple dome orientation given as single telescope pointing.

    :param ha: telescope hour angle (deg)
    :param dec: telescope declination (deg)
    :param az_values: list of dome orientations (deg)
    :param aperture: aperture configuration
    :param dome: dome properties
    """
    batch_result = batch_calculate_obstruction(ha, dec, az_values, aperture, dome)

    # Display the number of unobstructed dome orientations
    is_obstructed = np.isclose(batch_result.ratios, 1.0)

    n_azimuths = batch_result.ratios.size
    n_obstructed = is_obstructed.sum()

    logger.info(
        "%s aperture obstructed for %i / %i sampled dome positions",
        aperture_name,
        n_obstructed,
        n_azimuths,
    )


def main():
    # Configure the logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
    )

    # Parse CLI arguments
    args = parse_cli_arguments()

    # Load the telescope-dome configuration from the provided TOML file
    config_path = load_or_create_config(args.config)

    logger.info("loading telescope and dome parameters from %s", config_path.resolve())
    telescope_info = TelescopeInfo.from_file(config_path)
    dome_info = DomeInfo.from_file(config_path)

    # Compute and (optionally) visualise the obstruction
    aperture = create_aperture(args.aperture, args.rate, telescope_info)

    if args.az_range:
        start, end, step = args.az_range
        if step <= 0.0 or end <= start:
            raise ValueError(
                f"azimuth range [{start}, {end}) with step size {step} is invalid"
            )

        azimuths = np.arange(start, end, step)
        process_batch(args.ha, args.dec, azimuths, aperture, dome_info, args.aperture)
    else:
        process_single_azimuth(
            args.ha,
            args.dec,
            args.az,
            aperture,
            dome_info,
            args.aperture,
            visualise=args.visualise,
        )
